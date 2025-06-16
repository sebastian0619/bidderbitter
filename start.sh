#!/bin/bash

# 投标软件系统启动脚本

echo "🚀 正在启动投标软件系统..."

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ 错误：未检测到Docker，请先安装Docker"
    exit 1
fi

# 检查Docker Compose是否安装
if ! command -v docker-compose &> /dev/null; then
    echo "❌ 错误：未检测到Docker Compose，请先安装Docker Compose"
    exit 1
fi

# 创建必要的目录
echo "📁 创建必要的目录..."
mkdir -p uploads screenshots generated_docs

# 检查环境变量文件
if [ ! -f .env ]; then
    echo "⚙️  创建环境变量文件..."
    cat > .env << EOF
# 投标软件系统环境变量配置

# OpenAI API配置（可选，用于AI功能）
OPENAI_API_KEY=your_openai_api_key_here

# 数据库配置
DATABASE_URL=postgresql://bidder_user:bidder_pass@postgres:5432/bidder_db
POSTGRES_DB=bidder_db
POSTGRES_USER=bidder_user
POSTGRES_PASSWORD=bidder_pass

# Redis配置
REDIS_URL=redis://redis:6379

# 应用配置
API_BASE_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000

# Selenium配置
SELENIUM_HUB_URL=http://chrome:4444/wd/hub

# 文件上传配置
MAX_FILE_SIZE=50MB
UPLOAD_PATH=/app/uploads
SCREENSHOT_PATH=/app/screenshots
GENERATED_DOCS_PATH=/app/generated_docs

# 日志配置
LOG_LEVEL=INFO

# 是否启用AI功能
ENABLE_AI=true

# 是否启用截图功能
ENABLE_SCREENSHOT=true
EOF
    echo "✅ 环境变量文件已创建，请根据需要修改 .env 文件"
fi

# 停止可能运行的旧容器
echo "🛑 停止可能存在的旧容器..."
docker-compose down

# 构建和启动服务
echo "🏗️  构建并启动服务..."
docker-compose up -d --build

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
echo "🔍 检查服务状态..."
docker-compose ps

# 检查后端健康状态
echo "🏥 检查后端健康状态..."
max_attempts=30
attempt=1

while [ $attempt -le $max_attempts ]; do
    if curl -f http://localhost:8000/api/health > /dev/null 2>&1; then
        echo "✅ 后端服务已启动"
        break
    else
        echo "⏳ 等待后端服务启动... ($attempt/$max_attempts)"
        sleep 2
        ((attempt++))
    fi
done

if [ $attempt -gt $max_attempts ]; then
    echo "❌ 后端服务启动超时，请检查日志："
    echo "   docker-compose logs backend"
    exit 1
fi

# 检查前端状态
echo "🌐 检查前端服务..."
if curl -f http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ 前端服务已启动"
else
    echo "⚠️  前端服务可能还在启动中..."
fi

echo ""
echo "🎉 投标软件系统启动完成！"
echo ""
echo "📋 访问地址："
echo "   前端界面: http://localhost:3000"
echo "   后端API:  http://localhost:8000"
echo "   API文档:  http://localhost:8000/docs"
echo ""
echo "📖 使用说明："
echo "   1. 如需AI功能，请在 .env 文件中配置 OPENAI_API_KEY"
echo "   2. 首次使用建议先访问系统设置页面进行配置"
echo "   3. 查看日志: docker-compose logs -f"
echo "   4. 停止服务: docker-compose down"
echo ""
echo "🐛 如遇问题："
echo "   - 查看日志: docker-compose logs"
echo "   - 重启服务: docker-compose restart"
echo "   - 完全重建: docker-compose down && docker-compose up -d --build" 