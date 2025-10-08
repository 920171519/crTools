# crTools后台管理系统

基于工号认证的简单后台管理系统，使用Vue3 + FastAPI技术栈构建。

## 技术栈

### 前端
- **Vue 3** - 前端框架
- **TypeScript** - 类型支持
- **Pinia** - 状态管理
- **Vue Router** - 路由管理
- **Element Plus** - UI组件库
- **Axios** - HTTP客户端
- **Vite** - 构建工具

### 后端
- **FastAPI** - Web框架
- **Tortoise-ORM** - 异步ORM
- **SQLite** - 数据库（轻量级，无需额外安装）
- **JWT** - 身份认证
- **Python 3.8+** - 运行环境

## 功能特性

- ✅ 基于工号的用户认证系统（一个字母+8个数字）
- ✅ JWT令牌认证
- ✅ 基于角色的权限控制（RBAC）
- ✅ 动态菜单生成
- ✅ 用户管理
- ✅ 角色管理
- ✅ 权限管理
- ✅ 菜单管理
- ✅ 登录日志
- ✅ 响应式布局
- ✅ 密码修改
- ✅ 个人信息管理

## 快速开始

### 环境要求
- Python 3.8+
- Node.js 16+
- pnpm (推荐)
- 后端使用uv进行环境管理

### 后端安装运行

1. 进入后端目录
```bash
cd backend
```

2. 安装依赖
```bash
uv sync
```

3. 启动服务
```bash
# 使用启动脚本
python run.py
```

**注意**: 系统使用SQLite数据库，首次启动会自动创建数据库文件 `db.sqlite3` 并初始化基础数据。

后端服务将在 http://localhost:8000 启动

### 前端安装运行

1. 进入前端目录
```bash
cd frontend
```

2. 安装依赖
```bash
pnpm install
```

3. 启动开发服务器
```bash
pnpm dev
# 或
npm run dev
```

前端服务将在 http://localhost:5173 启动

## 默认账号

系统会自动创建默认管理员账号：
- **工号**: A12345678
- **密码**: admin123

## API文档

启动后端服务后，可以访问以下地址查看API文档：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 项目结构

```
crTools/
├── backend/                 # 后端代码
│   ├── main.py             # FastAPI主应用
│   ├── config.py           # 配置文件
│   ├── models.py           # 数据模型
│   ├── schemas.py          # Pydantic模式
│   ├── auth.py             # 认证模块
│   ├── database.py         # 数据库配置
│   ├── routers/            # API路由
│   │   ├── __init__.py
│   │   └── auth.py         # 认证路由
│   ├── requirements.txt    # Python依赖
│   ├── run.py             # 启动脚本
│   └── db.sqlite3         # SQLite数据库文件（自动生成）
└── frontend/               # 前端代码
    ├── src/
    │   ├── api/           # API接口
    │   ├── stores/        # Pinia状态管理
    │   ├── router/        # Vue Router配置
    │   ├── views/         # 页面组件
    │   │   ├── auth/      # 认证相关页面
    │   │   ├── system/    # 系统管理页面
    │   │   └── error/     # 错误页面
    │   ├── layout/        # 布局组件
    │   ├── App.vue        # 根组件
    │   └── main.ts        # 入口文件
    ├── package.json       # 前端依赖
    └── vite.config.ts     # Vite配置
```

## 工号格式

系统使用工号作为唯一身份标识，格式要求：
- 由一个字母加8个数字组成
- 例如：A12345678、B98765432
- 不区分大小写，系统会自动转换为大写

## 权限说明

系统实现了基于角色的访问控制（RBAC）：

### 默认角色
- **超级管理员**: 拥有所有权限
- **管理员**: 拥有大部分管理权限
- **普通用户**: 拥有基本访问权限

### 权限类型
- 用户管理（增删改查）
- 角色管理（增删改查）
- 权限管理（增删改查）
- 菜单管理（增删改查）
- 系统配置
- 日志查看

## 数据库说明

### SQLite 优势
- **轻量级**: 无需安装数据库服务器
- **零配置**: 开箱即用
- **可移植**: 数据库文件可直接复制
- **适用于**: 中小型应用、开发测试环境

### 数据库文件
- 位置: `backend/db.sqlite3`
- 首次启动自动创建
- 包含完整的表结构和基础数据

## 开发指南

### 添加新功能

1. 后端添加API路由到 `routers/` 目录
2. 前端添加页面组件到 `views/` 目录
3. 在路由配置中添加新路由
4. 如需权限控制，在数据库中添加相应权限记录

### 数据库管理

使用Aerich进行数据库迁移：
```bash
# 初始化
aerich init -t database.TORTOISE_ORM

# 生成迁移文件
aerich migrate

# 应用迁移
aerich upgrade
```

### 数据库重置
如需重置数据库，删除 `db.sqlite3` 文件，重新启动应用即可。

## 生产部署

### 后端部署
1. 安装生产级WSGI服务器（如Gunicorn）
2. 配置反向代理（如Nginx）
3. 设置环境变量
4. 配置SSL证书
5. 备份SQLite数据库文件

### 前端部署
1. 构建生产版本：`pnpm build`
2. 将dist目录部署到Web服务器

### SQLite在生产环境的考虑
- 适合中小型应用（< 100GB数据）
- 读密集型工作负载
- 需要定期备份数据库文件
- 如需更高并发，可考虑迁移到PostgreSQL或MySQL

## 故障排除

### 常见问题

1. **后端启动失败**
   - 检查Python版本是否符合要求
   - 确认所有依赖已正确安装
   - 查看控制台错误信息

2. **数据库相关问题**
   - SQLite文件权限问题：确保应用有读写权限
   - 数据库锁定：确保没有其他进程在访问数据库
   - 数据损坏：删除db.sqlite3文件重新初始化

3. **前端API请求失败**
   - 确认后端服务已启动
   - 检查CORS配置
   - 查看浏览器控制台错误信息

4. **登录失败**
   - 确认工号格式正确
   - 检查密码是否正确
   - 查看后端日志

## 性能优化

### SQLite优化建议
1. 启用WAL模式提高并发性能
2. 设置合适的缓存大小
3. 定期执行VACUUM清理
4. 为查询字段创建索引

### 前端优化
1. 路由懒加载
2. 组件按需导入
3. 图片压缩优化
4. 启用Gzip压缩

## 贡献指南

1. Fork项目
2. 创建功能分支
3. 提交变更
4. 推送到分支
5. 创建Pull Request

正在开发中....
