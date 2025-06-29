"""
用户管理相关的API路由
包含用户列表查询、用户信息更新等功能
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from tortoise.expressions import Q
from models.admin import User, Role, UserRole, UserTypeEnum
from schemas import BaseResponse, PaginationResponse, UserResponse
from auth import AuthManager, require_active_user, PermissionChecker, Permissions

router = APIRouter(prefix="/api/users", tags=["用户管理"])

# 权限检查器
require_user_read = Depends(PermissionChecker(Permissions.USER_READ))
require_user_update = Depends(PermissionChecker(Permissions.USER_UPDATE))
require_user_delete = Depends(PermissionChecker(Permissions.USER_DELETE))


@router.get("/", response_model=BaseResponse, summary="获取用户列表")
async def get_users(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    employee_id: Optional[str] = Query(None, description="工号搜索"),
    username: Optional[str] = Query(None, description="姓名搜索"),
    user_type: Optional[str] = Query(None, description="用户类型搜索"),
    current_user: User = require_active_user,
    _: bool = require_user_read
):
    """
    获取用户列表
    - 支持分页
    - 支持按工号、姓名、用户类型搜索
    - 需要user:read权限
    """
    # 构建查询条件
    query = User.all()
    
    if employee_id:
        query = query.filter(employee_id__icontains=employee_id)
    if username:
        query = query.filter(username__icontains=username)
    if user_type:
        query = query.filter(user_type=user_type)
    
    # 获取总数
    total = await query.count()
    
    # 分页查询
    offset = (page - 1) * page_size
    users = await query.offset(offset).limit(page_size)
    
    # 转换为响应格式
    user_list = []
    for user in users:
        # 获取用户角色
        user_roles = await UserRole.filter(user=user).prefetch_related('role')
        roles = [ur.role.name for ur in user_roles]
        
        user_data = {
            "id": user.id,
            "employee_id": user.employee_id,
            "username": user.username,
            "user_type": user.user_type,
            "is_superuser": user.is_superuser,
            "roles": roles
        }
        user_list.append(user_data)
    
    return BaseResponse(
        code=200,
        message="获取用户列表成功",
        data={
            "items": user_list,
            "total": total,
            "page": page,
            "page_size": page_size
        }
    )


@router.put("/{user_id}/type", response_model=BaseResponse, summary="更新用户类型")
async def update_user_type(
    user_id: int,
    new_type: str,
    current_user: User = require_active_user,
    _: bool = require_user_update
):
    """
    更新用户类型
    - 只有管理员可以修改普通用户和高级用户的类型
    - 不能修改超级用户的类型
    - 不能将用户设置为管理员类型（只能通过is_superuser字段）
    """
    # 验证新类型是否有效
    if new_type not in [UserTypeEnum.NORMAL, UserTypeEnum.ADVANCED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的用户类型，只能设置为普通用户或高级用户"
        )
    
    # 检查权限：只有管理员可以修改
    if not (current_user.is_superuser or current_user.user_type == UserTypeEnum.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以修改用户类型"
        )
    
    # 获取目标用户
    target_user = await User.filter(id=user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 不能修改超级用户的类型
    if target_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能修改超级用户的类型"
        )
    
    # 不能修改自己的类型
    if target_user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能修改自己的用户类型"
        )
    
    # 更新用户类型
    old_type = target_user.user_type
    target_user.user_type = new_type
    await target_user.save()
    
    return BaseResponse(
        code=200,
        message=f"用户类型已从{old_type}更新为{new_type}",
        data={
            "user_id": user_id,
            "old_type": old_type,
            "new_type": new_type
        }
    )


@router.get("/{user_id}", response_model=BaseResponse, summary="获取用户详情")
async def get_user_detail(
    user_id: int,
    current_user: User = require_active_user,
    _: bool = require_user_read
):
    """
    获取用户详细信息
    """
    user = await User.filter(id=user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 获取用户角色
    user_roles = await UserRole.filter(user=user).prefetch_related('role')
    roles = [ur.role.name for ur in user_roles]
    
    return BaseResponse(
        code=200,
        message="获取用户信息成功",
        data={
            "id": user.id,
            "employee_id": user.employee_id,
            "username": user.username,
            "user_type": user.user_type,
            "is_superuser": user.is_superuser,
            "roles": roles
        }
    )


@router.delete("/{user_id}", response_model=BaseResponse, summary="删除用户")
async def delete_user(
    user_id: int,
    current_user: User = require_active_user,
    _: bool = require_user_delete
):
    """
    删除用户
    - 不能删除超级用户
    - 不能删除自己
    """
    # 获取目标用户
    target_user = await User.filter(id=user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 不能删除超级用户
    if target_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除超级用户"
        )
    
    # 不能删除自己
    if target_user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除自己"
        )
    
    # 删除用户相关的角色关联
    await UserRole.filter(user=target_user).delete()
    
    # 删除用户
    await target_user.delete()
    
    return BaseResponse(
        code=200,
        message="用户删除成功",
        data={"deleted_user_id": user_id}
    ) 