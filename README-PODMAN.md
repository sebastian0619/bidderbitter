# 投标软件系统 Podman 调试指南

## 快速开始

### 1. 启动系统
```bash
# 使用 podman 启动系统
./start-podman.sh
```

### 2. 访问系统
- **前端界面**: http://localhost:5555
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs

## 调试功能

### 热重载支持
- **后端**: 修改 `backend/` 目录下的 Python 文件会自动重启服务
- **前端**: 修改 `frontend/src/` 目录下的 Vue 文件会自动刷新页面

### 源代码挂载
源代码目录已挂载到容器中，您可以直接在宿主机上编辑代码：
- 后端代码: `./backend/` → `/app/`
- 前端代码: `./frontend/src/` → `/app/src/`

## 常用调试命令

### 容器管理
```bash
# 查看运行中的容器
podman ps

# 查看所有容器（包括停止的）
podman ps -a

# 停止所有服务
podman compose -f docker-compose.podman.yml down

# 重启服务
podman compose -f docker-compose.podman.yml restart

# 重新构建并启动
podman compose -f docker-compose.podman.yml up -d --build
```

### 日志查看
```bash
# 查看所有服务日志
podman compose -f docker-compose.podman.yml logs -f

# 查看特定服务日志
podman compose -f docker-compose.podman.yml logs -f backend
podman compose -f docker-compose.podman.yml logs -f frontend
podman compose -f docker-compose.podman.yml logs -f postgres
podman compose -f docker-compose.podman.yml logs -f redis

# 查看最近的日志
podman compose -f docker-compose.podman.yml logs --tail=50 backend
```

### 进入容器调试
```bash
# 进入后端容器
podman compose -f docker-compose.podman.yml exec backend bash

# 进入前端容器
podman compose -f docker-compose.podman.yml exec frontend sh

# 进入数据库容器
podman compose -f docker-compose.podman.yml exec postgres psql -U bidder_user -d bidder_db
```

### 端口检查
```bash
# 检查端口占用情况
lsof -i :5555  # 前端
lsof -i :8000  # 后端API
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis
lsof -i :4444  # Chrome (Selenium)
```

## 开发配置

### 环境变量
调试时主要环境变量配置（在 `.env` 文件中）：
```bash
# 开发模式
APP_ENV=development
LOG_LEVEL=DEBUG
DEBUG=true

# 允许的CORS源
CORS_ORIGINS=http://localhost:5555,http://frontend:3000

# AI服务配置（可选）
OPENAI_API_KEY=your_api_key_here
```

### 数据库调试
```bash
# 连接数据库
podman compose -f docker-compose.podman.yml exec postgres psql -U bidder_user -d bidder_db

# 查看数据库表
\dt

# 查看表结构
\d table_name

# 退出数据库
\q
```

## 常见问题排除

### 1. 端口冲突
如果遇到端口占用问题：
```bash
# 查看端口占用
sudo lsof -i :5555
sudo lsof -i :8000

# 杀死占用端口的进程
sudo kill -9 <PID>
```

### 2. 容器构建失败
```bash
# 清理所有容器和镜像
podman system prune -a

# 重新构建
podman compose -f docker-compose.podman.yml build --no-cache
```

### 3. 前端无法访问后端
检查 CORS 配置：
```bash
# 查看后端日志中的 CORS 错误
podman compose -f docker-compose.podman.yml logs backend | grep -i cors
```

### 4. 数据库连接问题
```bash
# 检查数据库是否启动
podman compose -f docker-compose.podman.yml ps postgres

# 测试数据库连接
podman compose -f docker-compose.podman.yml exec backend python -c "
import psycopg2
try:
    conn = psycopg2.connect('postgresql://bidder_user:bidder_pass@postgres:5432/bidder_db')
    print('数据库连接成功')
    conn.close()
except Exception as e:
    print(f'数据库连接失败: {e}')
"
```

### 5. AI 服务不可用
```bash
# 检查 AI 相关环境变量
podman compose -f docker-compose.podman.yml exec backend env | grep -i ai
podman compose -f docker-compose.podman.yml exec backend env | grep -i openai
```

## 性能调试

### 监控资源使用
```bash
# 查看容器资源使用情况
podman stats

# 查看系统资源
top
htop  # 如果已安装
```

### 内存和CPU优化
如果遇到性能问题，可以在 `docker-compose.podman.yml` 中添加资源限制：
```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.5'
```

## 调试技巧

### 1. 使用 Python 调试器
在后端代码中添加断点：
```python
import pdb; pdb.set_trace()
```

### 2. 前端调试
- 使用浏览器开发者工具
- 查看 Network 面板中的 API 调用
- 检查 Console 中的错误信息

### 3. API 测试
```bash
# 测试后端 API
curl http://localhost:8000/api/health
curl http://localhost:8000/docs
```

## 生产环境部署

当调试完成后，要部署到生产环境：
1. 修改 `.env` 文件中的配置
2. 使用原始的 `docker-compose.yml`
3. 设置 `APP_ENV=production`
4. 配置适当的安全密钥

## 获取帮助

如果遇到问题：
1. 查看相关服务的日志
2. 检查 `.env` 配置文件
3. 确保所有必要的端口未被占用
4. 参考原始的 `start.sh` 脚本对比差异 