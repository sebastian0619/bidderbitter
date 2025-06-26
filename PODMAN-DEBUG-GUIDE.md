# 投标软件系统 Podman 调试使用指南

## 🎉 快速成功部署

我们已经成功通过 Podman 构建并启动了后端服务！以下是完整的操作指南。

## ✅ 已完成的部署

### 当前可用服务：
- **后端 API**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs

### 已成功构建的镜像：
- `localhost/bidderbitter-backend:latest`

## 🚀 快速启动命令

### 1. 启动后端服务
```bash
# 创建网络
podman network create bidder_network

# 启动后端服务
podman run -d --name bidderbitter-backend \
    --network bidder_network \
    -p 8000:8000 \
    --env-file .env \
    localhost/bidderbitter-backend:latest
```

### 2. 查看服务状态
```bash
# 查看运行中的容器
podman ps

# 查看服务日志
podman logs -f bidderbitter-backend

# 测试 API 访问
curl http://localhost:8000/docs
```

## 🔧 完整系统部署

由于网络连接问题，我们无法直接拉取外部镜像。以下是解决方案：

### 网络问题解决方案

#### 方案1：配置镜像代理
```bash
# 编辑 podman 配置
nano ~/.config/containers/registries.conf

# 添加镜像代理
[[registry]]
prefix = "docker.io"
location = "docker.m.daocloud.io"
```

#### 方案2：使用国内镜像源
```bash
# 编辑配置文件
nano ~/.config/containers/registries.conf

# 添加以下内容
unqualified-search-registries = ["docker.io"]

[[registry]]
prefix = "docker.io"
location = "registry.cn-hangzhou.aliyuncs.com"
```

#### 方案3：手动下载并导入镜像
```bash
# 如果有其他可用网络，下载镜像并导入
podman save postgres:15 | gzip > postgres-15.tar.gz
podman load < postgres-15.tar.gz
```

### 完整服务启动（网络正常后）

```bash
# 1. 启动数据库
podman run -d --name postgres \
    --network bidder_network \
    -e POSTGRES_DB=bidder_db \
    -e POSTGRES_USER=bidder_user \
    -e POSTGRES_PASSWORD=bidder_pass \
    -v postgres_data:/var/lib/postgresql/data \
    -p 5432:5432 \
    postgres:15

# 2. 启动 Redis
podman run -d --name redis \
    --network bidder_network \
    -p 6379:6379 \
    redis:7-alpine

# 3. 启动 Chrome（用于截图）
podman run -d --name chrome \
    --network bidder_network \
    -p 4444:4444 \
    selenium/standalone-chrome:latest

# 4. 重新启动后端（连接所有服务）
podman stop bidderbitter-backend
podman rm bidderbitter-backend

podman run -d --name bidderbitter-backend \
    --network bidder_network \
    -p 8000:8000 \
    --env-file .env \
    -v ./uploads:/app/uploads \
    -v ./screenshots:/app/screenshots \
    -v ./generated_docs:/app/generated_docs \
    localhost/bidderbitter-backend:latest
```

## 🛠️ 调试命令大全

### 容器管理
```bash
# 查看所有容器
podman ps -a

# 启动/停止/重启容器
podman start <container-name>
podman stop <container-name>
podman restart <container-name>

# 删除容器
podman rm <container-name>

# 查看容器详细信息
podman inspect <container-name>
```

### 日志查看
```bash
# 查看实时日志
podman logs -f bidderbitter-backend

# 查看最近 100 行日志
podman logs --tail=100 bidderbitter-backend

# 查看特定时间的日志
podman logs --since="2025-06-22T10:00:00" bidderbitter-backend
```

### 进入容器调试
```bash
# 进入后端容器
podman exec -it bidderbitter-backend bash

# 在容器内运行命令
podman exec bidderbitter-backend ls -la /app

# 检查网络连接
podman exec bidderbitter-backend ping postgres
```

### 网络管理
```bash
# 查看网络
podman network list

# 查看网络详情
podman network inspect bidder_network

# 创建自定义网络
podman network create --driver bridge my_network
```

### 卷管理
```bash
# 查看卷
podman volume list

# 创建卷
podman volume create postgres_data

# 查看卷详情
podman volume inspect postgres_data
```

## 🔍 故障排除

### 1. 后端无法启动
```bash
# 查看错误日志
podman logs bidderbitter-backend

# 检查端口占用
lsof -i :8000

# 检查镜像是否存在
podman images | grep bidderbitter
```

### 2. 数据库连接失败
```bash
# 检查数据库是否启动
podman ps | grep postgres

# 测试数据库连接
podman exec -it postgres psql -U bidder_user -d bidder_db

# 检查网络连接
podman exec bidderbitter-backend nslookup postgres
```

### 3. 端口冲突
```bash
# 查看端口占用
sudo lsof -i :8000
sudo lsof -i :5432

# 使用不同端口
podman run -p 8001:8000 ...
```

### 4. 权限问题
```bash
# 检查文件权限
ls -la uploads/ screenshots/

# 修改权限
chmod -R 755 uploads/ screenshots/
```

## 📁 文件挂载（macOS 修复版）

在 macOS 上，如果遇到文件挂载问题，使用以下方法：

```bash
# 方法1：不使用 :Z 标记
-v ./uploads:/app/uploads

# 方法2：使用绝对路径
-v "$(pwd)/uploads:/app/uploads"

# 方法3：先创建目录
mkdir -p uploads screenshots generated_docs
```

## 🎯 开发热重载设置

要启用代码热重载功能：

```bash
# 停止现有容器
podman stop bidderbitter-backend
podman rm bidderbitter-backend

# 以开发模式启动（挂载源代码）
podman run -d --name bidderbitter-backend \
    --network bidder_network \
    -p 8000:8000 \
    --env-file .env \
    -v "$(pwd)/backend:/app" \
    -v "$(pwd)/uploads:/app/uploads" \
    -v "$(pwd)/screenshots:/app/screenshots" \
    localhost/bidderbitter-backend:latest
```

## 📊 性能监控

```bash
# 查看容器资源使用
podman stats

# 查看特定容器资源
podman stats bidderbitter-backend

# 查看系统资源
podman system df
```

## 🧹 清理命令

```bash
# 停止所有容器
podman stop $(podman ps -q)

# 删除所有停止的容器
podman container prune

# 删除未使用的镜像
podman image prune

# 完全清理系统
podman system prune -a
```

## 🚀 生产环境准备

当准备部署到生产环境时：

1. **修改环境变量**：
   ```bash
   # 编辑 .env 文件
   APP_ENV=production
   DEBUG=false
   LOG_LEVEL=INFO
   ```

2. **配置资源限制**：
   ```bash
   podman run --memory=1g --cpus=2 ...
   ```

3. **设置自动重启**：
   ```bash
   podman run --restart=always ...
   ```

## 📝 下一步计划

1. **解决网络连接问题**：配置镜像代理或使用国内镜像源
2. **构建前端镜像**：网络恢复后构建前端服务
3. **完整系统集成**：启动所有依赖服务
4. **添加数据持久化**：配置数据库卷挂载
5. **设置监控和日志**：添加系统监控

## 🎊 成功验证

✅ 后端服务已成功启动  
✅ API 文档可以访问: http://localhost:8000/docs  
✅ 镜像构建流程完整  
✅ 调试环境配置完成  

恭喜！你已经成功通过 Podman 部署了投标软件系统的后端服务！ 