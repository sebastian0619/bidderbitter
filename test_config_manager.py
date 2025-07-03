#!/usr/bin/env python3
"""
测试配置管理器和AI学习功能
"""

import requests
import json
import time
import os

# 配置
BASE_URL = "http://localhost:8000"

def test_config_manager():
    """测试配置管理器功能"""
    print("=== 测试配置管理器功能 ===")
    
    try:
        # 1. 测试获取业务领域
        print("1. 测试获取业务领域...")
        response = requests.get(f"{BASE_URL}/api/performances/config/business-fields")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 业务领域获取成功: {len(data.get('business_fields', []))} 个字段")
            for field in data.get('business_fields', [])[:3]:  # 显示前3个
                print(f"   - {field.get('name')}: {field.get('description')}")
        else:
            print(f"❌ 业务领域获取失败: {response.status_code}")
        
        # 2. 测试获取业绩类型
        print("\n2. 测试获取业绩类型...")
        response = requests.get(f"{BASE_URL}/api/performances/config/performance-types")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 业绩类型获取成功: {len(data.get('performance_types', []))} 个类型")
            for type_info in data.get('performance_types', [])[:3]:  # 显示前3个
                print(f"   - {type_info.get('name')}: {type_info.get('description')}")
        else:
            print(f"❌ 业绩类型获取失败: {response.status_code}")
        
        # 3. 测试重新加载配置
        print("\n3. 测试重新加载配置...")
        response = requests.post(f"{BASE_URL}/api/performances/config/reload")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 配置重新加载成功: {data.get('message')}")
        else:
            print(f"❌ 配置重新加载失败: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 配置管理器测试失败: {e}")

def test_ai_learning():
    """测试AI学习功能"""
    print("\n=== 测试AI学习功能 ===")
    
    try:
        # 1. 测试获取AI学习统计
        print("1. 测试获取AI学习统计...")
        response = requests.get(f"{BASE_URL}/api/performances/ai-learning/stats")
        if response.status_code == 200:
            data = response.json()
            stats = data.get('stats', {})
            print(f"✅ AI学习统计获取成功:")
            print(f"   - 总反馈数: {stats.get('total_feedback', 0)}")
            print(f"   - 总修正数: {stats.get('total_corrections', 0)}")
            print(f"   - 字段修正分布: {stats.get('field_corrections', {})}")
        else:
            print(f"❌ AI学习统计获取失败: {response.status_code}")
        
        # 2. 测试获取修正模式
        print("\n2. 测试获取修正模式...")
        response = requests.get(f"{BASE_URL}/api/performances/ai-learning/patterns")
        if response.status_code == 200:
            data = response.json()
            patterns = data.get('patterns', [])
            print(f"✅ 修正模式获取成功: {len(patterns)} 个模式")
            for pattern in patterns[:3]:  # 显示前3个
                print(f"   - {pattern.get('field')}: {pattern.get('original_value')} -> {pattern.get('corrected_value')}")
        else:
            print(f"❌ 修正模式获取失败: {response.status_code}")
            
    except Exception as e:
        print(f"❌ AI学习测试失败: {e}")

def test_performance_edit_with_learning():
    """测试业绩编辑和AI学习"""
    print("\n=== 测试业绩编辑和AI学习 ===")
    
    try:
        # 1. 获取业绩列表
        print("1. 获取业绩列表...")
        response = requests.get(f"{BASE_URL}/api/performances/list?page_size=1")
        if response.status_code != 200:
            print(f"❌ 获取业绩列表失败: {response.status_code}")
            return
        
        data = response.json()
        performances = data.get('performances', [])
        if not performances:
            print("❌ 没有找到业绩记录，无法测试编辑功能")
            return
        
        performance = performances[0]
        performance_id = performance['id']
        print(f"✅ 找到业绩记录: ID={performance_id}, 项目={performance['project_name']}")
        
        # 2. 测试带AI学习的验证
        print("\n2. 测试带AI学习的验证...")
        original_values = {
            "project_name": performance['project_name'],
            "client_name": performance['client_name'],
            "business_field": performance['business_field'],
            "project_type": performance['project_type']
        }
        
        corrected_values = {
            "project_name": f"{performance['project_name']}_修正版",
            "client_name": f"{performance['client_name']}_修正版",
            "business_field": "并购重组",  # 修改为不同的业务领域
            "project_type": "重大个案"  # 修改为不同的项目类型
        }
        
        learning_data = {
            "original_values": original_values,
            "corrected_values": corrected_values,
            "learning_notes": "测试AI学习功能：用户修正了项目名称、客户名称、业务领域和项目类型"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/performances/{performance_id}/verify-with-learning",
            json=learning_data
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ AI学习验证成功: {data.get('message')}")
            if data.get('learning_recorded'):
                print("   - AI学习数据已记录")
        else:
            print(f"❌ AI学习验证失败: {response.status_code} - {response.text}")
        
        # 3. 验证AI学习数据是否被记录
        print("\n3. 验证AI学习数据...")
        time.sleep(1)  # 等待数据写入
        
        response = requests.get(f"{BASE_URL}/api/performances/ai-learning/stats")
        if response.status_code == 200:
            data = response.json()
            stats = data.get('stats', {})
            print(f"✅ AI学习统计更新:")
            print(f"   - 总反馈数: {stats.get('total_feedback', 0)}")
            print(f"   - 总修正数: {stats.get('total_corrections', 0)}")
            print(f"   - 字段修正分布: {stats.get('field_corrections', {})}")
        else:
            print(f"❌ 获取AI学习统计失败: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 业绩编辑测试失败: {e}")

def test_config_file_operations():
    """测试配置文件操作"""
    print("\n=== 测试配置文件操作 ===")
    
    try:
        # 检查配置文件是否存在
        config_files = [
            "backend/config/business_fields.json",
            "backend/config/performance_types.json",
            "backend/config/ai_learning.json"
        ]
        
        for config_file in config_files:
            if os.path.exists(config_file):
                print(f"✅ 配置文件存在: {config_file}")
                # 读取并显示文件大小
                file_size = os.path.getsize(config_file)
                print(f"   - 文件大小: {file_size} 字节")
                
                # 尝试解析JSON
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    print(f"   - JSON格式正确")
                except json.JSONDecodeError as e:
                    print(f"   - JSON格式错误: {e}")
            else:
                print(f"❌ 配置文件不存在: {config_file}")
                
    except Exception as e:
        print(f"❌ 配置文件操作测试失败: {e}")

def main():
    """主函数"""
    print("🚀 开始测试配置管理器和AI学习功能")
    print("=" * 50)
    
    # 测试配置管理器
    test_config_manager()
    
    # 测试AI学习功能
    test_ai_learning()
    
    # 测试业绩编辑和AI学习
    test_performance_edit_with_learning()
    
    # 测试配置文件操作
    test_config_file_operations()
    
    print("\n" + "=" * 50)
    print("✅ 测试完成")

if __name__ == "__main__":
    main() 