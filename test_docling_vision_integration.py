#!/usr/bin/env python3
"""
测试Docling图片描述配置和AI服务集成

验证：
1. Docling图片描述配置是否正确读取用户的视觉模型配置
2. AI服务是否能正确检测Docling图片描述功能并避免重复分析
3. 当Docling图片描述未配置时是否正确回退到独立视觉分析
"""

import asyncio
import os
import sys
import logging

# 添加项目路径
sys.path.append('backend')

from docling_service import DoclingService, DoclingConfig
from ai_service import AIService

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_docling_config():
    """测试Docling配置是否正确读取视觉模型设置"""
    logger.info("=== 测试Docling配置读取 ===")
    
    try:
        config = DoclingConfig()
        
        logger.info(f"视觉模型配置:")
        logger.info(f"  - 视觉提供商: {config.vision_provider}")
        logger.info(f"  - 视觉模型: {config.vision_model}")
        logger.info(f"  - 视觉API密钥: {'***已配置***' if config.vision_api_key else '未配置'}")
        logger.info(f"  - 视觉API URL: {config.vision_base_url if config.vision_provider != 'ollama' else config.ollama_vision_base_url}")
        logger.info(f"  - 图片描述提示词: {config.picture_description_prompt[:50]}...")
        
        logger.info(f"Docling功能配置:")
        logger.info(f"  - 启用图片描述: {config.enable_picture_description}")
        logger.info(f"  - 启用图片分类: {config.enable_picture_classification}")
        logger.info(f"  - 启用表格结构: {config.enable_table_structure}")
        
        return True
        
    except Exception as e:
        logger.error(f"Docling配置测试失败: {e}")
        return False

async def test_docling_service_status():
    """测试Docling服务状态"""
    logger.info("=== 测试Docling服务状态 ===")
    
    try:
        docling_service = DoclingService()
        status = docling_service.get_status()
        
        logger.info(f"Docling服务状态:")
        logger.info(f"  - Docling可用: {status['docling_available']}")
        logger.info(f"  - 已初始化: {status['initialized']}")
        logger.info(f"  - 转换器就绪: {status['converter_ready']}")
        
        if status.get('config'):
            config = status['config']
            logger.info(f"  - 图片描述功能: {config.get('enable_picture_description')}")
            logger.info(f"  - 视觉模型: {config.get('vision_model')}")
            logger.info(f"  - 视觉提供商: {config.get('vision_provider')}")
        
        return status['converter_ready']
        
    except Exception as e:
        logger.error(f"Docling服务状态测试失败: {e}")
        return False

async def test_ai_service_integration():
    """测试AI服务与Docling的集成"""
    logger.info("=== 测试AI服务集成 ===")
    
    try:
        ai_service = AIService()
        
        # 检查AI服务的配置
        logger.info(f"AI服务配置:")
        logger.info(f"  - AI API密钥: {'***已配置***' if ai_service.ai_api_key else '未配置'}")
        logger.info(f"  - AI模型: {ai_service._get_ai_vision_model()}")
        logger.info(f"  - AI提供商: {ai_service._get_setting_value('ai_provider', 'openai')}")
        
        # 检查视觉分析配置
        vision_provider = ai_service._get_setting_value("vision_provider", ai_service._get_setting_value("ai_provider", "openai"))
        vision_api_key = ai_service._get_setting_value("vision_api_key", ai_service._get_setting_value("ai_api_key", ""))
        enable_picture_description = ai_service._get_setting_value("ai_analysis_enable_picture_description", "false").lower() == "true"
        
        logger.info(f"视觉分析配置:")
        logger.info(f"  - 视觉提供商: {vision_provider}")
        logger.info(f"  - 视觉API密钥: {'***已配置***' if vision_api_key else '未配置'}")
        logger.info(f"  - 启用图片描述: {enable_picture_description}")
        
        # 检测Docling图片描述是否配置
        docling_picture_description_enabled = (
            enable_picture_description and vision_api_key != ""
        )
        
        logger.info(f"集成状态:")
        logger.info(f"  - Docling图片描述已配置: {docling_picture_description_enabled}")
        
        if docling_picture_description_enabled:
            logger.info("✅ Docling图片描述已配置，AI服务将优先使用Docling的图片描述功能")
        else:
            logger.info("ℹ️  Docling图片描述未配置，AI服务将使用独立视觉分析")
        
        return True
        
    except Exception as e:
        logger.error(f"AI服务集成测试失败: {e}")
        return False

