#!/bin/bash

# 投标软件系统 Podman 启动脚本

echo "🚀 正在通过 Podman 启动投标软件系统..."

# 检查Podman是否安装
if ! command -v podman &> /dev/null; then
    echo "❌ 错误：未检测到Podman，请先安装Podman"
    exit 1
fi

# 检查Docker Compose是否可用（用作 podman compose 的后端）
if ! command -v docker-compose &> /dev/null; then
    echo "❌ 错误：未检测到Docker Compose，请先安装Docker Compose（podman compose 需要它）"
    echo "   安装方法: brew install docker-compose"
    exit 1
fi

# 创建必要的目录
echo "📁 创建必要的目录..."
mkdir -p uploads screenshots generated_docs templates

# 检查环境变量文件
if [ ! -f .env ]; then
    echo "⚙️  创建环境变量文件..."
    cat > .env << 'EOF'
# ==================== 投标软件系统环境变量配置 ====================

# ==================== 数据库配置 ====================
DATABASE_URL=postgresql://bidder_user:bidder_pass@postgres:5432/bidder_db
REDIS_URL=redis://redis:6379

# ==================== AI服务配置 ====================
# AI服务提供商选择: openai, azure, anthropic, google, custom
AI_PROVIDER=openai

# OpenAI配置
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4
OPENAI_VISION_MODEL=gpt-4-vision-preview

# Azure OpenAI配置（如果使用Azure）
# AZURE_OPENAI_API_KEY=your_azure_api_key
# AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
# AZURE_OPENAI_API_VERSION=2024-02-01
# AZURE_OPENAI_DEPLOYMENT_NAME=your-deployment-name
# AZURE_OPENAI_VISION_DEPLOYMENT_NAME=your-vision-deployment-name

# 其他AI服务配置
# ANTHROPIC_API_KEY=your_anthropic_api_key
# GOOGLE_API_KEY=your_google_api_key
# CUSTOM_AI_API_KEY=your_custom_api_key
# CUSTOM_AI_BASE_URL=https://your-custom-api.com/v1

# ==================== 截图服务配置 ====================
SELENIUM_HUB_URL=http://chrome:4444/wd/hub
ENABLE_SCREENSHOT=true
SCREENSHOT_TIMEOUT=30
SCREENSHOT_MAX_PAGES=20

# ==================== 文件上传配置 ====================
MAX_FILE_SIZE=52428800
ALLOWED_FILE_TYPES=pdf,docx,doc,png,jpg,jpeg
UPLOAD_PATH=/app/uploads
SCREENSHOT_PATH=/app/screenshots
GENERATED_DOCS_PATH=/app/generated_docs

# ==================== 应用配置 - 开发模式 ====================
APP_ENV=development
LOG_LEVEL=DEBUG
DEBUG=true
SECRET_KEY=dev-secret-key-change-in-production

# ==================== 功能开关 ====================
ENABLE_AI=true
ENABLE_OCR=true
ENABLE_DOCUMENT_GENERATION=true

# ==================== OCR配置 ====================
OCR_LANGUAGES=chi_sim+eng
OCR_ENGINE=tesseract

# ==================== 文档生成配置 ====================
WORD_TEMPLATE_PATH=/app/templates
DEFAULT_FONT=Microsoft YaHei
IMAGE_MAX_WIDTH=1654
IMAGE_QUALITY=85

# ==================== 性能配置 ====================
WORKER_CONNECTIONS=1000
MAX_CONCURRENT_REQUESTS=100
REQUEST_TIMEOUT=300

# ==================== 安全配置 ====================
ALLOWED_HOSTS=*
CORS_ORIGINS=http://localhost:5555,http://frontend:3000

EOF
    echo "✅ 环境变量文件已创建，请根据需要修改 .env 文件"
    echo ""
    echo "🔑 重要提示："
    echo "   请在 .env 文件中配置您的 API 密钥："
    echo "   - OPENAI_API_KEY: OpenAI API密钥（用于AI功能）"
    echo "   - 或配置其他AI服务商的相关密钥"
fi

# 停止可能运行的旧容器
echo "🛑 停止可能存在的旧容器..."
podman compose -f docker-compose.podman.yml down 2>/dev/null || true

# 构建和启动服务
echo "🏗️  构建并启动服务..."
podman compose -f docker-compose.podman.yml up -d --build

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 15

# 检查服务状态
echo "🔍 检查服务状态..."
podman compose -f docker-compose.podman.yml ps

# 检查后端健康状态
echo "🏥 检查后端健康状态..."
max_attempts=30
attempt=1

while [ $attempt -le $max_attempts ]; do
    if curl -f http://localhost:8000/api/health > /dev/null 2>&1; then
        echo "✅ 后端服务已启动"
        break
    elif curl -f http://localhost:8000 > /dev/null 2>&1; then
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
    echo "   podman compose -f docker-compose.podman.yml logs backend"
    exit 1
fi

# 检查前端状态
echo "🌐 检查前端服务..."
if curl -f http://localhost:5555 > /dev/null 2>&1; then
    echo "✅ 前端服务已启动"
else
    echo "⚠️  前端服务可能还在启动中..."
fi

echo ""
echo "🎉 投标软件系统启动完成！"
echo ""
echo "📋 访问地址："
echo "   前端界面: http://localhost:5555"
echo "   后端API:  http://localhost:8000"
echo "   API文档:  http://localhost:8000/docs"
echo ""
echo "🔧 调试功能："
echo "   - 后端支持热重载，修改 Python 文件会自动重启"
echo "   - 前端支持热重载，修改 Vue 文件会自动刷新"
echo "   - 源代码已挂载到容器，可直接编辑调试"
echo ""
echo "📖 常用命令："
echo "   查看所有日志: podman compose -f docker-compose.podman.yml logs -f"
echo "   查看后端日志: podman compose -f docker-compose.podman.yml logs -f backend"
echo "   查看前端日志: podman compose -f docker-compose.podman.yml logs -f frontend"
echo "   重启服务:    podman compose -f docker-compose.podman.yml restart"
echo "   停止服务:    podman compose -f docker-compose.podman.yml down"
echo "   进入容器:    podman compose -f docker-compose.podman.yml exec backend bash"
echo "   查看容器:    podman ps -a"
echo ""
echo "🐛 如遇问题："
echo "   1. 查看具体日志找出错误原因"
echo "   2. 确保端口 5555, 8000, 5432, 6379, 4444 未被占用"
echo "   3. 检查 .env 文件配置是否正确"
echo "   4. 完全重建: podman compose -f docker-compose.podman.yml down && podman compose -f docker-compose.podman.yml up -d --build" 