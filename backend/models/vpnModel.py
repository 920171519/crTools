"""
VPN配置相关模型
"""
from tortoise.models import Model
from tortoise import fields


class VPNConfig(Model):
    """VPN配置模型"""

    id = fields.IntField(pk=True, description="VPN配置ID")
    region = fields.CharField(max_length=50, description="地域")
    network = fields.CharField(max_length=50, description="网段")
    lns = fields.CharField(max_length=45, description="LNS地址")
    gw = fields.CharField(max_length=45, description="网关地址")
    ip = fields.CharField(max_length=45, description="VPN IP")
    mask = fields.CharField(max_length=45, description="子网掩码")

    class Meta:
        table = "vpn_configs"
        table_description = "VPN配置表"
        unique_together = (("region", "network"),)  # 地域和网段组合唯一

    def __str__(self):
        return f"{self.region}-{self.network}"


class UserVPNConfig(Model):
    """用户VPN IP配置模型"""

    id = fields.IntField(pk=True, description="配置ID")
    user = fields.ForeignKeyField(
        "models.User", related_name="vpn_configs", description="用户")
    vpn_config = fields.ForeignKeyField(
        "models.VPNConfig", related_name="user_configs", description="VPN配置")
    ip_address = fields.CharField(
        max_length=45, null=True, description="用户配置的IP地址")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        table = "user_vpn_configs"
        table_description = "用户VPN IP配置表"
        unique_together = (("user", "vpn_config"),)  # 每个用户对每个VPN只能有一个配置

    def __str__(self):
        return f"{self.user.employee_id} - {self.vpn_config.name} - {self.ip_address}"
