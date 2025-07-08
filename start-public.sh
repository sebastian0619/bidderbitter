#!/bin/bash

# 投标苦 - 使用GitHub Container Registry Public镜像启动脚本
# 无需认证，任何人都可以使用

set -e

# 配置变量
GITHUB_USERNAME=${GITHUB_USERNAME:-"sebastian0619"}
REPO_NAME=${REPO_NAME:-"bidderbitter"}
REGISTRY="ghcr.io"

# 镜像地址
BACKEND_IMAGE="${REGISTRY}/${GITHUB_USERNAME}/${REPO_NAME}/backend:latest"
FRONTEND_IMAGE="${REGISTRY}/${GITHUB_USERNAME}/${REPO_NAME}/frontend:latest"

echo "🐳 投标苦 - 使用Public镜像启动"
echo "=================================="
echo "📦 后端镜像: ${BACKEND_IMAGE}"
echo "📦 前端镜像: ${FRONTEND_IMAGE}"
echo "🔓 所有镜像都是Public的，无需认证"
echo ""

# 检查Docker是否运行
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker未运行，请先启动Docker"
    exit 1
fi

# 创建必要的目录
echo "📁 创建必要的目录..."
mkdir -p uploads screenshots generated_docs templates easyocr_models docling_models

# 拉取最新镜像
echo "⬇️  拉取最新镜像..."
docker pull ${BACKEND_IMAGE}
docker pull ${FRONTEND_IMAGE}

# 停止并删除现有容器
echo "🛑 停止现有容器..."
docker-compose -f docker-compose.ghcr.yml down 2>/dev/null || true

# 启动服务
echo "🚀 启动服务..."
docker-compose -f docker-compose.ghcr.yml up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
echo "🔍 检查服务状态..."
if curl -f http://localhost:8000/api/health > /dev/null 2>&1; then
    echo "✅ 后端服务运行正常"
else
    echo "⚠️  后端服务可能还在启动中..."
fi

if curl -f http://localhost:5555 > /dev/null 2>&1; then
    echo "✅ 前端服务运行正常"
else
    echo "⚠️  前端服务可能还在启动中..."
fi

echo ""
echo "🎉 启动完成！"
echo "=================================="
echo "🌐 前端地址: http://localhost:5555"
echo "🔧 后端API: http://localhost:8000"
echo "📊 健康检查: http://localhost:8000/api/health"
echo ""
echo "📝 使用说明:"
echo "   - 前端界面: 打开浏览器访问 http://localhost:5555"
echo "   - API文档: 访问 http://localhost:8000/docs"
echo "   - 停止服务: docker-compose -f docker-compose.ghcr.yml down"
echo "   - 查看日志: docker-compose -f docker-compose.ghcr.yml logs -f"
echo ""
echo "🔓 这些镜像都是Public的，任何人都可以拉取使用！" 