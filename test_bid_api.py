#!/usr/bin/env python3
"""
测试投标文档API功能
"""

import requests
import json
import os

# API基础URL
BASE_URL = "http://localhost:8000/api"

def test_api_endpoints():
    """测试API端点"""
    print("=== 测试投标文档API端点 ===")
    
    # 1. 测试模板列表
    print("\n1. 测试获取模板列表...")
    try:
        response = requests.get(f"{BASE_URL}/bid-documents/templates")
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
    except Exception as e:
        print(f"错误: {e}")
    
    # 2. 测试项目列表
    print("\n2. 测试获取项目列表...")
    try:
        response = requests.get(f"{BASE_URL}/projects")
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
    except Exception as e:
        print(f"错误: {e}")
    
    # 3. 测试创建项目
    print("\n3. 测试创建项目...")
    try:
        project_data = {
            "name": "测试投标项目",
            "description": "这是一个测试项目",
            "bidder_name": "测试律师事务所"
        }
        response = requests.post(f"{BASE_URL}/projects", json=project_data)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        
        if response.status_code == 200:
            project_id = response.json().get("data", {}).get("id")
            print(f"项目ID: {project_id}")
            return project_id
    except Exception as e:
        print(f"错误: {e}")
    
    return None

def test_file_upload(project_id):
    """测试文件上传"""
    if not project_id:
        print("没有项目ID，跳过文件上传测试")
        return
    
    print(f"\n4. 测试文件上传到项目 {project_id}...")
    
    # 创建一个测试文件
    test_file_path = "test_tender_doc.txt"
    with open(test_file_path, "w", encoding="utf-8") as f:
        f.write("""
招标文件测试

招标人：测试招标公司
招标代理机构：测试代理公司
项目名称：测试法律服务项目
投标截止时间：2024年12月31日
项目预算：100万元
业务范围：法律顾问服务

投标要求：
1. 具备相关资质
2. 提供相关业绩证明
3. 提供律师团队介绍

评标标准：
1. 技术方案 40%
2. 业绩经验 30%
3. 价格 30%
        """)
    
    try:
        with open(test_file_path, "rb") as f:
            files = {"file": ("test_tender_doc.txt", f, "text/plain")}
            data = {"project_id": str(project_id)}
            
            response = requests.post(
                f"{BASE_URL}/bid-documents/analyze-tender-document",
                files=files,
                data=data
            )
            
            print(f"状态码: {response.status_code}")
            print(f"响应: {response.json()}")
            
    except Exception as e:
        print(f"错误: {e}")
    finally:
        # 清理测试文件
        if os.path.exists(test_file_path):
            os.remove(test_file_path)

def test_project_sections(project_id):
    """测试项目章节"""
    if not project_id:
        print("没有项目ID，跳过章节测试")
        return
    
    print(f"\n5. 测试项目章节 (项目ID: {project_id})...")
    
    try:
        response = requests.get(f"{BASE_URL}/bid-documents/projects/{project_id}/sections")
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
    except Exception as e:
        print(f"错误: {e}")

if __name__ == "__main__":
    print("开始测试投标文档API...")
    
    # 测试基本端点
    project_id = test_api_endpoints()
    
    # 测试文件上传
    test_file_upload(project_id)
    
    # 测试项目章节
    test_project_sections(project_id)
    
    print("\n测试完成！") 