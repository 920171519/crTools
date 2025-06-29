"""
数据库配置和初始化
"""
from tortoise import Tortoise
from tortoise.contrib.fastapi import register_tortoise
from config import settings
from auth import AuthManager


# Tortoise ORM 配置
TORTOISE_ORM = {
    "connections": {
        "default": settings.DATABASE_URL
    },
    "apps": {
        "models": {
            "models": ["models", "aerich.models"],
            "default_connection": "default",
        },
    },
}


async def init_database():
    """初始化数据库"""
    from models.admin import User, Role, Permission, UserRole, RolePermission, Menu
    # 创建超级管理员用户（如果不存在）
    admin_user = await User.filter(employee_id="a12345678").first()
    if not admin_user:
        admin_user = await User.create(
            employee_id = "a12345678",
            username = "超级管理员",
            hashed_password = AuthManager.get_password_hash("admin123"),
            is_superuser = True,
        )
        print("✅ 创建默认超级管理员账号: a12345678 / admin123")
    
    # 创建默认角色
    roles_data = [
        {"name": "超级管理员", "description": "系统超级管理员，拥有所有权限"},
        {"name": "管理员", "description": "系统管理员，拥有大部分权限"},
        {"name": "普通用户", "description": "普通用户，拥有基本权限"}
    ]
    
    for role_data in roles_data:
        role = await Role.filter(name=role_data["name"]).first()
        if not role:
            role = await Role.create(**role_data)
            print(f"✅ 创建角色: {role.name}")
    
    # 创建默认权限
    permissions_data = [
        # 用户管理权限
        {"name": "用户查看", "code": "user:read", "resource": "user", "action": "read", "description": "查看用户信息"},
        {"name": "用户创建", "code": "user:create", "resource": "user", "action": "create", "description": "创建用户"},
        {"name": "用户更新", "code": "user:update", "resource": "user", "action": "update", "description": "更新用户信息"},
        {"name": "用户删除", "code": "user:delete", "resource": "user", "action": "delete", "description": "删除用户"},
        
        # 角色管理权限
        {"name": "角色查看", "code": "role:read", "resource": "role", "action": "read", "description": "查看角色信息"},
        {"name": "角色创建", "code": "role:create", "resource": "role", "action": "create", "description": "创建角色"},
        {"name": "角色更新", "code": "role:update", "resource": "role", "action": "update", "description": "更新角色信息"},
        {"name": "角色删除", "code": "role:delete", "resource": "role", "action": "delete", "description": "删除角色"},
        
        # 权限管理权限
        {"name": "权限查看", "code": "permission:read", "resource": "permission", "action": "read", "description": "查看权限信息"},
        {"name": "权限创建", "code": "permission:create", "resource": "permission", "action": "create", "description": "创建权限"},
        {"name": "权限更新", "code": "permission:update", "resource": "permission", "action": "update", "description": "更新权限信息"},
        {"name": "权限删除", "code": "permission:delete", "resource": "permission", "action": "delete", "description": "删除权限"},
        
        # 菜单管理权限
        {"name": "菜单查看", "code": "menu:read", "resource": "menu", "action": "read", "description": "查看菜单信息"},
        {"name": "菜单创建", "code": "menu:create", "resource": "menu", "action": "create", "description": "创建菜单"},
        {"name": "菜单更新", "code": "menu:update", "resource": "menu", "action": "update", "description": "更新菜单信息"},
        {"name": "菜单删除", "code": "menu:delete", "resource": "menu", "action": "delete", "description": "删除菜单"},
        
        # 系统管理权限
        {"name": "系统配置", "code": "system:config", "resource": "system", "action": "config", "description": "系统配置管理"},
        {"name": "系统日志", "code": "system:log", "resource": "system", "action": "log", "description": "查看系统日志"},
        
        # 设备管理权限
        {"name": "设备查看", "code": "device:read", "resource": "device", "action": "read", "description": "查看设备信息"},
        {"name": "设备创建", "code": "device:create", "resource": "device", "action": "create", "description": "创建设备"},
        {"name": "设备更新", "code": "device:update", "resource": "device", "action": "update", "description": "更新设备信息"},
        {"name": "设备删除", "code": "device:delete", "resource": "device", "action": "delete", "description": "删除设备"},
        {"name": "设备使用", "code": "device:use", "resource": "device", "action": "use", "description": "使用设备"},
    ]
    
    for perm_data in permissions_data:
        permission = await Permission.filter(code=perm_data["code"]).first()
        if not permission:
            permission = await Permission.create(**perm_data)
            print(f"✅ 创建权限: {permission.name}")
    
    # 创建默认菜单
    menus_data = [
        {
            "name": "首页",
            "path": "/dashboard",
            "component": "Dashboard",
            "icon": "Monitor",
            "parent_id": None,
            "sort_order": 1,
            "is_visible": True,
            "permission_code": None
        },
        {
            "name": "设备管理",
            "path": "/devices",
            "component": "DeviceManagement",
            "icon": "Monitor",
            "parent_id": None,
            "sort_order": 50,
            "is_visible": True,
            "permission_code": "device:read"
        },
        {
            "name": "环境管理",
            "path": "/system",
            "component": None,
            "icon": "Setting",
            "parent_id": None,
            "sort_order": 100,
            "is_visible": True,
            "permission_code": "user:read"
        }
    ]
    
    # 先创建父菜单
    for menu_data in menus_data:
        menu = await Menu.filter(path=menu_data["path"]).first()
        if not menu:
            menu = await Menu.create(**menu_data)
            print(f"✅ 创建菜单: {menu.name}")
    
    # 获取系统管理菜单ID
    system_menu = await Menu.filter(path="/system").first()
    if system_menu:
        sub_menus_data = [
            {
                "name": "用户管理",
                "path": "/system/users",
                "component": "UserManagement",
                "icon": "User",
                "parent_id": system_menu.id,
                "sort_order": 101,
                "is_visible": True,
                "permission_code": "user:read"
            },
            {
                "name": "角色管理",
                "path": "/system/roles",
                "component": "RoleManagement",
                "icon": "UserFilled",
                "parent_id": system_menu.id,
                "sort_order": 102,
                "is_visible": True,
                "permission_code": "role:read"
            },
            {
                "name": "权限管理",
                "path": "/system/permissions",
                "component": "PermissionManagement",
                "icon": "Key",
                "parent_id": system_menu.id,
                "sort_order": 103,
                "is_visible": True,
                "permission_code": "permission:read"
            },
            {
                "name": "菜单管理",
                "path": "/system/menus",
                "component": "MenuManagement",
                "icon": "Menu",
                "parent_id": system_menu.id,
                "sort_order": 104,
                "is_visible": True,
                "permission_code": "menu:read"
            },
            {
                "name": "登录日志",
                "path": "/system/logs",
                "component": "LoginLogs",
                "icon": "Document",
                "parent_id": system_menu.id,
                "sort_order": 105,
                "is_visible": True,
                "permission_code": "system:log"
            }
        ]
        
        for menu_data in sub_menus_data:
            menu = await Menu.filter(path=menu_data["path"]).first()
            if not menu:
                menu = await Menu.create(**menu_data)
                print(f"✅ 创建子菜单: {menu.name}")
    
    # 为超级管理员分配超级管理员角色
    super_admin_role = await Role.filter(name="超级管理员").first()
    if super_admin_role and admin_user:
        user_role = await UserRole.filter(user=admin_user, role=super_admin_role).first()
        if not user_role:
            await UserRole.create(user=admin_user, role=super_admin_role)
            print("✅ 为超级管理员分配角色")
    
    # 为普通用户角色分配基本权限（设备查看和使用）
    normal_user_role = await Role.filter(name="普通用户").first()
    if normal_user_role:
        # 普通用户需要的权限
        basic_permissions = [
            "device:read",  # 查看设备
            "device:use",   # 使用设备
        ]
        
        for perm_code in basic_permissions:
            permission = await Permission.filter(code=perm_code).first()
            if permission:
                # 检查权限是否已分配
                role_perm = await RolePermission.filter(role=normal_user_role, permission=permission).first()
                if not role_perm:
                    await RolePermission.create(role=normal_user_role, permission=permission)
                    print(f"✅ 为普通用户角色分配权限: {permission.name}")
    
    print("✅ 数据库初始化完成")


def setup_database(app):
    """设置数据库连接"""
    register_tortoise(
        app,
        config=TORTOISE_ORM,
        generate_schemas=True,
        add_exception_handlers=True,
    ) 