#!/usr/bin/env python3
"""
测试破产重整分类功能
验证"代表伊朗第一大植物油生产商在重整案中申报债权"文档是否能正确识别为破产重整
"""

import sys
import os
sys.path.append('backend')

from config_manager import ConfigManager
import asyncio
import aiohttp
import json

async def test_ai_classification():
    """测试AI分类功能"""
    print("=== 测试AI分类API ===")
    
    # 测试文本内容
    test_content = """
    RETAINER AGREEMENT

    Between:
    Behshahr Industrial Company (hereinafter Behshahr)

    And:
    Jingtian & Gongcheng Shanghai Office

    代表伊朗第一大植物油生产商在重整案中申报债权

    This agreement is for legal services related to bankruptcy restructuring 
    and debt claim filing for the largest vegetable oil producer in Iran.
    
    重整案、债权申报、破产重整、债务重组
    """
    
    # 使用新的文档分类API
    request_data = {
        "content": test_content,
        "classification_type": "both"
    }
    
    try:
        # 调用文档分类API
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://localhost:8000/api/ai-tools/classify-document",
                json=request_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print("✅ 文档分类API调用成功")
                    
                    # 解析结果
                    if result.get("success"):
                        results = result.get("results", {})
                        
                        # 检查文档类型分类
                        doc_type = results.get("document_type", {})
                        if doc_type:
                            print(f"  - 文档类型: {doc_type.get('name', 'unknown')} (方法: {doc_type.get('method', 'unknown')})")
                            print(f"    置信度: {doc_type.get('confidence', 0.0)}")
                            print(f"    理由: {doc_type.get('reason', 'N/A')}")
                        
                        # 检查业务领域分类
                        business_field = results.get("business_field", {})
                        if business_field:
                            field_name = business_field.get("name", "未识别")
                            method = business_field.get("method", "unknown")
                            confidence = business_field.get("confidence", 0.0)
                            reason = business_field.get("reason", "N/A")
                            keywords = business_field.get("keywords_found", [])
                            
                            print(f"  - 业务领域: {field_name} (方法: {method})")
                            print(f"    置信度: {confidence}")
                            print(f"    理由: {reason}")
                            if keywords:
                                print(f"    找到关键词: {keywords}")
                            
                            # 检查是否正确识别为破产重整
                            if "破产重整" in field_name or "bankruptcy" in field_name.lower():
                                print("  ✅ 正确识别为破产重整相关业务")
                                return True
                            else:
                                print(f"  ❌ 未正确识别破产重整，当前识别为: {field_name}")
                                return False
                        else:
                            print("  ❌ 未返回业务领域分类结果")
                            return False
                    else:
                        print(f"  ❌ API调用失败: {result.get('error', 'Unknown error')}")
                        return False
                else:
                    error_text = await response.text()
                    print(f"  ❌ API调用失败: {response.status} - {error_text}")
                    return False
                    
    except Exception as e:
        print(f"  ❌ 请求异常: {e}")
        return False

def test_config_classification():
    """测试配置分类功能"""
    print("\n=== 测试配置分类功能 ===")
    
    config_manager = ConfigManager("backend/config")
    
    test_content = "代表伊朗第一大植物油生产商在重整案中申报债权"
    
    # 测试业务领域关键词分类
    business_result = config_manager.classify_business_field_by_keywords(test_content)
    if business_result:
        code, name, score = business_result
        print(f"  业务领域分类: {name} (代码: {code}, 置信度: {score:.2f})")
        if "破产重整" in name:
            print("  ✅ 配置分类正确识别为破产重整")
        else:
            print(f"  ❌ 配置分类未正确识别，当前为: {name}")
    else:
        print("  ❌ 配置分类无匹配结果")
    
    # 测试文档类型分类
    doc_result = config_manager.classify_document_type_by_keywords(test_content)
    if doc_result:
        code, name, score = doc_result
        print(f"  文档类型分类: {name} (代码: {code}, 置信度: {score:.2f})")
    else:
        print("  文档类型分类: 无匹配结果")

def test_prompt_building():
    """测试prompt构建"""
    print("\n=== 测试Prompt构建 ===")
    
    config_manager = ConfigManager("backend/config")
    
    test_content = "代表伊朗第一大植物油生产商在重整案中申报债权"
    
    # 测试业务领域分类prompt
    system_prompt, user_prompt = config_manager.build_prompt(
        "business_field_classification",
        content=test_content
    )
    
    if system_prompt and user_prompt:
        print("✅ 业务领域分类prompt构建成功")
        
        # 检查prompt中是否包含破产重整相关信息
        if "破产重整" in user_prompt and "债务重组" in user_prompt:
            print("  ✅ Prompt包含破产重整相关指导信息")
        else:
            print("  ❌ Prompt缺少破产重整相关指导信息")
            
        # 显示prompt片段
        print(f"  系统提示: {system_prompt[:100]}...")
        if "破产重整" in user_prompt:
            # 找到破产重整相关的部分
            lines = user_prompt.split('\n')
            for line in lines:
                if "破产重整" in line:
                    print(f"  关键指导: {line.strip()}")
                    break
    else:
        print("❌ 业务领域分类prompt构建失败")

async def main():
    """主测试函数"""
    print("开始测试破产重整分类功能...")
    print("测试文档: '代表伊朗第一大植物油生产商在重整案中申报债权'")
    print("期望结果: 业务领域应识别为'破产重整'\n")
    
    # 测试配置分类
    test_config_classification()
    
    # 测试prompt构建
    test_prompt_building()
    
    # 测试AI API分析
    await test_ai_classification()
    
    print("\n=== 测试总结 ===")
    print("如果所有项目都显示 ✅，则破产重整分类功能正常工作")
    print("特别关注业务领域是否正确识别为'破产重整'")

if __name__ == "__main__":
    asyncio.run(main()) 