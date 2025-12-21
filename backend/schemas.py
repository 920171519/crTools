"""
Pydantic模式定义
用于API请求和响应的数据验证
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Any
from datetime import datetime, date
import re


# ===== 基础响应模式 =====
class BaseResponse(BaseModel):
    """基础响应模式"""
    code: int = Field(default=200, description="状态码")
    message: str = Field(default="success", description="响应消息")
    data: Optional[Any] = Field(default=None, description="响应数据")


class PaginationResponse(BaseModel):
    """分页响应模式"""
    total: int = Field(description="总数量")
    page: int = Field(description="当前页码")
    page_size: int = Field(description="每页数量")
    items: List[dict] = Field(description="数据列表")


# ===== 用户相关模式 =====
class UserRegister(BaseModel):
    """用户注册请求模式"""
    employee_id: str = Field(..., description="工号(一个字母+8个数字)")
    username: str = Field(..., min_length=2, max_length=50, description="姓名")
    password: str = Field(..., min_length=6, max_length=20, description="密码")
    
    @validator('employee_id')
    def validate_employee_id(cls, v):
        """验证工号格式"""
        pattern = r'^[A-Za-z]\d{8}$'
        if not re.match(pattern, v):
            raise ValueError('工号格式错误，应为一个字母加8个数字')
        return v.lower()


class UserLogin(BaseModel):
    """用户登录请求模式"""
    employee_id: str = Field(..., description="工号")
    password: str = Field(..., description="密码")
    
    @validator('employee_id')
    def validate_employee_id(cls, v):
        """验证工号格式"""
        pattern = r'^[A-Za-z]\d{8}$'
        if not re.match(pattern, v):
            raise ValueError('工号格式错误')
        return v.lower()


class UserResponse(BaseModel):
    """用户响应模式"""
    id: int
    employee_id: str
    username: str
    is_superuser: bool
    role: Optional[str] = None
    groups: List["GroupSummary"] = []

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    """用户更新请求模式"""
    username: Optional[str] = Field(None, min_length=2, max_length=50)


class PasswordChange(BaseModel):
    """密码修改请求模式"""
    old_password: str = Field(..., description="原密码")
    new_password: str = Field(..., min_length=6, max_length=20, description="新密码")


# ===== 分组相关模式 =====
class GroupSummary(BaseModel):
    """分组概要信息"""
    id: int
    name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True


class GroupDetail(GroupSummary):
    """包含成员数量的分组详情"""
    member_count: int = 0


class GroupCreate(BaseModel):
    """创建分组请求"""
    name: str = Field(..., min_length=1, max_length=100, description="分组名称")
    description: Optional[str] = Field(None, max_length=255, description="分组描述")
    sort_order: int = Field(0, description="排序")


class GroupUpdate(GroupCreate):
    """更新分组请求"""
    pass


class UserGroupUpdateRequest(BaseModel):
    """更新用户分组请求"""
    group_ids: List[int] = Field(default_factory=list, description="分组ID列表")


class GroupMembersAddRequest(BaseModel):
    """为分组添加成员请求"""
    user_ids: List[int] = Field(default_factory=list, description="用户ID列表")


class GroupMembersResponse(BaseModel):
    """分组及成员信息"""
    id: int
    name: str
    description: Optional[str]
    members: List[UserResponse] = []


# ===== 认证相关模式 =====
class Token(BaseModel):
    """JWT令牌响应模式"""
    access_token: str = Field(..., description="访问令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_in: int = Field(..., description="过期时间(秒)")


class TokenData(BaseModel):
    """令牌数据模式"""
    employee_id: Optional[str] = None


# ===== 角色相关模式 =====
class RoleCreate(BaseModel):
    """角色创建请求模式"""
    name: str = Field(..., min_length=2, max_length=50, description="角色名称")
    description: Optional[str] = Field(None, max_length=200, description="角色描述")


class RoleResponse(BaseModel):
    """角色响应模式"""
    id: int
    name: str
    description: Optional[str]
    
    class Config:
        from_attributes = True


class RoleUpdate(BaseModel):
    """角色更新请求模式"""
    name: Optional[str] = Field(None, min_length=2, max_length=50)
    description: Optional[str] = Field(None, max_length=200)


# ===== 权限相关模式 =====
class PermissionCreate(BaseModel):
    """权限创建请求模式"""
    name: str = Field(..., min_length=2, max_length=50, description="权限名称")
    code: str = Field(..., min_length=2, max_length=50, description="权限代码")
    description: Optional[str] = Field(None, max_length=200, description="权限描述")
    resource: str = Field(..., max_length=100, description="资源名称")
    action: str = Field(..., max_length=50, description="动作类型")


class PermissionResponse(BaseModel):
    """权限响应模式"""
    id: int
    name: str
    code: str
    description: Optional[str]
    resource: str
    action: str
    
    class Config:
        from_attributes = True


# ===== 菜单相关模式 =====
class MenuCreate(BaseModel):
    """菜单创建请求模式"""
    name: str = Field(..., min_length=2, max_length=50, description="菜单名称")
    path: str = Field(..., max_length=200, description="路由路径")
    component: Optional[str] = Field(None, max_length=200, description="组件路径")
    icon: Optional[str] = Field(None, max_length=50, description="菜单图标")
    parent_id: Optional[int] = Field(None, description="父菜单ID")
    sort_order: int = Field(default=0, description="排序")
    is_visible: bool = Field(default=True, description="是否显示")
    permission_code: Optional[str] = Field(None, max_length=50, description="所需权限代码")


class MenuResponse(BaseModel):
    """菜单响应模式"""
    id: int
    name: str
    path: str
    component: Optional[str]
    icon: Optional[str]
    parent_id: Optional[int]
    sort_order: int
    is_visible: bool
    permission_code: Optional[str]
    children: Optional[List['MenuResponse']] = None
    
    class Config:
        from_attributes = True


# ===== 分页查询模式 =====
class PageQuery(BaseModel):
    """分页查询参数"""
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=10, ge=1, le=100, description="每页数量")
    keyword: Optional[str] = Field(None, description="搜索关键词")


# ===== 用户管理相关模式 =====
class UserRoleAssign(BaseModel):
    """用户角色分配请求模式"""
    user_id: int = Field(..., description="用户ID")
    role_id: int = Field(..., description="角色ID")


class RolePermissionAssign(BaseModel):
    """角色权限分配请求模式"""
    role_id: int = Field(..., description="角色ID")
    permission_ids: List[int] = Field(..., description="权限ID列表")


# ===== 登录日志模式 =====
class LoginLogResponse(BaseModel):
    """登录日志响应模式"""
    id: int
    user_id: int
    employee_id: str
    username: str
    login_time: datetime
    ip_address: str
    login_result: bool
    failure_reason: Optional[str]

    class Config:
        from_attributes = True


# ===== VPN配置模式 =====
class VPNConfigBase(BaseModel):
    """VPN配置基础模式"""
    region: str = Field(..., min_length=1, max_length=50, description="地域")
    network: str = Field(..., min_length=1, max_length=50, description="网段")
    lns: str = Field(..., min_length=1, max_length=45, description="LNS地址")
    gw: str = Field(..., min_length=1, max_length=45, description="网关地址")
    ip: str = Field(..., min_length=1, max_length=45, description="VPN IP")
    mask: str = Field(..., min_length=1, max_length=45, description="子网掩码")


class VPNConfigCreate(VPNConfigBase):
    """创建VPN配置请求模式"""
    pass


class VPNConfigUpdate(BaseModel):
    """更新VPN配置请求模式"""
    region: Optional[str] = Field(None, min_length=1, max_length=50, description="地域")
    network: Optional[str] = Field(None, min_length=1, max_length=50, description="网段")
    lns: Optional[str] = Field(None, min_length=1, max_length=45, description="LNS地址")
    gw: Optional[str] = Field(None, min_length=1, max_length=45, description="网关地址")
    ip: Optional[str] = Field(None, min_length=1, max_length=45, description="VPN IP")
    mask: Optional[str] = Field(None, min_length=1, max_length=45, description="子网掩码")


class VPNConfigResponse(VPNConfigBase):
    """VPN配置响应模式"""
    id: int
    status: Optional[bool] = None

    class Config:
        from_attributes = True


class UserVPNConfigUpdate(BaseModel):
    """用户VPN IP配置更新请求模式"""
    ip_address: Optional[str] = Field(None, max_length=45, description="IP地址")


class UserVPNConfigResponse(BaseModel):
    """用户VPN配置响应模式"""
    id: int
    vpn_config_id: int
    vpn_region: str
    vpn_network: str
    ip_address: Optional[str]

    class Config:
        from_attributes = True


# 设备相关Schema
class DeviceBase(BaseModel):
    """设备基本信息基础模型"""
    name: str = Field(..., description="设备名称")
    ip: str = Field(..., description="设备IP地址")
    vpn_config_id: Optional[int] = Field(None, description="VPN配置ID")
    creator: str = Field(..., description="设备添加人")
    ftp_prefix: bool = Field(False, description="FTP连接是否需要输入前缀")
    support_queue: bool = Field(True, description="是否支持排队占用")
    max_occupy_minutes: Optional[int] = Field(None, description="最大占用时长（分钟），有排队时超时会自动释放")
    owner: str = Field(..., description="设备归属人")
    admin_username: str = Field(..., description="管理员账号")
    admin_password: str = Field(..., description="管理员密码")
    device_type: str = Field("test", description="设备归属类")
    form_type: str = Field(..., description="设备形态")
    remarks: Optional[str] = Field(None, description="设备备注信息")
    group_ids: Optional[List[int]] = Field(default=None, description="设备所属分组ID列表")
    
    @validator('form_type')
    def validate_form_type(cls, v):
        """验证设备形态"""
        allowed_values = ["单", "双", "未知"]
        if v not in allowed_values:
            raise ValueError(f'设备形态必须是以下值之一: {", ".join(allowed_values)}')
        return v


class DeviceCreate(DeviceBase):
    """创建设备模型"""
    pass


class DeviceUpdate(BaseModel):
    """更新设备模型"""
    name: Optional[str] = None
    vpn_config_id: Optional[int] = None
    ftp_prefix: Optional[bool] = None
    support_queue: Optional[bool] = None
    max_occupy_minutes: Optional[int] = None
    owner: Optional[str] = None
    admin_username: Optional[str] = None
    admin_password: Optional[str] = None
    device_type: Optional[str] = None
    form_type: Optional[str] = None
    remarks: Optional[str] = None
    group_ids: Optional[List[int]] = None
    
    @validator('form_type')
    def validate_form_type(cls, v):
        """验证设备形态"""
        if v is not None:
            allowed_values = ["单", "双", "未知"]
            if v not in allowed_values:
                raise ValueError(f'设备形态必须是以下值之一: {", ".join(allowed_values)}')
        return v


class DeviceResponse(BaseModel):
    """设备响应模型"""
    id: int
    name: str
    ip: str
    vpn_config_id: Optional[int] = None
    vpn_region: Optional[str] = None
    vpn_network: Optional[str] = None
    vpn_display_name: Optional[str] = None
    creator: str
    ftp_prefix: bool
    support_queue: bool
    max_occupy_minutes: Optional[int] = None
    owner: str
    admin_username: str
    admin_password: str
    device_type: str
    form_type: str
    remarks: Optional[str] = None
    groups: List[GroupSummary] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DeviceUsageBase(BaseModel):
    """设备使用情况基础模型"""
    current_user: Optional[str] = None
    is_long_term: bool = Field(False, description="是否为长时间占用")
    long_term_purpose: Optional[str] = None
    status: str = Field("available", description="设备状态")


class DeviceUsageUpdate(BaseModel):
    """更新设备使用情况"""
    current_user: Optional[str] = None
    is_long_term: Optional[bool] = None
    long_term_purpose: Optional[str] = None
    status: Optional[str] = None


class DeviceSharedUser(BaseModel):
    """共用用户信息"""
    employee_id: str
    username: str
    approved_at: Optional[datetime] = None


class DeviceUsageResponse(DeviceUsageBase):
    """设备使用情况响应模型"""
    id: int
    device_id: int
    start_time: Optional[datetime]
    queue_users: List[str] = []
    occupied_duration: int = 0
    queue_count: int = 0
    updated_at: datetime
    shared_users: List[DeviceSharedUser] = []
    has_pending_share_request: bool = False
    is_shared_user: bool = False
    share_request_id: Optional[int] = None
    share_status: Optional[str] = None
    
    class Config:
        from_attributes = True


class DeviceListItem(BaseModel):
    """设备列表项模型"""
    id: int
    name: str
    ip: str
    device_type: str
    form_type: str
    vpn_region: Optional[str] = None
    vpn_network: Optional[str] = None
    vpn_display_name: Optional[str] = None
    current_user: Optional[str] = None
    queue_count: int = 0
    status: str
    start_time: Optional[datetime] = None
    occupied_duration: int = 0
    is_current_user_in_queue: bool = False
    connectivity_status: Optional[bool] = None
    admin_username: Optional[str] = None
    project_name: Optional[str] = None
    support_queue: bool = True
    groups: List[GroupSummary] = []
    is_shared_user: bool = False
    has_pending_share_request: bool = False
    share_request_id: Optional[int] = None
    share_status: Optional[str] = None


class DeviceUseRequest(BaseModel):
    """使用设备请求模型"""
    device_id: int
    user: str


class DeviceLongTermUseRequest(BaseModel):
    """长时间占用设备请求模型"""
    device_id: int
    user: str
    end_date: datetime = Field(..., description="截至时间")
    purpose: str = Field(..., description="使用目的")


class DeviceReleaseRequest(BaseModel):
    """释放设备请求模型"""
    device_id: int
    user: str


class DevicePreemptRequest(BaseModel):
    """抢占设备请求模型"""
    device_id: int
    user: str
    purpose: Optional[str] = None


class DevicePriorityQueueRequest(BaseModel):
    """优先排队请求模型"""
    device_id: int
    user: str
    purpose: Optional[str] = None


class DeviceUnifiedQueueRequest(BaseModel):
    """统一排队请求模型"""
    device_id: int
    user: str
    purpose: Optional[str] = None


class DeviceShareRequestCreate(BaseModel):
    """申请共用设备"""
    device_id: int = Field(..., description="设备ID")
    message: Optional[str] = Field(None, description="申请备注信息")


class DeviceForceShareRequest(BaseModel):
    """强制共用设备"""
    message: Optional[str] = Field(None, description="强制共用备注信息")


class DeviceShareDecision(BaseModel):
    """共用申请处理请求"""
    approve: bool = Field(..., description="是否通过")
    reason: Optional[str] = Field(None, description="处理说明")


class DeviceShareRequestResponse(BaseModel):
    """共用申请响应数据"""
    id: int
    device_id: int
    device_name: str
    requester_employee_id: str
    requester_username: str
    status: str
    request_message: Optional[str] = None
    decision_reason: Optional[str] = None
    processed_by: Optional[str] = None
    processed_at: Optional[datetime] = None
    created_at: datetime


class MyUsageDeviceSummary(BaseModel):
    """个人当前环境概要"""
    id: int
    name: str
    ip: str
    status: str
    owner: str
    current_user: Optional[str] = None


class MyUsageSummaryResponse(BaseModel):
    """个人当前占用与共用环境"""
    occupied_devices: List[MyUsageDeviceSummary] = []
    shared_devices: List[MyUsageDeviceSummary] = []


# ===== 设备配置相关模式 =====
class DeviceConfigBase(BaseModel):
    """设备配置基础模式"""
    config_param1: int = Field(..., description="配置参数1 (1-8)", ge=1, le=8)
    config_param2: int = Field(..., description="配置参数2 (1-40)", ge=1, le=40)
    config_value: str = Field(..., description="配置值")


class DeviceConfigCreate(DeviceConfigBase):
    """创建设备配置请求模式"""
    pass


class DeviceConfigUpdate(DeviceConfigBase):
    """更新设备配置请求模式"""
    pass


class DeviceConfigResponse(DeviceConfigBase):
    """设备配置响应模式"""
    id: int = Field(..., description="配置ID")
    device_id: int = Field(..., description="设备ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    class Config:
        from_attributes = True


# ===== 命令行集相关模式 =====
class CommandBase(BaseModel):
    """命令行基础模式"""
    command_text: str = Field(..., min_length=1, max_length=1000, description="命令内容")
    link: Optional[str] = Field(None, max_length=1000, description="介绍网页链接")
    view: Optional[str] = Field(None, max_length=100, description="视图/类别")
    description: Optional[str] = Field(None, description="描述")
    notice: Optional[str] = Field(None, description="注意事项")
    param_ranges: Optional[List[dict]] = Field(default_factory=list, description="参数范围表")
    remarks: Optional[str] = Field(None, max_length=5000, description="备注信息")


class CommandCreate(CommandBase):
    """创建命令行请求模式"""
    pass


class CommandUpdate(BaseModel):
    """更新命令行请求模式"""
    command_text: Optional[str] = Field(None, min_length=1, max_length=1000, description="命令内容")
    link: Optional[str] = Field(None, max_length=1000, description="介绍网页链接")
    view: Optional[str] = Field(None, max_length=100, description="视图/类别")
    description: Optional[str] = Field(None, description="描述")
    notice: Optional[str] = Field(None, description="注意事项")
    param_ranges: Optional[List[dict]] = Field(default=None, description="参数范围表")
    remarks: Optional[str] = Field(None, max_length=5000, description="备注信息")


class CommandResponse(CommandBase):
    """命令行响应模式"""
    id: int = Field(..., description="命令ID")
    creator: str = Field(..., description="创建人工号")
    last_editor: Optional[str] = Field(None, description="最后编辑人工号")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    class Config:
        from_attributes = True


class CommandListItem(BaseModel):
    """命令行列表项模式"""
    id: int
    command_text: str
    view: Optional[str]
    description: Optional[str]
    last_editor: Optional[str]
    updated_at: datetime


# ===== AI 工具相关模式 =====
class AIDiagnosisCreate(BaseModel):
    """AI 诊断创建请求模式"""
    device_id: int = Field(..., description="设备ID")
    problem_description: str = Field(..., min_length=1, max_length=5000, description="问题描述")


class AIDiagnosisResponse(BaseModel):
    """AI 诊断响应模式"""
    id: int
    device_id: int
    device_ip: str
    user_id: int
    employee_id: str
    username: str
    problem_description: str
    diagnosis_result: Optional[str]
    status: str
    connectivity_status: Optional[bool]
    error_message: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class AIDiagnosisListItem(BaseModel):
    """AI 诊断列表项模式"""
    id: int
    device_ip: str
    username: str
    problem_description: str
    status: str
    connectivity_status: Optional[bool]
    created_at: datetime
    completed_at: Optional[datetime]
