#!/usr/bin/env python3
"""
测试AI分析功能修复
"""
import asyncio
import json
import sys
import os

# 添加backend目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

async def test_ai_analysis():
    """测试AI分析功能"""
    try:
        from ai_service import ai_service
        from config_manager import ConfigManager
        
        print("🔍 测试AI分析功能...")
        
        # 测试配置管理器
        config_manager = ConfigManager()
        print("✅ ConfigManager初始化成功")
        
        # 测试AI分析配置加载
        ai_config = config_manager.get_ai_analysis_config()
        print(f"✅ AI分析配置加载成功，版本: {ai_config.get('version', 'unknown')}")
        
        # 测试prompt模板构建
        test_prompt = config_manager.build_prompt("performance_analysis", {
            "text_content": "甲方：河南大京江房地产开发有限公司管理人\n乙方：竞天公诚律师事务所\n关于河南大京江房地产开发有限公司重整项目之法律服务委托协议"
        })
        print(f"✅ Prompt模板构建成功，长度: {len(test_prompt)} 字符")
        
        # 测试AI服务状态
        print(f"✅ AI服务状态: 启用={ai_service.enable_ai}, 提供商={ai_service.ai_provider}")
        
        # 测试AI文本分析
        if ai_service.enable_ai:
            print("🤖 测试AI文本分析...")
            result = await ai_service.analyze_text("请简单回复'测试成功'")
            if result.get("success"):
                print("✅ AI文本分析成功")
                print(f"   结果: {result.get('result', '')}")
            else:
                print(f"❌ AI文本分析失败: {result.get('error', '未知错误')}")
        else:
            print("⚠️  AI服务未启用，跳过AI测试")
        
        print("\n🎉 所有测试完成！")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_ai_analysis())
    sys.exit(0 if success else 1) 