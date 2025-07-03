#!/usr/bin/env python3
"""
测试项目名称生成功能
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.performance_api import _extract_performance_info

def test_project_name_generation():
    """测试项目名称生成功能"""
    print("开始测试项目名称生成功能...")
    
    # 测试案例
    test_cases = [
        {
            "name": "诉讼仲裁案例",
            "ai_result": {
                "results": {
                    "text_extraction_result": {
                        "text": "甲方：华为技术有限公司\n委托事项：知识产权侵权纠纷\n案由：专利侵权纠纷\n签订时间：2023年5月\n律师费：50万元"
                    },
                    "final_classification": {
                        "business_field": "知识产权"
                    }
                }
            },
            "expected_type": "诉讼仲裁",
            "expected_pattern": "代表华为技术有限公司的.*纠纷"
        },
        {
            "name": "常年法律顾问案例",
            "ai_result": {
                "results": {
                    "text_extraction_result": {
                        "text": "甲方：腾讯科技（深圳）有限公司\n服务内容：常年法律顾问服务\n服务期限：2023年1月1日至2023年12月31日\n顾问费：100万元"
                    },
                    "final_classification": {
                        "business_field": "合规监管"
                    }
                }
            },
            "expected_type": "常年法律顾问",
            "expected_pattern": "腾讯科技（深圳）有限公司常年法律顾问.*2023年度.*"
        },
        {
            "name": "并购重组项目案例",
            "ai_result": {
                "results": {
                    "text_extraction_result": {
                        "text": "甲方：阿里巴巴集团控股有限公司\n项目名称：收购某电商平台项目\n服务内容：并购重组法律服务\n签订时间：2023年8月\n服务费：200万元"
                    },
                    "final_classification": {
                        "business_field": "并购重组"
                    }
                }
            },
            "expected_type": "重大个案(非诉)",
            "expected_pattern": "代表阿里巴巴集团控股有限公司的.*项目"
        },
        {
            "name": "IPO项目案例",
            "ai_result": {
                "results": {
                    "text_extraction_result": {
                        "text": "委托方：小米集团\nIPO上市法律服务协议\n服务内容：协助公司香港联交所主板上市\n签订日期：2024年3月\n律师费：500万元"
                    },
                    "final_classification": {
                        "business_field": "资本市场"
                    }
                }
            },
            "expected_type": "重大个案(非诉)",
            "expected_pattern": "代表小米集团的.*项目"
        },
        {
            "name": "破产重整案例",
            "ai_result": {
                "results": {
                    "text_extraction_result": {
                        "text": "委托人：伊朗第一大植物油生产商\n委托事项：代表债权人在重整案中申报债权\n案件性质：破产重整\n签订时间：2023年\n服务费：30万元"
                    },
                    "final_classification": {
                        "business_field": "破产重整"
                    }
                }
            },
            "expected_type": "重大个案(非诉)",
            "expected_pattern": "代表伊朗第一大植物油生产商的.*项目"
        }
    ]
    
    # 执行测试
    for i, case in enumerate(test_cases, 1):
        print(f"\n=== 测试案例 {i}: {case['name']} ===")
        
        try:
            # 调用项目信息提取函数
            result = _extract_performance_info(case['ai_result'])
            
            print(f"提取结果:")
            print(f"  项目名称: {result.get('project_name', '未提取到')}")
            print(f"  客户名称: {result.get('client_name', '未提取到')}")
            print(f"  项目类型: {result.get('project_type', '未提取到')}")
            print(f"  业务领域: {result.get('business_field', '未提取到')}")
            print(f"  项目描述: {result.get('description', '未提取到')}")
            print(f"  合同金额: {result.get('contract_amount', '未提取到')}")
            print(f"  年份: {result.get('year', '未提取到')}")
            
            # 验证项目类型
            if result.get('project_type') == case['expected_type']:
                print(f"  ✅ 项目类型正确: {case['expected_type']}")
            else:
                print(f"  ❌ 项目类型错误: 期望 {case['expected_type']}, 实际 {result.get('project_type')}")
            
            # 验证项目名称格式
            import re
            project_name = result.get('project_name', '')
            if project_name and re.search(case['expected_pattern'], project_name):
                print(f"  ✅ 项目名称格式正确")
            else:
                print(f"  ❌ 项目名称格式错误")
                print(f"     期望模式: {case['expected_pattern']}")
                print(f"     实际名称: {project_name}")
            
            # 验证必要字段
            required_fields = ['project_name', 'client_name', 'project_type', 'business_field']
            missing_fields = [field for field in required_fields if not result.get(field)]
            if not missing_fields:
                print(f"  ✅ 所有必要字段都已提取")
            else:
                print(f"  ⚠️ 缺少字段: {', '.join(missing_fields)}")
                
        except Exception as e:
            print(f"  ❌ 测试失败: {str(e)}")
    
    # 测试边界情况
    print(f"\n=== 测试边界情况 ===")
    
    # 空输入
    print("\n测试空输入:")
    result = _extract_performance_info(None)
    print(f"  结果: {result}")
    
    # 无文本内容
    print("\n测试无文本内容:")
    result = _extract_performance_info({"results": {}})
    print(f"  结果: {result}")
    
    # 文本内容不完整
    print("\n测试不完整文本:")
    incomplete_result = {
        "results": {
            "text_extraction_result": {
                "text": "某个合同片段，没有完整信息"
            }
        }
    }
    result = _extract_performance_info(incomplete_result)
    print(f"  结果: {result}")
    
    print("\n=== 测试完成 ===")
    print("如果所有项目都显示 ✅，则项目名称生成功能正常工作")

if __name__ == "__main__":
    test_project_name_generation() 