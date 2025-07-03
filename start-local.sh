#!/bin/bash

# BidderBitter 本地开发启动脚本
# 使用本地配置文件启动服务（包含代理配置）

echo "🚀 启动BidderBitter本地开发环境（使用代理配置）"

# 检查本地配置文件是否存在
if [ ! -f "docker-compose.local.yml" ]; then
    echo "❌ 错误：docker-compose.local.yml 文件不存在"
    echo "请确保已创建本地配置文件"
    exit 1
fi

echo "📋 本地配置文件: docker-compose.local.yml"
echo "🔧 启动服务..."

# 使用基础配置 + 本地覆盖配置启动
docker compose -f docker-compose.yml -f docker-compose.local.yml up -d

echo "✅ 服务启动完成！"
echo ""
echo "🌐 访问地址："
echo "   前端: http://localhost:5555"
echo "   后端API: http://localhost:8000"
echo "   API文档: http://localhost:8000/docs"
echo ""
echo "📋 常用命令："
echo "   查看日志: docker compose -f docker-compose.yml -f docker-compose.local.yml logs -f"
echo "   停止服务: docker compose -f docker-compose.yml -f docker-compose.local.yml down"
echo "   重启后端: docker compose -f docker-compose.yml -f docker-compose.local.yml restart backend" 
 