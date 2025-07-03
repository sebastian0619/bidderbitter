#!/bin/bash

# 投标苦系统重构版启动脚本
# Author: AI Assistant
# Date: 2024-12-30

set -e

echo "🚀 投标苦系统重构版启动中..."
echo "=================================="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检查Docker/Podman
if command -v docker &> /dev/null; then
    DOCKER_CMD="docker"
    COMPOSE_CMD="docker compose"
    echo -e "${GREEN}✅ 检测到Docker环境${NC}"
elif command -v podman &> /dev/null; then
    DOCKER_CMD="podman"
    COMPOSE_CMD="podman-compose"
    echo -e "${GREEN}✅ 检测到Podman环境${NC}"
else
    echo -e "${RED}❌ 未检测到Docker或Podman环境${NC}"
    exit 1
fi

# 检查配置文件
if [ ! -f "docker-compose.local.yml" ]; then
    echo -e "${RED}❌ 未找到 docker-compose.local.yml 配置文件${NC}"
    exit 1
fi

echo -e "${BLUE}📋 启动配置:${NC}"
echo "   - 后端端口: 8000"
echo "   - 前端端口: 5555"
echo "   - 数据库: PostgreSQL 15"
echo "   - 缓存: Redis 7"
echo "   - 代理: kingscross.online:6785"
echo ""

# 清理之前的容器
echo -e "${YELLOW}🧹 清理之前的容器...${NC}"
$COMPOSE_CMD -f docker-compose.local.yml down --remove-orphans 2>/dev/null || true

# 清理悬空的镜像和网络
echo -e "${YELLOW}🧹 清理悬空资源...${NC}"
$DOCKER_CMD system prune -f 2>/dev/null || true

# 创建必要的目录
echo -e "${YELLOW}📁 创建必要的目录...${NC}"
mkdir -p uploads screenshots generated_docs templates easyocr_models docling_models

# 构建并启动服务
echo -e "${BLUE}🔨 构建并启动服务...${NC}"
$COMPOSE_CMD -f docker-compose.local.yml up --build -d

# 等待服务启动
echo -e "${YELLOW}⏳ 等待服务启动...${NC}"
sleep 10

# 检查服务状态
echo -e "${BLUE}🔍 检查服务状态...${NC}"
$COMPOSE_CMD -f docker-compose.local.yml ps

# 等待健康检查通过
echo -e "${YELLOW}💚 等待健康检查通过...${NC}"
max_attempts=30
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ 后端服务健康检查通过${NC}"
        break
    fi
    attempt=$((attempt + 1))
    echo -n "."
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    echo -e "${RED}❌ 后端服务健康检查超时${NC}"
    echo -e "${YELLOW}📋 显示后端日志:${NC}"
    $COMPOSE_CMD -f docker-compose.local.yml logs backend | tail -20
    exit 1
fi

# 检查前端服务
echo -e "${YELLOW}🌐 检查前端服务...${NC}"
if curl -s http://localhost:5555 > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 前端服务运行正常${NC}"
else
    echo -e "${YELLOW}⚠️  前端服务可能仍在启动中${NC}"
fi

# 显示访问信息
echo ""
echo -e "${GREEN}🎉 投标苦系统重构版启动完成!${NC}"
echo "=================================="
echo -e "${BLUE}📱 访问地址:${NC}"
echo "   前端界面: http://localhost:5555"
echo "   后端API:  http://localhost:8000"
echo "   API文档:  http://localhost:8000/docs"
echo ""
echo -e "${BLUE}🛠️  管理命令:${NC}"
echo "   查看日志: $COMPOSE_CMD -f docker-compose.local.yml logs -f"
echo "   停止服务: $COMPOSE_CMD -f docker-compose.local.yml down"
echo "   重启服务: $COMPOSE_CMD -f docker-compose.local.yml restart"
echo ""
echo -e "${BLUE}🔧 功能特点:${NC}"
echo "   ✅ MCP客户端集成"
echo "   ✅ 统一Docling OCR"
echo "   ✅ 智能文档分析"
echo "   ✅ 业绩管理系统"
echo "   ✅ 律师证管理"
echo "   ✅ 文件管理系统"
echo "   ✅ 健康检查机制"
echo ""

# 实时显示启动日志
if [ "$1" == "--logs" ] || [ "$1" == "-l" ]; then
    echo -e "${YELLOW}📋 显示实时日志 (Ctrl+C 退出):${NC}"
    $COMPOSE_CMD -f docker-compose.local.yml logs -f
fi 