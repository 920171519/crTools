"""
设备管理路由
提供设备的增删改查、使用管理等API接口
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel

from models.deviceModel import Device, DeviceUsage, DeviceInternal, DeviceUsageHistory, DeviceStatusEnum
from models.admin import User
from schemas import (
    DeviceBase, DeviceUpdate, DeviceResponse, DeviceListItem,
    DeviceUsageResponse, DeviceUsageUpdate, DeviceUseRequest, DeviceReleaseRequest
)
from schemas import BaseResponse
from auth import AuthManager

router = APIRouter(prefix="/api/devices", tags=["设备管理"])


def get_current_time():
    """获取当前时间，统一使用naive datetime"""
    return datetime.now()


@router.get("/", response_model=BaseResponse, summary="获取设备列表")
async def get_devices(current_user: User = Depends(AuthManager.get_current_user)):
    """获取所有设备及其使用状态"""
    devices = await Device.all().prefetch_related("usage_info")
    result = []
    for device in devices:
        print(device)
        usage_info = await device.usage_info # 这里没有await，因为预取已经将关联对象加载到内存
        if not usage_info:
            # 创建默认使用情况
            usage_info = await DeviceUsage.create(device=device)
        
        # 计算占用时长
        occupied_duration = 0
        if usage_info.start_time and usage_info.current_user:
            # 统一使用naive datetime进行计算
            current_time = get_current_time()
            # 如果数据库中的时间是aware的，转换为naive
            start_time = usage_info.start_time.replace(tzinfo=None) if usage_info.start_time.tzinfo else usage_info.start_time
            duration = current_time - start_time
            occupied_duration = int(duration.total_seconds() / 60)
        
        # 检查当前用户是否在排队中
        is_current_user_in_queue = False
        if usage_info.queue_users and current_user.username in usage_info.queue_users:
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
        data=result
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
    """删除设备"""
    device = await Device.filter(id=device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    
    await device.delete()
    return {"message": "设备删除成功"}


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
        
        # 检查用户是否已在排队
        if request.user in (usage_info.queue_users or []):
            raise HTTPException(status_code=400, detail="您已在排队中")
        
        # 加入排队
        if not usage_info.queue_users:
            usage_info.queue_users = []
        usage_info.queue_users.append(request.user)
        await usage_info.save()
        
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
    
    # 检查权限：只有当前使用者或者管理员才能释放设备
    is_current_user = usage_info.current_user == current_user.username
    is_admin = current_user.is_superuser
    
    if not (is_current_user or is_admin):
        raise HTTPException(status_code=403, detail="只有当前使用者或管理员才能释放设备")
    
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
        
        return {"message": "设备已释放并分配给下一个用户", "next_user": next_user}
    else:
        # 没有排队，设备变为可用
        usage_info.current_user = None
        usage_info.start_time = None
        usage_info.expected_duration = 0
        usage_info.status = DeviceStatusEnum.AVAILABLE
        await usage_info.save()
        
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
    if not usage_info.queue_users or current_user.username not in usage_info.queue_users:
        raise HTTPException(status_code=400, detail="您当前不在排队中")
    
    # 从排队列表中移除用户
    usage_info.queue_users.remove(current_user.username)
    await usage_info.save()
    
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
    
    # 计算占用时长
    occupied_duration = 0
    if usage_info.start_time and usage_info.current_user:
        # 统一使用naive datetime进行计算
        current_time = get_current_time()
        # 如果数据库中的时间是aware的，转换为naive
        start_time = usage_info.start_time.replace(tzinfo=None) if usage_info.start_time.tzinfo else usage_info.start_time
        duration = current_time - start_time
        occupied_duration = int(duration.total_seconds() / 60)
    
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