#!/usr/bin/env python3
"""
测试优化后的DoclingService
验证移除artifacts_path后是否工作正常
"""
import requests
import json

def test_docling_service():
    """测试DoclingService状态和功能"""
    print("🔍 测试优化后的DoclingService...")
    
    try:
        # 1. 测试服务状态
        print("\n1. 检查DoclingService状态...")
        response = requests.get("http://localhost:8000/api/ai-tools/tool-status")
        if response.status_code == 200:
            status = response.json()
            print(f"✅ AI工具状态获取成功")
            print(f"   - Docling可用: {status.get('docling_available', False)}")
            print(f"   - EasyOCR可用: {status.get('easyocr_available', False)}")
            print(f"   - 服务初始化: {status.get('initialized', False)}")
            
            # 检查配置
            config = status.get('config', {})
            print(f"   - OCR启用: {config.get('enable_ocr', False)}")
            print(f"   - 使用GPU: {config.get('use_gpu', False)}")
            print(f"   - OCR语言: {config.get('ocr_languages', [])}")
            print(f"   - EasyOCR模型路径: {config.get('easyocr_models_path', 'N/A')}")
            print(f"   - Docling模型管理: {config.get('docling_models', 'N/A')}")
        else:
            print(f"❌ 状态获取失败: {response.status_code}")
            
        # 2. 检查可用工具
        print("\n2. 检查可用工具...")
        response = requests.get("http://localhost:8000/api/ai-tools/tools")
        if response.status_code == 200:
            tools = response.json()
            print(f"✅ 可用工具获取成功，共 {len(tools)} 个工具")
            for tool_name in tools.keys():
                print(f"   - {tool_name}")
        else:
            print(f"❌ 工具列表获取失败: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")

def test_performance_upload():
    """测试业绩上传和AI分析功能"""
    print("\n🎯 测试业绩AI分析功能...")
    
    try:
        # 创建测试PDF文件内容
        test_content = """
        法律服务合同
        
        甲方：深圳市科技创新有限公司
        乙方：XX律师事务所
        
        项目名称：企业知识产权保护法律服务
        服务内容：专利申请、商标注册、版权保护
        合同金额：人民币50万元
        服务期间：2024年1月1日至2024年12月31日
        
        业务领域：知识产权法
        """
        
        # 创建表单数据
        files = {
            'files': ('test_contract.txt', test_content, 'text/plain')
        }
        data = {
            'enable_ai_analysis': 'true',
            'enable_vision_analysis': 'true'
        }
        
        print("📤 上传测试业绩文件...")
        response = requests.post(
            "http://localhost:8000/api/performances/upload",
            files=files,
            data=data
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 业绩上传成功")
            print(f"   - 业绩ID: {result.get('performance_id')}")
            print(f"   - 文件ID: {result.get('file_id')}")
            
            # 检查AI分析结果
            if 'ai_analysis' in result:
                analysis = result['ai_analysis']
                print(f"   - AI分析成功: {analysis.get('success', False)}")
                if analysis.get('success'):
                    extracted = analysis.get('extracted_info', {})
                    print(f"     * 项目名称: {extracted.get('project_name', 'N/A')}")
                    print(f"     * 客户名称: {extracted.get('client_name', 'N/A')}")
                    print(f"     * 业务领域: {extracted.get('business_field', 'N/A')}")
                    print(f"     * 置信度: {analysis.get('confidence_score', 0)}")
        else:
            print(f"❌ 业绩上传失败: {response.status_code}")
            print(f"   错误信息: {response.text}")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    print("🚀 开始测试优化后的DoclingService架构...")
    test_docling_service()
    test_performance_upload()
    print("\n✅ 测试完成！") 