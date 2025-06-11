"""
认证相关工具函数
包含JWT令牌生成/验证、密码加密/验证等功能
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from models.admin import UserRole, RolePermission, Permission
from models.admin import User, LoginLog
from schemas import TokenData
from config import settings
import ipaddress
import asyncio
import bcrypt


# JWT Bearer认证
security = HTTPBearer()


class AuthManager:
    """认证管理器"""
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        plain_password = plain_password.encode('utf-8')
        hashed_password = hashed_password.encode('utf-8') # 和get_password_hash对应,此处得到str
        return bcrypt.checkpw(plain_password, hashed_password)
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """生成密码哈希"""
        password = password.encode('utf-8')
        hashPassword = bcrypt.hashpw(password, bcrypt.gensalt())
        print("TESTLN hashPassword: ", hashPassword, " type:", type(hashPassword))
        return hashPassword.decode('utf-8') # 这里虽然是返回给数据库存储, 但是它貌似只能存str, 不能存bytes, 因此先decode

    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """创建访问令牌"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> Optional[TokenData]:
        """验证令牌"""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            employee_id: str = payload.get("sub")
            if employee_id is None:
                return None
            token_data = TokenData(employee_id=employee_id)
            return token_data
        except JWTError:
            return None
    
    @staticmethod
    async def authenticate_user(employee_id: str, password: str) -> Optional[User]:
        """认证用户"""
        # 查找用户
        user = await User.filter(employee_id=employee_id).first()
        if not user:
            return None
        
        # 验证密码
        if not AuthManager.verify_password(password, user.hashed_password):
            return None
        
        return user
        # if not AuthManager.verify_password(password, "$2b$12$JOsHHibB7dQ.7NeM9RAJ9u/W8K0l.6vAvfHX7SYw23PEHncSceOue"):
        #     return None
        # return user

    @staticmethod
    async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
        """获取当前用户"""
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        token_data = AuthManager.verify_token(credentials.credentials)
        if token_data is None:
            raise credentials_exception
        user = await User.filter(employee_id=token_data.employee_id).first()
        if user is None:
            raise credentials_exception
        
        return user

    @staticmethod
    async def get_current_superuser(current_user: User = Depends(get_current_user)) -> User:
        """获取当前超级用户（仅超级用户可访问）"""
        if not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="The user doesn't have enough privileges"
            )
        return current_user


class PermissionChecker:
    """权限检查器"""
    
    def __init__(self, required_permission: str):
        self.required_permission = required_permission
    
    async def __call__(self, current_user: User = Depends(AuthManager.get_current_user)) -> bool:
        """检查用户是否有指定权限"""
        # 超级用户拥有所有权限
        if current_user.is_superuser:
            return True
        
        # 查询用户权限
        user_permissions = await self._get_user_permissions(current_user.id)
        
        if self.required_permission not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {self.required_permission}"
            )
        
        return True
    
    async def _get_user_permissions(self, user_id: int) -> list:
        """获取用户权限列表"""
        
        # 通过用户角色获取权限
        permissions = await Permission.filter(
            permission_roles__role__role_users__user_id=user_id
        ).values_list('code', flat=True)
        
        return list(permissions)


class LoginManager:
    """登录管理器"""
    
    @staticmethod
    async def record_login_attempt(
        user: Optional[User], 
        ip_address: str, 
        user_agent: str, 
        success: bool, 
        failure_reason: Optional[str] = None
    ):
        """记录登录尝试"""
        if user:
            await LoginLog.create(
                user=user,
                ip_address=ip_address,
                user_agent=user_agent,
                login_result=success,
                failure_reason=failure_reason
            )
    
    @staticmethod
    def get_client_ip(request) -> str:
        """获取客户端IP地址"""
        # 尝试从X-Forwarded-For头获取真实IP
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        # 尝试从X-Real-IP头获取
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # 返回直接连接的IP
        return request.client.host
    
    @staticmethod
    def validate_ip_address(ip: str) -> bool:
        """验证IP地址格式"""
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False


# 权限装饰器
def require_permission(permission_code: str):
    """权限装饰器"""
    return Depends(PermissionChecker(permission_code))


# 常用的权限检查依赖
require_superuser = Depends(AuthManager.get_current_superuser)
require_active_user = Depends(AuthManager.get_current_user)

# 常见权限定义
class Permissions:
    """权限常量定义"""
    # 用户管理
    USER_CREATE = "user:create"
    USER_READ = "user:read"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    
    # 角色管理
    ROLE_CREATE = "role:create"
    ROLE_READ = "role:read"
    ROLE_UPDATE = "role:update"
    ROLE_DELETE = "role:delete"
    
    # 权限管理
    PERMISSION_CREATE = "permission:create"
    PERMISSION_READ = "permission:read"
    PERMISSION_UPDATE = "permission:update"
    PERMISSION_DELETE = "permission:delete"
    
    # 菜单管理
    MENU_CREATE = "menu:create"
    MENU_READ = "menu:read"
    MENU_UPDATE = "menu:update"
    MENU_DELETE = "menu:delete"
    
    # 系统管理
    SYSTEM_CONFIG = "system:config"
    SYSTEM_LOG = "system:log" 