"""
操作日志路由
"""
from fastapi import APIRouter, Depends, Query
from typing import Optional
from models.admin import OperationLog, LoginLog, User
from schemas import BaseResponse
from auth import AuthManager

router = APIRouter(prefix="/api/operation-logs", tags=["操作日志"])

@router.get("", summary="获取操作日志列表")
async def get_operation_logs(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    employee_id: Optional[str] = Query(None, description="工号"),
    operation_type: Optional[str] = Query(None, description="操作类型"),
    start_date: Optional[str] = Query(None, description="开始日期"),
    end_date: Optional[str] = Query(None, description="结束日期"),
    current_user: User = Depends(AuthManager.get_current_user)
):
    """获取操作日志列表"""
    try:
        # 构建查询条件
        query_conditions = {}
        
        if employee_id:
            query_conditions["employee_id__icontains"] = employee_id
        
        # 处理操作类型过滤
        if operation_type:
            if operation_type in ["login", "logout"]:
                # 查询登录日志
                login_query = LoginLog.all()
                
                if employee_id:
                    # 通过用户关联查询
                    login_query = login_query.filter(user__employee_id__icontains=employee_id)
                
                # 分页
                offset = (page - 1) * page_size
                login_logs = await login_query.offset(offset).limit(page_size).prefetch_related('user')
                total = await login_query.count()
                
                # 转换为统一格式
                items = []
                for log in login_logs:
                    items.append({
                        "id": log.id,
                        "employee_id": log.user.employee_id,
                        "username": log.user.username,
                        "operation_type": "login" if log.login_result else "logout",
                        "operation_result": "success" if log.login_result else "failed",
                        "device_name": None,
                        "description": f"用户{'登录成功' if log.login_result else '登录失败'}",
                        "ip_address": log.ip_address,
                        "user_agent": log.user_agent,
                        "created_at": log.login_time.isoformat() if log.login_time else None
                    })
                
                return BaseResponse(
                    code=200,
                    message="获取登录日志成功",
                    data={
                        "items": items,
                        "total": total,
                        "page": page,
                        "page_size": page_size
                    }
                )
            
            elif operation_type == "device":
                # 查询设备操作日志
                query_conditions["operation_type__not_in"] = ["login", "logout"]
        
        # 查询操作日志
        query = OperationLog.all()
        
        # 应用过滤条件
        if query_conditions:
            query = query.filter(**query_conditions)
        
        # 日期范围过滤
        if start_date:
            query = query.filter(created_at__gte=start_date)
        if end_date:
            query = query.filter(created_at__lte=end_date)
        
        # 分页
        total = await query.count()
        offset = (page - 1) * page_size
        logs = await query.offset(offset).limit(page_size).order_by('-created_at')
        
        # 转换为字典格式
        items = []
        for log in logs:
            items.append({
                "id": log.id,
                "employee_id": log.employee_id,
                "username": log.username,
                "operation_type": log.operation_type,
                "operation_result": log.operation_result,
                "device_name": log.device_name,
                "description": log.description,
                "ip_address": log.ip_address,
                "user_agent": log.user_agent,
                "created_at": log.created_at.isoformat() if log.created_at else None
            })
        
        return BaseResponse(
            code=200,
            message="获取操作日志成功",
            data={
                "items": items,
                "total": total,
                "page": page,
                "page_size": page_size
            }
        )
        
    except Exception as e:
        print(f"获取操作日志失败: {e}")
        return BaseResponse(
            code=500,
            message="获取操作日志失败",
            data=None
        )
