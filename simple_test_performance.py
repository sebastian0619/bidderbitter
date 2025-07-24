#!/usr/bin/env python3
"""
简单测试脚本 - 检查Docling功能是否正常
"""

import requests
import time
import json

def test_health():
    """测试健康状态"""
    try:
        response = requests.get('http://localhost:8000/api/health', timeout=5)
        if response.status_code == 200:
            print("✅ 后端服务正常")
            return True
        else:
            print(f"❌ 后端服务异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 连接后端失败: {e}")
        return False

def test_docling_status():
    """测试Docling状态"""
    try:
        # 检查是否有docling状态接口
        response = requests.get('http://localhost:8000/api/ai-tools/docling/status', timeout=10)
        if response.status_code == 200:
            result = response.json()
            print("✅ Docling状态:")
            print(f"  - 可用: {result.get('docling_available', False)}")
            print(f"  - 已初始化: {result.get('initialized', False)}")
            print(f"  - 转换器就绪: {result.get('converter_ready', False)}")
            config = result.get('config', {})
            print(f"  - OCR启用: {config.get('enable_ocr', False)}")
            print(f"  - 图片描述启用: {config.get('enable_picture_description', False)}")
            print(f"  - 视觉模型: {config.get('vision_provider', 'N/A')} - {config.get('vision_model', 'N/A')}")
            return True
        else:
            print(f"❌ Docling状态获取失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Docling状态检查失败: {e}")
        return False

def test_simple_analysis():
    """测试简单的文档分析"""
    try:
        # 创建一个简单的测试数据
        test_data = {
            "text": "这是一个测试文档，用于验证AI分析功能。"
        }
        
        response = requests.post(
            'http://localhost:8000/api/ai-tools/analyze-text',
            json=test_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 文本分析测试通过")
            print(f"  - 分析结果: {result.get('success', False)}")
            return True
        else:
            print(f"❌ 文本分析失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 文本分析测试失败: {e}")
        return False

if __name__ == "__main__":
    print("🚀 开始性能测试...")
    
    # 测试1: 健康检查
    if not test_health():
        exit(1)
    
    # 测试2: Docling状态
    if not test_docling_status():
        print("⚠️  Docling状态检查失败，但继续其他测试")
    
    # 测试3: 简单分析
    if not test_simple_analysis():
        print("⚠️  简单分析测试失败")
    
    print("\n✅ 基础测试完成")
    print("\n📊 现在让我们查看后端日志，看看详细的处理过程:")
    print("docker compose logs backend --tail 50 | grep -E '(DoclingService|图片分析|AI分析|文本提取)'") 