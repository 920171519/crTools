"""
系统设置模型
"""
from tortoise.models import Model
from tortoise import fields
from datetime import datetime

class SystemSettings(Model):
    """系统设置模型"""
    id = fields.IntField(pk=True)
    cleanup_time = fields.CharField(max_length=5, null=True, description="定时清理时间 (HH:MM)")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        table = "system_settings"
        table_description = "系统设置表"

    def __str__(self):
        return f"SystemSettings(cleanup_time={self.cleanup_time})"
