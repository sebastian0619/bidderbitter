#!/usr/bin/env python3
"""
测试Docling文本提取功能
"""

import asyncio
import sys
import os

# 添加backend目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

async def test_docling_text_extraction():
    """测试Docling文本提取"""
    try:
        from docling_service import docling_service
        
        # 测试文件路径
        test_file = "/app/uploads/performances/20250701_074418_4_5. 法律服务委托协议.pdf"
        
        print(f"🔍 测试文件: {test_file}")
        print(f"📁 文件是否存在: {os.path.exists(test_file)}")
        
        if not os.path.exists(test_file):
            print("❌ 测试文件不存在")
            return
        
        # 测试文档转换
        print("\n📄 步骤1: 测试文档转换...")
        convert_result = await docling_service.convert_document(test_file)
        print(f"转换结果: {convert_result['success']}")
        
        if not convert_result['success']:
            print(f"❌ 文档转换失败: {convert_result.get('error', '未知错误')}")
            return
        
        # 获取文档对象
        doc = convert_result['document']
        print(f"✅ 文档转换成功")
        print(f"  - 页数: {doc.num_pages()}")
        print(f"  - 文本元素数量: {len(doc.texts)}")
        print(f"  - 表格数量: {len(doc.tables)}")
        print(f"  - 图片数量: {len(doc.pictures)}")
        
        # 检查文本元素
        if len(doc.texts) > 0:
            print(f"\n📝 前3个文本元素:")
            for i, text in enumerate(doc.texts[:3]):
                text_content = text.text[:100] + "..." if len(text.text) > 100 else text.text
                print(f"  文本{i+1}: {text_content}")
        else:
            print("\n⚠️ 没有找到文本元素")
        
        # 测试文本提取
        print("\n📄 步骤2: 测试文本提取...")
        extract_result = await docling_service.extract_text(test_file, format="text")
        print(f"提取结果: {extract_result['success']}")
        
        if extract_result['success']:
            text_content = extract_result['text_content']
            print(f"✅ 文本提取成功")
            print(f"  - 文本长度: {len(text_content)} 字符")
            if len(text_content) > 0:
                print(f"  - 文本预览: {text_content[:200]}...")
            else:
                print("  - ⚠️ 提取的文本为空")
        else:
            print(f"❌ 文本提取失败: {extract_result.get('error', '未知错误')}")
        
        # 测试Markdown格式
        print("\n📄 步骤3: 测试Markdown格式...")
        markdown_result = await docling_service.extract_text(test_file, format="markdown")
        if markdown_result['success']:
            markdown_content = markdown_result['text_content']
            print(f"✅ Markdown提取成功")
            print(f"  - 长度: {len(markdown_content)} 字符")
            if len(markdown_content) > 0:
                print(f"  - 预览: {markdown_content[:200]}...")
            else:
                print("  - ⚠️ Markdown内容为空")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_docling_text_extraction()) 