# GitHub Actions 自动构建指南

## 概述

本项目配置了GitHub Actions工作流，在每次push到指定分支时自动构建前后端Docker镜像并推送到GitHub Container Registry (ghcr.io)。**所有镜像都设置为PUBLIC，无需认证即可拉取。**

## 工作流文件

### 1. `.github/workflows/push-build.yml` (推荐)
- **触发条件**: 推送到 `main`、`master`、`develop` 分支
- **功能**: 构建并推送前后端镜像，自动设置为PUBLIC
- **标签策略**: 
  - `latest`: 最新版本
  - `{branch-name}`: 分支名标签
  - `{commit-sha}`: 提交哈希标签
- **权限**: 所有镜像设置为PUBLIC，无需认证

### 2. `.github/workflows/build-and-push.yml` (完整版)
- **触发条件**: 推送到指定分支、创建标签、Pull Request
- **功能**: 更完整的构建流程，支持多平台和多标签策略

## 镜像命名规则

### 后端镜像
```
ghcr.io/{your-username}/{repo-name}/backend:{tag}
```

### 前端镜像
```
ghcr.io/{your-username}/{repo-name}/frontend:{tag}
```

## 标签说明

| 标签类型 | 示例 | 说明 |
|---------|------|------|
| `latest` | `backend:latest` | 最新版本 |
| 分支名 | `backend:main` | 对应分支的最新版本 |
| 提交哈希 | `backend:abc123` | 特定提交的版本 |

## 使用方法

### 1. 启用GitHub Actions

1. 确保仓库已启用GitHub Actions
2. 确保仓库有适当的权限设置
3. 推送代码到指定分支即可触发构建

### 2. 查看构建状态

1. 进入GitHub仓库页面
2. 点击 "Actions" 标签页
3. 查看最新的工作流运行状态

### 3. 拉取镜像 (无需认证)

```bash
# 拉取最新版本 (无需登录)
docker pull ghcr.io/{your-username}/{repo-name}/backend:latest
docker pull ghcr.io/{your-username}/{repo-name}/frontend:latest

# 拉取特定分支版本
docker pull ghcr.io/{your-username}/{repo-name}/backend:main
docker pull ghcr.io/{your-username}/{repo-name}/frontend:main

# 拉取特定提交版本
docker pull ghcr.io/{your-username}/{repo-name}/backend:abc123
docker pull ghcr.io/{your-username}/{repo-name}/frontend:abc123
```

### 4. 使用镜像

```bash
# 运行后端服务
docker run -d \
  --name bidderbitter-backend \
  -p 8000:8000 \
  ghcr.io/{your-username}/{repo-name}/backend:latest

# 运行前端服务
docker run -d \
  --name bidderbitter-frontend \
  -p 3000:3000 \
  ghcr.io/{your-username}/{repo-name}/frontend:latest
```

## 配置说明

### 🔓 Public镜像设置

**重要**: 所有镜像都自动设置为PUBLIC，这意味着：
- ✅ 任何人都可以拉取镜像，无需GitHub账号
- ✅ 无需配置认证信息
- ✅ 可以直接在CI/CD中使用
- ✅ 适合开源项目分享

### 环境变量

工作流中使用的环境变量：

- `REGISTRY`: 镜像仓库地址 (ghcr.io)
- `IMAGE_NAME`: 镜像名称 (自动从仓库名获取)

### 权限设置

工作流需要以下权限：
- `contents: read`: 读取仓库内容
- `packages: write`: 推送镜像到GitHub Container Registry

### 缓存策略

- 使用GitHub Actions缓存加速构建
- 支持Docker层缓存
- 多平台构建支持 (linux/amd64)

## 故障排除

### 1. 构建失败

**常见原因:**
- Dockerfile语法错误
- 依赖安装失败
- 权限不足

**解决方法:**
1. 检查GitHub Actions日志
2. 验证Dockerfile语法
3. 确保所有依赖文件存在

### 2. 推送失败

**常见原因:**
- GitHub Token权限不足
- 镜像仓库不存在
- 网络连接问题

**解决方法:**
1. 检查仓库权限设置
2. 确保GitHub Token有packages:write权限
3. 检查网络连接

### 3. 镜像拉取失败

**常见原因:**
- 镜像不存在
- 权限不足
- 网络问题

**解决方法:**
1. 确认镜像已成功推送
2. 检查镜像名称和标签
3. 确保有拉取权限

## 自定义配置

### 修改触发分支

编辑 `.github/workflows/push-build.yml` 文件中的 `branches` 配置：

```yaml
on:
  push:
    branches: [ main, master, develop, feature/* ]  # 添加更多分支
```

### 修改镜像标签策略

在 `docker/build-push-action` 步骤中修改 `tags` 配置：

```yaml
tags: |
  ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}/backend:${{ github.sha }}
  ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}/backend:${{ github.ref_name }}
  ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}/backend:latest
  ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}/backend:v1.0.0  # 添加自定义标签
```

### 添加多平台支持

修改 `platforms` 配置：

```yaml
platforms: linux/amd64,linux/arm64,linux/arm/v7
```

## 快速启动

### 使用Public镜像启动

```bash
# 使用提供的启动脚本
./start-public.sh

# 或者手动启动
docker-compose -f docker-compose.ghcr.yml up -d
```

### 手动拉取和使用

```bash
# 拉取镜像 (无需认证)
docker pull ghcr.io/sebastian0619/bidderbitter/backend:latest
docker pull ghcr.io/sebastian0619/bidderbitter/frontend:latest

# 运行容器
docker run -d -p 8000:8000 ghcr.io/sebastian0619/bidderbitter/backend:latest
docker run -d -p 3000:3000 ghcr.io/sebastian0619/bidderbitter/frontend:latest
```

## 最佳实践

1. **定期清理旧镜像**: GitHub Container Registry有存储限制
2. **使用语义化标签**: 为重要版本创建有意义的标签
3. **监控构建时间**: 优化Dockerfile减少构建时间
4. **测试镜像**: 在本地测试镜像后再推送
5. **文档化**: 保持镜像使用说明的更新
6. **Public镜像优势**: 无需认证，便于分享和部署

## 相关链接

- [GitHub Actions 文档](https://docs.github.com/en/actions)
- [GitHub Container Registry 文档](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
- [Docker Buildx 文档](https://docs.docker.com/buildx/) 