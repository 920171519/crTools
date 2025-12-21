"""
设备管理路由
提供设备的增删改查、使用管理等API接口
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from datetime import datetime, timezone
import traceback
from pydantic import BaseModel

from models.deviceModel import (
    Device,
    DeviceUsage,
    DeviceInternal,
    DeviceUsageHistory,
    DeviceConfig,
    DeviceStatusEnum,
    DeviceShareRequest,
    DeviceAccessIP
)
from models.admin import User, OperationLog
from models.vpnModel import VPNConfig, UserVPNConfig
from models.groupModel import Group, GroupMember, DeviceGroup
from schemas import (
    DeviceBase,
    DeviceUpdate,
    DeviceResponse,
    DeviceListItem,
    DeviceUsageResponse,
    DeviceUsageUpdate,
    DeviceUseRequest,
    DeviceLongTermUseRequest,
    DeviceReleaseRequest,
    DevicePreemptRequest,
    DevicePriorityQueueRequest,
    DeviceUnifiedQueueRequest,
    DeviceConfigCreate,
    DeviceConfigUpdate,
    DeviceConfigResponse,
    DeviceShareRequestCreate,
    DeviceForceShareRequest,
    DeviceShareDecision,
    DeviceShareRequestResponse,
    MyUsageSummaryResponse,
    MyUsageDeviceSummary
)
from schemas import BaseResponse
from auth import AuthManager
from connectivity_manager import connectivity_manager
from scheduler.scheduler import device_scheduler
from utils.notification import send_device_notification

router = APIRouter(prefix="/api/devices", tags=["设备管理"])


def get_current_time():
    """获取当前时间，统一使用naive datetime"""
    return datetime.now()


def normalize_employee_id(employee_id: Optional[str]) -> Optional[str]:
    """工号统一小写处理"""
    if isinstance(employee_id, str):
        return employee_id.lower()
    return employee_id


def resolve_request_user(user_input: Optional[str], fallback_user: User) -> str:
    """获取请求中的工号（优先使用请求参数，其次当前用户），统一小写"""
    normalized_input = normalize_employee_id(user_input)
    if normalized_input:
        return normalized_input
    return normalize_employee_id(fallback_user.employee_id) or fallback_user.employee_id


async def get_user_group_ids(user: User) -> Optional[set]:
    """获取用户所属分组ID集合"""
    if user.is_superuser:
        return None
    group_ids = await GroupMember.filter(user_id=user.id).values_list('group_id', flat=True)
    return set(group_ids)


async def user_has_device_access(device: Device, user: User, user_group_ids: Optional[set] = None) -> bool:
    """判断用户是否可以访问设备"""
    if user.is_superuser:
        return True
    device_group_ids = await DeviceGroup.filter(device=device).values_list('group_id', flat=True)
    if not device_group_ids:
        return True  # 未绑定分组的设备对所有人可见
    if user_group_ids is None:
        user_group_ids = await get_user_group_ids(user) or set()
    return bool(user_group_ids and set(device_group_ids) & user_group_ids)


async def ensure_device_access(device: Device, user: User, user_group_ids: Optional[set] = None):
    """确保用户有权限访问设备"""
    has_access = await user_has_device_access(device, user, user_group_ids)
    if not has_access:
        raise HTTPException(status_code=403, detail="您无权访问该设备")


async def ensure_user_vpn_ip(device: Device, user: User):
    """确保用户已录入设备所需VPN的IP地址"""
    if not device.vpn_config_id:
        return

    vpn_config = await device.vpn_config
    if not vpn_config:
        return

    user_vpn = await UserVPNConfig.filter(user_id=user.id, vpn_config_id=vpn_config.id).first()
    if not user_vpn or not user_vpn.ip_address:
        vpn_name = f"{vpn_config.region}-{vpn_config.network}"
        raise HTTPException(
            status_code=400,
            detail=f"请先前往个人中心录入 {vpn_name} 的VPN IP地址后再进行设备操作"
        )


async def revoke_shared_access(device: Device, actor: Optional[User] = None, reason: str = "device_state_changed"):
    """占用人变化或释放时撤销已审批的共用"""
    now = get_current_time()
    actor_employee = actor.employee_id if actor else None
    await DeviceShareRequest.filter(device=device, status="approved").update(
        status="revoked",
        processed_by=actor_employee,
        processed_at=now,
        decision_reason=reason
    )
    # 清理已审批共用用户的访问IP记录
    approved_users = await DeviceShareRequest.filter(device=device, status="revoked").values_list("requester_employee_id", flat=True)
    for emp in approved_users:
        await delete_device_access_ip(device, emp, role="shared")


async def get_device_shared_users(device: Device):
    """获取当前已审批的共用用户"""
    share_requests = await DeviceShareRequest.filter(device=device, status="approved").order_by("processed_at")
    result = []
    for share in share_requests:
        # 返回本地时间字符串，避免前端解析ISO字符串被当作UTC导致+8小时偏移
        approved_at = None
        if share.processed_at:
            try:
                approved_at = share.processed_at.strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                approved_at = share.processed_at.isoformat()
        result.append({
            "share_request_id": share.id,
            "employee_id": share.requester_employee_id,
            "username": share.requester_username,
            "approved_at": approved_at,
            "request_message": share.request_message
        })
    return result


@router.post("/{device_id:int}/force-share", response_model=BaseResponse, summary="强制加入共用")
async def force_share_device(
    device_id: int,
    payload: DeviceForceShareRequest,
    current_user: User = Depends(AuthManager.get_current_user),
):
    """将当前用户强制加入设备共用列表，并记录备注信息"""
    device = await Device.filter(id=device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    await ensure_device_access(device, current_user)
    await ensure_user_vpn_ip(device, current_user)

    usage_info = await DeviceUsage.filter(device=device).first()
    if not usage_info or usage_info.status not in [DeviceStatusEnum.OCCUPIED, DeviceStatusEnum.LONG_TERM_OCCUPIED]:
        raise HTTPException(status_code=400, detail="设备当前未被占用，无需强制共用")

    normalized_employee = normalize_employee_id(current_user.employee_id)
    if usage_info.current_user and normalize_employee_id(usage_info.current_user) == normalized_employee:
        raise HTTPException(status_code=400, detail="您已是当前占用人，无需强制共用")

    # 若已存在待处理/已通过记录，则直接更新为已通过并写入备注
    share_request = await DeviceShareRequest.filter(
        device=device,
        requester_employee_id__iexact=normalized_employee,
        status__in=["pending", "approved"]
    ).first()

    now = get_current_time()
    if share_request:
        share_request.status = "approved"
        share_request.request_message = payload.message
        share_request.processed_by = current_user.employee_id
        share_request.processed_at = now
        share_request.decision_reason = "强制共用"
        await share_request.save()
    else:
        share_request = await DeviceShareRequest.create(
            device=device,
            requester_employee_id=normalized_employee,
            requester_username=current_user.username,
            status="approved",
            request_message=payload.message,
            processed_by=current_user.employee_id,
            processed_at=now,
            decision_reason="强制共用"
        )

    # 同步访问IP记录（共用用户）
    try:
        await upsert_device_access_ip(device, current_user, role="shared")
    except Exception as e:
        print(f"强制共用同步访问IP失败: {e}")

    await OperationLog.create_log(
        user=current_user,
        operation_type="device_force_share",
        operation_result="success",
        device_name=device.name,
        description=f"强制共用设备 {device.name}",
        device_ip=device.ip
    )

    return BaseResponse(
        code=200,
        message="已强制加入共用",
        data=serialize_share_request_record(share_request)
    )


async def get_user_vpn_ip_for_device(user: User, device: Device) -> str | None:
    """获取用户在设备所需VPN下的IP地址"""
    if not device.vpn_config_id:
        return None
    uvpn = await UserVPNConfig.filter(user_id=user.id, vpn_config_id=device.vpn_config_id).first()
    return uvpn.ip_address if uvpn else None


async def upsert_device_access_ip(device: Device, user: User, role: str):
    """创建或更新设备访问IP记录"""
    ip = await get_user_vpn_ip_for_device(user, device)
    # 以 device + employee 唯一
    existing = await DeviceAccessIP.filter(device=device, employee_id=user.employee_id).first()
    if existing:
        existing.username = user.username
        existing.vpn_ip = ip
        existing.role = role
        await existing.save()
    else:
        await DeviceAccessIP.create(
            device=device,
            employee_id=user.employee_id,
            username=user.username,
            role=role,
            vpn_ip=ip
        )


async def delete_device_access_ip(device: Device, employee_id: str, role: str | None = None):
    """删除指定用户的访问IP记录"""
    q = DeviceAccessIP.filter(device=device, employee_id__iexact=employee_id)
    if role:
        q = q.filter(role=role)
    await q.delete()


async def clear_role_access(device: Device, role: str):
    await DeviceAccessIP.filter(device=device, role=role).delete()


async def fetch_user_share_status(device_ids: List[int], employee_id: str):
    """批量获取当前用户在各设备上的共用状态"""
    if not device_ids:
        return {}
    records = await DeviceShareRequest.filter(
        device_id__in=device_ids,
        requester_employee_id__iexact=employee_id,
        status__in=["pending", "approved"]
    ).values("device_id", "status", "id")
    status_map = {}
    for record in records:
        status_map[record["device_id"]] = {
            "status": record["status"],
            "id": record["id"]
        }
    return status_map


def serialize_share_request_record(share_request: DeviceShareRequest) -> dict:
    """序列化共用申请"""
    device_name = ""
    if hasattr(share_request, "device") and share_request.device:
        device_name = share_request.device.name
    return {
        "id": share_request.id,
        "device_id": share_request.device_id,
        "device_name": device_name,
        "requester_employee_id": share_request.requester_employee_id,
        "requester_username": share_request.requester_username,
        "status": share_request.status,
        "request_message": share_request.request_message,
        "decision_reason": share_request.decision_reason,
        "processed_by": share_request.processed_by,
        "processed_at": share_request.processed_at.isoformat() if share_request.processed_at else None,
        "created_at": share_request.created_at.isoformat() if share_request.created_at else None
    }


def serialize_group_links(device) -> List[dict]:
    """将设备的分组信息序列化"""
    groups = []
    if hasattr(device, "group_links"):
        group_links = device.group_links
    else:
        group_links = []
    for link in group_links or []:
        if link.group:
            groups.append({
                "id": link.group.id,
                "name": link.group.name,
                "description": link.group.description
            })
    return groups


async def sync_device_groups(device: Device, group_ids: Optional[List[int]]):
    """同步设备的分组关联"""
    if group_ids is None:
        return
    group_ids = list(set(group_ids))
    if not group_ids:
        await DeviceGroup.filter(device=device).delete()
        return

    valid_groups = await Group.filter(id__in=group_ids)
    valid_ids = {group.id for group in valid_groups}
    if not valid_ids:
        await DeviceGroup.filter(device=device).delete()
        return

    # 删除不在列表中的关联
    await DeviceGroup.filter(device=device).exclude(group_id__in=valid_ids).delete()

    # 新增缺失的关联
    existing_ids = set(await DeviceGroup.filter(device=device).values_list('group_id', flat=True))
    for group_id in valid_ids - existing_ids:
        group = next((g for g in valid_groups if g.id == group_id), None)
        if group:
            await DeviceGroup.create(device=device, group=group)


@router.get("/", response_model=BaseResponse, summary="获取设备列表")
async def get_devices(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=1000, description="每页数量"),
    name: Optional[str] = Query(None, description="环境名称搜索"),
    ip: Optional[str] = Query(None, description="环境IP搜索"),
    status: Optional[str] = Query(None, description="环境状态搜索"),
    config_value: Optional[str] = Query(None, description="配置值搜索"),
    current_user: User = Depends(AuthManager.get_current_user)
):
    """
    获取设备列表
    - 支持分页
    - 支持按环境名称、IP、状态搜索
    """
    # 构建查询条件，预取分组信息
    query = Device.all().prefetch_related(
        "usage_info", "vpn_config", "group_links__group")

    if name:
        query = query.filter(name__icontains=name)
    if ip:
        query = query.filter(ip__icontains=ip)
    if config_value:
        config_device_ids = await DeviceConfig.filter(
            config_value__icontains=config_value
        ).values_list("device_id", flat=True)
        device_id_set = set(config_device_ids)
        if not device_id_set:
            return BaseResponse(
                code=200,
                message="设备列表获取成功",
                data={
                    "items": [],
                    "total": 0,
                    "page": page,
                    "page_size": page_size
                }
            )
        query = query.filter(id__in=list(device_id_set))

    # 获取所有设备用于过滤
    all_devices = await query

    user_group_ids = await get_user_group_ids(current_user)
    filtered_devices = []

    for device in all_devices:
        usage_info = getattr(device, 'usage_info', None)
        if usage_info is None:
            # 通过查询获取最新的使用信息，避免OneToOne未创建导致的异常
            usage_info = await DeviceUsage.filter(device=device).first()
        if usage_info is None:
            usage_info = await DeviceUsage.create(device=device)

        # 状态过滤
        if status and usage_info.status != status:
            continue

        # 分组权限过滤：未绑定分组默认可见
        device_group_ids = set()
        for link in getattr(device, "group_links", []) or []:
            if link.group_id:
                device_group_ids.add(link.group_id)

        if device_group_ids and user_group_ids is not None and not (device_group_ids & user_group_ids):
            continue

        filtered_devices.append((device, usage_info))

    # 分页
    total = len(filtered_devices)
    offset = (page - 1) * page_size
    paged_devices = filtered_devices[offset:offset + page_size]

    device_ids = [device.id for device, _ in paged_devices]
    normalized_employee = normalize_employee_id(current_user.employee_id)
    user_share_status = await fetch_user_share_status(device_ids, normalized_employee)

    result = []
    for device, usage_info in paged_devices:

        # 计算占用时长（精确到秒，但以分钟为单位显示）
        occupied_duration = 0
        if usage_info.start_time and usage_info.current_user:
            # 统一使用naive datetime进行计算
            current_time = get_current_time()
            # 如果数据库中的时间是aware的，转换为naive
            start_time = usage_info.start_time.replace(
                tzinfo=None) if usage_info.start_time.tzinfo else usage_info.start_time
            duration = current_time - start_time
            # 改为向上取整，确保即使不到1分钟也显示为1分钟
            occupied_duration = max(
                1, int((duration.total_seconds() + 59) / 60))

        # 检查当前用户是否在排队中
        is_current_user_in_queue = False
        if usage_info.queue_users:
            normalized_queue = [normalize_employee_id(
                u) for u in usage_info.queue_users]
            if normalized_employee in normalized_queue:
                is_current_user_in_queue = True

        # 获取VPN配置信息
        vpn_region = None
        vpn_network = None
        vpn_display_name = None
        if hasattr(device, 'vpn_config') and device.vpn_config:
            vpn_region = device.vpn_config.region
            vpn_network = device.vpn_config.network
            vpn_display_name = f"{vpn_region} - {vpn_network}"
        elif device.required_vpn_display:
            vpn_display_name = device.required_vpn_display

        share_info = user_share_status.get(device.id) or {}

        result.append(DeviceListItem(
            id=device.id,
            name=device.name,
            ip=device.ip,
            device_type=device.device_type,
            form_type=device.form_type,
            vpn_region=vpn_region,
            vpn_network=vpn_network,
            vpn_display_name=vpn_display_name,
            current_user=usage_info.current_user,
            queue_count=len(
                usage_info.queue_users) if usage_info.queue_users else 0,
            status=usage_info.status,
            start_time=usage_info.start_time,
            occupied_duration=occupied_duration,
            is_current_user_in_queue=is_current_user_in_queue,
            connectivity_status=device.connectivity_status,
            admin_username=device.admin_username,
            project_name=device.owner,  # 使用owner作为project_name
            support_queue=device.support_queue,
            groups=serialize_group_links(device),
            is_shared_user=share_info.get("status") == "approved",
            has_pending_share_request=share_info.get("status") == "pending",
            share_request_id=share_info.get("id"),
            share_status=share_info.get("status")
        ))

    return BaseResponse(
        code=200,
        message="设备列表获取成功",
        data={
            "items": result,
            "total": total,
            "page": page,
            "page_size": page_size
        }
    )


@router.post("/", response_model=BaseResponse, summary="创建设备")
async def create_device(device_data: DeviceBase, current_user: User = Depends(AuthManager.get_current_user)):
    """创建新设备"""
    try:
        print(f"收到设备创建请求: {device_data}")
    except Exception as e:
        print(f"打印设备数据时出错: {e}")
    try:
        # 检查IP是否已存在
        print(f"检查IP是否已存在: {device_data.ip}")
        existing_device = await Device.filter(ip=device_data.ip).first()
        if existing_device:
            print(f"IP地址已存在: {device_data.ip}")
            raise HTTPException(status_code=400, detail="该IP地址已存在")

        # 验证VPN配置是否存在
        vpn_config = None
        vpn_display_name = None
        if device_data.vpn_config_id:
            print(f"查找VPN配置: {device_data.vpn_config_id}")
            vpn_config = await VPNConfig.filter(id=device_data.vpn_config_id).first()
            if not vpn_config:
                print(f"VPN配置不存在: {device_data.vpn_config_id}")
                raise HTTPException(status_code=400, detail="指定的VPN配置不存在")
            vpn_display_name = f"{vpn_config.region} - {vpn_config.network}"
            print(f"找到VPN配置: {vpn_display_name}")

        # 准备设备数据
        print("准备设备数据...")
        device_dict = device_data.model_dump()
        group_ids = device_dict.pop('group_ids', None)
        # 移除vpn_config_id，因为我们要设置vpn_config对象
        device_dict.pop('vpn_config_id', None)
        print(f"设备数据: {device_dict}")

        # 创建设备
        print("开始创建设备...")
        device = await Device.create(
            vpn_config=vpn_config,
            required_vpn_display=vpn_display_name,
            **device_dict
        )
        print(f"设备创建成功: {device.id}")

        # 同步分组
        await sync_device_groups(device, group_ids)
        await device.fetch_related("group_links__group")
    except Exception as e:
        print(f"创建设备时出错: {e}")
        print(f"错误类型: {type(e)}")
        print(f"错误堆栈: {traceback.format_exc()}")
        raise

    # 创建设备使用情况记录
    await DeviceUsage.create(device=device)

    # 创建设备内部信息记录
    internal_info = await DeviceInternal.create(device=device)
    internal_info.init_ports()
    await internal_info.save()

    # 构建响应数据
    device_response = {
        "id": device.id,
        "name": device.name,
        "ip": device.ip,
        "vpn_config_id": device.vpn_config.id if device.vpn_config else None,
        "vpn_region": device.vpn_config.region if device.vpn_config else None,
        "vpn_network": device.vpn_config.network if device.vpn_config else None,
        "vpn_display_name": vpn_display_name,
        "creator": device.creator,
        "ftp_prefix": device.ftp_prefix,
        "max_occupy_minutes": device.max_occupy_minutes,
        "support_queue": device.support_queue,
        "owner": device.owner,
        "device_type": device.device_type,
        "form_type": device.form_type,
        "remarks": device.remarks,
        "groups": serialize_group_links(device),
        "created_at": device.created_at,
        "updated_at": device.updated_at
    }

    return BaseResponse(
        code=200,
        message="设备创建成功",
        data=device_response
    )


@router.get("/connectivity-status", response_model=BaseResponse, summary="获取设备连通性状态")
async def get_devices_connectivity_status(
    device_ids: str = Query(..., description="设备ID列表，用逗号分隔"),
    current_user: User = Depends(AuthManager.get_current_user)
):
    """
    批量获取设备连通性状态
    - device_ids: 设备ID列表，用逗号分隔，如 "1,2,3"
    """
    try:
        # 解析设备ID列表
        device_id_list = [int(id.strip())
                          for id in device_ids.split(',') if id.strip()]

        if not device_id_list:
            raise HTTPException(status_code=400, detail="设备ID列表不能为空")

        # 验证设备是否存在
        existing_devices = await Device.filter(id__in=device_id_list).prefetch_related("group_links__group")
        existing_device_ids = {device.id for device in existing_devices}
        accessible_device_ids = set()
        user_group_ids = await get_user_group_ids(current_user)
        for device in existing_devices:
            device_group_ids = {link.group_id for link in getattr(
                device, "group_links", []) or [] if link.group_id}
            if device_group_ids and user_group_ids is not None and not (device_group_ids & user_group_ids):
                continue
            accessible_device_ids.add(device.id)

        # 获取连通性状态
        connectivity_results = await connectivity_manager.get_multiple_connectivity_status(device_id_list)

        # 格式化返回结果
        results = {}
        for device_id in device_id_list:
            if device_id not in existing_device_ids:
                results[device_id] = {
                    "status": False,
                    "last_check": None,
                    "last_ping": None,
                    "error": "设备不存在"
                }
            elif device_id not in accessible_device_ids:
                results[device_id] = {
                    "status": False,
                    "last_check": None,
                    "last_ping": None,
                    "error": "无权访问该设备"
                }
            elif device_id in connectivity_results:
                connectivity_data = connectivity_results[device_id]
                results[device_id] = {
                    "status": connectivity_data["status"],
                    "last_check": connectivity_data["last_check"].isoformat() if connectivity_data.get("last_check") else None,
                    "last_ping": connectivity_data["last_ping"].isoformat() if connectivity_data.get("last_ping") else None
                }
            else:
                results[device_id] = {
                    "status": False,
                    "last_check": None,
                    "last_ping": None
                }

        return BaseResponse(
            code=200,
            message="连通性状态获取成功",
            data=results
        )

    except ValueError:
        raise HTTPException(status_code=400, detail="设备ID格式错误")
    except Exception as e:
        print(f"获取连通性状态失败: {e}")
        raise HTTPException(status_code=500, detail="获取连通性状态失败")


@router.get("/connectivity-cache-info", response_model=BaseResponse, summary="获取连通性缓存信息")
async def get_connectivity_cache_info(current_user: User = Depends(AuthManager.get_current_user)):
    """获取连通性缓存信息（调试用）"""
    # 检查管理员权限
    is_admin = (current_user.is_superuser or
                await current_user.has_role("管理员"))
    if not is_admin:
        raise HTTPException(status_code=403, detail="权限不足，只有管理员可以查看缓存信息")

    cache_info = connectivity_manager.get_cache_info()

    return BaseResponse(
        code=200,
        message="缓存信息获取成功",
        data=cache_info
    )


@router.get("/{device_id:int}", response_model=BaseResponse, summary="获取设备详情")
async def get_device(device_id: int, current_user: User = Depends(AuthManager.get_current_user)):
    """根据ID获取设备详情"""
    device = await Device.filter(id=device_id).prefetch_related("vpn_config", "group_links__group").first()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")

    await ensure_device_access(device, current_user)

    # 获取VPN配置信息
    vpn_config_id = None
    vpn_region = None
    vpn_network = None
    vpn_display_name = None

    if device.vpn_config:
        vpn_config_id = device.vpn_config.id
        vpn_region = device.vpn_config.region
        vpn_network = device.vpn_config.network
        vpn_display_name = f"{vpn_region} - {vpn_network}"
    elif device.required_vpn_display:
        vpn_display_name = device.required_vpn_display

    device_data = {
        "id": device.id,
        "name": device.name,
        "ip": device.ip,
        "vpn_config_id": vpn_config_id,
        "vpn_region": vpn_region,
        "vpn_network": vpn_network,
        "vpn_display_name": vpn_display_name,
        "creator": device.creator,
        "ftp_prefix": device.ftp_prefix,
        "support_queue": device.support_queue,
        "max_occupy_minutes": device.max_occupy_minutes,
        "owner": device.owner,
        "admin_username": device.admin_username,
        "admin_password": device.admin_password,
        "device_type": device.device_type,
        "form_type": device.form_type,
        "remarks": device.remarks,
        "groups": serialize_group_links(device),
        "created_at": device.created_at,
        "updated_at": device.updated_at
    }

    return BaseResponse(
        code=200,
        message="设备详情获取成功",
        data=device_data
    )


@router.get("/{device_id:int}/connectivity", response_model=BaseResponse, summary="获取单个设备连通性状态")
async def get_device_connectivity_status(
    device_id: int,
    current_user: User = Depends(AuthManager.get_current_user)
):
    """获取单个设备的连通性状态"""
    try:
        # 验证设备是否存在
        device = await Device.filter(id=device_id).first()
        if not device:
            raise HTTPException(status_code=404, detail="设备不存在")
        await ensure_device_access(device, current_user)

        # 获取连通性状态
        connectivity_data = await connectivity_manager.get_connectivity_status(device_id)

        if connectivity_data:
            result = {
                "device_id": device_id,
                "device_name": device.name,
                "device_ip": device.ip,
                "status": connectivity_data["status"],
                "last_check": connectivity_data["last_check"].isoformat() if connectivity_data.get("last_check") else None,
                "last_ping": connectivity_data["last_ping"].isoformat() if connectivity_data.get("last_ping") else None
            }
        else:
            result = {
                "device_id": device_id,
                "device_name": device.name,
                "device_ip": device.ip,
                "status": False,
                "last_check": None,
                "last_ping": None
            }

        return BaseResponse(
            code=200,
            message="连通性状态获取成功",
            data=result
        )

    except Exception as e:
        print(f"获取设备连通性状态失败: {e}")
        raise HTTPException(status_code=500, detail="获取设备连通性状态失败")


@router.put("/{device_id:int}", response_model=BaseResponse, summary="更新设备信息")
async def update_device(device_id: int, device_data: DeviceUpdate, current_user: User = Depends(AuthManager.get_current_user)):
    """更新设备信息"""
    device = await Device.filter(id=device_id).prefetch_related("vpn_config").first()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")

    # 处理VPN配置更新
    update_data = device_data.dict(exclude_unset=True)
    old_vpn_config_id = device.vpn_config_id
    vpn_config_id = update_data.pop('vpn_config_id', None)
    group_ids = update_data.pop('group_ids', None)

    if vpn_config_id is not None:
        if vpn_config_id:
            # 验证VPN配置是否存在
            vpn_config = await VPNConfig.filter(id=vpn_config_id).first()
            if not vpn_config:
                raise HTTPException(status_code=400, detail="指定的VPN配置不存在")
            device.vpn_config = vpn_config
            device.required_vpn_display = f"{vpn_config.region} - {vpn_config.network}"
        else:
            # 清空VPN配置
            device.vpn_config = None
            device.required_vpn_display = None

    # 更新其他字段
    if update_data:
        await device.update_from_dict(update_data)
    await device.save()

    # 更新设备分组
    await sync_device_groups(device, group_ids)

    # 重新获取设备信息以包含最新的VPN配置
    device = await Device.filter(id=device_id).prefetch_related("vpn_config", "group_links__group").first()

    # 如果设备VPN发生变化，迁移访问IP记录到新VPN对应的用户IP
    try:
        if old_vpn_config_id != device.vpn_config_id:
            access_records = await DeviceAccessIP.filter(device=device).all()
            for rec in access_records:
                user = await User.filter(employee_id__iexact=rec.employee_id).first()
                if user and device.vpn_config_id:
                    uvpn = await UserVPNConfig.filter(user_id=user.id, vpn_config_id=device.vpn_config_id).first()
                    rec.vpn_ip = uvpn.ip_address if uvpn else None
                else:
                    rec.vpn_ip = None
                await rec.save()
    except Exception as e:
        print(f"迁移设备访问IP失败: {e}")

    # 构建响应数据
    vpn_config_id = device.vpn_config.id if device.vpn_config else None
    vpn_region = device.vpn_config.region if device.vpn_config else None
    vpn_network = device.vpn_config.network if device.vpn_config else None
    vpn_display_name = f"{vpn_region} - {vpn_network}" if device.vpn_config else device.required_vpn_display

    device_response = {
        "id": device.id,
        "name": device.name,
        "ip": device.ip,
        "vpn_config_id": vpn_config_id,
        "vpn_region": vpn_region,
        "vpn_network": vpn_network,
        "vpn_display_name": vpn_display_name,
        "creator": device.creator,
        "ftp_prefix": device.ftp_prefix,
        "support_queue": device.support_queue,
        "max_occupy_minutes": device.max_occupy_minutes,
        "owner": device.owner,
        "device_type": device.device_type,
        "form_type": device.form_type,
        "remarks": device.remarks,
        "groups": serialize_group_links(device),
        "created_at": device.created_at,
        "updated_at": device.updated_at
    }

    # 分组变更后的可见性联动处理
    try:
        usage_info = await DeviceUsage.filter(device=device).first()
        # 处理占用人无权访问的情况
        if usage_info and usage_info.current_user:
            occ_emp = normalize_employee_id(usage_info.current_user)
            occ_user = await User.filter(employee_id__iexact=occ_emp).first()
            if occ_user and not await user_has_device_access(device, occ_user):
                await revoke_shared_access(device, current_user, "device_groups_changed")
                if usage_info.queue_users and len(usage_info.queue_users) > 0:
                    next_user = usage_info.queue_users.pop(0)
                    normalized_next = normalize_employee_id(next_user)
                    usage_info.current_user = normalized_next
                    usage_info.start_time = get_current_time()
                    await usage_info.save()
                    try:
                        await clear_role_access(device, role="occupant")
                        next_user_obj = await User.filter(employee_id__iexact=normalized_next).first()
                        if next_user_obj:
                            await upsert_device_access_ip(device, next_user_obj, role="occupant")
                    except Exception as e:
                        print(f"分组变更切换占用人访问IP失败: {e}")
                    await OperationLog.create_log(
                        user=current_user,
                        operation_type="device_release",
                        operation_result="success",
                        device_name=device.name,
                        description=f"分组调整导致占用人无权访问，设备分配给下一个用户 {normalized_next}",
                        device_ip=device.ip
                    )
                else:
                    usage_info.current_user = None
                    usage_info.start_time = None
                    usage_info.status = DeviceStatusEnum.AVAILABLE
                    await usage_info.save()
                    try:
                        await delete_device_access_ip(device, occ_emp, role="occupant")
                    except Exception as e:
                        print(f"分组变更清理占用人访问IP失败: {e}")
                    await OperationLog.create_log(
                        user=current_user,
                        operation_type="device_release",
                        operation_result="success",
                        device_name=device.name,
                        description="分组调整导致占用人无权访问，设备已释放",
                        device_ip=device.ip
                    )

        # 处理共用用户无权访问的情况（已审批 + 待审批），并同步移除队列
        # 已审批共用
        approved_shares = await DeviceShareRequest.filter(device=device, status="approved").all()
        for s in approved_shares:
            share_user = await User.filter(employee_id__iexact=s.requester_employee_id).first()
            if share_user and not await user_has_device_access(device, share_user):
                s.status = "revoked"
                s.processed_by = current_user.employee_id
                s.processed_at = get_current_time()
                s.decision_reason = "device_groups_changed"
                await s.save()
                # 从队列中剔除该用户（如果存在）
                if usage_info and usage_info.queue_users:
                    q = usage_info.queue_users
                    normalized_queue = [normalize_employee_id(u) for u in q]
                    target = normalize_employee_id(s.requester_employee_id)
                    if target in normalized_queue:
                        usage_info.queue_users = [
                            uid for uid, norm in zip(q, normalized_queue) if norm != target
                        ]
                        await usage_info.save()
                try:
                    await delete_device_access_ip(device, s.requester_employee_id, role="shared")
                except Exception as e:
                    print(f"分组变更清理共用访问IP失败: {e}")
                await OperationLog.create_log(
                    user=current_user,
                    operation_type="device_share_revoke",
                    operation_result="success",
                    device_name=device.name,
                    description=f"分组调整导致用户 {s.requester_employee_id} 无权访问，已取消共用并移出队列",
                    device_ip=device.ip
                )
                # 通知：共用被强制取消
                try:
                    share_user_obj = await User.filter(employee_id__iexact=s.requester_employee_id).first()
                    await send_device_notification(device, share_user_obj, "分组变更：共用被强制取消")
                except Exception as e:
                    print(f"通知失败: {e}")

        # 待审批共用
        pending_shares = await DeviceShareRequest.filter(device=device, status="pending").all()
        for s in pending_shares:
            share_user = await User.filter(employee_id__iexact=s.requester_employee_id).first()
            if share_user and not await user_has_device_access(device, share_user):
                s.status = "cancelled"
                s.processed_by = current_user.employee_id
                s.processed_at = get_current_time()
                s.decision_reason = "device_groups_changed"
                await s.save()
                # 从队列中剔除该用户（如果存在）
                if usage_info and usage_info.queue_users:
                    q = usage_info.queue_users
                    normalized_queue = [normalize_employee_id(u) for u in q]
                    target = normalize_employee_id(s.requester_employee_id)
                    if target in normalized_queue:
                        usage_info.queue_users = [
                            uid for uid, norm in zip(q, normalized_queue) if norm != target
                        ]
                        await usage_info.save()
                await OperationLog.create_log(
                    user=current_user,
                    operation_type="device_share_cancel",
                    operation_result="success",
                    device_name=device.name,
                    description=f"分组调整导致用户 {s.requester_employee_id} 无权访问，已取消共用申请并移出队列",
                    device_ip=device.ip
                )
                # 通知：共用申请被系统取消
                try:
                    share_user_obj = await User.filter(employee_id__iexact=s.requester_employee_id).first()
                    await send_device_notification(device, share_user_obj, "分组变更：共用申请被取消")
                except Exception as e:
                    print(f"通知失败: {e}")
    except Exception as e:
        print(f"分组变更联动处理失败: {e}")

    return BaseResponse(
        code=200,
        message="设备更新成功",
        data=device_response
    )


@router.delete("/{device_id:int}", summary="删除设备")
async def delete_device(device_id: int, current_user: User = Depends(AuthManager.get_current_user)):
    """删除设备，只有设备归属人或管理员可以删除"""
    device = await Device.filter(id=device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")

    # 权限检查：只有设备归属人或管理员可以删除
    if not (device.owner == current_user.employee_id or current_user.is_superuser):
        raise HTTPException(
            status_code=403,
            detail="权限不足，只有设备归属人或管理员可以删除设备"
        )

    # 检查设备是否正在使用中
    usage_info = await DeviceUsage.filter(device=device).first()
    if usage_info and usage_info.status == DeviceStatusEnum.OCCUPIED:
        raise HTTPException(
            status_code=400,
            detail="设备正在使用中，无法删除"
        )

    # 删除相关数据
    if usage_info:
        await usage_info.delete()

    # 删除设备内部信息
    internal_info = await DeviceInternal.filter(device=device).first()
    if internal_info:
        await internal_info.delete()

    # 删除使用历史记录
    await DeviceUsageHistory.filter(device=device).delete()

    # 删除设备
    await device.delete()

    return BaseResponse(
        code=200,
        message="设备删除成功",
        data=None
    )


@router.post("/use", summary="使用设备")
async def use_device(request: DeviceUseRequest, current_user: User = Depends(AuthManager.get_current_user)):
    """直接使用设备（普通占用）"""
    device = await Device.filter(id=request.device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    await ensure_device_access(device, current_user)
    await ensure_user_vpn_ip(device, current_user)
    if not device.support_queue:
        raise HTTPException(status_code=400, detail="该设备未开放使用")

    usage_info = await DeviceUsage.filter(device=device).first()
    if not usage_info:
        usage_info = await DeviceUsage.create(device=device)

    # 检查设备状态
    if usage_info.status != DeviceStatusEnum.AVAILABLE:
        raise HTTPException(status_code=400, detail="设备当前不可用")

    normalized_request_user = normalize_employee_id(
        request.user) or normalize_employee_id(current_user.employee_id)

    # 直接占用设备
    await revoke_shared_access(device, current_user, "device_used")
    usage_info.current_user = normalized_request_user
    usage_info.start_time = get_current_time()
    usage_info.status = DeviceStatusEnum.OCCUPIED
    usage_info.is_long_term = False
    usage_info.long_term_purpose = None
    usage_info.end_date = None
    await usage_info.save()

    # 创建使用历史记录
    await DeviceUsageHistory.create(
        device=device,
        user=normalized_request_user,
        start_time=get_current_time(),
        purpose="普通使用"
    )

    # 记录操作日志
    await OperationLog.create_log(
        user=current_user,
        operation_type="device_use",
        operation_result="success",
        device_name=device.name,
        description=f"成功使用设备 {device.name}",
        device_ip=device.ip
    )

    # 更新访问IP记录（占用人）
    occupant_user = await User.filter(employee_id__iexact=normalized_request_user).first() or current_user
    await upsert_device_access_ip(device, occupant_user, role="occupant")

    # 通知
    # 主动占用成功无需通知

    return BaseResponse(
        code=200,
        message="设备占用成功",
        data={
            "device_id": device.id,
        },
    )

    # 更新访问IP记录（占用人）
    try:
        await current_user.fetch_related('role')
    except Exception:
        pass
    # 占用人为当前操作人或指定用户
    occupant_user = await User.filter(employee_id__iexact=normalized_request_user).first() or current_user
    await upsert_device_access_ip(device, occupant_user, role="occupant")


@router.post("/long-term-use", summary="申请长时间占用设备")
async def long_term_use_device(request: DeviceLongTermUseRequest, current_user: User = Depends(AuthManager.get_current_user)):
    """申请长时间占用设备"""
    device = await Device.filter(id=request.device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    await ensure_device_access(device, current_user)
    await ensure_user_vpn_ip(device, current_user)
    if not device.support_queue:
        raise HTTPException(status_code=400, detail="该设备未开放使用")

    usage_info = await DeviceUsage.filter(device=device).first()
    if not usage_info:
        usage_info = await DeviceUsage.create(device=device)

    # 检查设备状态
    if usage_info.status != DeviceStatusEnum.AVAILABLE:
        raise HTTPException(status_code=400, detail="设备当前不可用")

    # 验证截至时间
    if request.end_date <= get_current_time():
        raise HTTPException(status_code=400, detail="截至时间必须是未来时间")

    normalized_request_user = resolve_request_user(request.user, current_user)

    # 长时间占用设备
    await revoke_shared_access(device, current_user, "device_long_term_use")
    usage_info.current_user = normalized_request_user
    usage_info.start_time = get_current_time()
    usage_info.status = DeviceStatusEnum.LONG_TERM_OCCUPIED
    usage_info.is_long_term = True
    usage_info.long_term_purpose = request.purpose
    usage_info.end_date = request.end_date
    await usage_info.save()

    # 创建使用历史记录
    await DeviceUsageHistory.create(
        device=device,
        user=normalized_request_user,
        start_time=get_current_time(),
        purpose=request.purpose
    )

    # 记录操作日志
    await OperationLog.create_log(
        user=current_user,
        operation_type="device_long_term_use",
        operation_result="success",
        device_name=device.name,
        description=f"成功申请长时间占用设备 {device.name}，截至时间：{request.end_date}",
        device_ip=device.ip
    )

    # 更新访问IP记录（占用人）
    occupant_user = await User.filter(employee_id__iexact=normalized_request_user).first() or current_user
    await upsert_device_access_ip(device, occupant_user, role="occupant")

    # 通知
    # 主动长时间占用成功无需通知

    return BaseResponse(
        code=200,
        message="长时间占用申请成功",
        data={
            "device_id": device.id,
            "end_date": str(request.end_date),
        },
    )


@router.post("/queue", summary="排队等待设备")
async def queue_device(request: DeviceUseRequest, current_user: User = Depends(AuthManager.get_current_user)):
    """排队等待设备"""
    device = await Device.filter(id=request.device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    await ensure_device_access(device, current_user)
    await ensure_user_vpn_ip(device, current_user)

    usage_info = await DeviceUsage.filter(device=device).first()
    if not usage_info:
        usage_info = await DeviceUsage.create(device=device)

    normalized_current_user = normalize_employee_id(current_user.employee_id)
    requested_user = resolve_request_user(request.user, current_user)

    if usage_info.status == DeviceStatusEnum.OCCUPIED:
        # 设备被占用，检查是否支持排队
        if not device.support_queue:
            raise HTTPException(status_code=400, detail="该设备不支持排队等待")

        # 检查是否是当前使用者尝试排队
        if normalize_employee_id(usage_info.current_user) == requested_user:
            raise HTTPException(status_code=400, detail="您已经在使用此设备")

        # 检查用户是否已在排队
        existing_queue = [normalize_employee_id(
            u) for u in (usage_info.queue_users or [])]
        if requested_user in existing_queue:
            raise HTTPException(status_code=400, detail="您已在排队中")

        # 加入排队
        if not usage_info.queue_users:
            usage_info.queue_users = []
        usage_info.queue_users.append(requested_user)
        await usage_info.save()

        # 记录操作日志
        await OperationLog.create_log(
            user=current_user,
            operation_type="device_queue",
            operation_result="success",
            device_name=device.name,
            description=f"加入设备 {device.name} 排队，排队位置: {len(usage_info.queue_users)}",
            device_ip=device.ip
        )

        return BaseResponse(
            code=200,
            message="已加入排队",
            data={
                "device_id": device.id,
                "status": "queued",
                "queue_position": len(usage_info.queue_users)
            }
        )

    else:
        raise HTTPException(status_code=400, detail="设备当前不可用")


@router.post("/release", summary="释放设备")
async def release_device(request: DeviceReleaseRequest, current_user: User = Depends(AuthManager.get_current_user)):
    """释放设备"""
    device = await Device.filter(id=request.device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")

    usage_info = await DeviceUsage.filter(device=device).first()
    if not usage_info:
        raise HTTPException(status_code=404, detail="设备使用信息不存在")

    current_employee_id = normalize_employee_id(current_user.employee_id)
    # 检查权限：当前使用者、管理员或超级管理员才能释放设备
    is_current_user = normalize_employee_id(
        usage_info.current_user) == current_employee_id
    is_admin_or_super = (current_user.is_superuser or
                         await current_user.has_role("管理员"))

    if not (is_current_user or is_admin_or_super):
        raise HTTPException(status_code=403, detail="只有当前使用者、管理员或超级管理员才能释放设备")

    # 记录释放操作的相关信息
    release_user = usage_info.current_user
    is_force_release = not is_current_user

    # 占用人变化前撤销共用
    await revoke_shared_access(device, current_user, "device_released")

    # 更新使用历史记录
    # if usage_info.start_time:
    #     history = await DeviceUsageHistory.filter(
    #         device=device,
    #         user=request.user,
    #         end_time__isnull=True
    #     ).first()
    #     if history:
    #         history.end_time = datetime.now()
    #         duration = datetime.now() - history.start_time
    #         history.duration = int(duration.total_seconds() / 60)
    #         await history.save()

    # 检查排队情况
    if usage_info.queue_users and len(usage_info.queue_users) > 0:
        # 有人排队，将设备分配给下一个用户
        next_user = usage_info.queue_users.pop(0)
        normalized_next_user = normalize_employee_id(next_user) or next_user
        usage_info.current_user = normalized_next_user
        usage_info.start_time = get_current_time()
        await usage_info.save()

        # 创建新的使用历史记录
        await DeviceUsageHistory.create(
            device=device,
            user=next_user,
            start_time=get_current_time()
        )

        # 记录释放操作日志
        release_type = "强制释放" if is_force_release else "释放"
        await OperationLog.create_log(
            user=current_user,
            operation_type="device_release",
            operation_result="success",
            device_name=device.name,
            description=f"{release_type}设备 {device.name}，设备已分配给下一个用户 {normalized_next_user}",
            device_ip=device.ip
        )

        # 更新访问IP：切换占用人
        try:
            await clear_role_access(device, role="occupant")
            next_user_obj = await User.filter(employee_id__iexact=normalized_next_user).first()
            if next_user_obj:
                await upsert_device_access_ip(device, next_user_obj, role="occupant")
        except Exception as e:
            print(f"更新占用人访问IP失败: {e}")

        # 通知：原占用人、下一位占用者
        try:
            # 若为强制释放则通知原占用人
            if is_force_release:
                prev_user_obj = await User.filter(employee_id__iexact=release_user).first()
                await send_device_notification(device, prev_user_obj, "设备已被释放，分配给下一位")
            next_user_obj = await User.filter(employee_id__iexact=normalized_next_user).first()
            await send_device_notification(device, next_user_obj, "由排队状态转为占用状态")
        except Exception as e:
            print(f"通知失败: {e}")

        return BaseResponse(
            code=200,
            message="设备已释放并分配给下一个用户",
            data={
                "device_id": device.id,
                "next_user": next_user,
                "status": "reassigned"
            }
        )
    else:
        # 没有排队，设备变为可用
        usage_info.current_user = None
        usage_info.start_time = None
        usage_info.status = DeviceStatusEnum.AVAILABLE
        await usage_info.save()

        # 记录释放操作日志
        release_type = "强制释放" if is_force_release else "释放"
        await OperationLog.create_log(
            user=current_user,
            operation_type="device_release",
            operation_result="success",
            device_name=device.name,
            description=f"{release_type}设备 {device.name}，设备现在可用",
            device_ip=device.ip
        )

        # 清理占用人的访问IP
        try:
            if release_user:
                await delete_device_access_ip(device, release_user, role="occupant")
        except Exception as e:
            print(f"清理占用人访问IP失败: {e}")

        # 通知：原占用人
        try:
            # 若为强制释放则通知原占用人
            if is_force_release:
                prev_user_obj = await User.filter(employee_id__iexact=release_user).first()
                await send_device_notification(device, prev_user_obj, "设备已被释放，设备变为可用")
        except Exception as e:
            print(f"通知失败: {e}")

        return BaseResponse(
            code=200,
            message="设备已释放",
            data={
                "device_id": device.id,
                "status": "available"
            }
        )


class DeviceCancelQueueRequest(BaseModel):
    """取消排队请求模型"""
    device_id: int


@router.post("/cancel-queue", summary="取消排队")
async def cancel_queue(request: DeviceCancelQueueRequest, current_user: User = Depends(AuthManager.get_current_user)):
    """取消排队"""
    device = await Device.filter(id=request.device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")

    usage_info = await DeviceUsage.filter(device=device).first()
    if not usage_info:
        raise HTTPException(status_code=404, detail="设备使用信息不存在")

    normalized_employee = normalize_employee_id(current_user.employee_id)
    queue_users = usage_info.queue_users or []
    normalized_queue = [normalize_employee_id(u) for u in queue_users]

    # 检查用户是否在排队中
    if normalized_employee not in normalized_queue:
        raise HTTPException(status_code=400, detail="您当前不在排队中")

    # 从排队列表中移除用户（保持原顺序）
    new_queue = []
    removed = False
    for user_id, normalized in zip(queue_users, normalized_queue):
        if not removed and normalized == normalized_employee:
            removed = True
            continue
        new_queue.append(user_id)
    usage_info.queue_users = new_queue
    await usage_info.save()

    # 记录取消排队操作日志
    await OperationLog.create_log(
        user=current_user,
        operation_type="device_cancel_queue",
        operation_result="success",
        device_name=device.name,
        description=f"取消设备 {device.name} 排队",
        device_ip=device.ip
    )

    return BaseResponse(
        code=200,
        message="已取消排队",
        data={
            "device_id": device.id,
            "queue_count": len(usage_info.queue_users)
        }
    )


@router.get("/{device_id:int}/usage", response_model=BaseResponse, summary="获取设备使用情况")
async def get_device_usage(device_id: int, current_user: User = Depends(AuthManager.get_current_user)):
    """获取设备使用情况详情"""
    device = await Device.filter(id=device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    await ensure_device_access(device, current_user)
    # 预取VPN配置，供IP匹配
    try:
        await device.fetch_related("vpn_config")
    except Exception:
        pass

    usage_info = await DeviceUsage.filter(device=device).first()
    if not usage_info:
        usage_info = await DeviceUsage.create(device=device)

    # 计算占用时长（精确到秒，但以分钟为单位显示）
    occupied_duration = 0
    if usage_info.start_time and usage_info.current_user:
        # 统一使用naive datetime进行计算
        current_time = get_current_time()
        # 如果数据库中的时间是aware的，转换为naive
        start_time = usage_info.start_time.replace(
            tzinfo=None) if usage_info.start_time.tzinfo else usage_info.start_time
        duration = current_time - start_time
        # 改为向上取整，确保即使不到1分钟也显示为1分钟
        occupied_duration = max(1, int((duration.total_seconds() + 59) / 60))

    usage_data = {
        "id": usage_info.id,
        "device_id": device.id,
        "current_user": usage_info.current_user,
        "start_time": usage_info.start_time.isoformat() if usage_info.start_time else None,
        "is_long_term": usage_info.is_long_term,
        "long_term_purpose": usage_info.long_term_purpose,
        "end_date": usage_info.end_date.isoformat() if usage_info.end_date else None,
        "queue_users": usage_info.queue_users or [],
        "status": usage_info.status,
        "occupied_duration": occupied_duration,
        "queue_count": len(usage_info.queue_users) if usage_info.queue_users else 0,
        "updated_at": usage_info.updated_at.isoformat() if usage_info.updated_at else None
    }

    shared_users = await get_device_shared_users(device)
    usage_data["shared_users"] = shared_users
    normalized_employee = normalize_employee_id(current_user.employee_id)
    usage_data["is_shared_user"] = any(
        user["employee_id"] == normalized_employee for user in shared_users
    )
    pending_share = await DeviceShareRequest.filter(
        device=device,
        requester_employee_id__iexact=normalized_employee,
        status__in=["pending", "approved"]
    ).first()
    if pending_share:
        usage_data["share_request_id"] = pending_share.id
        usage_data["share_status"] = pending_share.status
        usage_data["has_pending_share_request"] = pending_share.status == "pending"
        if pending_share.status == "approved":
            usage_data["is_shared_user"] = True
    else:
        usage_data["has_pending_share_request"] = False

    # 从持久化表读取访问IP记录
    records = await DeviceAccessIP.filter(device=device).order_by("-updated_at")
    access_entries = [
        {
            "employee_id": r.employee_id,
            "username": r.username,
            "role": ("占用人" if r.role == "occupant" else "共用用户"),
            "vpn_ip": r.vpn_ip,
            "updated_at": r.updated_at.isoformat() if r.updated_at else None,
        }
        for r in records
    ]

    # 可见性：占用人、共用用户、管理员/超级管理员可见
    is_admin_or_super = current_user.is_superuser or (await current_user.has_role("管理员"))
    is_occupant = usage_info.current_user and normalize_employee_id(
        usage_info.current_user) == normalized_employee
    is_shared = usage_data.get("is_shared_user", False)
    usage_data["can_view_access_ips"] = bool(
        is_admin_or_super or is_occupant or is_shared)
    usage_data["access_ips"] = access_entries

    return BaseResponse(
        code=200,
        message="设备使用情况获取成功",
        data=usage_data
    )


@router.post("/preempt", summary="抢占设备")
async def preempt_device(request: DevicePreemptRequest, current_user: User = Depends(AuthManager.get_current_user)):
    """高级用户抢占设备"""
    # 检查用户权限 - 只有高级用户、管理员、超级用户才能抢占
    is_advanced_or_admin = (current_user.is_superuser or
                            await current_user.has_role("管理员") or
                            await current_user.has_role("高级用户"))

    if not is_advanced_or_admin:
        raise HTTPException(status_code=403, detail="只有高级用户、管理员或超级管理员才能抢占设备")

    device = await Device.filter(id=request.device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    await ensure_user_vpn_ip(device, current_user)

    usage_info = await DeviceUsage.filter(device=device).first()
    if not usage_info:
        usage_info = await DeviceUsage.create(device=device)

    normalized_current_employee = normalize_employee_id(
        current_user.employee_id)
    requested_user = resolve_request_user(request.user, current_user)

    # 检查设备状态
    if usage_info.status == DeviceStatusEnum.AVAILABLE:
        # 设备可用，直接占用
        await revoke_shared_access(device, current_user, "device_preempt")
        usage_info.current_user = requested_user
        usage_info.start_time = get_current_time()
        usage_info.status = DeviceStatusEnum.OCCUPIED
        await usage_info.save()

        # 创建使用历史记录
        await DeviceUsageHistory.create(
            device=device,
            user=requested_user,
            start_time=get_current_time(),
            purpose=request.purpose
        )

        # 记录抢占操作日志（设备可用时直接占用）
        await OperationLog.create_log(
            user=current_user,
            operation_type="device_preempt",
            operation_result="success",
            device_name=device.name,
            description=f"抢占设备 {device.name}（设备可用，直接占用）",
            device_ip=device.ip
        )

        # 抢占者主动行为，无需通知

        return BaseResponse(
            code=200,
            message="设备占用成功",
            data={"device_id": device.id}
        )

    elif usage_info.status == DeviceStatusEnum.OCCUPIED:
        # 检查是否试图抢占自己正在使用的设备
        if normalize_employee_id(usage_info.current_user) == requested_user:
            raise HTTPException(status_code=400, detail="您已经在使用此设备")

        # 抢占设备，将当前用户加入排队列表首位
        previous_user = usage_info.current_user

        # 检查抢占者是否已在排队中，如果在则先移除
        if not usage_info.queue_users:
            usage_info.queue_users = []
        normalized_queue = [normalize_employee_id(
            u) for u in usage_info.queue_users]
        if requested_user in normalized_queue:
            usage_info.queue_users = [
                user_id for user_id, normalized in zip(usage_info.queue_users, normalized_queue)
                if normalized != requested_user
            ]

        # 将原用户加入排队列表首位（如果原用户不在排队中）
        previous_user_normalized = normalize_employee_id(previous_user)
        if previous_user_normalized and previous_user_normalized not in [normalize_employee_id(u) for u in usage_info.queue_users]:
            usage_info.queue_users.insert(0, previous_user_normalized)

        # 更新设备占用者
        await revoke_shared_access(device, current_user, "device_preempt")
        usage_info.current_user = requested_user
        usage_info.start_time = get_current_time()
        await usage_info.save()

        # 创建使用历史记录
        await DeviceUsageHistory.create(
            device=device,
            user=requested_user,
            start_time=get_current_time(),
            purpose=request.purpose
        )

        # 记录抢占操作日志
        await OperationLog.create_log(
            user=current_user,
            operation_type="device_preempt",
            operation_result="success",
            device_name=device.name,
            description=f"抢占设备 {device.name}，原用户 {previous_user} 已加入排队列表首位",
            device_ip=device.ip
        )

        # 通知：仅通知原占用人被抢占
        try:
            prev_user_obj = await User.filter(employee_id__iexact=previous_user).first()
            await send_device_notification(device, prev_user_obj, "占用状态被抢占，已加入排队")
        except Exception as e:
            print(f"通知失败: {e}")

        return BaseResponse(
            code=200,
            message="设备抢占成功，原用户已加入排队列表首位",
            data={
                "device_id": device.id,
                "previous_user": previous_user
            }
        )

    else:
        raise HTTPException(status_code=400, detail="设备当前不可用")


@router.post("/priority-queue", summary="优先排队")
async def priority_queue(request: DevicePriorityQueueRequest, current_user: User = Depends(AuthManager.get_current_user)):
    """高级用户优先排队"""
    # 检查用户权限 - 只有高级用户、管理员、超级用户才能优先排队
    is_advanced_or_admin = (current_user.is_superuser or
                            await current_user.has_role("管理员") or
                            await current_user.has_role("高级用户"))

    if not is_advanced_or_admin:
        raise HTTPException(status_code=403, detail="只有高级用户、管理员或超级管理员才能优先排队")

    device = await Device.filter(id=request.device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    await ensure_user_vpn_ip(device, current_user)

    if not device.support_queue:
        raise HTTPException(status_code=400, detail="该设备不支持排队等待")

    usage_info = await DeviceUsage.filter(device=device).first()
    if not usage_info:
        usage_info = await DeviceUsage.create(device=device)

    # 检查设备状态
    normalized_request_user = resolve_request_user(request.user, current_user)

    if usage_info.status == DeviceStatusEnum.AVAILABLE:
        # 设备可用，直接占用
        await revoke_shared_access(device, current_user, "device_priority_queue_use")
        usage_info.current_user = normalized_request_user
        usage_info.start_time = get_current_time()
        usage_info.status = DeviceStatusEnum.OCCUPIED
        await usage_info.save()

        # 创建使用历史记录
        await DeviceUsageHistory.create(
            device=device,
            user=normalized_request_user,
            start_time=get_current_time(),
            purpose=request.purpose
        )

        # 记录优先排队操作日志（设备可用时直接占用）
        await OperationLog.create_log(
            user=current_user,
            operation_type="device_priority_queue",
            operation_result="success",
            device_name=device.name,
            description=f"优先排队设备 {device.name}（设备可用，直接占用）",
            device_ip=device.ip
        )

        return BaseResponse(
            code=200,
            message="设备占用成功",
            data={"device_id": device.id}
        )

    elif usage_info.status == DeviceStatusEnum.OCCUPIED:
        # 检查是否是当前使用者尝试排队
        if normalize_employee_id(usage_info.current_user) == normalized_request_user:
            raise HTTPException(status_code=400, detail="您已经在使用此设备")

        # 检查用户是否已在排队
        normalized_queue = [normalize_employee_id(
            u) for u in (usage_info.queue_users or [])]
        if normalized_request_user in normalized_queue:
            raise HTTPException(status_code=400, detail="您已在排队中")

        # 优先加入排队列表首位
        if not usage_info.queue_users:
            usage_info.queue_users = []
        usage_info.queue_users.insert(0, normalized_request_user)
        await usage_info.save()

        # 记录优先排队操作日志
        await OperationLog.create_log(
            user=current_user,
            operation_type="device_priority_queue",
            operation_result="success",
            device_name=device.name,
            description=f"优先排队设备 {device.name}，排队位置: 1",
            device_ip=device.ip
        )

        return BaseResponse(
            code=200,
            message="已优先加入排队",
            data={
                "device_id": device.id,
                "status": "queued",
                "queue_position": 1
            }
        )

    else:
        raise HTTPException(status_code=400, detail="设备当前不可用")


@router.post("/unified-queue", summary="统一排队")
async def unified_queue(request: DeviceUnifiedQueueRequest, current_user: User = Depends(AuthManager.get_current_user)):
    """统一排队接口：设备可用时直接使用，否则加入排队"""
    device = await Device.filter(id=request.device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    await ensure_user_vpn_ip(device, current_user)
    await ensure_device_access(device, current_user)

    usage_info = await DeviceUsage.filter(device=device).first()
    if not usage_info:
        usage_info = await DeviceUsage.create(device=device)

    # 检查设备状态
    normalized_request_user = resolve_request_user(request.user, current_user)

    if usage_info.status == DeviceStatusEnum.AVAILABLE:
        # 设备可用，直接占用
        await revoke_shared_access(device, current_user, "device_unified_queue_use")
        usage_info.current_user = normalized_request_user
        usage_info.start_time = get_current_time()
        usage_info.status = DeviceStatusEnum.OCCUPIED
        await usage_info.save()

        # 创建使用历史记录
        await DeviceUsageHistory.create(
            device=device,
            user=normalized_request_user,
            start_time=get_current_time(),
            purpose=request.purpose
        )

        # 记录统一排队操作日志（设备可用时直接使用）
        await OperationLog.create_log(
            user=current_user,
            operation_type="device_unified_queue",
            operation_result="success",
            device_name=device.name,
            description=f"统一排队设备 {device.name}（设备可用，直接使用）",
            device_ip=device.ip
        )

        return BaseResponse(
            code=200,
            message="设备使用成功",
            data={
                "device_id": device.id,
                "action": "use"
            }
        )

    elif usage_info.status == DeviceStatusEnum.OCCUPIED:
        # 设备被占用，检查是否支持排队
        if not device.support_queue:
            raise HTTPException(status_code=400, detail="该设备不支持排队等待")

        # 检查是否是当前使用者尝试排队
        if normalize_employee_id(usage_info.current_user) == normalized_request_user:
            raise HTTPException(status_code=400, detail="您已经在使用此设备")

        # 检查用户是否已在排队
        normalized_queue = [normalize_employee_id(
            u) for u in (usage_info.queue_users or [])]
        if normalized_request_user in normalized_queue:
            raise HTTPException(status_code=400, detail="您已在排队中")

        # 加入排队列表末尾
        if not usage_info.queue_users:
            usage_info.queue_users = []
        usage_info.queue_users.append(normalized_request_user)
        await usage_info.save()

        # 记录统一排队操作日志（加入排队）
        await OperationLog.create_log(
            user=current_user,
            operation_type="device_unified_queue",
            operation_result="success",
            device_name=device.name,
            description=f"统一排队设备 {device.name}，排队位置: {len(usage_info.queue_users)}",
            device_ip=device.ip
        )

        return BaseResponse(
            code=200,
            message="已加入排队",
            data={
                "device_id": device.id,
                "action": "queue",
                "queue_position": len(usage_info.queue_users)
            }
        )


@router.post("/share-requests", response_model=BaseResponse, summary="申请共用设备")
async def create_share_request(
    share_data: DeviceShareRequestCreate,
    current_user: User = Depends(AuthManager.get_current_user)
):
    """申请共用已被占用的设备"""
    device = await Device.filter(id=share_data.device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    await ensure_device_access(device, current_user)
    await ensure_user_vpn_ip(device, current_user)

    usage_info = await DeviceUsage.filter(device=device).first()
    if not usage_info or usage_info.status not in [DeviceStatusEnum.OCCUPIED, DeviceStatusEnum.LONG_TERM_OCCUPIED]:
        raise HTTPException(status_code=400, detail="设备当前未被占用，无法申请共用")

    normalized_employee = normalize_employee_id(current_user.employee_id)

    if normalize_employee_id(usage_info.current_user) == normalized_employee:
        raise HTTPException(status_code=400, detail="您已经在使用该设备")

    existing = await DeviceShareRequest.filter(
        device=device,
        requester_employee_id__iexact=normalized_employee,
        status__in=["pending", "approved"]
    ).first()
    if existing:
        message = "您已提交共用申请，请等待占用人处理" if existing.status == "pending" else "您已经拥有共用权限"
        raise HTTPException(status_code=400, detail=message)

    share_request = await DeviceShareRequest.create(
        device=device,
        requester_employee_id=normalized_employee,
        requester_username=current_user.username,
        request_message=share_data.message
    )
    await share_request.fetch_related("device")

    # 自动加入排队列表
    try:
        if device.support_queue:
            usage_info = await DeviceUsage.filter(device=device).first()
            if usage_info and usage_info.status in [DeviceStatusEnum.OCCUPIED, DeviceStatusEnum.LONG_TERM_OCCUPIED]:
                queue = usage_info.queue_users or []
                normalized_queue = [normalize_employee_id(u) for u in queue]
                if normalized_employee != normalize_employee_id(usage_info.current_user) and normalized_employee not in normalized_queue:
                    queue.append(normalized_employee)
                    usage_info.queue_users = queue
                    await usage_info.save()
                    await OperationLog.create_log(
                        user=current_user,
                        operation_type="device_queue",
                        operation_result="success",
                        device_name=device.name,
                        description=f"共用申请自动加入排队，当前排队位置: {len(queue)}",
                        device_ip=device.ip
                    )
    except Exception as e:
        print(f"共用申请自动排队失败: {e}")

    await OperationLog.create_log(
        user=current_user,
        operation_type="device_share_request",
        operation_result="success",
        device_name=device.name,
        description=f"申请共用设备 {device.name}",
        device_ip=device.ip
    )

    return BaseResponse(
        code=200,
        message="共用申请已提交",
        data=serialize_share_request_record(share_request)
    )


@router.get("/share-requests/pending", response_model=BaseResponse, summary="获取待处理共用申请")
async def get_pending_share_requests(current_user: User = Depends(AuthManager.get_current_user)):
    """获取由当前用户占用设备的共用申请"""
    normalized_employee = normalize_employee_id(current_user.employee_id)
    usage_infos = await DeviceUsage.filter(current_user__iexact=normalized_employee).values_list("device_id", flat=True)
    device_ids = list(usage_infos)
    if not device_ids:
        return BaseResponse(code=200, message="暂无共用申请", data=[])

    pending_requests = await DeviceShareRequest.filter(
        device_id__in=device_ids,
        status="pending"
    ).prefetch_related("device").order_by("created_at")

    data = [serialize_share_request_record(req) for req in pending_requests]
    return BaseResponse(code=200, message="共用申请获取成功", data=data)


@router.post("/share-requests/{request_id:int}/decision", response_model=BaseResponse, summary="处理共用申请")
async def decide_share_request(
    request_id: int,
    decision: DeviceShareDecision,
    current_user: User = Depends(AuthManager.get_current_user)
):
    """占用人处理共用申请"""
    share_request = await DeviceShareRequest.filter(id=request_id).prefetch_related("device").first()
    if not share_request:
        raise HTTPException(status_code=404, detail="共用申请不存在")

    usage_info = await DeviceUsage.filter(device=share_request.device).first()
    normalized_employee = normalize_employee_id(current_user.employee_id)
    if not usage_info or normalize_employee_id(usage_info.current_user) != normalized_employee:
        raise HTTPException(status_code=403, detail="只有当前占用人可以处理共用申请")

    if share_request.status != "pending":
        raise HTTPException(status_code=400, detail="该共用申请已处理")

    share_request.status = "approved" if decision.approve else "rejected"
    share_request.processed_by = current_user.employee_id
    share_request.processed_at = get_current_time()
    share_request.decision_reason = decision.reason
    await share_request.save()
    await share_request.fetch_related("device")

    operation_type = "device_share_approve" if decision.approve else "device_share_reject"
    description = (
        f"同意用户 {share_request.requester_employee_id} 共用设备 {share_request.device.name}"
        if decision.approve else
        f"拒绝用户 {share_request.requester_employee_id} 共用设备 {share_request.device.name}"
    )
    await OperationLog.create_log(
        user=current_user,
        operation_type=operation_type,
        operation_result="success",
        device_name=share_request.device.name if share_request.device else None,
        description=description,
        device_ip=share_request.device.ip if share_request.device else None
    )

    # 同步访问IP记录
    try:
        if decision.approve and share_request.device:
            requester = await User.filter(employee_id__iexact=share_request.requester_employee_id).first()
            if requester:
                await upsert_device_access_ip(share_request.device, requester, role="shared")
        else:
            # 拒绝则清理（保险起见）
            await delete_device_access_ip(share_request.device, share_request.requester_employee_id, role="shared")
    except Exception as e:
        print(f"同步共用访问IP失败: {e}")

    # 消息通知：申请人
    try:
        requester = await User.filter(employee_id__iexact=share_request.requester_employee_id).first()
        await send_device_notification(
            share_request.device,
            requester,
            "共用申请已通过" if decision.approve else "共用申请被拒绝"
        )
    except Exception as e:
        print(f"通知失败: {e}")

    return BaseResponse(
        code=200,
        message="共用申请已处理",
        data=serialize_share_request_record(share_request)
    )


@router.post("/share-requests/{request_id:int}/revoke", response_model=BaseResponse, summary="剔除共用用户")
async def revoke_shared_user(
    request_id: int,
    current_user: User = Depends(AuthManager.get_current_user)
):
    """占用人或管理员剔除已审批的共用用户"""
    share_request = await DeviceShareRequest.filter(id=request_id).prefetch_related("device").first()
    if not share_request:
        raise HTTPException(status_code=404, detail="共用记录不存在")

    device = share_request.device
    usage_info = await DeviceUsage.filter(device=device).first()
    if not usage_info:
        raise HTTPException(status_code=404, detail="设备使用信息不存在")

    # 权限：设备当前占用人或管理员/超级管理员
    normalized_employee = normalize_employee_id(current_user.employee_id)
    is_admin_or_super = current_user.is_superuser or (await current_user.has_role("管理员"))
    is_occupant = usage_info.current_user and normalize_employee_id(
        usage_info.current_user) == normalized_employee
    if not (is_admin_or_super or is_occupant):
        raise HTTPException(status_code=403, detail="只有占用人或管理员可以剔除共用用户")

    if share_request.status != "approved":
        raise HTTPException(status_code=400, detail="当前记录不是已审批状态")

    # 设置为revoked
    share_request.status = "revoked"
    share_request.processed_by = current_user.employee_id
    share_request.processed_at = get_current_time()
    share_request.decision_reason = "占用人/管理员剔除共用"
    await share_request.save()

    # 清理访问IP
    await delete_device_access_ip(device, share_request.requester_employee_id, role="shared")

    # 日志
    await OperationLog.create_log(
        user=current_user,
        operation_type="device_share_revoke",
        operation_result="success",
        device_name=device.name if device else None,
        description=f"剔除共用用户 {share_request.requester_employee_id}（设备 {device.name if device else ''}）",
        device_ip=device.ip if device else None
    )

    # 消息通知：被剔除的共用用户
    try:
        requester = await User.filter(employee_id__iexact=share_request.requester_employee_id).first()
        await send_device_notification(share_request.device, requester, "共用权限被占用人/管理员剔除")
    except Exception as e:
        print(f"通知失败: {e}")

    return BaseResponse(
        code=200,
        message="已剔除共用用户",
        data=serialize_share_request_record(share_request)
    )


@router.post("/share-requests/{request_id:int}/cancel", response_model=BaseResponse, summary="取消我的共用申请")
async def cancel_share_request(
    request_id: int,
    current_user: User = Depends(AuthManager.get_current_user)
):
    """申请人在待审批或已通过后取消共用"""
    share_request = await DeviceShareRequest.filter(id=request_id).prefetch_related("device").first()
    if not share_request:
        raise HTTPException(status_code=404, detail="共用申请不存在")

    normalized_employee = normalize_employee_id(current_user.employee_id)
    if normalize_employee_id(share_request.requester_employee_id) != normalized_employee:
        raise HTTPException(status_code=403, detail="只能取消自己的共用申请")

    if share_request.status not in ["pending", "approved"]:
        raise HTTPException(status_code=400, detail="当前状态不支持取消")

    new_status = "cancelled" if share_request.status == "pending" else "revoked"
    share_request.status = new_status
    share_request.processed_by = normalized_employee
    share_request.processed_at = get_current_time()
    share_request.decision_reason = "申请人取消共用"
    await share_request.save()
    await share_request.fetch_related("device")

    action_text = "取消共用申请" if new_status == "cancelled" else "取消已审批的共用"
    await OperationLog.create_log(
        user=current_user,
        operation_type="device_share_cancel",
        operation_result="success",
        device_name=share_request.device.name if share_request.device else None,
        description=f"{action_text}（设备 {share_request.device.name if share_request.device else ''}）",
        device_ip=share_request.device.ip if share_request.device else None
    )

    # 清理访问IP（若为已审批的共用）
    try:
        if new_status == "revoked" and share_request.device:
            await delete_device_access_ip(share_request.device, share_request.requester_employee_id, role="shared")
    except Exception as e:
        print(f"取消共用时清理访问IP失败: {e}")

    return BaseResponse(
        code=200,
        message="共用申请已取消",
        data=serialize_share_request_record(share_request)
    )


@router.get("/my-usage-summary", response_model=BaseResponse, summary="获取我的环境使用情况")
async def get_my_usage_summary(current_user: User = Depends(AuthManager.get_current_user)):
    """获取我当前占用和共用的设备"""
    normalized_employee = normalize_employee_id(current_user.employee_id)
    usage_infos = await DeviceUsage.filter(current_user__iexact=normalized_employee).prefetch_related("device")
    occupied_devices = []
    for usage in usage_infos:
        if not usage.device:
            continue
        try:
            await usage.device.fetch_related("usage_info", "group_links__group")
        except Exception:
            pass
        occupied_duration = 0
        if usage.start_time and usage.current_user:
            current_time = get_current_time()
            start_time = usage.start_time.replace(
                tzinfo=None) if usage.start_time.tzinfo else usage.start_time
            duration = current_time - start_time
            occupied_duration = max(
                1, int((duration.total_seconds() + 59) / 60))
        occupied_devices.append({
            "id": usage.device.id,
            "name": usage.device.name,
            "ip": usage.device.ip,
            "status": usage.status,
            "owner": usage.device.owner,
            "current_user": usage.current_user,
            "occupied_duration": occupied_duration,
            "groups": serialize_group_links(usage.device)
        })

    shared_requests = await DeviceShareRequest.filter(
        requester_employee_id__iexact=normalized_employee,
        status="approved"
    ).prefetch_related("device")

    shared_devices = []
    for share in shared_requests:
        device = share.device
        if not device:
            continue
        try:
            await device.fetch_related("usage_info", "group_links__group")
        except Exception:
            pass
        current_usage = getattr(device, "usage_info", None)
        occupied_duration = 0
        if current_usage and current_usage.start_time and current_usage.current_user:
            current_time = get_current_time()
            start_time = current_usage.start_time.replace(
                tzinfo=None) if current_usage.start_time.tzinfo else current_usage.start_time
            duration = current_time - start_time
            occupied_duration = max(
                1, int((duration.total_seconds() + 59) / 60))
        shared_devices.append({
            "id": device.id,
            "name": device.name,
            "ip": device.ip,
            "status": current_usage.status if current_usage else DeviceStatusEnum.AVAILABLE,
            "owner": device.owner,
            "current_user": current_usage.current_user if current_usage else None,
            "occupied_duration": occupied_duration,
            "groups": serialize_group_links(device),
            "share_message": share.request_message,
            "share_request_id": share.id
        })

    return BaseResponse(
        code=200,
        message="环境信息获取成功",
        data={
            "occupied_devices": occupied_devices,
            "shared_devices": shared_devices
        }
    )


@router.post("/batch-release-my-devices", summary="批量释放我的设备")
async def batch_release_my_devices(current_user: User = Depends(AuthManager.get_current_user)):
    """批量释放当前用户占用的所有设备"""
    try:
        # 查找当前用户占用的所有设备
        normalized_employee = normalize_employee_id(current_user.employee_id)
        usage_infos = await DeviceUsage.filter(current_user__iexact=normalized_employee).prefetch_related("device")

        if not usage_infos:
            return BaseResponse(
                code=200,
                message="您当前没有占用任何设备",
                data={"released_count": 0}
            )

        released_count = 0
        failed_devices = []

        for usage_info in usage_infos:
            try:
                await revoke_shared_access(usage_info.device, current_user, "device_batch_release")
                # 释放设备
                usage_info.current_user = None
                usage_info.start_time = None
                usage_info.purpose = None
                usage_info.status = DeviceStatusEnum.AVAILABLE
                usage_info.is_long_term = False
                usage_info.long_term_purpose = None

                # 如果有排队用户，让第一个用户占用设备
                next_user_display = None
                if usage_info.queue_users:
                    next_user = usage_info.queue_users[0]
                    normalized_next_user = normalize_employee_id(
                        next_user) or next_user
                    next_user_display = normalized_next_user
                    usage_info.current_user = normalized_next_user
                    usage_info.start_time = get_current_time()
                    usage_info.status = DeviceStatusEnum.OCCUPIED
                    # 移除第一个用户
                    usage_info.queue_users = usage_info.queue_users[1:]

                await usage_info.save()
                released_count += 1

                # 记录批量释放操作日志
                next_user_info = f"，设备已分配给下一个用户 {next_user_display}" if next_user_display else "，设备现在可用"
                await OperationLog.create_log(
                    user=current_user,
                    operation_type="device_batch_release",
                    operation_result="success",
                    device_name=usage_info.device.name,
                    description=f"批量释放设备 {usage_info.device.name}{next_user_info}",
                    device_ip=usage_info.device.ip if usage_info.device else None
                )

            except Exception as e:
                failed_devices.append(usage_info.device.name)
                print(f"释放设备 {usage_info.device.name} 失败: {e}")

        message = f"成功释放 {released_count} 台设备"
        if failed_devices:
            message += f"，{len(failed_devices)} 台失败"

        return BaseResponse(
            code=200,
            message=message,
            data={
                "released_count": released_count,
                "failed_count": len(failed_devices),
                "failed_devices": failed_devices
            }
        )

    except Exception as e:
        print(f"批量释放设备失败: {e}")
        return BaseResponse(
            code=500,
            message="批量释放设备失败",
            data=None
        )


@router.post("/batch-cancel-my-queues", summary="批量取消我的排队")
async def batch_cancel_my_queues(current_user: User = Depends(AuthManager.get_current_user)):
    """批量取消当前用户的所有排队"""
    try:
        # 查找包含当前用户排队的所有设备
        all_usage_infos = await DeviceUsage.all().prefetch_related("device")

        cancelled_count = 0
        failed_devices = []

        normalized_employee = normalize_employee_id(current_user.employee_id)
        for usage_info in all_usage_infos:
            if not usage_info.queue_users:
                continue
            queue_users = usage_info.queue_users
            normalized_queue = [normalize_employee_id(u) for u in queue_users]
            if normalized_employee not in normalized_queue:
                continue
            try:
                # 从排队列表中移除当前用户
                usage_info.queue_users = [
                    user_id for user_id, normalized in zip(queue_users, normalized_queue)
                    if normalized != normalized_employee
                ]

                await usage_info.save()
                cancelled_count += 1

                # 记录批量取消排队操作日志
                await OperationLog.create_log(
                    user=current_user,
                    operation_type="device_batch_cancel_queue",
                    operation_result="success",
                    device_name=usage_info.device.name,
                    description=f"批量取消设备 {usage_info.device.name} 排队",
                    device_ip=usage_info.device.ip if usage_info.device else None
                )

            except Exception as e:
                failed_devices.append(usage_info.device.name)
                print(f"取消设备 {usage_info.device.name} 排队失败: {e}")

        if cancelled_count == 0:
            return BaseResponse(
                code=200,
                message="您当前没有排队任何设备",
                data={"cancelled_count": 0}
            )

        message = f"成功取消 {cancelled_count} 台设备排队"
        if failed_devices:
            message += f"，{len(failed_devices)} 台失败"

        return BaseResponse(
            code=200,
            message=message,
            data={
                "cancelled_count": cancelled_count,
                "failed_count": len(failed_devices),
                "failed_devices": failed_devices
            }
        )

    except Exception as e:
        print(f"批量取消排队失败: {e}")
        return BaseResponse(
            code=500,
            message="批量取消排队失败",
            data=None
        )

    else:
        raise HTTPException(status_code=400, detail="设备当前不可用")


@router.post("/admin/force-cleanup-all", summary="管理员强制清理所有设备")
async def admin_force_cleanup_all_devices(current_user: User = Depends(AuthManager.get_current_user)):
    """管理员强制清理所有设备的占用和排队状态"""
    # 检查管理员权限
    is_admin = (current_user.is_superuser or
                await current_user.has_role("管理员"))
    if not is_admin:
        raise HTTPException(status_code=403, detail="权限不足，只有管理员可以执行此操作")

    try:
        # 执行清理任务
        await device_scheduler.force_cleanup_all_devices()

        return BaseResponse(
            code=200,
            message="所有设备已强制清理完成",
            data={"action": "force_cleanup_all",
                  "executor": current_user.employee_id}
        )

    except Exception as e:
        print(f"管理员强制清理失败: {e}")
        raise HTTPException(status_code=500, detail="强制清理失败")


# ===== 设备配置管理接口 =====

@router.get("/{device_id:int}/configs", response_model=BaseResponse, summary="获取设备配置列表")
async def get_device_configs(
    device_id: int,
    current_user: User = Depends(AuthManager.get_current_user)
):
    """
    获取设备配置列表
    - 所有用户都可以查看
    """
    # 检查设备是否存在
    device = await Device.get_or_none(id=device_id)
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")

    # 获取配置列表
    configs = await DeviceConfig.filter(device=device).order_by('config_param1', 'config_param2')

    result = []
    for config in configs:
        result.append({
            "id": config.id,
            "device_id": config.device_id,
            "config_param1": config.config_param1,
            "config_param2": config.config_param2,
            "config_value": config.config_value,
            "created_at": config.created_at,
            "updated_at": config.updated_at
        })

    return BaseResponse(data=result)


@router.post("/{device_id:int}/configs", response_model=BaseResponse, summary="添加设备配置")
async def add_device_config(
    device_id: int,
    config_data: DeviceConfigCreate,
    current_user: User = Depends(AuthManager.get_current_user)
):
    """
    添加设备配置
    - 只有设备归属人或管理员可以添加
    - 同一设备的配置类型不可重复
    """
    # 检查设备是否存在
    device = await Device.get_or_none(id=device_id)
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")

    # 权限检查：只有设备归属人或管理员可以修改
    current_user_id = current_user.employee_id or current_user.username
    is_admin = current_user.is_superuser or current_user.role == '管理员'
    is_owner = device.owner == current_user_id

    if not (is_admin or is_owner):
        raise HTTPException(status_code=403, detail="没有权限操作此设备的配置")

    # 检查参数组合是否已存在
    existing_config = await DeviceConfig.get_or_none(
        device=device,
        config_param1=config_data.config_param1,
        config_param2=config_data.config_param2
    )
    if existing_config:
        raise HTTPException(
            status_code=400, detail=f"配置参数组合 ({config_data.config_param1}, {config_data.config_param2}) 已存在")

    # 创建配置
    try:
        config = await DeviceConfig.create(
            device=device,
            config_param1=config_data.config_param1,
            config_param2=config_data.config_param2,
            config_value=config_data.config_value
        )

        # 记录操作日志
        await OperationLog.create_log(
            user=current_user,
            operation_type="add_device_config",
            operation_result="success",
            device_name=device.name,
            description=f"添加配置: 参数1={config_data.config_param1}, 参数2={config_data.config_param2}, 值={config_data.config_value}",
            device_ip=device.ip
        )

        result = {
            "id": config.id,
            "device_id": config.device_id,
            "config_param1": config.config_param1,
            "config_param2": config.config_param2,
            "config_value": config.config_value,
            "created_at": config.created_at,
            "updated_at": config.updated_at
        }

        return BaseResponse(data=result, message="配置添加成功")

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"添加配置失败: {str(e)}")


@router.post("/{device_id:int}/configs/import-all", response_model=BaseResponse, summary="一键导入设备全部配置")
async def import_all_device_configs(
    device_id: int,
    current_user: User = Depends(AuthManager.get_current_user)
):
    """
    一键导入设备所有配置（占位实现）
    - 只有设备归属人或管理员可以操作
    - 当前实现为打印导入动作
    """
    device = await Device.get_or_none(id=device_id)
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")

    current_user_id = current_user.employee_id or current_user.username
    is_admin = current_user.is_superuser or current_user.role == '管理员'
    is_owner = device.owner == current_user_id

    if not (is_admin or is_owner):
        raise HTTPException(status_code=403, detail="没有权限操作此设备的配置")

    try:
        print(f"[配置批量导入] 设备: {device.name}({device.ip})，准备拉取全部配置")
        await OperationLog.create_log(
            user=current_user,
            operation_type="import_device_configs_all",
            operation_result="success",
            device_name=device.name,
            description="触发一键导入全部配置",
            device_ip=device.ip
        )
    except Exception as e:
        print(f"[配置批量导入失败] device_id={device_id}, error={e}")
        raise HTTPException(status_code=500, detail="触发导入失败")

    return BaseResponse(
        code=200,
        message="导入任务已触发，正在拉取设备配置",
        data={"device_id": device.id}
    )


@router.put("/{device_id:int}/configs/{config_id:int}", response_model=BaseResponse, summary="更新设备配置")
async def update_device_config(
    device_id: int,
    config_id: int,
    config_data: DeviceConfigUpdate,
    current_user: User = Depends(AuthManager.get_current_user)
):
    """
    更新设备配置
    - 只有设备归属人或管理员可以更新
    """
    # 检查设备是否存在
    device = await Device.get_or_none(id=device_id)
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")

    # 检查配置是否存在
    config = await DeviceConfig.get_or_none(id=config_id, device=device)
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")

    # 权限检查：只有设备归属人或管理员可以修改
    current_user_id = current_user.employee_id or current_user.username
    is_admin = current_user.is_superuser or current_user.role == '管理员'
    is_owner = device.owner == current_user_id

    if not (is_admin or is_owner):
        raise HTTPException(status_code=403, detail="没有权限操作此设备的配置")

    # 如果更改了参数组合，检查是否会产生重复
    if config_data.config_param1 != config.config_param1 or config_data.config_param2 != config.config_param2:
        existing_config = await DeviceConfig.get_or_none(
            device=device,
            config_param1=config_data.config_param1,
            config_param2=config_data.config_param2
        )
        if existing_config:
            raise HTTPException(
                status_code=400, detail=f"配置参数组合 ({config_data.config_param1}, {config_data.config_param2}) 已存在")

    # 更新配置
    try:
        old_config = f"参数1={config.config_param1}, 参数2={config.config_param2}, 值={config.config_value}"

        config.config_param1 = config_data.config_param1
        config.config_param2 = config_data.config_param2
        config.config_value = config_data.config_value
        await config.save()

        # 记录操作日志
        await OperationLog.create_log(
            user=current_user,
            operation_type="update_device_config",
            operation_result="success",
            device_name=device.name,
            description=f"更新配置: {old_config} => 参数1={config.config_param1}, 参数2={config.config_param2}, 值={config.config_value}",
            device_ip=device.ip
        )

        result = {
            "id": config.id,
            "device_id": config.device_id,
            "config_param1": config.config_param1,
            "config_param2": config.config_param2,
            "config_value": config.config_value,
            "created_at": config.created_at,
            "updated_at": config.updated_at
        }

        return BaseResponse(data=result, message="配置更新成功")

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"更新配置失败: {str(e)}")


@router.post("/{device_id:int}/configs/{config_id:int}/import", response_model=BaseResponse, summary="一键导入设备配置")
async def import_device_config(
    device_id: int,
    config_id: int,
    current_user: User = Depends(AuthManager.get_current_user)
):
    """
    一键导入设备配置
    - 权限与添加配置一致（设备归属人或管理员）
    - 当前实现为占位符：打印导入动作
    """
    device = await Device.get_or_none(id=device_id)
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")

    config = await DeviceConfig.get_or_none(id=config_id, device=device)
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")

    current_user_id = current_user.employee_id or current_user.username
    is_admin = current_user.is_superuser or current_user.role == '管理员'
    is_owner = device.owner == current_user_id

    if not (is_admin or is_owner):
        raise HTTPException(status_code=403, detail="没有权限操作此设备的配置")

    try:
        print(
            f"[配置导入] 设备: {device.name}({device.ip}) 配置: ({config.config_param1}, {config.config_param2}) 值: {config.config_value}")
        await OperationLog.create_log(
            user=current_user,
            operation_type="import_device_config",
            operation_result="success",
            device_name=device.name,
            description=f"触发一键导入，配置ID={config.id}",
            device_ip=device.ip
        )
    except Exception as e:
        print(
            f"[配置导入失败] device_id={device_id}, config_id={config_id}, error={e}")
        raise HTTPException(status_code=500, detail="触发导入失败")

    return BaseResponse(
        code=200,
        message="导入任务已触发",
        data={
            "device_id": device.id,
            "config_id": config.id
        }
    )


@router.delete("/{device_id:int}/configs/{config_id:int}", response_model=BaseResponse, summary="删除设备配置")
async def delete_device_config(
    device_id: int,
    config_id: int,
    current_user: User = Depends(AuthManager.get_current_user)
):
    """
    删除设备配置
    - 只有设备归属人或管理员可以删除
    """
    # 检查设备是否存在
    device = await Device.get_or_none(id=device_id)
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")

    # 检查配置是否存在
    config = await DeviceConfig.get_or_none(id=config_id, device=device)
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")

    # 权限检查：只有设备归属人或管理员可以修改
    current_user_id = current_user.employee_id or current_user.username
    is_admin = current_user.is_superuser or current_user.role == '管理员'
    is_owner = device.owner == current_user_id

    if not (is_admin or is_owner):
        raise HTTPException(status_code=403, detail="没有权限操作此设备的配置")

    # 删除配置
    try:
        config_info = f"参数1={config.config_param1}, 参数2={config.config_param2}, 值={config.config_value}"
        await config.delete()

        # 记录操作日志
        await OperationLog.create_log(
            user=current_user,
            operation_type="delete_device_config",
            operation_result="success",
            device_name=device.name,
            description=f"删除配置: {config_info}",
            device_ip=device.ip
        )

        return BaseResponse(message="配置删除成功")

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"删除配置失败: {str(e)}")
