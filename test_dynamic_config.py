#!/usr/bin/env python3
"""
测试动态配置功能
验证AI分析配置的动态加载和prompt构建
"""

import sys
import os
sys.path.append('backend')

from config_manager import ConfigManager
import json

def test_config_manager():
    """测试配置管理器"""
    print("=== 测试配置管理器 ===")
    
    config_manager = ConfigManager("backend/config")
    
    # 测试文档类型配置
    print("\n1. 文档类型配置:")
    doc_types = config_manager.get_document_types()
    for code, info in doc_types.items():
        print(f"  - {code}: {info.get('name')} (关键词: {len(info.get('keywords', []))}个)")
    
    # 测试业务领域配置
    print("\n2. 业务领域配置:")
    business_fields = config_manager.get_business_field_classifications()
    for code, info in business_fields.items():
        print(f"  - {code}: {info.get('name')} (关键词: {len(info.get('keywords', []))}个)")
    
    # 测试prompt模板
    print("\n3. Prompt模板:")
    prompt_types = ["document_classification", "business_field_classification", "performance_analysis"]
    for prompt_type in prompt_types:
        template = config_manager.get_prompt_template(prompt_type)
        if template:
            print(f"  - {prompt_type}: ✅ 已配置")
        else:
            print(f"  - {prompt_type}: ❌ 未配置")
    
    return config_manager

def test_prompt_building(config_manager):
    """测试prompt构建"""
    print("\n=== 测试Prompt构建 ===")
    
    test_content = """
    RETAINER AGREEMENT
    
    Between:
    Behshahr Industrial Company (hereinafter Behshahr)
    
    And:
    Jingtian & Gongcheng Shanghai Office
    
    代表伊朗第一大植物油生产商在重整案中申报债权
    """
    
    # 测试文档分类prompt
    print("\n1. 文档分类Prompt:")
    system_prompt, user_prompt = config_manager.build_prompt(
        "document_classification",
        content=test_content
    )
    
    if system_prompt and user_prompt:
        print(f"  系统提示: {system_prompt[:100]}...")
        print(f"  用户提示长度: {len(user_prompt)} 字符")
        print("  ✅ 文档分类prompt构建成功")
    else:
        print("  ❌ 文档分类prompt构建失败")
    
    # 测试业务领域分类prompt
    print("\n2. 业务领域分类Prompt:")
    system_prompt, user_prompt = config_manager.build_prompt(
        "business_field_classification",
        content=test_content
    )
    
    if system_prompt and user_prompt:
        print(f"  系统提示: {system_prompt[:100]}...")
        print(f"  用户提示长度: {len(user_prompt)} 字符")
        print("  ✅ 业务领域分类prompt构建成功")
    else:
        print("  ❌ 业务领域分类prompt构建失败")

def test_keyword_classification(config_manager):
    """测试关键词分类"""
    print("\n=== 测试关键词分类 ===")
    
    # 测试业务领域分类
    print("\n1. 业务领域分类:")
    business_test_cases = [
        ("代表伊朗第一大植物油生产商在重整案中申报债权", "破产重整"),
        ("企业并购重组法律服务合同", "并购重组"),
        ("IPO上市法律服务协议", "资本市场"),
    ]
    
    for text, expected in business_test_cases:
        result = config_manager.classify_business_field_by_keywords(text)
        if result:
            code, name, score = result
            print(f"  文本: {text[:30]}...")
            print(f"    分类: {name} (预期: {expected})")
            print(f"    置信度: {score:.2f}")
            print(f"    匹配: {'✅' if expected in name else '❌'}")
        else:
            print(f"  文本: {text[:30]}...")
            print(f"    分类: 无匹配 (预期: {expected})")
            print(f"    匹配: ❌")
        print()
    
    # 测试文档类型分类
    print("2. 文档类型分类:")
    doc_type_test_cases = [
        ("律师执业证书", "律师证"),
        ("律师事务所执业许可证", "资质证照"),
        ("法律服务合同协议", "业绩案例"),
        ("获奖证书表彰", "获奖证书")
    ]
    
    for text, expected in doc_type_test_cases:
        result = config_manager.classify_document_type_by_keywords(text)
        if result:
            code, name, score = result
            print(f"  文本: {text[:30]}...")
            print(f"    分类: {name} (预期: {expected})")
            print(f"    置信度: {score:.2f}")
            print(f"    匹配: {'✅' if expected in name else '❌'}")
        else:
            print(f"  文本: {text[:30]}...")
            print(f"    分类: 无匹配 (预期: {expected})")
            print(f"    匹配: ❌")
        print()

def test_ai_analysis_config():
    """测试AI分析配置文件"""
    print("\n=== 测试AI分析配置文件 ===")
    
    config_file = "backend/config/ai_analysis_config.json"
    
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            print("✅ AI分析配置文件加载成功")
            
            # 检查必要的配置项
            required_sections = [
                "document_classification",
                "business_fields", 
                "prompts",
                "analysis_settings"
            ]
            
            for section in required_sections:
                if section in config:
                    print(f"  ✅ {section}: 已配置")
                else:
                    print(f"  ❌ {section}: 缺失")
            
            # 检查破产重整配置
            business_fields = config.get("business_fields", {})
            if "bankruptcy_restructuring" in business_fields:
                bankruptcy_config = business_fields["bankruptcy_restructuring"]
                print(f"  ✅ 破产重整配置: {bankruptcy_config.get('name')}")
                print(f"    关键词: {bankruptcy_config.get('keywords', [])}")
            else:
                print("  ❌ 破产重整配置缺失")
                
        except Exception as e:
            print(f"❌ AI分析配置文件解析失败: {e}")
    else:
        print(f"❌ AI分析配置文件不存在: {config_file}")

def main():
    """主测试函数"""
    print("开始测试动态配置功能...")
    
    # 测试配置文件
    test_ai_analysis_config()
    
    # 测试配置管理器
    config_manager = test_config_manager()
    
    # 测试prompt构建
    test_prompt_building(config_manager)
    
    # 测试关键词分类
    test_keyword_classification(config_manager)
    
    print("\n=== 测试完成 ===")
    print("动态配置功能测试结果:")
    print("- 配置文件加载: 检查上述输出")
    print("- Prompt构建: 检查上述输出")
    print("- 关键词分类: 检查上述输出")
    print("\n如果所有项目都显示 ✅，则动态配置功能正常工作")

if __name__ == "__main__":
    main() 