#!/usr/bin/env python3
"""
测试业绩项目类型和业务领域分类
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.config_manager import ConfigManager

def test_performance_configurations():
    """测试业绩相关配置"""
    print("开始测试业绩配置功能...")
    
    config_manager = ConfigManager()
    
    # 测试项目类型配置
    print("\n=== 测试项目类型配置 ===")
    performance_types = config_manager.get_performance_types()
    print(f"共加载 {len(performance_types)} 种项目类型:")
    
    for i, ptype in enumerate(performance_types, 1):
        print(f"  {i}. {ptype['name']} (代码: {ptype['code']})")
        print(f"     关键词: {', '.join(ptype.get('keywords', []))}")
    
    # 测试业务领域配置
    print("\n=== 测试业务领域配置 ===")
    business_fields = config_manager.get_business_fields()
    print(f"共加载 {len(business_fields)} 种业务领域:")
    
    for i, field in enumerate(business_fields, 1):
        print(f"  {i}. {field['name']} (代码: {field['code']})")
        print(f"     关键词: {', '.join(field.get('keywords', []))}")
    
    # 测试特定分类案例
    print("\n=== 测试分类案例 ===")
    
    test_cases = [
        {
            "text": "代表伊朗第一大植物油生产商在重整案中申报债权",
            "expected_business": "破产重整",
            "expected_project": "重大个案(非诉)"
        },
        {
            "text": "企业并购重组法律服务合同",
            "expected_business": "并购重组", 
            "expected_project": "重大个案(非诉)"
        },
        {
            "text": "公司IPO上市法律顾问服务协议",
            "expected_business": "资本市场",
            "expected_project": "重大个案(非诉)"
        },
        {
            "text": "某公司常年法律顾问合同",
            "expected_business": "合规监管",
            "expected_project": "常年法律顾问"
        },
        {
            "text": "商标侵权诉讼代理协议",
            "expected_business": "知识产权",
            "expected_project": "诉讼仲裁"
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n案例 {i}: {case['text']}")
        
        # 测试业务领域分类
        business_result = config_manager.classify_business_field_by_keywords(case['text'])
        if business_result:
            print(f"  ✅ 业务领域: {business_result['name']} (置信度: {business_result['confidence']:.2f})")
            print(f"     预期: {case['expected_business']}")
            if business_result['name'] == case['expected_business']:
                print("     ✅ 匹配正确")
            else:
                print("     ⚠️ 匹配不符")
        else:
            print("  ❌ 业务领域: 无匹配结果")
        
        # 测试项目类型分类
        project_result = config_manager.classify_document_type_by_keywords(case['text'])
        if project_result:
            print(f"  ✅ 项目类型: {project_result['name']} (置信度: {project_result['confidence']:.2f})")
        else:
            print("  ❌ 项目类型: 无匹配结果")
    
    # 验证三大项目类型结构
    print("\n=== 验证三大项目类型结构 ===")
    expected_types = ["常年法律顾问", "重大个案(非诉)", "诉讼仲裁"]
    actual_types = [ptype['name'] for ptype in performance_types]
    
    print(f"预期项目类型: {expected_types}")
    print(f"实际项目类型: {actual_types}")
    
    if set(expected_types) == set(actual_types):
        print("✅ 项目类型结构正确")
    else:
        print("❌ 项目类型结构不符")
        missing = set(expected_types) - set(actual_types)
        extra = set(actual_types) - set(expected_types)
        if missing:
            print(f"   缺少: {list(missing)}")
        if extra:
            print(f"   多余: {list(extra)}")
    
    # 验证关键业务领域
    print("\n=== 验证关键业务领域 ===")
    key_fields = ["破产重整", "并购重组", "资本市场", "知识产权", "争议解决"]
    available_fields = [field['name'] for field in business_fields]
    
    for field in key_fields:
        if field in available_fields:
            print(f"  ✅ {field}: 已配置")
        else:
            print(f"  ❌ {field}: 未配置")
    
    print("\n=== 测试完成 ===")
    print("如果所有项目都显示 ✅，则配置正确")

if __name__ == "__main__":
    test_performance_configurations() 