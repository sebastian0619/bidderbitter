#!/usr/bin/env python3
"""
综合分析测试脚本
验证所有文档类型都使用统一的OCR+视觉分析逻辑
"""

import asyncio
import requests
import time
import json

def test_document_analysis():
    """测试文档分析的综合逻辑"""
    
    base_url = "http://localhost:8000"
    
    print("🔍 开始测试综合分析逻辑...")
    
    # 测试文件管理的分析
    print("\n1. 测试文件管理分析...")
    try:
        response = requests.post(
            f"{base_url}/api/files/analyze-document?file_id=1&enable_vision=true&force_reanalyze=true",
            headers={"Content-Type": "application/json"},
            timeout=120
        )
        if response.status_code == 200:
            result = response.json()
            classification = result.get("classification", {})
            print(f"   ✅ 文件分析成功: {classification.get('type')} (置信度: {classification.get('confidence')})")
            print(f"   📊 数据源: {classification.get('data_sources', [])}")
        else:
            print(f"   ❌ 文件分析失败: {response.status_code}")
    except Exception as e:
        print(f"   ❌ 文件分析异常: {e}")
    
    # 测试业绩分析
    print("\n2. 测试业绩分析...")
    try:
        # 假设有业绩记录ID为1
        response = requests.post(
            f"{base_url}/api/performances/1/reanalyze",
            data={
                "enable_vision_analysis": "true",
                "enable_ocr": "true", 
                "update_fields": "true"
            },
            timeout=120
        )
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ 业绩分析成功: {result.get('message')}")
            ai_analysis = result.get("ai_analysis", {})
            print(f"   📊 置信度: {ai_analysis.get('confidence_score')}")
        else:
            print(f"   ❌ 业绩分析失败: {response.status_code}")
    except Exception as e:
        print(f"   ❌ 业绩分析异常: {e}")
    
    # 测试律师证分析（如果有的话）
    print("\n3. 测试律师证分析...")
    try:
        # 获取律师证列表
        response = requests.get(f"{base_url}/api/lawyer-certificates/list?page=1&page_size=1")
        if response.status_code == 200:
            certificates = response.json().get("certificates", [])
            if certificates:
                cert_id = certificates[0]["id"]
                # 重新分析律师证
                reanalyze_response = requests.post(
                    f"{base_url}/api/lawyer-certificates/{cert_id}/reanalyze",
                    data={
                        "enable_vision_analysis": "true",
                        "enable_ocr": "true"
                    },
                    timeout=120
                )
                if reanalyze_response.status_code == 200:
                    result = reanalyze_response.json()
                    print(f"   ✅ 律师证分析成功: {result.get('message')}")
                else:
                    print(f"   ❌ 律师证分析失败: {reanalyze_response.status_code}")
            else:
                print("   ℹ️ 暂无律师证记录")
        else:
            print(f"   ❌ 获取律师证列表失败: {response.status_code}")
    except Exception as e:
        print(f"   ❌ 律师证分析异常: {e}")

def monitor_analysis_logs():
    """监控分析日志"""
    print("\n📋 监控分析日志 (10秒)...")
    print("请在另一个终端运行: docker compose logs backend --follow --tail 20 | grep -E '(AI综合分析|数据源|视觉分析|OCR文本)'")
    time.sleep(10)

if __name__ == "__main__":
    print("🚀 开始测试所有文档类型的综合分析逻辑")
    print("=" * 60)
    
    # 检查服务状态
    try:
        response = requests.get("http://localhost:8000/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ 后端服务正常")
        else:
            print("❌ 后端服务异常")
            exit(1)
    except:
        print("❌ 无法连接后端服务")
        exit(1)
    
    test_document_analysis()
    monitor_analysis_logs()
    
    print("\n🎉 测试完成！")
    print("\n💡 预期结果:")
    print("   - 所有分析都应该显示数据源包含: OCR文本, 独立视觉分析")
    print("   - 视觉分析不应该超时")
    print("   - 分类结果应该正确更新到数据库") 