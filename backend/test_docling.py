#!/usr/bin/env python3
"""
测试Docling安装和配置
"""

import os
import sys
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_docling_import():
    """测试Docling导入"""
    try:
        from docling.document_converter import DocumentConverter
        from docling.datamodel.base_models import InputFormat
        from docling.datamodel.pipeline_options import PdfPipelineOptions
        from docling.datamodel.accelerator_options import AcceleratorDevice, AcceleratorOptions
        
        logger.info("✅ Docling导入成功")
        return True
    except ImportError as e:
        logger.error(f"❌ Docling导入失败: {e}")
        return False

def test_docling_converter():
    """测试Docling转换器创建"""
    try:
        from docling.document_converter import DocumentConverter
        from docling.datamodel.base_models import InputFormat
        from docling.datamodel.pipeline_options import PdfPipelineOptions
        from docling.datamodel.accelerator_options import AcceleratorDevice, AcceleratorOptions
        
        # 配置PDF处理选项
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = True
        pipeline_options.do_table_structure = True
        pipeline_options.table_structure_options.do_cell_matching = True
        pipeline_options.ocr_options.lang = ["chi_sim", "eng"]
        pipeline_options.ocr_options.use_gpu = False
        
        # 配置加速选项
        pipeline_options.accelerator_options = AcceleratorOptions(
            num_threads=4, 
            device=AcceleratorDevice.CPU
        )
        
        # 创建转换器
        converter = DocumentConverter(
            format_options={
                InputFormat.PDF: pipeline_options
            }
        )
        
        logger.info("✅ Docling转换器创建成功")
        return True
    except Exception as e:
        logger.error(f"❌ Docling转换器创建失败: {e}")
        return False

def test_easyocr():
    """测试EasyOCR"""
    try:
        import easyocr
        logger.info("✅ EasyOCR导入成功")
        return True
    except ImportError as e:
        logger.error(f"❌ EasyOCR导入失败: {e}")
        return False

def test_pymupdf():
    """测试PyMuPDF"""
    try:
        import fitz
        logger.info("✅ PyMuPDF导入成功")
        return True
    except ImportError as e:
        logger.error(f"❌ PyMuPDF导入失败: {e}")
        return False

def test_python_docx():
    """测试python-docx"""
    try:
        from docx import Document
        logger.info("✅ python-docx导入成功")
        return True
    except ImportError as e:
        logger.error(f"❌ python-docx导入失败: {e}")
        return False

def main():
    """主测试函数"""
    logger.info("开始测试Docling相关依赖...")
    
    tests = [
        ("Docling导入", test_docling_import),
        ("Docling转换器", test_docling_converter),
        ("EasyOCR", test_easyocr),
        ("PyMuPDF", test_pymupdf),
        ("python-docx", test_python_docx),
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\n--- 测试 {test_name} ---")
        result = test_func()
        results.append((test_name, result))
    
    # 输出总结
    logger.info("\n" + "="*50)
    logger.info("测试结果总结:")
    logger.info("="*50)
    
    success_count = 0
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        logger.info(f"{test_name}: {status}")
        if result:
            success_count += 1
    
    logger.info(f"\n总计: {success_count}/{len(results)} 个测试通过")
    
    if success_count == len(results):
        logger.info("🎉 所有测试通过！Docling配置正确。")
        return 0
    else:
        logger.error("⚠️  部分测试失败，请检查依赖安装。")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 