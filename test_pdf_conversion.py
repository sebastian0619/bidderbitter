#!/usr/bin/env python3
"""
测试PDF转换功能 - 支持扫描件和非扫描件PDF
"""

import asyncio
import os
import sys
import tempfile
from pathlib import Path

# 添加backend目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from document_processor import DoclingDocumentProcessor, DocumentProcessor

async def test_pdf_type_detection():
    """测试PDF类型检测功能"""
    print("=== 测试PDF类型检测功能 ===")
    
    # 创建测试用的DoclingDocumentProcessor实例
    processor = DoclingDocumentProcessor()
    
    # 测试文件路径（需要用户提供）
    test_pdf_path = input("请输入要测试的PDF文件路径: ").strip()
    
    if not os.path.exists(test_pdf_path):
        print(f"错误：文件不存在: {test_pdf_path}")
        return
    
    try:
        # 测试类型检测
        pdf_type = await processor._detect_pdf_type(test_pdf_path)
        print(f"PDF类型检测结果: {pdf_type}")
        
        # 测试静态方法
        static_pdf_type = await DocumentProcessor._detect_pdf_type_static(test_pdf_path)
        print(f"静态方法检测结果: {static_pdf_type}")
        
        if pdf_type == static_pdf_type:
            print("✓ 两种检测方法结果一致")
        else:
            print("⚠ 两种检测方法结果不一致")
            
    except Exception as e:
        print(f"测试失败: {e}")

async def test_pdf_conversion():
    """测试PDF转换功能"""
    print("\n=== 测试PDF转换功能 ===")
    
    # 测试文件路径（需要用户提供）
    test_pdf_path = input("请输入要转换的PDF文件路径: ").strip()
    
    if not os.path.exists(test_pdf_path):
        print(f"错误：文件不存在: {test_pdf_path}")
        return
    
    try:
        # 创建临时输出目录
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "converted_document.docx")
            
            print(f"开始转换PDF: {test_pdf_path}")
            print(f"输出路径: {output_path}")
            
            # 使用DocumentProcessor转换
            result_path, page_count = await DocumentProcessor.convert_pdf_to_word(
                test_pdf_path, output_path
            )
            
            print(f"✓ 转换成功!")
            print(f"输出文件: {result_path}")
            print(f"页数: {page_count}")
            
            # 检查输出文件是否存在
            if os.path.exists(result_path):
                file_size = os.path.getsize(result_path)
                print(f"文件大小: {file_size / 1024:.2f} KB")
            else:
                print("⚠ 输出文件不存在")
                
    except Exception as e:
        print(f"转换失败: {e}")

async def test_docling_processor():
    """测试DoclingDocumentProcessor的完整处理流程"""
    print("\n=== 测试DoclingDocumentProcessor完整流程 ===")
    
    # 测试文件路径（需要用户提供）
    test_pdf_path = input("请输入要处理的PDF文件路径: ").strip()
    
    if not os.path.exists(test_pdf_path):
        print(f"错误：文件不存在: {test_pdf_path}")
        return
    
    try:
        # 创建DoclingDocumentProcessor实例
        processor = DoclingDocumentProcessor()
        
        # 创建临时输出目录
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "docling_processed.docx")
            
            print(f"开始使用DoclingDocumentProcessor处理PDF: {test_pdf_path}")
            print(f"输出路径: {output_path}")
            
            # 创建Word文档
            from docx import Document
            doc = Document()
            
            # 处理PDF
            filename = os.path.basename(test_pdf_path)
            result = await processor.process_pdf_with_docling(
                test_pdf_path, doc, filename, 
                show_file_titles=True, 
                file_title_level=2, 
                is_last_file=True
            )
            
            # 保存文档
            doc.save(output_path)
            
            print(f"✓ 处理完成!")
            print(f"处理结果: {result}")
            print(f"输出文件: {output_path}")
            
            # 检查输出文件
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                print(f"文件大小: {file_size / 1024:.2f} KB")
            else:
                print("⚠ 输出文件不存在")
                
    except Exception as e:
        print(f"处理失败: {e}")

async def main():
    """主测试函数"""
    print("PDF转换功能测试工具")
    print("=" * 50)
    
    while True:
        print("\n请选择测试项目:")
        print("1. 测试PDF类型检测")
        print("2. 测试PDF转换功能")
        print("3. 测试DoclingDocumentProcessor完整流程")
        print("4. 退出")
        
        choice = input("\n请输入选择 (1-4): ").strip()
        
        if choice == "1":
            await test_pdf_type_detection()
        elif choice == "2":
            await test_pdf_conversion()
        elif choice == "3":
            await test_docling_processor()
        elif choice == "4":
            print("退出测试工具")
            break
        else:
            print("无效选择，请重新输入")

if __name__ == "__main__":
    asyncio.run(main()) 