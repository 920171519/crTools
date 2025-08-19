"""
设备管理数据模型
定义设备基本信息、使用情况、内部信息等数据库表结构
"""
from tortoise.models import Model
from tortoise import fields
from datetime import datetime
from enum import Enum


class DeviceTypeEnum(str, Enum):
    """设备归属类型枚举"""
    TEST = "test"        # 测试设备
    DEVELOP = "develop"  # 开发设备
    CI = "ci"           # CI设备


class DeviceStatusEnum(str, Enum):
    """设备状态枚举"""
    AVAILABLE = "available"  # 可用
    OCCUPIED = "occupied"    # 占用中
    LONG_TERM_OCCUPIED = "long_term_occupied"  # 长时间占用
    MAINTENANCE = "maintenance"  # 维护中
    OFFLINE = "offline"      # 离线


class PortStatusEnum(str, Enum):
    """端口状态枚举"""
    ACTIVE = "active"      # 运行中
    INACTIVE = "inactive"  # 未运行
    ERROR = "error"        # 错误


class Device(Model):
    """设备基本信息模型"""

    id = fields.IntField(pk=True, description="设备ID")
    name = fields.CharField(max_length=100, description="设备名称")
    ip = fields.CharField(max_length=45, unique=True, description="设备IP地址")
    # VPN配置外键关联
    vpn_config = fields.ForeignKeyField(
        "models.VPNConfig",
        related_name="devices",
        null=True,
        on_delete=fields.SET_NULL,
        description="所需VPN配置"
    )
    # 保留原字段作为显示备用，当VPN配置被删除时使用
    required_vpn_display = fields.CharField(max_length=100, null=True, description="VPN显示名称")
    creator = fields.CharField(max_length=50, description="设备添加人")
    need_vpn_login = fields.BooleanField(default=False, description="登录是否需要VPN")
    support_queue = fields.BooleanField(default=True, description="是否支持排队占用")
    owner = fields.CharField(max_length=50, description="设备归属人")
    admin_username = fields.CharField(max_length=50, description="管理员账号")
    admin_password = fields.CharField(max_length=255, description="管理员密码")
    device_type = fields.CharEnumField(DeviceTypeEnum, default=DeviceTypeEnum.TEST, description="设备归属类")
    remarks = fields.TextField(null=True, description="设备备注信息")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")
    # 连通性相关字段
    connectivity_status = fields.BooleanField(default=False, description="连通性状态")
    last_ping_time = fields.DatetimeField(null=True, description="最后一次ping检测时间")
    last_connectivity_check = fields.DatetimeField(null=True, description="最后一次连通性检查时间")
    
    # 关联关系
    usage_info: fields.ReverseRelation["DeviceUsage"]
    internal_info: fields.ReverseRelation["DeviceInternal"]
    
    class Meta:
        table = "devices"
        table_description = "设备基本信息表"
    
    def __str__(self):
        return f"{self.name}({self.ip})"

    @property
    def vpn_display_name(self):
        """获取VPN显示名称"""
        if self.vpn_config:
            return f"{self.vpn_config.region} - {self.vpn_config.network}"
        return self.required_vpn_display or "未配置VPN"


class DeviceUsage(Model):
    """设备使用情况模型"""

    id = fields.IntField(pk=True, description="使用情况ID")
    device = fields.OneToOneField("models.Device", related_name="usage_info", description="设备")
    current_user = fields.CharField(max_length=50, null=True, description="当前占用人")
    start_time = fields.DatetimeField(null=True, description="开始占用时间")
    expected_duration = fields.IntField(default=0, description="预计占用时间(分钟)")
    is_long_term = fields.BooleanField(default=False, description="是否为长时间占用")
    long_term_purpose = fields.TextField(null=True, description="长时间占用的用途备注")
    end_date = fields.DatetimeField(null=True, description="长时间占用截至时间")
    queue_users = fields.JSONField(default=list, description="排队中的用户列表")
    status = fields.CharEnumField(DeviceStatusEnum, default=DeviceStatusEnum.AVAILABLE, description="设备状态")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")
    
    class Meta:
        table = "device_usage"
        table_description = "设备使用情况表"
    
    def __str__(self):
        return f"{self.device.name} - {self.status}"
    
    @property
    def occupied_duration(self):
        """已占用时间(分钟)"""
        if self.start_time and self.current_user:
            duration = datetime.now() - self.start_time
            return int(duration.total_seconds() / 60)
        return 0
    
    @property
    def queue_count(self):
        """排队人数"""
        return len(self.queue_users) if self.queue_users else 0


class DeviceInternal(Model):
    """设备内部信息模型"""
    
    id = fields.IntField(pk=True, description="内部信息ID")
    device = fields.ForeignKeyField("models.Device", related_name="internal_info", description="设备", unique=True)
    power_status = fields.BooleanField(default=True, description="设备开机状态")
    used_ports = fields.JSONField(default=list, description="已使用端口列表")
    available_ports = fields.JSONField(default=list, description="可用端口列表")
    port_status = fields.JSONField(default=dict, description="各端口运行状态")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")
    
    class Meta:
        table = "device_internal"
        table_description = "设备内部信息表"
    
    def __str__(self):
        return f"{self.device.name} - 内部信息"
    
    def init_ports(self):
        """初始化20个端口"""
        if not self.available_ports:
            self.available_ports = list(range(1, 21))  # 1-20端口
        if not self.used_ports:
            self.used_ports = []
        if not self.port_status:
            self.port_status = {str(i): PortStatusEnum.INACTIVE for i in range(1, 21)}


class DeviceUsageHistory(Model):
    """设备使用历史记录"""
    
    id = fields.IntField(pk=True, description="历史记录ID")
    device = fields.ForeignKeyField("models.Device", related_name="usage_history", description="设备")
    user = fields.CharField(max_length=50, description="使用人")
    start_time = fields.DatetimeField(description="开始时间")
    end_time = fields.DatetimeField(null=True, description="结束时间")
    duration = fields.IntField(null=True, description="使用时长(分钟)")
    purpose = fields.CharField(max_length=200, null=True, description="使用目的")
    created_at = fields.DatetimeField(auto_now_add=True, description="记录创建时间")
    
    class Meta:
        table = "device_usage_history"
        table_description = "设备使用历史表"
    
    def __str__(self):
        return f"{self.device.name} - {self.user} - {self.start_time}" 