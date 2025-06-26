#!/bin/bash

echo "🚀 正在完整部署投标软件系统..."

# 创建必要的目录
mkdir -p uploads screenshots generated_docs templates

# 创建网络
podman network create bidder_network 2>/dev/null || echo "网络已存在"

# 停止可能存在的旧容器
podman stop bidderbitter-backend bidderbitter-frontend 2>/dev/null || true
podman rm bidderbitter-backend bidderbitter-frontend 2>/dev/null || true

# 启动后端服务
echo "🔧 启动后端服务..."
podman run -d --name bidderbitter-backend \
    --network bidder_network \
    -p 8000:8000 \
    --env-file .env \
    -v "$(pwd)/uploads:/app/uploads" \
    -v "$(pwd)/screenshots:/app/screenshots" \
    -v "$(pwd)/generated_docs:/app/generated_docs" \
    -v "$(pwd)/templates:/app/templates" \
    localhost/bidderbitter-backend:latest

# 启动前端服务
echo "🎨 启动前端服务..."
podman run -d --name bidderbitter-frontend \
    --network bidder_network \
    -p 3000:3000 \
    localhost/bidderbitter-frontend:latest

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
echo "🔍 检查服务状态..."
podman ps

echo "🎉 部署完成！"
echo "前端: http://localhost:3000"
echo "后端: http://localhost:8000"
echo "API文档: http://localhost:8000/docs"
