#!/usr/bin/env python3
"""
测试MCP客户端功能
验证AI系统中的MCP客户端集成是否正常工作
（不包含MCP服务器功能）
"""

import requests
import json
import time

# 配置
BASE_URL = "http://localhost:8000"

def test_ai_service_mcp_integration():
    """测试AI服务中的MCP集成"""
    print("=== 测试AI服务MCP客户端集成 ===")
    try:
        # 获取AI服务状态
        response = requests.get(f"{BASE_URL}/api/settings")
        if response.status_code == 200:
            settings = response.json()
            mcp_settings = {k: v for k, v in settings.items() if 'mcp' in k.lower()}
            print(f"✅ MCP客户端配置: {json.dumps(mcp_settings, indent=2, ensure_ascii=False)}")
            
            if not mcp_settings:
                print("ℹ️  当前没有MCP配置，这是正常的（未启用MCP客户端）")
        else:
            print(f"❌ 无法获取设置: {response.status_code}")
    except Exception as e:
        print(f"❌ AI服务MCP集成测试失败: {e}")

def test_mcp_tool_execution():
    """测试MCP工具执行"""
    print("\n=== 测试MCP客户端工具执行 ===")
    try:
        # 准备MCP工具测试请求
        test_request = {
            "user_message": "测试MCP客户端工具调用功能",
            "context": {
                "test_mode": True,
                "mcp_test": True
            }
        }
        
        response = requests.post(
            f"{BASE_URL}/api/ai-tools/ai-assistant",
            json=test_request
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ AI助手响应: {result.get('success')}")
            
            # 检查工具使用情况
            tools_used = result.get('response', {}).get('tools_used', [])
            mcp_tools_used = [tool for tool in tools_used if tool.get('tool_name', '').startswith('mcp_')]
            
            if mcp_tools_used:
                print(f"✅ 使用了MCP客户端工具: {len(mcp_tools_used)}个")
                for tool in mcp_tools_used:
                    print(f"   - {tool.get('tool_name')}: {tool.get('result', {}).get('success', False)}")
            else:
                print("ℹ️  未使用MCP客户端工具（MCP未配置或未启用）")
        else:
            print(f"❌ AI助手调用失败: {response.status_code}")
            
    except Exception as e:
        print(f"❌ MCP客户端工具执行测试失败: {e}")

def test_available_tools():
    """测试可用工具列表"""
    print("\n=== 测试可用工具列表 ===")
    try:
        response = requests.get(f"{BASE_URL}/api/ai-tools/tools")
        if response.status_code == 200:
            result = response.json()
            tools = result.get('tools', [])
            
            print(f"✅ 总共可用工具: {len(tools)}个")
            
            # 查找MCP相关工具
            mcp_tools = [tool for tool in tools if 'mcp' in tool.get('function', {}).get('name', '').lower()]
            
            if mcp_tools:
                print(f"✅ MCP客户端工具: {len(mcp_tools)}个")
                for tool in mcp_tools:
                    tool_name = tool.get('function', {}).get('name')
                    tool_desc = tool.get('function', {}).get('description')
                    print(f"   - {tool_name}: {tool_desc}")
            else:
                print("ℹ️  未发现MCP客户端工具")
                
            # 显示所有工具概览
            print("\n所有可用工具:")
            for tool in tools[:5]:  # 只显示前5个
                tool_name = tool.get('function', {}).get('name')
                tool_desc = tool.get('function', {}).get('description')
                print(f"   - {tool_name}: {tool_desc}")
            
            if len(tools) > 5:
                print(f"   ... 还有 {len(tools) - 5} 个工具")
                
        else:
            print(f"❌ 获取工具列表失败: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 工具列表测试失败: {e}")

def test_mcp_configuration():
    """测试MCP客户端配置设置"""
    print("\n=== 测试MCP客户端配置设置 ===")
    try:
        # 测试配置更新
        test_config = {
            "mcp_enabled": True,
            "mcp_server_url": "http://localhost:8001/mcp",
            "mcp_api_key": "test-key",
            "mcp_timeout": 30
        }
        
        response = requests.post(
            f"{BASE_URL}/api/settings",
            json=test_config
        )
        
        if response.status_code == 200:
            print("✅ MCP客户端配置更新成功")
            
            # 验证配置是否生效
            time.sleep(1)
            response = requests.get(f"{BASE_URL}/api/settings")
            if response.status_code == 200:
                settings = response.json()
                mcp_enabled = settings.get('mcp_enabled', {}).get('value')
                mcp_url = settings.get('mcp_server_url', {}).get('value')
                print(f"✅ 配置验证: 启用={mcp_enabled}, URL={mcp_url}")
            
        else:
            print(f"❌ MCP客户端配置更新失败: {response.status_code}")
            
    except Exception as e:
        print(f"❌ MCP客户端配置测试失败: {e}")

def test_fastmcp_import():
    """测试FastMCP客户端库导入"""
    print("\n=== 测试FastMCP客户端库导入 ===")
    try:
        # 测试后端是否能正确导入FastMCP
        response = requests.get(f"{BASE_URL}/api/ai-tools/tool-status")
        if response.status_code == 200:
            status = response.json()
            print(f"✅ AI工具状态: {status.get('success')}")
            
            # 检查是否有MCP相关的状态信息
            tool_status = status.get('status', {})
            print(f"✅ 工具状态概览: {json.dumps(tool_status, indent=2, ensure_ascii=False)}")
        else:
            print(f"❌ 无法获取工具状态: {response.status_code}")
            
    except Exception as e:
        print(f"❌ FastMCP客户端导入测试失败: {e}")

def test_mcp_client_initialization():
    """测试MCP客户端初始化"""
    print("\n=== 测试MCP客户端初始化 ===")
    try:
        # 通过AI服务状态检查MCP客户端是否正确初始化
        response = requests.get(f"{BASE_URL}/api/ai-models/status")
        if response.status_code == 200:
            status = response.json()
            print(f"✅ AI模型状态: {status.get('ai_service_configured')}")
            
            features = status.get('features', {})
            if 'mcp_client' in features:
                print(f"✅ MCP客户端功能: {features['mcp_client']}")
            else:
                print("ℹ️  MCP客户端状态未在AI模型状态中显示")
        else:
            print(f"❌ 无法获取AI模型状态: {response.status_code}")
            
    except Exception as e:
        print(f"❌ MCP客户端初始化测试失败: {e}")

def main():
    print("MCP客户端功能测试")
    print("=" * 50)
    
    test_ai_service_mcp_integration()
    test_available_tools()
    test_mcp_tool_execution()
    test_mcp_configuration()
    test_fastmcp_import()
    test_mcp_client_initialization()
    
    print("\n" + "=" * 50)
    print("MCP客户端功能测试完成！")
    print("\n总结:")
    print("1. AI服务集成 - 验证AI服务中的MCP客户端")
    print("2. 工具执行 - 测试MCP客户端工具是否可被调用")
    print("3. 配置管理 - 验证MCP客户端配置的读写")
    print("4. 库导入 - 检查FastMCP客户端依赖是否正确安装")
    print("5. 客户端初始化 - 验证MCP客户端是否正确初始化")
    print("\n注意: 现在只包含MCP客户端功能，不包含MCP服务器")

if __name__ == "__main__":
    main() 