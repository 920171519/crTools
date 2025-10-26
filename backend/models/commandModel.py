"""
命令行集数据模型
定义命令行的基本信息和操作日志
"""
from tortoise.models import Model
from tortoise import fields


class Command(Model):
    """命令行模型"""

    id = fields.IntField(pk=True, description="命令ID")
    command_text = fields.CharField(max_length=1000, description="命令内容")
    link = fields.CharField(max_length=1000, null=True, description="介绍网页链接")
    remarks = fields.TextField(null=True, description="备注内容")
    creator = fields.CharField(max_length=50, description="创建人工号")
    last_editor = fields.CharField(max_length=50, null=True, description="最后编辑人工号")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")
    
    class Meta:
        table = "commands"
        table_description = "命令行集表"
    
    def __str__(self):
        return f"{self.command_text[:50]}"


class CommandOperationLog(Model):
    """命令行操作日志模型"""

    id = fields.IntField(pk=True, description="日志ID")
    command_id = fields.IntField(description="命令ID")
    employee_id = fields.CharField(max_length=20, description="操作人工号")
    username = fields.CharField(max_length=50, description="操作人用户名")
    operation_type = fields.CharField(max_length=50, description="操作类型")
    operation_result = fields.CharField(max_length=20, default="success", description="操作结果")
    description = fields.TextField(null=True, description="操作描述")
    ip_address = fields.CharField(max_length=45, null=True, description="IP地址")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")

    class Meta:
        table = "command_operation_logs"
        table_description = "命令行操作日志表"

    @classmethod
    async def create_log(
        cls,
        command_id: int,
        user: "User",
        operation_type: str,
        operation_result: str = "success",
        description: str = None,
        ip_address: str = None
    ):
        """创建命令行操作日志的便捷方法"""
        return await cls.create(
            command_id=command_id,
            employee_id=user.employee_id,
            username=user.username,
            operation_type=operation_type,
            operation_result=operation_result,
            description=description,
            ip_address=ip_address
        )

