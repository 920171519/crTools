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
        # 处理操作类型过滤
        if operation_type:
            # 支持逗号分隔的操作类型
            operation_types = [t.strip()
                               for t in operation_type.split(',') if t.strip()]
            if any(t in ["login", "logout"] for t in operation_types):
                # 查询登录日志
                login_query = LoginLog.all()

                if employee_id:
                    # 通过用户关联查询
                    login_query = login_query.filter(
                        user__employee_id__icontains=employee_id)

                # 获取所有登录日志用于过滤
                all_login_logs = await login_query.prefetch_related('user')

                # 根据操作类型过滤
                filtered_items = []
                for log in all_login_logs:
                    # 根据login_result和failure_reason判断操作类型
                    if log.login_result:
                        # 登录成功
                        log_operation_type = "login"
                        operation_result = "success"
                        description = "用户登录成功"
                    elif log.failure_reason == "用户主动登出":
                        # 用户登出
                        log_operation_type = "logout"
                        operation_result = "success"
                        description = "用户登出"
                    else:
                        # 登录失败
                        log_operation_type = "login"
                        operation_result = "failed"
                        description = f"用户登录失败: {log.failure_reason or '未知原因'}"

                    # 检查是否匹配搜索的操作类型
                    if log_operation_type in operation_types:
                        filtered_items.append({
                            "id": log.id,
                            "employee_id": log.user.employee_id,
                            "username": log.user.username,
                            "operation_type": log_operation_type,
                            "operation_result": operation_result,
                            "device_name": None,
                            "description": description,
                            "ip_address": log.ip_address,
                            "created_at": log.login_time.isoformat() if log.login_time else None
                        })

                # 手动分页
                total = len(filtered_items)
                offset = (page - 1) * page_size
                items = filtered_items[offset:offset + page_size]

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

            else:
                # 查询设备操作日志，添加操作类型过滤
                query = OperationLog.all()
                if employee_id:
                    query = query.filter(employee_id__icontains=employee_id)
                query = query.filter(operation_type__in=operation_types)
        else:
            # 查询操作日志并排除登录相关操作
            query = OperationLog.all()
            if employee_id:
                query = query.filter(employee_id__icontains=employee_id)
            query = query.exclude(operation_type__in=["login", "logout"])

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
