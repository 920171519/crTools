"""
设备管理路由
提供设备的增删改查、使用管理等API接口
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel

from models.deviceModel import Device, DeviceUsage, DeviceInternal, DeviceUsageHistory, DeviceStatusEnum
from models.admin import User, OperationLog
from schemas import (
    DeviceBase, DeviceUpdate, DeviceResponse, DeviceListItem,
    DeviceUsageResponse, DeviceUsageUpdate, DeviceUseRequest, DeviceReleaseRequest,
    DevicePreemptRequest, DevicePriorityQueueRequest, DeviceUnifiedQueueRequest
)
from schemas import BaseResponse
from auth import AuthManager

router = APIRouter(prefix="/api/devices", tags=["设备管理"])


def get_current_time():
    """获取当前时间，统一使用naive datetime"""
    return datetime.now()


@router.get("/", response_model=BaseResponse, summary="获取设备列表")
async def get_devices(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    name: Optional[str] = Query(None, description="环境名称搜索"),
    ip: Optional[str] = Query(None, description="环境IP搜索"),
    status: Optional[str] = Query(None, description="环境状态搜索"),
    current_user: User = Depends(AuthManager.get_current_user)
):
    """
    获取设备列表
    - 支持分页
    - 支持按环境名称、IP、状态搜索
    """
    # 构建查询条件
    query = Device.all().prefetch_related("usage_info")

    if name:
        query = query.filter(name__icontains=name)
    if ip:
        query = query.filter(ip__icontains=ip)

    # 如果有状态搜索，需要先获取所有设备然后过滤
    if status:
        # 获取所有符合名称和IP条件的设备
        all_devices = await query
        filtered_devices = []

        for device in all_devices:
            usage_info = await device.usage_info
            if not usage_info:
                usage_info = await DeviceUsage.create(device=device)

            if usage_info.status == status:
                filtered_devices.append(device)

        # 计算总数和分页
        total = len(filtered_devices)
        offset = (page - 1) * page_size
        devices = filtered_devices[offset:offset + page_size]
    else:
        # 没有状态搜索时，正常分页查询
        total = await query.count()
        offset = (page - 1) * page_size
        devices = await query.offset(offset).limit(page_size)

    result = []
    for device in devices:
        if hasattr(device, 'usage_info') and device.usage_info:
            usage_info = device.usage_info
        else:
            usage_info = await device.usage_info
            if not usage_info:
                # 创建默认使用情况
                usage_info = await DeviceUsage.create(device=device)
        
        # 计算占用时长（精确到秒，但以分钟为单位显示）
        occupied_duration = 0
        if usage_info.start_time and usage_info.current_user:
            # 统一使用naive datetime进行计算
            current_time = get_current_time()
            # 如果数据库中的时间是aware的，转换为naive
            start_time = usage_info.start_time.replace(tzinfo=None) if usage_info.start_time.tzinfo else usage_info.start_time
            duration = current_time - start_time
            # 改为向上取整，确保即使不到1分钟也显示为1分钟
            occupied_duration = max(1, int((duration.total_seconds() + 59) / 60))
        
        # 检查当前用户是否在排队中
        is_current_user_in_queue = False
        if usage_info.queue_users and current_user.employee_id in usage_info.queue_users:
            is_current_user_in_queue = True

        result.append(DeviceListItem(
            id=device.id,
            name=device.name,
            ip=device.ip,
            device_type=device.device_type,
            current_user=usage_info.current_user,
            queue_count=len(usage_info.queue_users) if usage_info.queue_users else 0,
            status=usage_info.status,
            start_time=usage_info.start_time,
            occupied_duration=occupied_duration,
            is_current_user_in_queue=is_current_user_in_queue
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
    # 检查IP是否已存在
    existing_device = await Device.filter(ip=device_data.ip).first()
    if existing_device:
        raise HTTPException(status_code=400, detail="该IP地址已存在")
    
    # 创建设备
    device = await Device.create(**device_data.dict())
    
    # 创建设备使用情况记录
    await DeviceUsage.create(device=device)
    
    # 创建设备内部信息记录
    internal_info = await DeviceInternal.create(device=device)
    internal_info.init_ports()
    await internal_info.save()
    
    device_response = {
        "id": device.id,
        "name": device.name,
        "ip": device.ip,
        "required_vpn": device.required_vpn,
        "creator": device.creator,
        "need_vpn_login": device.need_vpn_login,
        "support_queue": device.support_queue,
        "owner": device.owner,
        "device_type": device.device_type,
        "remarks": device.remarks,
        "created_at": device.created_at,
        "updated_at": device.updated_at
    }
    
    return BaseResponse(
        code=200,
        message="设备创建成功",
        data=device_response
    )


@router.get("/{device_id}", response_model=BaseResponse, summary="获取设备详情")
async def get_device(device_id: int):
    """根据ID获取设备详情"""
    device = await Device.filter(id=device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    
    device_data = {
        "id": device.id,
        "name": device.name,
        "ip": device.ip,
        "required_vpn": device.required_vpn,
        "creator": device.creator,
        "need_vpn_login": device.need_vpn_login,
        "support_queue": device.support_queue,
        "owner": device.owner,
        "device_type": device.device_type,
        "remarks": device.remarks,
        "created_at": device.created_at,
        "updated_at": device.updated_at
    }
    
    return BaseResponse(
        code=200,
        message="设备详情获取成功",
        data=device_data
    )


@router.put("/{device_id}", response_model=BaseResponse, summary="更新设备信息")
async def update_device(device_id: int, device_data: DeviceUpdate, current_user: User = Depends(AuthManager.get_current_user)):
    """更新设备信息"""
    device = await Device.filter(id=device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    
    # 更新设备信息
    update_data = device_data.dict(exclude_unset=True)
    await device.update_from_dict(update_data)
    await device.save()
    
    device_data = {
        "id": device.id,
        "name": device.name,
        "ip": device.ip,
        "required_vpn": device.required_vpn,
        "creator": device.creator,
        "need_vpn_login": device.need_vpn_login,
        "support_queue": device.support_queue,
        "owner": device.owner,
        "device_type": device.device_type,
        "remarks": device.remarks,
        "created_at": device.created_at,
        "updated_at": device.updated_at
    }
    
    return BaseResponse(
        code=200,
        message="设备更新成功",
        data=device_data
    )


@router.delete("/{device_id}", summary="删除设备")
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
    """使用设备或加入排队"""
    device = await Device.filter(id=request.device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")

    usage_info = await DeviceUsage.filter(device=device).first()
    if not usage_info:
        usage_info = await DeviceUsage.create(device=device)

    # 检查设备状态
    if usage_info.status == DeviceStatusEnum.AVAILABLE:
        # 设备可用，直接占用
        usage_info.current_user = request.user
        usage_info.start_time = get_current_time()
        usage_info.expected_duration = request.expected_duration
        usage_info.status = DeviceStatusEnum.OCCUPIED
        await usage_info.save()

        # 创建使用历史记录
        await DeviceUsageHistory.create(
            device=device,
            user=request.user,
            start_time=get_current_time(),
            purpose=request.purpose
        )

        # 记录操作日志
        await OperationLog.create_log(
            user=current_user,
            operation_type="device_use",
            operation_result="success",
            device_name=device.name,
            description=f"成功使用设备 {device.name}，预计使用时长 {request.expected_duration} 分钟"
        )

        return BaseResponse(
            code = 200,
            message= "设备占用成功",
            data = {
                "device_id": device.id,
            },
        )
    
    elif usage_info.status == DeviceStatusEnum.OCCUPIED:
        # 设备被占用，检查是否支持排队
        if not device.support_queue:
            raise HTTPException(status_code=400, detail="该设备不支持排队等待")
        
        # 检查是否是当前使用者尝试排队
        if usage_info.current_user == request.user:
            raise HTTPException(status_code=400, detail="您已经在使用此设备")
        
        # 检查用户是否已在排队
        if request.user in (usage_info.queue_users or []):
            raise HTTPException(status_code=400, detail="您已在排队中")
        
        # 加入排队
        if not usage_info.queue_users:
            usage_info.queue_users = []
        usage_info.queue_users.append(request.user)
        await usage_info.save()

        # 记录操作日志
        await OperationLog.create_log(
            user=current_user,
            operation_type="device_queue",
            operation_result="success",
            device_name=device.name,
            description=f"加入设备 {device.name} 排队，排队位置: {len(usage_info.queue_users)}"
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

    # 检查权限：当前使用者、管理员或超级管理员才能释放设备
    is_current_user = usage_info.current_user == current_user.employee_id
    is_admin_or_super = (current_user.is_superuser or
                        await current_user.has_role("管理员"))

    if not (is_current_user or is_admin_or_super):
        raise HTTPException(status_code=403, detail="只有当前使用者、管理员或超级管理员才能释放设备")

    # 记录释放操作的相关信息
    release_user = usage_info.current_user
    is_force_release = not is_current_user

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
        usage_info.current_user = next_user
        usage_info.start_time = get_current_time()
        usage_info.expected_duration = 60  # 默认60分钟
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
            description=f"{release_type}设备 {device.name}，设备已分配给下一个用户 {next_user}"
        )

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
        usage_info.expected_duration = 0
        usage_info.status = DeviceStatusEnum.AVAILABLE
        await usage_info.save()

        # 记录释放操作日志
        release_type = "强制释放" if is_force_release else "释放"
        await OperationLog.create_log(
            user=current_user,
            operation_type="device_release",
            operation_result="success",
            device_name=device.name,
            description=f"{release_type}设备 {device.name}，设备现在可用"
        )

        return BaseResponse(
            code=200,
            message = "设备已释放",
            data= {
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
    
    # 检查用户是否在排队中
    if not usage_info.queue_users or current_user.employee_id not in usage_info.queue_users:
        raise HTTPException(status_code=400, detail="您当前不在排队中")
    
    # 从排队列表中移除用户
    usage_info.queue_users.remove(current_user.employee_id)
    await usage_info.save()

    # 记录取消排队操作日志
    await OperationLog.create_log(
        user=current_user,
        operation_type="device_cancel_queue",
        operation_result="success",
        device_name=device.name,
        description=f"取消设备 {device.name} 排队"
    )

    return BaseResponse(
        code=200,
        message="已取消排队",
        data={
            "device_id": device.id,
            "queue_count": len(usage_info.queue_users)
        }
    )


@router.get("/{device_id}/usage", response_model=BaseResponse, summary="获取设备使用情况")
async def get_device_usage(device_id: int):
    """获取设备使用情况详情"""
    device = await Device.filter(id=device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    
    usage_info = await DeviceUsage.filter(device=device).first()
    if not usage_info:
        usage_info = await DeviceUsage.create(device=device)
    
    # 计算占用时长（精确到秒，但以分钟为单位显示）
    occupied_duration = 0
    if usage_info.start_time and usage_info.current_user:
        # 统一使用naive datetime进行计算
        current_time = get_current_time()
        # 如果数据库中的时间是aware的，转换为naive
        start_time = usage_info.start_time.replace(tzinfo=None) if usage_info.start_time.tzinfo else usage_info.start_time
        duration = current_time - start_time
        # 改为向上取整，确保即使不到1分钟也显示为1分钟
        occupied_duration = max(1, int((duration.total_seconds() + 59) / 60))
    
    usage_data = {
        "id": usage_info.id,
        "device_id": device.id,
        "current_user": usage_info.current_user,
        "start_time": usage_info.start_time.isoformat() if usage_info.start_time else None,
        "expected_duration": usage_info.expected_duration,
        "is_long_term": usage_info.is_long_term,
        "long_term_purpose": usage_info.long_term_purpose,
        "queue_users": usage_info.queue_users or [],
        "status": usage_info.status,
        "occupied_duration": occupied_duration,
        "queue_count": len(usage_info.queue_users) if usage_info.queue_users else 0,
        "updated_at": usage_info.updated_at.isoformat() if usage_info.updated_at else None
    }
    
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
    
    usage_info = await DeviceUsage.filter(device=device).first()
    if not usage_info:
        usage_info = await DeviceUsage.create(device=device)
    
    # 检查设备状态
    if usage_info.status == DeviceStatusEnum.AVAILABLE:
        # 设备可用，直接占用
        usage_info.current_user = request.user
        usage_info.start_time = get_current_time()
        usage_info.expected_duration = request.expected_duration
        usage_info.status = DeviceStatusEnum.OCCUPIED
        await usage_info.save()
        
        # 创建使用历史记录
        await DeviceUsageHistory.create(
            device=device,
            user=request.user,
            start_time=get_current_time(),
            purpose=request.purpose
        )

        # 记录抢占操作日志（设备可用时直接占用）
        await OperationLog.create_log(
            user=current_user,
            operation_type="device_preempt",
            operation_result="success",
            device_name=device.name,
            description=f"抢占设备 {device.name}（设备可用，直接占用）"
        )

        return BaseResponse(
            code=200,
            message="设备占用成功",
            data={"device_id": device.id}
        )
    
    elif usage_info.status == DeviceStatusEnum.OCCUPIED:
        # 检查是否试图抢占自己正在使用的设备
        if usage_info.current_user == request.user:
            raise HTTPException(status_code=400, detail="您已经在使用此设备")
        
        # 抢占设备，将当前用户加入排队列表首位
        previous_user = usage_info.current_user
        
        # 检查抢占者是否已在排队中，如果在则先移除
        if not usage_info.queue_users:
            usage_info.queue_users = []
        if request.user in usage_info.queue_users:
            usage_info.queue_users.remove(request.user)
        
        # 将原用户加入排队列表首位（如果原用户不在排队中）
        if previous_user not in usage_info.queue_users:
            usage_info.queue_users.insert(0, previous_user)
        
        # 更新设备占用者
        usage_info.current_user = request.user
        usage_info.start_time = get_current_time()
        usage_info.expected_duration = request.expected_duration
        await usage_info.save()
        
        # 创建使用历史记录
        await DeviceUsageHistory.create(
            device=device,
            user=request.user,
            start_time=get_current_time(),
            purpose=request.purpose
        )

        # 记录抢占操作日志
        await OperationLog.create_log(
            user=current_user,
            operation_type="device_preempt",
            operation_result="success",
            device_name=device.name,
            description=f"抢占设备 {device.name}，原用户 {previous_user} 已加入排队列表首位"
        )

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
    
    if not device.support_queue:
        raise HTTPException(status_code=400, detail="该设备不支持排队等待")
    
    usage_info = await DeviceUsage.filter(device=device).first()
    if not usage_info:
        usage_info = await DeviceUsage.create(device=device)
    
    # 检查设备状态
    if usage_info.status == DeviceStatusEnum.AVAILABLE:
        # 设备可用，直接占用
        usage_info.current_user = request.user
        usage_info.start_time = get_current_time()
        usage_info.expected_duration = request.expected_duration
        usage_info.status = DeviceStatusEnum.OCCUPIED
        await usage_info.save()
        
        # 创建使用历史记录
        await DeviceUsageHistory.create(
            device=device,
            user=request.user,
            start_time=get_current_time(),
            purpose=request.purpose
        )

        # 记录优先排队操作日志（设备可用时直接占用）
        await OperationLog.create_log(
            user=current_user,
            operation_type="device_priority_queue",
            operation_result="success",
            device_name=device.name,
            description=f"优先排队设备 {device.name}（设备可用，直接占用）"
        )

        return BaseResponse(
            code=200,
            message="设备占用成功",
            data={"device_id": device.id}
        )
    
    elif usage_info.status == DeviceStatusEnum.OCCUPIED:
        # 检查是否是当前使用者尝试排队
        if usage_info.current_user == request.user:
            raise HTTPException(status_code=400, detail="您已经在使用此设备")
        
        # 检查用户是否已在排队
        if request.user in (usage_info.queue_users or []):
            raise HTTPException(status_code=400, detail="您已在排队中")
        
        # 优先加入排队列表首位
        if not usage_info.queue_users:
            usage_info.queue_users = []
        usage_info.queue_users.insert(0, request.user)
        await usage_info.save()

        # 记录优先排队操作日志
        await OperationLog.create_log(
            user=current_user,
            operation_type="device_priority_queue",
            operation_result="success",
            device_name=device.name,
            description=f"优先排队设备 {device.name}，排队位置: 1"
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
    
    usage_info = await DeviceUsage.filter(device=device).first()
    if not usage_info:
        usage_info = await DeviceUsage.create(device=device)
    
    # 检查设备状态
    if usage_info.status == DeviceStatusEnum.AVAILABLE:
        # 设备可用，直接占用
        usage_info.current_user = request.user
        usage_info.start_time = get_current_time()
        usage_info.expected_duration = request.expected_duration
        usage_info.status = DeviceStatusEnum.OCCUPIED
        await usage_info.save()
        
        # 创建使用历史记录
        await DeviceUsageHistory.create(
            device=device,
            user=request.user,
            start_time=get_current_time(),
            purpose=request.purpose
        )

        # 记录统一排队操作日志（设备可用时直接使用）
        await OperationLog.create_log(
            user=current_user,
            operation_type="device_unified_queue",
            operation_result="success",
            device_name=device.name,
            description=f"统一排队设备 {device.name}（设备可用，直接使用）"
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
        if usage_info.current_user == request.user:
            raise HTTPException(status_code=400, detail="您已经在使用此设备")
        
        # 检查用户是否已在排队
        if request.user in (usage_info.queue_users or []):
            raise HTTPException(status_code=400, detail="您已在排队中")
        
        # 加入排队列表末尾
        if not usage_info.queue_users:
            usage_info.queue_users = []
        usage_info.queue_users.append(request.user)
        await usage_info.save()

        # 记录统一排队操作日志（加入排队）
        await OperationLog.create_log(
            user=current_user,
            operation_type="device_unified_queue",
            operation_result="success",
            device_name=device.name,
            description=f"统一排队设备 {device.name}，排队位置: {len(usage_info.queue_users)}"
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


@router.post("/batch-release-my-devices", summary="批量释放我的设备")
async def batch_release_my_devices(current_user: User = Depends(AuthManager.get_current_user)):
    """批量释放当前用户占用的所有设备"""
    try:
        # 查找当前用户占用的所有设备
        usage_infos = await DeviceUsage.filter(current_user=current_user.employee_id).prefetch_related("device")

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
                # 释放设备
                usage_info.current_user = None
                usage_info.start_time = None
                usage_info.expected_duration = 0  # 设置为0而不是None
                usage_info.purpose = None
                usage_info.status = DeviceStatusEnum.AVAILABLE
                usage_info.is_long_term = False
                usage_info.long_term_purpose = None

                # 如果有排队用户，让第一个用户占用设备
                if usage_info.queue_users:
                    next_user = usage_info.queue_users[0]
                    usage_info.current_user = next_user
                    usage_info.start_time = get_current_time()
                    usage_info.status = DeviceStatusEnum.OCCUPIED
                    usage_info.queue_users = usage_info.queue_users[1:]  # 移除第一个用户

                await usage_info.save()
                released_count += 1

                # 记录批量释放操作日志
                next_user_info = f"，设备已分配给下一个用户 {next_user}" if usage_info.queue_users else "，设备现在可用"
                await OperationLog.create_log(
                    user=current_user,
                    operation_type="device_batch_release",
                    operation_result="success",
                    device_name=usage_info.device.name,
                    description=f"批量释放设备 {usage_info.device.name}{next_user_info}"
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

        for usage_info in all_usage_infos:
            if usage_info.queue_users and current_user.employee_id in usage_info.queue_users:
                try:
                    # 从排队列表中移除当前用户
                    queue_users = usage_info.queue_users.copy()
                    queue_users.remove(current_user.employee_id)
                    usage_info.queue_users = queue_users

                    await usage_info.save()
                    cancelled_count += 1

                    # 记录批量取消排队操作日志
                    await OperationLog.create_log(
                        user=current_user,
                        operation_type="device_batch_cancel_queue",
                        operation_result="success",
                        device_name=usage_info.device.name,
                        description=f"批量取消设备 {usage_info.device.name} 排队"
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
    if not (current_user.is_superuser or current_user.role == '管理员'):
        raise HTTPException(status_code=403, detail="权限不足，只有管理员可以执行此操作")

    try:
        # 导入调度器（避免循环导入）
        from scheduler.scheduler import device_scheduler

        # 执行清理任务
        await device_scheduler.force_cleanup_all_devices()

        return BaseResponse(
            code=200,
            message="所有设备已强制清理完成",
            data={"action": "force_cleanup_all", "executor": current_user.employee_id}
        )

    except Exception as e:
        print(f"管理员强制清理失败: {e}")
        raise HTTPException(status_code=500, detail="强制清理失败")