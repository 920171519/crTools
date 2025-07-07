"""
用户管理相关的API路由
包含用户列表查询、用户角色更新等功能
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from tortoise.expressions import Q
from models.admin import User, Role
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
    role_name: Optional[str] = Query(None, description="角色搜索"),
    current_user: User = require_active_user,
    _: bool = require_user_read
):
    """
    获取用户列表
    - 支持分页
    - 支持按工号、姓名、角色搜索
    - 需要user:read权限
    """
    # 构建查询条件
    query = User.all().prefetch_related('role')
    
    if employee_id:
        query = query.filter(employee_id__icontains=employee_id)
    if username:
        query = query.filter(username__icontains=username)
    if role_name:
        query = query.filter(role__name__icontains=role_name)
    
    # 获取总数
    total = await query.count()
    
    # 分页查询
    offset = (page - 1) * page_size
    users = await query.offset(offset).limit(page_size).distinct()
    
    # 转换为响应格式
    user_list = []
    for user in users:
        # 获取用户角色
        role_name = await user.get_role_name()
        
        user_data = {
            "id": user.id,
            "employee_id": user.employee_id,
            "username": user.username,
            "role": role_name,
            "is_superuser": user.is_superuser,
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


@router.put("/{user_id}/role", response_model=BaseResponse, summary="更新用户主要角色")
async def update_user_role(
    user_id: int,
    new_role_name: str,
    current_user: User = require_active_user,
    _: bool = require_user_update
):
    """
    更新用户主要角色
    - 只有管理员可以修改用户角色
    - 不能修改超级用户的角色
    - 可选角色：普通用户、高级用户、管理员
    """
    # 验证新角色是否有效
    valid_roles = ["普通用户", "高级用户", "管理员"]
    if new_role_name not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的角色类型，只能设置为：{', '.join(valid_roles)}"
        )
    
    # 检查权限：只有管理员或超级用户可以修改
    if not (current_user.is_superuser or await current_user.has_role("管理员")):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以修改用户角色"
        )
    
    # 获取目标用户
    target_user = await User.filter(id=user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 不能修改超级用户的角色
    if target_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能修改超级用户的角色"
        )
    
    # 不能修改自己的角色
    if target_user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能修改自己的角色"
        )
    
    # 获取新角色
    new_role = await Role.filter(name=new_role_name).first()
    if not new_role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="指定的角色不存在"
        )
    
    # 获取当前角色名称
    old_role_name = await target_user.get_role_name()

    # 直接更新用户角色
    try:
        target_user.role = new_role
        await target_user.save()
    except Exception as e:
        print(f"更新用户角色时发生错误: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新用户角色失败，请稍后重试"
        )
    
    return BaseResponse(
        code=200,
        message=f"用户角色已从{old_role_name}更新为{new_role_name}",
        data={
            "user_id": user_id,
            "old_role": old_role_name,
            "new_role": new_role_name
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
    await user.fetch_related('role')
    role_name = await user.get_role_name()

    return BaseResponse(
        code=200,
        message="获取用户信息成功",
        data={
            "id": user.id,
            "employee_id": user.employee_id,
            "username": user.username,
            "role": role_name,
            "is_superuser": user.is_superuser
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
    
    # 删除用户（角色关联会自动处理）
    await target_user.delete()
    
    return BaseResponse(
        code=200,
        message="用户删除成功",
        data={"deleted_user_id": user_id}
    )


@router.get("/roles/list", response_model=BaseResponse, summary="获取可用角色列表")
async def get_available_roles(
    current_user: User = require_active_user,
    _: bool = require_user_read
):
    """
    获取可用角色列表
    """
    roles = await Role.filter(name__in=["普通用户", "高级用户", "管理员"]).order_by('-priority')
    
    role_list = []
    for role in roles:
        role_list.append({
            "id": role.id,
            "name": role.name,
            "description": role.description,
            "priority": role.priority
        })
    
    return BaseResponse(
        code=200,
        message="获取角色列表成功",
        data={"roles": role_list}
    ) 