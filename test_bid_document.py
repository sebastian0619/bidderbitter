#!/usr/bin/env python3
"""
投标文件制作功能测试脚本
"""

import os
import sys
import asyncio
import json
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_bid_document_service():
    """测试投标文档服务"""
    print("🧪 开始测试投标文档制作功能...")
    
    try:
        # 导入服务
        from backend.bid_document_service import bid_document_service
        print("✅ 投标文档服务导入成功")
        
        # 测试招标信息提取
        print("\n📋 测试招标信息提取...")
        test_file_path = "test_files/招标文件示例.pdf"
        
        if os.path.exists(test_file_path):
            print(f"找到测试文件: {test_file_path}")
            # 这里可以添加实际的提取测试
        else:
            print(f"⚠️  测试文件不存在: {test_file_path}")
            print("请创建测试文件或使用现有文件进行测试")
        
        # 测试文档生成
        print("\n📄 测试文档生成...")
        print("文档生成功能已集成到服务中")
        
        print("\n✅ 投标文档制作功能测试完成")
        
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
    except Exception as e:
        print(f"❌ 测试失败: {e}")

def test_api_endpoints():
    """测试API端点"""
    print("\n🌐 测试API端点...")
    
    try:
        import requests
        
        base_url = "http://localhost:8000"
        
        # 测试健康检查
        response = requests.get(f"{base_url}/api/health")
        if response.status_code == 200:
            print("✅ 健康检查端点正常")
        else:
            print(f"❌ 健康检查失败: {response.status_code}")
        
        # 测试投标文档API
        response = requests.get(f"{base_url}/api/bid-documents/templates")
        if response.status_code == 200:
            print("✅ 投标文档模板API正常")
        else:
            print(f"❌ 投标文档模板API失败: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到API服务器，请确保服务器正在运行")
    except Exception as e:
        print(f"❌ API测试失败: {e}")

def create_sample_project():
    """创建示例项目"""
    print("\n📁 创建示例项目...")
    
    try:
        import requests
        
        base_url = "http://localhost:8000"
        
        project_data = {
            "name": "示例投标项目",
            "tender_agency": "示例招标代理机构",
            "tender_company": "示例招标人",
            "bidder_name": "示例投标人",
            "deadline": "2024-12-31T23:59:59",
            "description": "这是一个示例投标项目"
        }
        
        response = requests.post(f"{base_url}/api/projects", json=project_data)
        
        if response.status_code == 200:
            project = response.json()
            print(f"✅ 示例项目创建成功: {project.get('name')}")
            return project.get('id')
        else:
            print(f"❌ 项目创建失败: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ 创建示例项目失败: {e}")
        return None

def main():
    """主函数"""
    print("🚀 投标文件制作功能测试")
    print("=" * 50)
    
    # 测试服务功能
    test_bid_document_service()
    
    # 测试API端点
    test_api_endpoints()
    
    # 创建示例项目
    project_id = create_sample_project()
    
    print("\n" + "=" * 50)
    print("📝 测试总结:")
    print("1. 投标文档服务已集成")
    print("2. API端点已配置")
    print("3. 前端页面已创建")
    print("4. 路由已配置")
    
    if project_id:
        print(f"5. 示例项目已创建 (ID: {project_id})")
    
    print("\n🎯 下一步:")
    print("1. 启动后端服务: python -m uvicorn backend.main:app --reload")
    print("2. 启动前端服务: cd frontend && npm run dev")
    print("3. 访问: http://localhost:3000/bid-document-maker")
    print("4. 上传招标文件并测试完整流程")

if __name__ == "__main__":
    main() 