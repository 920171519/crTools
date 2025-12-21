"""
认证相关的API路由
包含用户注册、登录、登出等功能
"""
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from tortoise import models
from tortoise.expressions import Q
from models.admin import User, Role
from models.admin import Permission, RolePermission
from models.admin import Menu, Permission
from models.groupModel import Group, GroupMember
from schemas import (
    UserRegister, UserLogin, UserResponse, Token,
    BaseResponse, PasswordChange
)
from auth import AuthManager, LoginManager, require_active_user
from config import settings

router = APIRouter(prefix="/auth", tags=["认证"])


def serialize_user_groups(user: User) -> list:
    """序列化用户所属分组"""
    groups = []
    memberships = getattr(user, "group_memberships", []) or []
    for membership in memberships:
        if membership.group:
            groups.append({
                "id": membership.group.id,
                "name": membership.group.name,
                "description": membership.group.description
            })
    return groups


@router.post("/register", response_model=BaseResponse, summary="用户注册")
async def register(user_data: UserRegister):
    """
    用户注册接口
    - 验证工号格式（一个字母+8个数字）
    - 检查工号是否已存在
    - 创建新用户账户
    """
    # 检查工号是否已存在
    existing_user = await User.filter(employee_id=user_data.employee_id).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该工号已被注册"
        )

    # 检查姓名是否已存在
    existing_username = await User.filter(username=user_data.username).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="姓名已被使用"
        )

    # 创建用户
    hashed_password = AuthManager.get_password_hash(user_data.password)
    user = await User.create(
        employee_id=user_data.employee_id,
        username=user_data.username,
        hashed_password=hashed_password,
        is_superuser=False  # 新用户默认不是超级用户
    )

    # 为新用户分配默认角色
    default_role = await Role.filter(name="普通用户").first()
    if default_role:
        user.role = default_role
        await user.save()

    # 将新用户加入默认分组
    default_group = await Group.filter(name="公共组").first()
    if default_group:
        await GroupMember.get_or_create(group=default_group, user=user)

    return BaseResponse(
        code=200,
        message="注册成功",
        data={"user_id": user.id, "employee_id": user.employee_id}
    )


@router.post("/login", response_model=BaseResponse, summary="用户登录")
async def login(request: Request, login_data: UserLogin):
    """
    用户登录接口
    - 验证工号和密码
    - 生成JWT访问令牌
    - 记录登录日志
    """
    # 获取客户端信息
    ip_address = LoginManager.get_client_ip(request)

    # 认证用户
    user = await AuthManager.authenticate_user(
        login_data.employee_id,
        login_data.password
    )
    if not user:
        # 记录失败的登录尝试
        failed_user = await User.filter(employee_id=login_data.employee_id).first()
        await LoginManager.record_login_attempt(
            user=failed_user,
            ip_address=ip_address,
            success=False,
            failure_reason="姓名或密码错误"
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="姓名或密码错误"
        )

    # 创建访问令牌
    access_token_expires = timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = AuthManager.create_access_token(
        data={"sub": user.employee_id},
        expires_delta=access_token_expires
    )

    # 记录成功的登录
    await LoginManager.record_login_attempt(
        user=user,
        ip_address=ip_address,
        success=True
    )

    # 获取用户角色与分组
    await user.fetch_related('group_memberships__group', 'role')
    role_name = await user.get_role_name()
    group_data = serialize_user_groups(user)

    return BaseResponse(
        code=200,
        message="登录成功",
        data={
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": {
                "id": user.id,
                "employee_id": user.employee_id,
                "username": user.username,
                "is_superuser": user.is_superuser,
                "role": role_name,
                "groups": group_data
            }
        }
    )


@router.post("/logout", response_model=BaseResponse, summary="用户登出")
async def logout(request: Request, current_user: User = require_active_user):
    """
    用户登出接口
    注意：JWT是无状态的，真正的登出需要在前端删除token
    这里主要用于记录登出日志
    """
    # 获取客户端信息
    ip_address = LoginManager.get_client_ip(request)

    # 记录登出日志
    await LoginManager.record_logout_attempt(
        user=current_user,
        ip_address=ip_address
    )

    return BaseResponse(
        code=200,
        message="登出成功",
        data={"employee_id": current_user.employee_id}
    )


