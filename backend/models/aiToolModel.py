"""
AI 工具数据模型
用于保存 AI 诊断历史记录
"""
from tortoise import fields
from tortoise.models import Model
from datetime import datetime
from typing import Optional


class AIDiagnosisLog(Model):
    """AI 诊断日志模型"""
    
    id = fields.IntField(pk=True, description="主键ID")
    
    # 诊断信息
    device_id = fields.IntField(description="设备ID")
    device_ip = fields.CharField(max_length=50, description="设备IP地址")
    user_id = fields.IntField(description="操作用户ID")
    employee_id = fields.CharField(max_length=50, description="操作用户工号")
    username = fields.CharField(max_length=100, description="操作用户姓名")
    
    # 问题描述和诊断结果
    problem_description = fields.TextField(description="问题描述")
    diagnosis_result = fields.TextField(null=True, description="诊断结果(Markdown格式)")
    
    # 状态信息
    status = fields.CharField(
        max_length=20, 
        default="pending",
        description="诊断状态: pending-进行中, success-成功, failed-失败, timeout-超时"
    )
    connectivity_status = fields.BooleanField(null=True, description="设备连通性状态")
    error_message = fields.TextField(null=True, description="错误信息")
    
    # 时间戳
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    completed_at = fields.DatetimeField(null=True, description="完成时间")
    
    class Meta:
        table = "ai_diagnosis_logs"
        ordering = ["-created_at"]
    
    def __str__(self):
        return f"AIDiagnosisLog(id={self.id}, device_ip={self.device_ip}, user={self.username})"
    
    @classmethod
    async def create_log(
        cls,
        device_id: int,
        device_ip: str,
        user_id: int,
        employee_id: str,
        username: str,
        problem_description: str
    ):
        """创建诊断日志"""
        log = await cls.create(
            device_id=device_id,
            device_ip=device_ip,
            user_id=user_id,
            employee_id=employee_id,
            username=username,
            problem_description=problem_description,
            status="pending"
        )
        return log
    
    async def update_result(
        self,
        diagnosis_result: str,
        status: str,
        connectivity_status: Optional[bool] = None,
        error_message: Optional[str] = None
    ):
        """更新诊断结果"""
        self.diagnosis_result = diagnosis_result
        self.status = status
        self.connectivity_status = connectivity_status
        self.error_message = error_message
        self.completed_at = datetime.now()
        await self.save()

