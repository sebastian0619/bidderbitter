#!/usr/bin/env python3
"""
测试AI文本分析功能
"""

import asyncio
import sys
import os

# 添加backend目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

async def test_ai_text_analysis():
    """测试AI文本分析功能"""
    try:
        from ai_service import ai_service
        
        print("🔍 测试AI文本分析功能")
        print(f"AI服务启用状态: {ai_service.enable_ai}")
        print(f"AI API Key: {bool(ai_service.ai_api_key)}")
        print(f"AI Base URL: {ai_service.ai_base_url}")
        
        # 测试文本内容（模拟法律文档）
        test_text = """法律服务委托协议

委托人：河南大京江房地产开发有限公司管理人
受托人：竞天公诚律师事务所

委托事项：
关于河南大京江房地产开发有限公司重整项目的法律服务

具体委托内容：
1. 参与重整计划的制定和修改
2. 协助与债权人进行谈判
3. 处理重整过程中的法律事务
4. 代表管理人参与相关诉讼和仲裁程序

案件类型：破产重整案件
纠纷性质：非诉讼业务
业务领域：破产重整

服务期限：2023年1月至2024年12月
服务费用：人民币50万元"""
        
        print(f"\n📄 测试文本长度: {len(test_text)} 字符")
        print(f"测试文本预览: {test_text[:200]}...")
        
        # 构建AI分析提示
        text_analysis_prompt = f"""请分析以下法律文档内容，提取关键信息：

文档内容：
{test_text}

请提取以下信息并以JSON格式回复：
{{
    "category": "文档类型(lawyer_certificate/performance_contract/award_certificate/other)",
    "confidence": 0.0-1.0,
    "key_entities": {{
        "client_name": "委托人/客户名称",
        "law_firm": "律师事务所",
        "project_name": "项目名称",
        "case_type": "案件类型",
        "dispute_type": "纠纷类型(诉讼/非诉讼)",
        "business_field": "业务领域",
        "amount": "金额",
        "date": "相关日期"
    }},
    "description": "文档描述",
    "business_field": "业务领域"
}}"""
        
        print("\n🤖 开始AI文本分析...")
        ai_result = await ai_service.analyze_text(text_analysis_prompt)
        
        print(f"AI分析结果: {ai_result.get('success')}")
        if ai_result.get('success'):
            print(f"AI返回内容: {ai_result.get('result', '')[:500]}...")
            
            # 尝试解析JSON
            try:
                import json
                parsed_result = json.loads(ai_result.get('result', '{}'))
                print(f"解析后的JSON: {parsed_result}")
            except Exception as e:
                print(f"JSON解析失败: {e}")
        else:
            print(f"AI分析失败: {ai_result.get('error', '未知错误')}")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_ai_text_analysis()) 