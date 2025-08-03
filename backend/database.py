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
            "models": ["models.admin", "models.deviceModel", "models.systemModel", "models.vpnModel", "aerich.models"],
            "default_connection": "default",
        },
    },
}


async def init_database():
    """初始化数据库"""
    from models.admin import User, Role, Permission, RolePermission, Menu
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
        {"name": "超级管理员", "description": "系统超级管理员，拥有所有权限", "priority": 100},
        {"name": "管理员", "description": "系统管理员，拥有大部分权限", "priority": 80},
        {"name": "高级用户", "description": "高级用户，拥有较多权限", "priority": 60},
        {"name": "普通用户", "description": "普通用户，拥有基本权限", "priority": 40}
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
        

        
        # 系统管理权限
        {"name": "系统配置", "code": "system:config", "resource": "system", "action": "config", "description": "系统配置管理"},
        {"name": "系统日志", "code": "system:log", "resource": "system", "action": "log", "description": "查看系统日志"},
        
        # 设备管理权限
        {"name": "设备查看", "code": "device:read", "resource": "device", "action": "read", "description": "查看设备信息"},
        {"name": "设备创建", "code": "device:create", "resource": "device", "action": "create", "description": "创建设备"},
        {"name": "设备更新", "code": "device:update", "resource": "device", "action": "update", "description": "更新设备信息"},
        {"name": "设备删除", "code": "device:delete", "resource": "device", "action": "delete", "description": "删除设备"},
        {"name": "设备使用", "code": "device:use", "resource": "device", "action": "use", "description": "使用设备"},

        # 后台管理权限
        {"name": "后台管理", "code": "admin:read", "resource": "admin", "action": "read", "description": "访问后台管理"},
        {"name": "系统设置", "code": "admin:settings", "resource": "admin", "action": "settings", "description": "修改系统设置"},
        {"name": "VPN配置管理", "code": "admin:vpn", "resource": "admin", "action": "vpn", "description": "管理VPN配置"},
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
        # 直接显示子菜单，不要父菜单
        {
            "name": "用户管理",
            "path": "/system/users",
            "component": "UserManagement",
            "icon": "User",
            "parent_id": None,
            "sort_order": 101,
            "is_visible": True,
            "permission_code": "user:read"
        },

        {
            "name": "后台管理",
            "path": "/admin",
            "component": None,
            "icon": "Setting",
            "parent_id": None,
            "sort_order": 200,
            "is_visible": True,
            "permission_code": "admin:read"
        }
    ]
    
    # 创建所有菜单
    for menu_data in menus_data:
        menu = await Menu.filter(path=menu_data["path"]).first()
        if not menu:
            menu = await Menu.create(**menu_data)
            print(f"✅ 创建菜单: {menu.name}")

    # 获取后台管理菜单ID，创建设置子菜单
    admin_menu = await Menu.filter(path="/admin").first()
    if admin_menu:
        admin_sub_menus_data = [
            {
                "name": "系统设置",
                "path": "/admin/settings",
                "component": "SystemSettings",
                "icon": "Setting",
                "parent_id": admin_menu.id,
                "sort_order": 201,
                "is_visible": True,
                "permission_code": "admin:settings"
            },
            {
                "name": "VPN配置",
                "path": "/admin/vpn-config",
                "component": "VPNConfig",
                "icon": "Key",
                "parent_id": admin_menu.id,
                "sort_order": 202,
                "is_visible": True,
                "permission_code": "admin:vpn"
            }
        ]

        # 创建后台管理子菜单
        for sub_menu_data in admin_sub_menus_data:
            sub_menu = await Menu.filter(path=sub_menu_data["path"]).first()
            if not sub_menu:
                sub_menu = await Menu.create(**sub_menu_data)
                print(f"✅ 创建后台管理子菜单: {sub_menu.name}")
    
    # 为超级管理员分配超级管理员角色
    super_admin_role = await Role.filter(name="超级管理员").first()
    if super_admin_role and admin_user and not admin_user.role:
        admin_user.role = super_admin_role
        await admin_user.save()
        print("✅ 为超级管理员分配角色")
    
    # 为各角色分配权限
    
    # 为各角色分配权限

    # 普通用户权限
    normal_user_role = await Role.filter(name="普通用户").first()
    if normal_user_role:
        normal_permissions = [
            "device:read",  # 查看设备
            "device:use",   # 使用设备
        ]

        for perm_code in normal_permissions:
            permission = await Permission.filter(code=perm_code).first()
            if permission:
                role_perm = await RolePermission.filter(role=normal_user_role, permission=permission).first()
                if not role_perm:
                    await RolePermission.create(role=normal_user_role, permission=permission)
                    print(f"✅ 为普通用户角色分配权限: {permission.name}")

    # 高级用户权限（继承普通用户权限，增加设备管理权限）
    advanced_user_role = await Role.filter(name="高级用户").first()
    if advanced_user_role:
        advanced_permissions = [
            "device:read", "device:use",  # 基础权限
            "device:create", "device:update", "device:delete",  # 设备管理权限
        ]

        for perm_code in advanced_permissions:
            permission = await Permission.filter(code=perm_code).first()
            if permission:
                role_perm = await RolePermission.filter(role=advanced_user_role, permission=permission).first()
                if not role_perm:
                    await RolePermission.create(role=advanced_user_role, permission=permission)
                    print(f"✅ 为高级用户角色分配权限: {permission.name}")

    # 管理员权限（除了超级管理员功能外的所有权限）
    admin_role = await Role.filter(name="管理员").first()
    if admin_role:
        admin_permissions = [
            # 用户管理
            "user:read", "user:create", "user:update", "user:delete",
            # 系统管理
            "system:config", "system:log",
            # 设备管理
            "device:read", "device:create", "device:update", "device:delete", "device:use",
            # 后台管理
            "admin:read", "admin:settings", "admin:vpn",
        ]

        for perm_code in admin_permissions:
            permission = await Permission.filter(code=perm_code).first()
            if permission:
                role_perm = await RolePermission.filter(role=admin_role, permission=permission).first()
                if not role_perm:
                    await RolePermission.create(role=admin_role, permission=permission)
                    print(f"✅ 为管理员角色分配权限: {permission.name}")

    # 超级管理员权限（所有权限）
    super_admin_role = await Role.filter(name="超级管理员").first()
    if super_admin_role:
        # 获取所有权限
        all_permissions = await Permission.all()

        for permission in all_permissions:
            role_perm = await RolePermission.filter(role=super_admin_role, permission=permission).first()
            if not role_perm:
                await RolePermission.create(role=super_admin_role, permission=permission)
                print(f"✅ 为超级管理员角色分配权限: {permission.name}")
    
    print("✅ 数据库初始化完成")


def setup_database(app):
    """设置数据库连接"""
    register_tortoise(
        app,
        config=TORTOISE_ORM,
        generate_schemas=True,
        add_exception_handlers=True,
    ) 