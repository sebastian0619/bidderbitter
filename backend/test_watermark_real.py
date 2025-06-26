#!/usr/bin/env python3
"""测试真实的水印添加功能"""

import sys
import os
sys.path.append('/app')

from main import add_watermark_to_pdf
import fitz

def create_test_pdf():
    """创建一个测试PDF"""
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    
    # 添加一些基本内容
    page.insert_text(fitz.Point(100, 100), "这是一个测试PDF文档", fontsize=16)
    page.insert_text(fitz.Point(100, 150), "用来测试水印功能是否正常工作", fontsize=14)
    
    test_pdf_path = "/app/generated_docs/test_source.pdf"
    doc.save(test_pdf_path)
    doc.close()
    
    return test_pdf_path

def test_different_colors():
    """测试不同颜色的水印效果"""
    
    test_pdf = create_test_pdf()
    
    # 测试不同颜色
    test_colors = [
        ("#ff0000", "红色测试"),
        ("#00ff00", "绿色测试"), 
        ("#0000ff", "蓝色测试"),
        ("#ffff00", "黄色测试"),
        ("#ff00ff", "紫色测试"),
        ("#808080", "灰色测试")
    ]
    
    for color_hex, description in test_colors:
        print(f"\n=== 测试 {description} ({color_hex}) ===")
        
        result_pdf = add_watermark_to_pdf(
            pdf_path=test_pdf,
            text=f"{description}水印",
            font_size=24,
            angle=-45,
            opacity=50,
            color=color_hex,
            position="center"
        )
        
        print(f"生成的水印PDF: {result_pdf}")
        
        # 重命名以便区分
        final_path = f"/app/generated_docs/watermark_{description}_{color_hex.replace('#', '')}.pdf"
        if os.path.exists(result_pdf):
            os.rename(result_pdf, final_path)
            print(f"保存到: {final_path}")

if __name__ == "__main__":
    test_different_colors() 