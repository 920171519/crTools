"""
系统设置路由
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from models.systemModel import SystemSettings
from models.admin import User
from schemas import BaseResponse
from auth import AuthManager
from scheduler.scheduler import device_scheduler

router = APIRouter(prefix="/system", tags=["系统设置"])

class SystemSettingsRequest(BaseModel):
    """系统设置请求模型"""
    cleanup_time: Optional[str] = None

class SystemSettingsResponse(BaseModel):
    """系统设置响应模型"""
    cleanup_time: Optional[str] = None
    updated_at: Optional[str] = None

@router.get("/settings", summary="获取系统设置")
async def get_system_settings(current_user: User = Depends(AuthManager.get_current_user)):
    """获取系统设置"""
    # 检查权限
    await current_user.fetch_related('role')
    if not (current_user.is_superuser or (current_user.role and current_user.role.name == '管理员')):
        raise HTTPException(status_code=403, detail="权限不足")
    
    try:
        # 获取系统设置，如果不存在则创建默认设置
        settings = await SystemSettings.first()
        if not settings:
            settings = await SystemSettings.create(cleanup_time="00:30")
        
        return BaseResponse(
            code=200,
            message="获取系统设置成功",
            data={
                "cleanup_time": settings.cleanup_time,
                "updated_at": settings.updated_at.strftime("%Y-%m-%d %H:%M:%S") if settings.updated_at else None
            }
        )
    except Exception as e:
        print(f"获取系统设置失败: {e}")
        raise HTTPException(status_code=500, detail="获取系统设置失败")

@router.put("/settings", summary="更新系统设置")
async def update_system_settings(
    request: SystemSettingsRequest,
    current_user: User = Depends(AuthManager.get_current_user)
):
    """更新系统设置"""
    # 检查权限
    await current_user.fetch_related('role')
    if not (current_user.is_superuser or (current_user.role and current_user.role.name == '管理员')):
        raise HTTPException(status_code=403, detail="权限不足")
    
    try:
        # 验证时间格式
        if request.cleanup_time:
            try:
                hours, minutes = request.cleanup_time.split(':')
                hours, minutes = int(hours), int(minutes)
                if not (0 <= hours <= 23 and 0 <= minutes <= 59):
                    raise ValueError("时间范围无效")
            except (ValueError, IndexError):
                raise HTTPException(status_code=400, detail="时间格式无效，请使用 HH:MM 格式")
        
        # 获取或创建系统设置
        settings = await SystemSettings.first()
        if not settings:
            settings = await SystemSettings.create(cleanup_time=request.cleanup_time)
        else:
            settings.cleanup_time = request.cleanup_time
            await settings.save()
        
        # 更新调度器的定时任务
        try:
            await device_scheduler.update_cleanup_schedule(request.cleanup_time)
        except Exception as e:
            print(f"更新调度器失败: {e}")
            # 不抛出异常，因为设置已保存成功
        
        return BaseResponse(
            code=200,
            message="系统设置更新成功",
            data={
                "cleanup_time": settings.cleanup_time,
                "updated_at": settings.updated_at.strftime("%Y-%m-%d %H:%M:%S")
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"更新系统设置失败: {e}")
        raise HTTPException(status_code=500, detail="更新系统设置失败")
