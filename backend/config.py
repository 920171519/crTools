"""
项目配置文件
包含数据库连接、JWT设置等配置信息
"""
import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用程序设置类"""

    # 数据库配置 - 使用SQLite
    DATABASE_URL: str = "sqlite://db.sqlite3"

    # JWT配置
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 43200

    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True

    # 跨域配置
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:5173"]

    class Config:
        env_file = ".env"


# 创建设置实例
settings = Settings()
