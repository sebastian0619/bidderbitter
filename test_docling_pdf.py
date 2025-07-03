#!/usr/bin/env python3
"""
测试优化后的DoclingService - 使用PDF格式
验证移除artifacts_path和使用model_storage_directory后是否正常工作
"""
import requests
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

def create_test_pdf():
    """创建一个包含中文的测试PDF文件"""
    buffer = io.BytesIO()
    
    # 创建PDF
    p = canvas.Canvas(buffer, pagesize=letter)
    
    # 添加中文字体支持（如果需要）
    try:
        # 尝试使用系统字体
        p.setFont("Helvetica", 14)
    except:
        p.setFont("Helvetica", 14)
    
    # 添加内容
    p.drawString(100, 750, "Legal Service Contract")
    p.drawString(100, 730, "法律服务合同")
    p.drawString(100, 700, "")
    p.drawString(100, 680, "Party A: Shenzhen Technology Innovation Co., Ltd.")
    p.drawString(100, 660, "甲方：深圳市科技创新有限公司")
    p.drawString(100, 640, "")
    p.drawString(100, 620, "Party B: XX Law Firm")
    p.drawString(100, 600, "乙方：XX律师事务所")
    p.drawString(100, 580, "")
    p.drawString(100, 560, "Project: Intellectual Property Legal Services")
    p.drawString(100, 540, "项目名称：企业知识产权保护法律服务")
    p.drawString(100, 520, "")
    p.drawString(100, 500, "Services: Patent application, trademark registration")
    p.drawString(100, 480, "服务内容：专利申请、商标注册、版权保护")
    p.drawString(100, 460, "")
    p.drawString(100, 440, "Amount: RMB 500,000")
    p.drawString(100, 420, "合同金额：人民币50万元")
    p.drawString(100, 400, "")
    p.drawString(100, 380, "Period: 2024-01-01 to 2024-12-31")
    p.drawString(100, 360, "服务期间：2024年1月1日至2024年12月31日")
    p.drawString(100, 340, "")
    p.drawString(100, 320, "Business Field: Intellectual Property Law")
    p.drawString(100, 300, "业务领域：知识产权法")
    
    p.save()
    buffer.seek(0)
    return buffer.getvalue()

def test_docling_with_pdf():
    """使用PDF测试DoclingService"""
    print("🚀 开始测试优化后的DoclingService架构（PDF格式）...")
    
    try:
        # 1. 创建测试PDF
        print("📄 创建测试PDF文件...")
        pdf_content = create_test_pdf()
        print(f"✅ PDF文件创建成功，大小: {len(pdf_content)} 字节")
        
        # 2. 测试业绩上传和AI分析
        print("\n🎯 测试业绩AI分析功能（PDF格式）...")
        
        files = {
            'files': ('test_contract.pdf', pdf_content, 'application/pdf')
        }
        data = {
            'enable_ai_analysis': 'true',
            'enable_vision_analysis': 'true'
        }
        
        print("📤 上传测试PDF文件...")
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
                    print(f"     * 分析失败原因: {analysis.get('error', 'N/A')}")
            else:
                print("   - 未包含AI分析结果")
                
        else:
            print(f"❌ 业绩上传失败: {response.status_code}")
            print(f"   错误信息: {response.text}")
            
        # 3. 检查DoclingService状态
        print("\n🔍 检查DoclingService状态...")
        response = requests.get("http://localhost:8000/api/ai-tools/tool-status")
        if response.status_code == 200:
            status = response.json()
            print(f"✅ 服务状态:")
            print(f"   - Docling可用: {status.get('docling_available', False)}")
            print(f"   - EasyOCR可用: {status.get('easyocr_available', False)}")
            print(f"   - 服务初始化: {status.get('initialized', False)}")
            
            config = status.get('config', {})
            print(f"   - OCR启用: {config.get('enable_ocr', False)}")
            print(f"   - 使用GPU: {config.get('use_gpu', False)}")
            print(f"   - OCR语言: {config.get('ocr_languages', [])}")
            print(f"   - EasyOCR模型路径: {config.get('easyocr_models_path', 'N/A')}")
            print(f"   - Docling模型管理: {config.get('docling_models', 'N/A')}")
        else:
            print(f"❌ 状态获取失败: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_docling_with_pdf()
    print("\n✅ 测试完成！") 