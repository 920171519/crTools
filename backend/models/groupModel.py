"""
用户组与设备组关联模型
"""
from tortoise import fields
from tortoise.models import Model


class Group(Model):
    """用户-设备通用分组"""

    id = fields.IntField(pk=True, description="分组ID")
    name = fields.CharField(max_length=100, unique=True, description="分组名称")
    description = fields.CharField(
        max_length=255, null=True, description="分组描述")
    sort_order = fields.IntField(default=0, description="排序值")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    members: fields.ReverseRelation["GroupMember"]
    device_links: fields.ReverseRelation["DeviceGroup"]

    class Meta:
        table = "groups"
        table_description = "用户与设备分组表"

    def __str__(self):
        return self.name


class GroupMember(Model):
    """用户分组关联"""

    id = fields.IntField(pk=True, description="关联ID")
    group = fields.ForeignKeyField(
        "models.Group", related_name="members", description="分组")
    user = fields.ForeignKeyField(
        "models.User", related_name="group_memberships", description="用户")
    joined_at = fields.DatetimeField(auto_now_add=True, description="加入时间")

    class Meta:
        table = "group_members"
        unique_together = ("group", "user")
        table_description = "用户分组关联表"

    def __str__(self):
        return f"{self.user_id} -> {self.group_id}"


class DeviceGroup(Model):
    """设备与分组关联"""

    id = fields.IntField(pk=True, description="关联ID")
    group = fields.ForeignKeyField(
        "models.Group", related_name="device_groups", description="分组")
    device = fields.ForeignKeyField(
        "models.Device", related_name="group_links", description="设备")
    created_at = fields.DatetimeField(auto_now_add=True, description="关联时间")

    class Meta:
        table = "device_groups"
        unique_together = ("group", "device")
        table_description = "设备分组关联表"

    def __str__(self):
        return f"{self.device_id} -> {self.group_id}"
