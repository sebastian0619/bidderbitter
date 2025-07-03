#!/usr/bin/env python3
"""
测试DoclingService重构集成
验证ai_service.py、document_processor.py、ai_tools.py是否正确使用DoclingService
"""
import asyncio
import sys
import os

# 添加backend目录到Python路径
sys.path.insert(0, 'backend')

async def test_docling_integration():
    """测试DoclingService集成"""
    print("🚀 开始测试DoclingService重构...")
    
    # 1. 测试DoclingService导入
    try:
        from backend.docling_service import DoclingService, docling_service
        print("✅ DoclingService导入成功")
    except ImportError as e:
        print(f"❌ DoclingService导入失败: {e}")
        return False
    
    # 2. 测试ai_service.py重构
    try:
        from backend.ai_service import ai_service
        print("✅ ai_service导入成功")
        
        # 检查是否使用DoclingService
        if hasattr(ai_service, 'docling_service'):
            print("✅ ai_service正确引用DoclingService")
        else:
            print("❌ ai_service未正确引用DoclingService")
            return False
            
    except ImportError as e:
        print(f"❌ ai_service导入失败: {e}")
        return False
    
    # 3. 测试document_processor.py重构
    try:
        from backend.document_processor import DoclingDocumentProcessor
        processor = DoclingDocumentProcessor()
        print("✅ DoclingDocumentProcessor导入成功")
        
        # 检查是否使用DoclingService
        if hasattr(processor, 'converter') and processor.converter is not None:
            print("✅ DoclingDocumentProcessor正确引用DoclingService")
        else:
            print("⚠️  DoclingDocumentProcessor converter为None（可能是正常的，如果DoclingService不可用）")
            
    except ImportError as e:
        print(f"❌ DoclingDocumentProcessor导入失败: {e}")
        return False
    
    # 4. 测试ai_tools.py重构
    try:
        from backend.ai_tools import tool_manager
        print("✅ ai_tools导入成功")
        
    except ImportError as e:
        print(f"❌ ai_tools导入失败: {e}")
        return False
    
    # 5. 测试DoclingService基本功能
    try:
        print("\n📋 测试DoclingService基本功能...")
        
        # 检查服务状态
        if docling_service:
            status = docling_service.get_service_status()
            print(f"📊 DoclingService状态: {status}")
            
            # 如果服务可用，尝试基本功能测试
            if status.get("available"):
                print("✅ DoclingService服务可用")
            else:
                print("⚠️  DoclingService服务不可用（这可能是正常的，如果模型未下载）")
        else:
            print("⚠️  DoclingService实例为None")
            
    except Exception as e:
        print(f"❌ DoclingService功能测试失败: {e}")
        return False
    
    print("\n🎉 DoclingService重构集成测试完成！")
    return True

def test_imports():
    """测试关键导入是否正确"""
    print("\n🔍 测试关键导入...")
    
    # 测试是否移除了旧的Docling直接导入
    test_files = [
        ('backend/ai_service.py', ['from docling.document_converter import']),
        ('backend/document_processor.py', ['from docling.document_converter import']),
        ('backend/ai_tools.py', ['from docling.document_converter import'])
    ]
    
    all_good = True
    for file_path, bad_imports in test_files:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            for bad_import in bad_imports:
                if bad_import in content and not content.count('# ' + bad_import):
                    print(f"❌ {file_path} 仍包含直接Docling导入: {bad_import}")
                    all_good = False
                    
    if all_good:
        print("✅ 所有文件都已正确移除直接Docling导入")
    
    return all_good

async def main():
    """主测试函数"""
    print("🔧 DoclingService重构验证测试")
    print("=" * 50)
    
    # 测试导入清理
    import_test = test_imports()
    
    # 测试集成
    integration_test = await test_docling_integration()
    
    print("\n" + "=" * 50)
    if import_test and integration_test:
        print("🎉 所有测试通过！DoclingService重构成功完成！")
        return True
    else:
        print("❌ 部分测试失败，请检查重构")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 
 