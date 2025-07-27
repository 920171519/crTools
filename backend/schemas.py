"""
Pydantic模式定义
用于API请求和响应的数据验证
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Any
from datetime import datetime
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

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    """用户更新请求模式"""
    username: Optional[str] = Field(None, min_length=2, max_length=50)


class PasswordChange(BaseModel):
    """密码修改请求模式"""
    old_password: str = Field(..., description="原密码")
    new_password: str = Field(..., min_length=6, max_length=20, description="新密码")


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


# 设备相关Schema
class DeviceBase(BaseModel):
    """设备基本信息基础模型"""
    name: str = Field(..., description="设备名称")
    ip: str = Field(..., description="设备IP地址")
    required_vpn: str = Field(..., description="设备所需VPN")
    creator: str = Field(..., description="设备添加人")
    need_vpn_login: bool = Field(False, description="登录是否需要VPN")
    support_queue: bool = Field(True, description="是否支持排队占用")
    owner: str = Field(..., description="设备归属人")
    device_type: str = Field("test", description="设备归属类")
    remarks: Optional[str] = Field(None, description="设备备注信息")


class DeviceCreate(DeviceBase):
    """创建设备模型"""
    pass


class DeviceUpdate(BaseModel):
    """更新设备模型"""
    name: Optional[str] = None
    required_vpn: Optional[str] = None
    need_vpn_login: Optional[bool] = None
    support_queue: Optional[bool] = None
    owner: Optional[str] = None
    device_type: Optional[str] = None
    remarks: Optional[str] = None


class DeviceResponse(DeviceBase):
    """设备响应模型"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class DeviceUsageBase(BaseModel):
    """设备使用情况基础模型"""
    current_user: Optional[str] = None
    expected_duration: int = Field(0, description="预计占用时间(分钟)")
    is_long_term: bool = Field(False, description="是否为长时间占用")
    long_term_purpose: Optional[str] = None
    status: str = Field("available", description="设备状态")


class DeviceUsageUpdate(BaseModel):
    """更新设备使用情况"""
    current_user: Optional[str] = None
    expected_duration: Optional[int] = None
    is_long_term: Optional[bool] = None
    long_term_purpose: Optional[str] = None
    status: Optional[str] = None


class DeviceUsageResponse(DeviceUsageBase):
    """设备使用情况响应模型"""
    id: int
    device_id: int
    start_time: Optional[datetime]
    queue_users: List[str] = []
    occupied_duration: int = 0
    queue_count: int = 0
    updated_at: datetime
    
    class Config:
        from_attributes = True


class DeviceListItem(BaseModel):
    """设备列表项模型"""
    id: int
    name: str
    ip: str
    device_type: str
    current_user: Optional[str] = None
    queue_count: int = 0
    status: str
    start_time: Optional[datetime] = None
    occupied_duration: int = 0
    is_current_user_in_queue: bool = False


class DeviceUseRequest(BaseModel):
    """使用设备请求模型"""
    device_id: int
    user: str
    expected_duration: int = Field(60, description="预计使用时间(分钟)")
    purpose: Optional[str] = None


class DeviceReleaseRequest(BaseModel):
    """释放设备请求模型"""
    device_id: int
    user: str


class DevicePreemptRequest(BaseModel):
    """抢占设备请求模型"""
    device_id: int
    user: str
    expected_duration: int = Field(60, description="预计使用时间(分钟)")
    purpose: Optional[str] = None


class DevicePriorityQueueRequest(BaseModel):
    """优先排队请求模型"""
    device_id: int
    user: str
    expected_duration: int = Field(60, description="预计使用时间(分钟)")
    purpose: Optional[str] = None


class DeviceUnifiedQueueRequest(BaseModel):
    """统一排队请求模型"""
    device_id: int
    user: str
    expected_duration: int = Field(60, description="预计使用时间(分钟)")
    purpose: Optional[str] = None