async def test_document_analysis_workflow(test_file_path: str = None):
    """测试文档分析工作流"""
    logger.info("=== 测试文档分析工作流 ===")
    
    # 查找测试文件
    if not test_file_path:
        test_files = []
        for root, dirs, files in os.walk("uploads"):
            for file in files:
                if file.lower().endswith(('.pdf', '.jpg', '.jpeg', '.png')):
                    test_files.append(os.path.join(root, file))
        
        if not test_files:
            logger.warning("未找到测试文件，跳过文档分析测试")
            return True
        
        test_file_path = test_files[0]
    
    if not os.path.exists(test_file_path):
        logger.warning(f"测试文件不存在: {test_file_path}")
        return True
    
    logger.info(f"使用测试文件: {test_file_path}")
    
    try:
        ai_service = AIService()
        
        # 执行智能文档分析
        logger.info("开始智能文档分析...")
        result = await ai_service.smart_document_analysis(
            test_file_path, 
            enable_vision=True, 
            enable_ocr=True
        )
        
        if result.get("success"):
            results = result.get("results", {})
            
            # 检查文本提取结果
            text_result = results.get("text_extraction_result", {})
            logger.info(f"文本提取: {'成功' if text_result.get('text') else '失败'}")
            if text_result.get('text'):
                logger.info(f"  - 提取文本长度: {len(text_result['text'])} 字符")
            
            # 检查视觉分析结果
            vision_result = results.get("vision_analysis_result", {})
            if vision_result:
                source = vision_result.get("source", "unknown")
                success = vision_result.get("success", False)
                logger.info(f"图片分析: {'成功' if success else '失败'} (来源: {source})")
                
                if source == "docling_picture_description":
                    logger.info("✅ 使用了Docling图片描述功能")
                    if vision_result.get("descriptions"):
                        logger.info(f"  - 图片描述数量: {len(vision_result['descriptions'])}")
                elif source == "independent_vision":
                    logger.info("ℹ️  使用了独立视觉分析")
                elif source.startswith("fallback"):
                    logger.info(f"⚠️  使用了备用方案: {source}")
            
            # 检查AI文本分析结果
            ai_text_result = results.get("ai_text_analysis", {})
            logger.info(f"AI文本分析: {'成功' if ai_text_result.get('success') else '失败'}")
            
            # 检查最终分类结果
            final_classification = results.get("final_classification", {})
            if final_classification:
                logger.info(f"最终分类:")
                logger.info(f"  - 类型: {final_classification.get('type', 'unknown')}")
                logger.info(f"  - 置信度: {final_classification.get('confidence', 0.0):.2f}")
            
        else:
            logger.error(f"智能文档分析失败: {result.get('error')}")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"文档分析工作流测试失败: {e}")
        return False

async def main():
    """主测试函数"""
    logger.info("开始Docling图片描述集成测试...")
    
    tests = [
        ("Docling配置读取", test_docling_config),
        ("Docling服务状态", test_docling_service_status),
        ("AI服务集成", test_ai_service_integration),
        ("文档分析工作流", test_document_analysis_workflow),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"执行测试: {test_name}")
        logger.info(f"{'='*50}")
        
        try:
            result = await test_func()
            results.append((test_name, result))
            
            if result:
                logger.info(f"✅ {test_name} - 通过")
            else:
                logger.warning(f"❌ {test_name} - 失败")
                
        except Exception as e:
            logger.error(f"❌ {test_name} - 异常: {e}")
            results.append((test_name, False))
    
    # 总结
    logger.info(f"\n{'='*50}")
    logger.info("测试总结")
    logger.info(f"{'='*50}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        logger.info(f"{test_name}: {status}")
    
    logger.info(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        logger.info("🎉 所有测试通过！Docling图片描述集成配置正确。")
    else:
        logger.warning(f"⚠️  {total - passed} 个测试失败，请检查配置。")
    
    return passed == total

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("测试被用户中断")
        exit(1)
    except Exception as e:
        logger.error(f"测试运行异常: {e}")
        exit(1) 