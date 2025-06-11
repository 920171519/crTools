#!/usr/bin/env python3
"""
crTools后台管理系统启动脚本
"""
import uvicorn
from config import settings

if __name__ == "__main__":
    print("正在启动crTools后台管理系统...")
    print(f"服务地址: http://{settings.HOST}:{settings.PORT}")
    print(f"API文档: http://{settings.HOST}:{settings.PORT}/docs")
    print("默认管理员账号: A12345678 / admin123")
    print("-" * 50)
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    ) 