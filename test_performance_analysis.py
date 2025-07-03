#!/usr/bin/env python3
"""
测试AI分析业绩功能
"""

import requests
import json
import time
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

def create_test_contract_pdf():
    """创建一个测试的法律服务合同PDF"""
    filename = "test_legal_contract.pdf"
    
    # 创建PDF文档
    doc = SimpleDocTemplate(filename, pagesize=letter)
    story = []
    
    # 获取样式
    styles = getSampleStyleSheet()
    
    # 创建标题样式
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    # 创建正文样式
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=12,
        spaceAfter=12,
        alignment=TA_LEFT,
        fontName='Helvetica'
    )
    
    # 添加内容
    story.append(Paragraph("法律服务委托合同", title_style))
    story.append(Spacer(1, 20))
    
    story.append(Paragraph("合同编号：LS-2024-001", body_style))
    story.append(Paragraph("委托方：上海科技创新有限公司", body_style))
    story.append(Paragraph("受托方：某某律师事务所", body_style))
    story.append(Spacer(1, 20))
    
    story.append(Paragraph("一、项目概述", title_style))
    story.append(Paragraph("项目名称：企业并购重组法律服务", body_style))
    story.append(Paragraph("项目类型：企业并购", body_style))
    story.append(Paragraph("业务领域：公司法律事务", body_style))
    story.append(Paragraph("合同金额：人民币 800,000 元整", body_style))
    story.append(Paragraph("签约时间：2024年3月15日", body_style))
    story.append(Paragraph("项目期间：2024年3月15日至2024年9月15日", body_style))
    story.append(Spacer(1, 20))
    
    story.append(Paragraph("二、服务内容", title_style))
    story.append(Paragraph("1. 尽职调查：对目标公司进行全面的法律尽职调查", body_style))
    story.append(Paragraph("2. 合规审查：审查交易结构的合规性", body_style))
    story.append(Paragraph("3. 文件起草：起草并购协议、股权转让协议等法律文件", body_style))
    story.append(Paragraph("4. 交易执行：协助完成并购交易的法律程序", body_style))
    story.append(Paragraph("5. 风险防控：识别并防控交易中的法律风险", body_style))
    story.append(Spacer(1, 20))
    
    story.append(Paragraph("三、项目成果", title_style))
    story.append(Paragraph("本项目成功协助委托方完成对目标企业60%股权的收购，涉及资产规模约2.5亿元人民币。", body_style))
    story.append(Paragraph("项目执行期间，律师团队共完成法律文件60余份，组织法律会议15次。", body_style))
    story.append(Paragraph("交易于2024年8月30日顺利完成，较预期提前半个月。", body_style))
    story.append(Spacer(1, 20))
    
    story.append(Paragraph("四、特殊条款", title_style))
    story.append(Paragraph("本项目涉及跨境并购，需要协调中美两国的法律法规。", body_style))
    story.append(Paragraph("项目团队包括公司法、证券法、税法等多个专业领域的律师。", body_style))
    story.append(Paragraph("客户对服务质量表示高度满意，并签署了后续合作意向。", body_style))
    
    # 生成PDF
    doc.build(story)
    print(f"测试PDF已创建: {filename}")
    return filename

def test_ai_performance_analysis():
    """测试AI分析业绩功能"""
    print("🧪 开始测试AI分析业绩功能...")
    
    # 检查后端是否可访问
    try:
        response = requests.get("http://localhost:8000/api/health")
        if response.status_code == 200:
            print("✅ 后端服务正常")
        else:
            print("❌ 后端服务异常")
            return False
    except Exception as e:
        print(f"❌ 无法连接到后端: {e}")
        return False
    
    # 创建测试PDF
    pdf_filename = create_test_contract_pdf()
    
    if not os.path.exists(pdf_filename):
        print("❌ 测试PDF创建失败")
        return False
    
    # 上传文件并触发AI分析
    print("📤 上传业绩文件并触发AI分析...")
    
    url = "http://localhost:8000/api/performances/upload"
    
    with open(pdf_filename, 'rb') as f:
        files = {'file': (pdf_filename, f, 'application/pdf')}
        data = {
            'enable_ai_analysis': True,
            'project_description': '这是一个企业并购重组的法律服务项目'
        }
        
        try:
            response = requests.post(url, files=files, data=data)
            print(f"📊 上传响应状态: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 上传成功: {result}")
                
                # 检查是否有AI分析结果
                if 'ai_analysis' in result:
                    print("🤖 AI分析结果:")
                    ai_result = result['ai_analysis']
                    print(f"  - 项目名称: {ai_result.get('project_name', 'N/A')}")
                    print(f"  - 客户名称: {ai_result.get('client_name', 'N/A')}")
                    print(f"  - 项目类型: {ai_result.get('project_type', 'N/A')}")
                    print(f"  - 业务领域: {ai_result.get('business_field', 'N/A')}")
                    print(f"  - 合同金额: {ai_result.get('contract_amount', 'N/A')}")
                    print(f"  - 项目时间: {ai_result.get('project_year', 'N/A')}")
                    print(f"  - 置信度: {ai_result.get('confidence_score', 'N/A')}")
                    
                    if ai_result.get('confidence_score', 0) > 0.7:
                        print("✅ AI分析置信度较高，分析成功")
                        return True
                    else:
                        print("⚠️ AI分析置信度较低")
                        return False
                else:
                    print("❌ 未发现AI分析结果")
                    return False
            else:
                print(f"❌ 上传失败: {response.status_code}")
                print(f"📝 错误响应: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 测试异常: {e}")
            return False
        finally:
            # 清理测试文件
            if os.path.exists(pdf_filename):
                os.remove(pdf_filename)

def main():
    """主函数"""
    print("🚀 投标苦系统 - AI业绩分析功能测试")
    print("=" * 50)
    
    success = test_ai_performance_analysis()
    
    print("=" * 50)
    if success:
        print("✅ AI业绩分析功能测试通过！")
        print("🎉 AI可以正确识别和分析法律服务合同")
    else:
        print("❌ AI业绩分析功能测试失败")
        print("🔍 请检查后端日志获取更多信息")

if __name__ == "__main__":
    main() 
 