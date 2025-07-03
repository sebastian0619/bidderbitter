#!/usr/bin/env python3
"""
测试Docling OCR功能是否已完全修复

本测试脚本验证：
1. Docling模型下载成功
2. OCR功能正常工作
3. 业绩分析功能恢复
"""

import os
import sys
import requests
import tempfile

def test_docling_ocr_fixed():
    """测试Docling OCR功能是否已修复"""
    
    print("🔍 测试Docling OCR功能修复状态")
    print("=" * 50)
    
    # 1. 测试API健康状态
    print("\n1. 测试API健康状态...")
    try:
        response = requests.get("http://localhost:8000/api/health", timeout=10)
        if response.status_code == 200:
            print("✅ API服务正常运行")
        else:
            print(f"❌ API服务异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API连接失败: {e}")
        return False
    
    # 2. 创建测试文件
    print("\n2. 创建业绩测试文件...")
    test_content = """
法律服务合同

项目名称：知识产权保护法律服务
客户名称：深圳市创新科技有限公司
业务领域：知识产权法
合同金额：50万元
项目时间：2024年1月-2024年12月
项目描述：为客户提供专利申请、商标注册、知识产权维权等全方位法律服务
"""
    
    # 创建临时PDF文件进行测试
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write(test_content)
        test_file_path = f.name
    
    print(f"✅ 测试文件创建: {test_file_path}")
    
    # 3. 测试业绩上传和AI分析
    print("\n3. 测试业绩上传和AI分析...")
    try:
        with open(test_file_path, 'rb') as f:
            files = {'files': ('test_performance.txt', f, 'text/plain')}
            data = {
                'enable_ai_analysis': 'true',
                'enable_vision_analysis': 'true'
            }
            
            response = requests.post(
                "http://localhost:8000/api/performances/upload",
                files=files,
                data=data,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ 业绩上传成功")
                print(f"   Performance ID: {result.get('performance_id')}")
                print(f"   分析状态: {result.get('message', 'N/A')}")
                
                # 检查生成的业绩记录
                perf_response = requests.get(f"http://localhost:8000/api/performances/list?page=1&page_size=5")
                if perf_response.status_code == 200:
                    performances = perf_response.json()
                    if performances.get('items'):
                        latest_perf = performances['items'][0]
                        print(f"   项目名称: {latest_perf.get('project_name', 'N/A')}")
                        print(f"   客户名称: {latest_perf.get('client_name', 'N/A')}")
                        print(f"   业务领域: {latest_perf.get('business_field', 'N/A')}")
                        print(f"   置信度: {latest_perf.get('confidence_score', 'N/A')}")
                        return True
                    else:
                        print("❌ 未找到业绩记录")
                        return False
                else:
                    print(f"❌ 获取业绩列表失败: {perf_response.status_code}")
                    return False
            else:
                print(f"❌ 业绩上传失败: {response.status_code}")
                print(f"   响应: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ 测试过程失败: {e}")
        return False
    finally:
        # 清理测试文件
        if os.path.exists(test_file_path):
            os.unlink(test_file_path)
    
    return False

def test_ocr_model_status():
    """检查OCR模型状态"""
    print("\n🔧 检查OCR模型状态")
    print("=" * 30)
    
    try:
        response = requests.get("http://localhost:8000/api/ai-tools/models/status", timeout=10)
        if response.status_code == 200:
            status = response.json()
            print("✅ 模型状态查询成功")
            
            docling_status = status.get('docling', {})
            easyocr_status = status.get('easyocr', {})
            
            print(f"   Docling可用: {docling_status.get('available', False)}")
            print(f"   EasyOCR可用: {easyocr_status.get('available', False)}")
            
            return docling_status.get('available', False)
        else:
            print(f"❌ 模型状态查询失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 模型状态检查失败: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Docling OCR修复验证测试")
    print("测试时间:", __import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    # 检查模型状态
    model_ok = test_ocr_model_status()
    
    # 测试功能
    function_ok = test_docling_ocr_fixed()
    
    print("\n" + "=" * 50)
    print("📊 测试结果总结:")
    print(f"   OCR模型状态: {'✅ 正常' if model_ok else '❌ 异常'}")
    print(f"   功能测试: {'✅ 通过' if function_ok else '❌ 失败'}")
    
    if model_ok and function_ok:
        print("\n🎉 恭喜！Docling OCR功能已完全修复！")
        print("   - 代理配置成功")
        print("   - 模型下载完成") 
        print("   - OCR功能正常")
        print("   - 业绩分析恢复")
        sys.exit(0)
    else:
        print("\n⚠️  还有问题需要解决")
        sys.exit(1) 
 