@router.get("/me", response_model=BaseResponse, summary="获取当前用户信息")
async def get_current_user_info(current_user: User = require_active_user):
    """
    获取当前登录用户的详细信息
    """
    await current_user.fetch_related('group_memberships__group', 'role')
    # 获取用户角色
    role_name = await current_user.get_role_name()

    return BaseResponse(
        code=200,
        message="获取用户信息成功",
        data={
            "id": current_user.id,
            "employee_id": current_user.employee_id,
            "username": current_user.username,
            "is_superuser": current_user.is_superuser,
            "role": role_name,
            "groups": serialize_user_groups(current_user)
        }
    )


@router.post("/change-password", response_model=BaseResponse, summary="修改密码")
async def change_password(
    password_data: PasswordChange,
    current_user: User = require_active_user
):
    """
    修改当前用户密码
    """
    # 验证旧密码
    if not AuthManager.verify_password(password_data.old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="原密码错误"
        )

    # 更新密码
    current_user.hashed_password = AuthManager.get_password_hash(
        password_data.new_password)
    await current_user.save()

    return BaseResponse(
        code=200,
        message="密码修改成功"
    )


@router.get("/permissions", response_model=BaseResponse, summary="获取当前用户权限")
async def get_user_permissions(current_user: User = require_active_user):
    """
    获取当前用户的权限列表
    """

    if current_user.is_superuser:
        # 超级用户拥有所有权限
        all_permissions = await Permission.all().values('code', 'name', 'description')
        return BaseResponse(
            code=200,
            message="获取权限成功",
            data={"permissions": list(all_permissions)}
        )

    # 普通用户通过角色获取权限
    if current_user.role:
        permissions = await Permission.filter(
            permission_roles__role_id=current_user.role_id
        ).values('code', 'name', 'description')
    else:
        permissions = []

    return BaseResponse(
        code=200,
        message="获取权限成功",
        data={"permissions": list(permissions)}
    )


@router.get("/menus", response_model=BaseResponse, summary="获取用户菜单")
async def get_user_menus(current_user: User = require_active_user):
    """
    获取当前用户可访问的菜单列表
    """

    # 获取用户权限代码列表
    if current_user.is_superuser:
        # 超级用户看到所有菜单
        menus = await Menu.filter(is_visible=True).order_by('sort_order')
    else:
        # 获取用户权限
        if current_user.role:
            user_permissions = await Permission.filter(
                permission_roles__role_id=current_user.role_id
            ).values_list('code', flat=True)
        else:
            user_permissions = []

        # 获取有权限的菜单或无权限要求的菜单
        menus = await Menu.filter(
            is_visible=True
        ).filter(
            Q(permission_code__in=user_permissions) |
            Q(permission_code__isnull=True)
        ).order_by('sort_order')

    # 构建菜单树
    menu_dict = {}
    root_menus = []

    for menu in menus:
        menu_data = {
            "id": menu.id,
            "name": menu.name,
            "path": menu.path,
            "component": menu.component,
            "icon": menu.icon,
            "parent_id": menu.parent_id,
            "sort_order": menu.sort_order,
            "children": []
        }
        menu_dict[menu.id] = menu_data

        if menu.parent_id is None:
            root_menus.append(menu_data)

    # 构建树形结构
    for menu_id, menu_data in menu_dict.items():
        if menu_data["parent_id"] is not None:
            parent = menu_dict.get(menu_data["parent_id"])
            if parent:
                parent["children"].append(menu_data)

    # 过滤掉没有子菜单的父菜单（如果父菜单本身没有component）
    filtered_root_menus = []
    for menu in root_menus:
        if menu["component"] is not None:
            # 有组件的菜单（叶子菜单）直接显示
            filtered_root_menus.append(menu)
        else:
            # 没有组件的菜单（父菜单）只有在有可访问的子菜单时才显示
            if menu["children"]:
                filtered_root_menus.append(menu)

    return BaseResponse(
        code=200,
        message="获取菜单成功",
        data={"menus": filtered_root_menus}
    )
