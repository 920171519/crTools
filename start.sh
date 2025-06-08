#!/bin/bash

# crTools 后台管理系统启动脚本

echo "=================================="
echo "  crTools 后台管理系统"
echo "=================================="
echo ""

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装，请先安装 Python 3.8+"
    exit 1
fi

# 检查Node.js环境
if ! command -v node &> /dev/null; then
    echo "❌ Node.js 未安装，请先安装 Node.js 16+"
    exit 1
fi

echo "✅ 环境检查通过"
echo ""

# 启动后端服务
echo "🚀 启动后端服务..."
cd backend

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
echo "📦 安装后端依赖..."
pip install -r requirements.txt > /dev/null 2>&1

# 启动后端
echo "🔧 启动后端服务 (http://localhost:8000)..."
python run.py &
BACKEND_PID=$!

cd ..

# 启动前端服务
echo "🚀 启动前端服务..."
cd frontend

# 检查依赖
if [ ! -d "node_modules" ]; then
    echo "📦 安装前端依赖..."
    if command -v pnpm &> /dev/null; then
        pnpm install
    else
        npm install
    fi
fi

# 启动前端
echo "🔧 启动前端服务 (http://localhost:5173)..."
if command -v pnpm &> /dev/null; then
    pnpm dev &
else
    npm run dev &
fi
FRONTEND_PID=$!

cd ..

echo ""
echo "=================================="
echo "🎉 服务启动成功！"
echo "=================================="
echo "📱 前端地址: http://localhost:5173"
echo "🔧 后端地址: http://localhost:8000"
echo "📚 API文档: http://localhost:8000/docs"
echo "👤 默认账号: A12345678 / admin123"
echo ""
echo "💡 按 Ctrl+C 停止所有服务"
echo "=================================="

# 等待用户中断
wait

# 清理进程
echo ""
echo "🛑 正在停止服务..."
kill $BACKEND_PID 2>/dev/null
kill $FRONTEND_PID 2>/dev/null
echo "✅ 服务已停止" 