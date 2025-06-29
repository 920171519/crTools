"""
crTools后台管理系统 - 主应用入口
基于FastAPI的后台管理系统API
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from database import init_database, setup_database
from routers import auth, device, user
import uvicorn


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    print("🚀 crTools后台管理系统启动中...")
    
    # 初始化数据库数据
    await init_database()
    
    yield
    
    # 关闭时执行
    print("🛑 crTools后台管理系统关闭")


# 创建FastAPI应用实例
app = FastAPI(
    title="crTools后台管理系统",
    description="基于工号认证的CR工具集管理系统",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# 设置数据库
setup_database(app)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 全局异常处理器
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """HTTP异常处理器"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.status_code,
            "message": exc.detail,
            "data": None
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """通用异常处理器"""
    print(f"未处理的异常: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "code": 500,
            "message": "服务器内部错误",
            "data": None
        }
    )


# 注册路由
app.include_router(auth.router, prefix="/api")
app.include_router(device.router)
app.include_router(user.router)


@app.get("/", summary="健康检查")
async def root():
    """根路径健康检查"""
    return {
        "code": 200,
        "message": "crTools后台管理系统API运行正常",
        "data": {
            "version": "1.0.0",
            "status": "healthy"
        }
    }


@app.get("/api/health", summary="API健康检查")
async def health_check():
    """API健康检查"""
    return {
        "code": 200,
        "message": "API运行正常",
        "data": {
            "status": "healthy",
            "timestamp": "2024-01-01T00:00:00Z"
        }
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    ) 