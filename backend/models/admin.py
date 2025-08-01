"""
数据模型定义
定义用户、权限等数据库表结构
"""
from tortoise.models import Model
from tortoise import fields
import re
from datetime import datetime
from enum import Enum


class User(Model):
    """用户模型 - 基于工号的认证系统"""
    
    id = fields.IntField(pk=True, description="用户ID")
    employee_id = fields.CharField(max_length=9, unique=True, description="工号(一个字母+8个数字)")
    username = fields.CharField(max_length=50, description="姓名")
    hashed_password = fields.CharField(max_length=100, description="加密后的密码")
    is_superuser = fields.BooleanField(default=False, description="是否为超级用户")
    # 直接关联单个角色，简化设计
    role = fields.ForeignKeyField("models.Role", related_name="users", null=True, description="用户角色")

    
    class Meta:
        table = "users"
        table_description = "用户表"
    
    def __str__(self):
        return f"{self.employee_id}({self.username})"
    
    async def has_role(self, role_name: str) -> bool:
        """检查用户是否有指定角色"""
        if self.is_superuser:
            return True  # 超级用户拥有所有权限
        if not self.role:
            return False
        await self.fetch_related('role')
        return self.role.name == role_name
    
    async def get_role_name(self) -> str:
        """获取用户角色名称"""
        if self.is_superuser:
            return "超级管理员"
        if not self.role:
            return "普通用户"
        await self.fetch_related('role')
        return self.role.name

    
    @classmethod
    def validate_employee_id(cls, employee_id: str) -> bool:
        """验证工号格式：一个字母+8个数字"""
        pattern = r'^[A-Za-z]\d{8}$'
        return bool(re.match(pattern, employee_id))


class Role(Model):
    """角色模型"""
    
    id = fields.IntField(pk=True, description="角色ID")
    name = fields.CharField(max_length=50, unique=True, description="角色名称")
    description = fields.CharField(max_length=200, null=True, description="角色描述")
    # 角色优先级，数值越大优先级越高
    priority = fields.IntField(default=0, description="角色优先级")
    
    # 关联用户（反向关系由User.role定义）
    users: fields.ReverseRelation["User"]
    # 关联权限
    permissions: fields.ReverseRelation["RolePermission"]
    
    class Meta:
        table = "roles"
        table_description = "角色表"
    
    def __str__(self):
        return self.name


class Permission(Model):
    """权限模型"""
    
    id = fields.IntField(pk=True, description="权限ID")
    name = fields.CharField(max_length=50, unique=True, description="权限名称")
    code = fields.CharField(max_length=50, unique=True, description="权限代码")
    description = fields.CharField(max_length=200, null=True, description="权限描述")
    resource = fields.CharField(max_length=100, description="资源名称")
    action = fields.CharField(max_length=50, description="动作类型(create/read/update/delete)")
    
    # 关联角色
    roles: fields.ReverseRelation["RolePermission"]
    
    class Meta:
        table = "permissions"
        table_description = "权限表"
    
    def __str__(self):
        return f"{self.name}({self.code})"


# UserRole表已移除 - 改为User直接关联Role的一对多关系


class RolePermission(Model):
    """角色权限关联表"""
    
    id = fields.IntField(pk=True, description="关联ID")
    role = fields.ForeignKeyField("models.Role", related_name="role_permissions", description="角色")
    permission = fields.ForeignKeyField("models.Permission", related_name="permission_roles", description="权限")
    
    class Meta:
        table = "role_permissions"
        table_description = "角色权限关联表"
        unique_together = ("role", "permission")


class Menu(Model):
    """菜单模型 - 用于动态生成前端菜单"""
    
    id = fields.IntField(pk=True, description="菜单ID")
    name = fields.CharField(max_length=50, description="菜单名称")
    path = fields.CharField(max_length=200, description="路由路径")
    component = fields.CharField(max_length=200, null=True, description="组件路径")
    icon = fields.CharField(max_length=50, null=True, description="菜单图标")
    parent_id = fields.IntField(null=True, description="父菜单ID")
    sort_order = fields.IntField(default=0, description="排序")
    is_visible = fields.BooleanField(default=True, description="是否显示")
    permission_code = fields.CharField(max_length=50, null=True, description="所需权限代码")

    
    class Meta:
        table = "menus"
        table_description = "菜单表"
    
    def __str__(self):
        return self.name


class LoginLog(Model):
    """登录日志模型"""

    id = fields.IntField(pk=True, description="日志ID")
    user = fields.ForeignKeyField("models.User", related_name="login_logs", description="用户")
    login_time = fields.DatetimeField(auto_now_add=True, description="登录时间")
    ip_address = fields.CharField(max_length=45, description="IP地址")
    login_result = fields.BooleanField(description="登录结果")
    failure_reason = fields.CharField(max_length=200, null=True, description="失败原因")

    class Meta:
        table = "login_logs"
        table_description = "登录日志表"


class OperationLog(Model):
    """操作日志模型"""

    id = fields.IntField(pk=True, description="日志ID")
    employee_id = fields.CharField(max_length=20, description="操作人工号")
    username = fields.CharField(max_length=50, description="操作人用户名")
    operation_type = fields.CharField(max_length=50, description="操作类型")
    operation_result = fields.CharField(max_length=20, default="success", description="操作结果")
    device_name = fields.CharField(max_length=100, null=True, description="设备名称")
    description = fields.TextField(null=True, description="操作描述")
    ip_address = fields.CharField(max_length=45, null=True, description="IP地址")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")

    class Meta:
        table = "operation_logs"
        table_description = "操作日志表"

    @classmethod
    async def create_log(
        cls,
        user: "User",
        operation_type: str,
        operation_result: str = "success",
        device_name: str = None,
        description: str = None,
        ip_address: str = None
    ):
        """创建操作日志的便捷方法"""
        return await cls.create(
            employee_id=user.employee_id,
            username=user.username,
            operation_type=operation_type,
            operation_result=operation_result,
            device_name=device_name,
            description=description,
            ip_address=ip_address
        )
