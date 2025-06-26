#!/usr/bin/env python3
"""测试PyMuPDF颜色水印功能"""

import fitz
import os

def test_watermark_colors():
    """测试不同颜色的水印效果"""
    
    # 创建一个简单的PDF进行测试
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)  # A4尺寸
    
    # 测试颜色列表
    test_colors = [
        ("#ff0000", "红色"),
        ("#00ff00", "绿色"), 
        ("#0000ff", "蓝色"),
        ("#ffff00", "黄色"),
        ("#ff00ff", "紫色"),
        ("#00ffff", "青色"),
        ("#808080", "灰色"),
        ("#000000", "黑色")
    ]
    
    y_pos = 100
    
    for color_hex, color_name in test_colors:
        print(f"测试颜色: {color_name} ({color_hex})")
        
        # 解析颜色
        color_hex = color_hex.lstrip('#')
        if len(color_hex) == 6:
            r, g, b = tuple(int(color_hex[i:i+2], 16) for i in (0, 2, 4))
        else:
            r, g, b = 128, 128, 128
        
        # 转换为0-1范围
        color_r = r / 255.0
        color_g = g / 255.0
        color_b = b / 255.0
        
        print(f"  原始RGB: ({r}, {g}, {b})")
        print(f"  转换后: ({color_r:.3f}, {color_g:.3f}, {color_b:.3f})")
        
        # 添加水印文本
        try:
            page.insert_text(
                fitz.Point(100, y_pos),
                f"{color_name}水印测试 - {color_hex}",
                fontsize=16,
                color=(color_r, color_g, color_b),
                fill_opacity=0.7,
                fontname="china-ss"
            )
            print(f"  ✅ {color_name} 添加成功")
        except Exception as e:
            print(f"  ❌ {color_name} 添加失败: {e}")
        
        y_pos += 30
    
    # 保存测试PDF
    output_path = "/app/generated_docs/color_test.pdf"
    doc.save(output_path)
    doc.close()
    
    print(f"\n测试PDF已保存到: {output_path}")
    return output_path

if __name__ == "__main__":
    test_watermark_colors() 