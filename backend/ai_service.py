import os
import json
import logging
from typing import Dict, Any, List, Optional
import asyncio
import aiohttp
import fitz  # PyMuPDF
from mcp_client import MCPClient, MCPSettings
import base64
import re
from models import AITask
from sqlalchemy.orm import Session
from config_manager import config_manager

# 设置日志
logger = logging.getLogger(__name__)

# 导入统一的Docling服务
try:
    from docling_service import docling_service, get_service_status
    DOCLING_SERVICE_AVAILABLE = True
    logger.info("DoclingService可用")
except ImportError as e:
    DOCLING_SERVICE_AVAILABLE = False
    logger.warning(f"DoclingService不可用: {e}")
    docling_service = None

class AIService:
    """AI服务类，提供各种AI能力"""
    
    def __init__(self):
        self.ai_provider = os.getenv("AI_PROVIDER", "openai").lower()
        self.enable_ai = os.getenv("ENABLE_AI", "true").lower() == "true"
        
        # AI服务配置
        self.ai_api_key = self._get_ai_api_key()
        self.ai_base_url = self._get_ai_base_url()
        self.ai_model = self._get_ai_model()
        self.ai_vision_model = self._get_ai_vision_model()
        
        # 初始化MCP客户端
        self.mcp_client = MCPClient(MCPSettings())
        
        # 使用统一的Docling服务
        self.docling_service = docling_service
        
        # 业务领域配置
        self.business_fields = self._load_business_fields()
        
        # 配置管理器
        self.config_manager = config_manager
        
        self.reload_config()
        logger.info("AI服务初始化完成")
    
    def _get_setting_value(self, key: str, default: str = "") -> str:
        """从数据库获取设置值，如果不存在则返回环境变量或默认值"""
        try:
            from database import get_db
            from models import SystemSettings
            
            db = next(get_db())
            setting = db.query(SystemSettings).filter(
                SystemSettings.setting_key == key
            ).first()
            
            if setting and setting.setting_value:
                return setting.setting_value
                
        except Exception as e:
            logger.warning(f"无法从数据库获取设置 {key}: {str(e)}")
        finally:
            try:
                if 'db' in locals():
                    db.close()
            except:
                pass
        
        return os.getenv(key.upper(), default)
    
    def reload_config(self):
        """重新加载配置"""
        # AI服务配置
        self.enable_ai = self._get_setting_value("enable_ai", "true").lower() == "true"
        self.ai_provider = self._get_setting_value("ai_provider", "custom")
        self.ai_api_key = self._get_ai_api_key()
        self.ai_base_url = self._get_ai_base_url()
        self.ai_model = self._get_ai_model()
        self.ai_vision_model = self._get_ai_vision_model()
        
        # 业务领域
        self.business_fields = self._load_business_fields()
        
        # 加载MCP配置
        mcp_server_url = self._get_setting_value("mcp_server_url")
        mcp_api_key = self._get_setting_value("mcp_api_key")
        mcp_enabled = self._get_setting_value("mcp_enabled", "false").lower() == "true"
        mcp_timeout = int(self._get_setting_value("mcp_timeout", "30"))
        
        # 更新MCP客户端配置
        if self.mcp_client:
            self.mcp_client.settings = MCPSettings(
                server_url=mcp_server_url,
                api_key=mcp_api_key,
                enabled=mcp_enabled,
                timeout=mcp_timeout
            )
            self.mcp_client.initialize()
        
        logger.info(f"配置重载完成: AI={self.enable_ai}, Provider={self.ai_provider}, MCP={mcp_enabled}")
    
    async def smart_document_analysis(self, file_path: str, enable_vision: bool = True, enable_ocr: bool = True) -> Dict[str, Any]:
        """
        智能文档分析 - 使用Docling进行文档转换和OCR提取
        """
        if not os.path.exists(file_path):
            return {"success": False, "error": "文件不存在"}
        
        results = {
            "text_extraction_result": {"text": "", "extracted_content": {}},
            "vision_analysis_result": {"success": False, "error": "未启用"},
            "ai_text_analysis": {},
            "final_classification": {}
        }
        
        # 1. 使用DoclingService进行文档转换和OCR提取
        text_content = ""
        if enable_ocr and self.docling_service:
            try:
                if not os.path.exists(file_path):
                    return {"success": False, "error": "文件不存在"}
                
                # 使用convert_document方法进行完整转换
                docling_result = await self.docling_service.convert_document(file_path)
                if docling_result.get("success"):
                    doc = docling_result.get("document")
                    
                    # 尝试多种文本提取方法
                    text_content = ""
                    extraction_method = "unknown"
                    
                    # 方法1: 使用export_to_text()
                    try:
                        text_content = doc.export_to_text()
                        if text_content and len(text_content.strip()) > 0:
                            extraction_method = "export_to_text"
                    except Exception as e:
                        logger.warning(f"export_to_text()失败: {e}")
                    
                    # 方法2: 如果export_to_text()返回空，尝试从文本元素直接提取
                    if not text_content or len(text_content.strip()) == 0:
                        try:
                            text_parts = []
                            for text_element in doc.texts:
                                if hasattr(text_element, 'text') and text_element.text:
                                    text_parts.append(text_element.text.strip())
                            
                            if text_parts:
                                text_content = "\n".join(text_parts)
                                extraction_method = "direct_from_texts"
                                logger.info(f"成功从{len(text_parts)}个文本元素中提取内容")
                        except Exception as e:
                            logger.warning(f"从文本元素直接提取失败: {e}")
                    
                    # 方法3: 如果还是没有文本，尝试export_to_markdown()
                    if not text_content or len(text_content.strip()) == 0:
                        try:
                            markdown_content = doc.export_to_markdown()
                            if markdown_content and len(markdown_content.strip()) > 0:
                                text_content = markdown_content
                                extraction_method = "export_to_markdown"
                        except Exception as e:
                            logger.warning(f"export_to_markdown()失败: {e}")
                    
                    results["text_extraction_result"]["text"] = text_content
                    results["text_extraction_result"]["extracted_content"]["text"] = text_content
                    
                    # 详细的文档信息日志
                    logger.info(f"DoclingService 转换成功:")
                    logger.info(f"  - 提取文本: {len(text_content)} 字符 (方法: {extraction_method})")
                    logger.info(f"  - 页数: {doc.num_pages()}")
                    logger.info(f"  - 图片数量: {len(doc.pictures)}")
                    logger.info(f"  - 表格数量: {len(doc.tables)}")
                    logger.info(f"  - 文本元素: {len(doc.texts)}")
                    
                    if len(text_content) > 0:
                        logger.info(f"  - 文本预览: {text_content[:200]}...")
                    else:
                        logger.warning(f"  - ⚠️  提取的文本为空，详细调试信息:")
                        logger.warning(f"    * 文本元素数量: {len(doc.texts)}")
                        
                        # 详细检查文本元素
                        if len(doc.texts) > 0:
                            logger.info(f"    * 检查前3个文本元素:")
                            for i, text_elem in enumerate(doc.texts[:3]):
                                if hasattr(text_elem, 'text'):
                                    logger.info(f"      元素{i+1}: '{text_elem.text}' (长度: {len(text_elem.text) if text_elem.text else 0})")
                                else:
                                    logger.info(f"      元素{i+1}: 没有text属性")
                        
                        logger.warning(f"    * OCR功能未启用或失败")
                        logger.warning(f"    * 文档是纯图片且OCR无法识别")
                        logger.warning(f"    * 文档格式不支持或损坏")
                        
                        # 检查文档中的图片信息
                        if len(doc.pictures) > 0:
                            logger.info(f"    * 文档包含 {len(doc.pictures)} 张图片，建议检查OCR配置")
                        if len(doc.texts) == 0:
                            logger.warning(f"    * 没有找到文本元素，可能需要强制OCR")
                else:
                    logger.warning(f"DoclingService 转换失败: {docling_result.get('error')}")
                    results["text_extraction_result"]["error"] = docling_result.get("error")
            except Exception as e:
                logger.error(f"DoclingService 转换异常: {e}")
                results["text_extraction_result"]["error"] = str(e)
        
        # 2. 图片分析
        if enable_vision and self._is_image_or_pdf(file_path):
            try:
                # 检查Docling是否已经配置了图片描述功能
                docling_picture_description_enabled = (
                    self._get_setting_value("ai_analysis_enable_picture_description", "false").lower() == "true" and
                    self._get_setting_value("vision_api_key", self._get_setting_value("ai_api_key", "")) != ""
                )
                
                if docling_picture_description_enabled:
                    # Docling已配置图片描述，检查转换结果中是否包含图片描述
                    if docling_result.get("success") and docling_result.get("document"):
                        doc = docling_result.get("document")
                        if hasattr(doc, 'pictures') and len(doc.pictures) > 0:
                            # 检查图片是否有描述信息
                            picture_descriptions = []
                            for picture in doc.pictures:
                                if hasattr(picture, 'description') and picture.description:
                                    picture_descriptions.append(picture.description)
                            
                            if picture_descriptions:
                                # Docling已提供图片描述，无需重复分析
                                results["vision_analysis_result"] = {
                                    "success": True,
                                    "source": "docling_picture_description",
                                    "descriptions": picture_descriptions,
                                    "total_pictures": len(doc.pictures),
                                    "described_pictures": len(picture_descriptions)
                                }
                                logger.info(f"使用Docling图片描述: 共{len(doc.pictures)}张图片，{len(picture_descriptions)}张有描述")
                            else:
                                # Docling未能生成图片描述，使用独立视觉分析作为备用
                                logger.info("Docling图片描述为空，使用独立视觉分析作为备用")
                                vision_prompt = self._get_setting_value("vision_prompt", "请分析这个法律相关文档图像，提取关键信息和类型，以JSON格式返回。")
                                vision_result = await self.analyze_vision(file_path, vision_prompt)
                                results["vision_analysis_result"] = vision_result
                                results["vision_analysis_result"]["source"] = "fallback_independent_vision"
                        else:
                            # 文档中没有图片，跳过图片分析
                            results["vision_analysis_result"] = {
                                "success": True,
                                "source": "no_pictures",
                                "message": "文档中未发现图片"
                            }
                            logger.info("文档中没有图片，跳过图片分析")
                    else:
                        # Docling转换失败，使用独立视觉分析
                        logger.info("Docling转换失败，使用独立视觉分析")
                        vision_prompt = self._get_setting_value("vision_prompt", "请分析这个法律相关文档图像，提取关键信息和类型，以JSON格式返回。")
                        vision_result = await self.analyze_vision(file_path, vision_prompt)
                        results["vision_analysis_result"] = vision_result
                        results["vision_analysis_result"]["source"] = "fallback_docling_failed"
                else:
                    # 未配置Docling图片描述，使用独立视觉分析
                    logger.info("使用独立视觉服务: provider={}, model={}, url={}".format(
                        self._get_setting_value("vision_provider", self._get_setting_value("ai_provider", "openai")),
                        self._get_setting_value("ai_vision_model", "gpt-4-vision-preview"),
                        self._get_setting_value("vision_base_url", self._get_setting_value("ai_base_url", "https://api.openai.com/v1"))
                    ))
                    vision_prompt = self._get_setting_value("vision_prompt", "请分析这个法律相关文档图像，提取关键信息和类型，以JSON格式返回。")
                    vision_result = await self.analyze_vision(file_path, vision_prompt)
                    results["vision_analysis_result"] = vision_result
                    results["vision_analysis_result"]["source"] = "independent_vision"
                
                # 详细的视觉分析结果日志
                vision_result = results['vision_analysis_result']
                success = vision_result.get('success', False)
                source = vision_result.get('source', 'unknown')
                
                logger.info(f"图片分析完成: {success}")
                logger.info(f"  - 分析来源: {source}")
                
                if success:
                    if source == "docling_picture_description":
                        total_pics = vision_result.get('total_pictures', 0)
                        described_pics = vision_result.get('described_pictures', 0)
                        logger.info(f"  - 图片总数: {total_pics}")
                        logger.info(f"  - 已描述图片: {described_pics}")
                        if vision_result.get('descriptions'):
                            for i, desc in enumerate(vision_result['descriptions'][:2]):  # 只显示前两个描述
                                logger.info(f"  - 描述{i+1}: {desc[:100]}...")
                    elif source in ["independent_vision", "fallback_independent_vision", "fallback_docling_failed"]:
                        if vision_result.get('analysis_result'):
                            analysis = vision_result['analysis_result']
                            logger.info(f"  - 分析结果: {str(analysis)[:200]}...")
                        if vision_result.get('raw_content'):
                            raw = vision_result['raw_content']
                            logger.info(f"  - 原始内容: {raw[:150]}...")
                    elif source == "no_pictures":
                        logger.info(f"  - 消息: {vision_result.get('message', 'N/A')}")
                else:
                    error = vision_result.get('error', 'Unknown error')
                    logger.error(f"  - 错误: {error}")
            except Exception as e:
                logger.error(f"图片分析异常: {e}")
                results["vision_analysis_result"] = {"success": False, "error": str(e), "source": "error"}
        
        # 3. AI文本分析 - 综合OCR文本和视觉分析结果
        if self.ai_api_key:
            try:
                # 收集所有可用的分析内容
                analysis_content = []
                content_sources = []
                
                # 添加OCR文本内容
                if text_content and len(text_content.strip()) > 0:
                    analysis_content.append(f"OCR提取的文本内容：\n{text_content[:2000]}")
                    content_sources.append("OCR文本")
                
                # 添加视觉分析结果
                vision_result = results.get("vision_analysis_result", {})
                if vision_result.get("success"):
                    vision_source = vision_result.get("source", "unknown")
                    
                    if vision_source == "docling_picture_description":
                        # 使用Docling的图片描述
                        descriptions = vision_result.get("descriptions", [])
                        if descriptions:
                            vision_content = "Docling图片描述结果：\n" + "\n".join(descriptions)
                            analysis_content.append(vision_content)
                            content_sources.append("Docling图片描述")
                    
                    elif vision_source in ["independent_vision", "fallback_independent_vision", "fallback_docling_failed"]:
                        # 使用独立视觉分析结果
                        if vision_result.get("raw_content"):
                            vision_content = f"视觉分析结果：\n{vision_result['raw_content'][:1500]}"
                            analysis_content.append(vision_content)
                            content_sources.append("独立视觉分析")
                        elif vision_result.get("analysis_result"):
                            vision_content = f"视觉分析结果：\n{str(vision_result['analysis_result'])[:1500]}"
                            analysis_content.append(vision_content)
                            content_sources.append("独立视觉分析")
                
                # 如果有任何可分析的内容，则进行AI文本分析
                if analysis_content:
                    logger.info(f"开始AI综合分析 - 数据源: {', '.join(content_sources)}")
                    
                    # 构建综合分析提示词 - 使用动态配置
                    combined_content = "\n\n".join(analysis_content)
                    
                    # 尝试使用动态配置的prompt
                    try:
                        # 首先进行文档分类
                        system_prompt, user_prompt = self.config_manager.build_prompt(
                            "document_classification",
                            content=combined_content
                        )
                        
                        if system_prompt and user_prompt:
                            # 使用动态配置的分类prompt
                            classification_result = await self.analyze_text(user_prompt)
                            
                            if classification_result.get("success"):
                                # 解析分类结果
                                try:
                                    classification_content = classification_result.get("raw_content", "")
                                    json_match = re.search(r'\{.*\}', classification_content, re.DOTALL)
                                    if json_match:
                                        classification_data = json.loads(json_match.group())
                                        doc_type = classification_data.get("type", "unknown")
                                        confidence = classification_data.get("confidence", 0.0)
                                        reason = classification_data.get("reason", "")
                                        
                                        logger.info(f"动态分类结果: {doc_type} (置信度: {confidence})")
                                    else:
                                        # 分类失败，使用回退方案
                                        doc_type = "unknown"
                                        confidence = 0.0
                                        reason = "分类解析失败"
                                except json.JSONDecodeError:
                                    doc_type = "unknown"
                                    confidence = 0.0
                                    reason = "分类JSON解析失败"
                            else:
                                doc_type = "unknown"
                                confidence = 0.0
                                reason = "分类API调用失败"
                        else:
                            # 没有配置动态prompt，使用回退方案
                            doc_type = "unknown"
                            confidence = 0.0
                            reason = "未配置动态分类prompt"
                        
                        # 然后进行业务领域分类
                        business_field = "未识别"
                        business_confidence = 0.0
                        business_keywords = []
                        
                        system_prompt_bf, user_prompt_bf = self.config_manager.build_prompt(
                            "business_field_classification",
                            content=combined_content
                        )
                        
                        if system_prompt_bf and user_prompt_bf:
                            business_result = await self.analyze_text(user_prompt_bf)
                            if business_result.get("success"):
                                try:
                                    business_content = business_result.get("raw_content", "")
                                    json_match = re.search(r'\{.*\}', business_content, re.DOTALL)
                                    if json_match:
                                        business_data = json.loads(json_match.group())
                                        business_field = business_data.get("name", "未识别")
                                        business_confidence = business_data.get("confidence", 0.0)
                                        business_keywords = business_data.get("keywords_found", [])
                                        
                                        logger.info(f"动态业务领域分类: {business_field} (置信度: {business_confidence})")
                                except json.JSONDecodeError:
                                    logger.warning("业务领域分类JSON解析失败")
                        else:
                            # 回退到关键词匹配
                            keyword_result = self.config_manager.classify_business_field_by_keywords(combined_content)
                            if keyword_result:
                                business_field = keyword_result[1]
                                business_confidence = keyword_result[2]
                                logger.info(f"关键词业务领域分类: {business_field} (置信度: {business_confidence})")
                        
                        # 构建最终分析结果
                        parsed_result = {
                            "document_type": doc_type,
                            "confidence": confidence,
                            "business_field": business_field,
                            "business_confidence": business_confidence,
                            "classification_reasoning": reason,
                            "keywords_found": business_keywords,
                            "analysis_summary": f"文档类型: {doc_type}, 业务领域: {business_field}",
                            "extracted_entities": {
                                "business_field": business_field,
                                "classification_method": "dynamic_config"
                            }
                        }
                        
                        results["ai_text_analysis"] = {
                            "success": True,
                            "result": parsed_result,
                            "raw_content": f"分类结果: {doc_type}, 业务领域: {business_field}",
                            "data_sources": content_sources,
                            "method": "dynamic_config"
                        }
                        results["final_classification"] = {
                            "type": doc_type,
                            "confidence": confidence,
                            "entities": parsed_result.get("extracted_entities", {}),
                            "business_field": business_field,
                            "summary": parsed_result.get("analysis_summary", ""),
                            "data_sources": content_sources,
                            "method": "dynamic_config"
                        }
                        
                        logger.info(f"AI综合分析完成:")
                        logger.info(f"  - 数据源: {', '.join(content_sources)}")
                        logger.info(f"  - 文档类型: {doc_type}")
                        logger.info(f"  - 置信度: {confidence}")
                        logger.info(f"  - 业务领域: {business_field}")
                        logger.info(f"  - 方法: 动态配置")
                        
                    except Exception as config_error:
                        logger.warning(f"动态配置分析失败，使用回退方案: {config_error}")
                        
                        # 回退到原始硬编码prompt
                        prompt = f"""请分析以下法律文档内容，提取关键信息并以JSON格式回复：

{combined_content}

请基于以上内容（包括OCR文本和视觉分析结果）以JSON格式返回以下信息：
{{
    "document_type": "文档类型 (qualification_certificate/lawyer_certificate/performance/award_certificate/other)",
    "confidence": "置信度 (0.0-1.0)",
    "extracted_entities": {{
        "client_name": "客户名称",
        "project_name": "项目名称", 
        "amount": "金额",
        "date": "日期",
        "law_firm": "律师事务所",
        "lawyer_name": "律师姓名",
        "business_field": "业务领域",
        "institution_name": "机构名称",
        "certificate_type": "证书类型",
        "issuing_authority": "颁发机关"
    }},
    "business_field": "业务领域",
    "analysis_summary": "分析总结",
    "data_sources": {content_sources},
    "classification_reasoning": "分类理由（说明为什么选择这个类型）"
}}

注意文档类型分类标准：
- qualification_certificate: 律师事务所执业许可证、营业执照等机构资质证明文件
- lawyer_certificate: 个人律师执业证书，包含个人律师的姓名、执业证号等
- performance: 法律服务合同、委托协议等业绩相关文档（特别注意破产重整、债务重组等应归类为破产重整业务领域）
- award_certificate: 各种法律行业奖项证书、排名认证等荣誉文件
- other: 不属于以上类别的其他文档

业务领域特别提醒：
- 如果涉及破产、重整、债务重组、债权申报等，业务领域应为"破产重整"
- 如果涉及企业并购、股权转让、资产重组等，业务领域应为"并购重组"
- 请仔细分析文档的核心业务内容"""
                        
                        # 应用学习改进
                        prompt = self.improve_classification_with_learning(prompt)
                        
                        ai_result = await self.analyze_text(prompt)
                        if ai_result.get("success"):
                            try:
                                # 解析AI返回的JSON
                                ai_content = ai_result.get("raw_content", "")
                                if ai_content:
                                    # 尝试提取JSON部分
                                    json_match = re.search(r'\{.*\}', ai_content, re.DOTALL)
                                    if json_match:
                                        parsed_result = json.loads(json_match.group())
                                        results["ai_text_analysis"] = {
                                            "success": True,
                                            "result": parsed_result,
                                            "raw_content": ai_content,
                                            "data_sources": content_sources,
                                            "method": "fallback_hardcoded"
                                        }
                                        results["final_classification"] = {
                                            "type": parsed_result.get("document_type", "unknown"),
                                            "confidence": parsed_result.get("confidence", 0.0),
                                            "entities": parsed_result.get("extracted_entities", {}),
                                            "business_field": parsed_result.get("business_field", ""),
                                            "summary": parsed_result.get("analysis_summary", ""),
                                            "data_sources": content_sources,
                                            "method": "fallback_hardcoded"
                                        }
                                        
                                        logger.info(f"AI综合分析完成 (回退方案):")
                                        logger.info(f"  - 数据源: {', '.join(content_sources)}")
                                        logger.info(f"  - 文档类型: {parsed_result.get('document_type', 'unknown')}")
                                        logger.info(f"  - 置信度: {parsed_result.get('confidence', 0.0)}")
                                        logger.info(f"  - 业务领域: {parsed_result.get('business_field', '未识别')}")
                                        
                                        # 记录详细的分析内容供调试
                                        logger.debug(f"  - 综合分析内容: {combined_content[:500]}...")
                                    else:
                                        results["ai_text_analysis"] = {"success": False, "error": "AI返回结果格式错误"}
                                        results["final_classification"] = {"type": "unknown", "confidence": 0.0}
                                        logger.error("AI返回结果格式错误，无法解析JSON")
                                else:
                                    results["ai_text_analysis"] = {"success": False, "error": "AI返回内容为空"}
                                    results["final_classification"] = {"type": "unknown", "confidence": 0.0}
                                    logger.error("AI返回内容为空")
                            except json.JSONDecodeError as e:
                                logger.error(f"AI返回结果JSON解析失败: {e}")
                                results["ai_text_analysis"] = {"success": False, "error": f"JSON解析失败: {str(e)}"}
                                results["final_classification"] = {"type": "unknown", "confidence": 0.0}
                        else:
                            logger.error(f"AI分析失败: {ai_result.get('error')}")
                            results["ai_text_analysis"] = {"success": False, "error": ai_result.get("error")}
                            results["final_classification"] = {"type": "unknown", "confidence": 0.0}
                else:
                    # 没有任何可分析的内容
                    logger.warning("跳过AI文本分析 - 既没有OCR文本也没有视觉分析结果")
                    results["ai_text_analysis"] = {
                        "success": False, 
                        "error": "没有可分析的内容",
                        "details": {
                            "has_ocr_text": bool(text_content) and len(text_content.strip()) > 0,
                            "has_vision_result": bool(vision_result.get("success")),
                            "vision_source": vision_result.get("source", "none")
                        }
                    }
                    results["final_classification"] = {"type": "unknown", "confidence": 0.0}
                    
            except Exception as e:
                logger.error(f"AI分析异常: {e}")
                results["ai_text_analysis"] = {"success": False, "error": str(e)}
                results["final_classification"] = {"type": "unknown", "confidence": 0.0}
        else:
            # 没有配置AI API密钥
            logger.warning("跳过AI文本分析 - 未配置AI API密钥")
            results["ai_text_analysis"] = {
                "success": False, 
                "error": "未配置AI API密钥",
                "details": {
                    "has_api_key": False
                }
            }
            results["final_classification"] = {"type": "unknown", "confidence": 0.0}
        
        return {
            "success": True,
            "results": results,
            "file_path": file_path
        }
    
    def _is_image_or_pdf(self, file_path: str) -> bool:
        """判断是否为图片或PDF文件"""
        ext = os.path.splitext(file_path)[1].lower()
        return ext in ['.pdf', '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff']

    def _extract_lawyer_certificate_info(self, ai_result: Dict[str, Any]) -> Dict[str, str]:
        """从AI分析结果中提取律师证信息"""
        try:
            extracted_info = {}
            
            if not ai_result or not ai_result.get("results"):
                return extracted_info
            
            # 获取文本内容
            text_content = ""
            if ai_result.get("results", {}).get("text_extraction_result", {}).get("text"):
                text_content = ai_result["results"]["text_extraction_result"]["text"]
            elif ai_result.get("results", {}).get("text_extraction_result", {}).get("extracted_content", {}).get("text"):
                text_content = ai_result["results"]["text_extraction_result"]["extracted_content"]["text"]
            
            if not text_content:
                return extracted_info
            
            # 使用正则表达式提取关键信息
            import re
            
            # 提取律师姓名
            name_patterns = [
                r'姓\s*名[：:]\s*([^\s\n]+)',
                r'律师姓名[：:]\s*([^\s\n]+)',
                r'执业者[：:]\s*([^\s\n]+)',
                r'持有人[：:]\s*([^\s\n]+)'
            ]
            
            for pattern in name_patterns:
                match = re.search(pattern, text_content)
                if match:
                    extracted_info['lawyer_name'] = match.group(1).strip()
                    break
            
            # 提取执业证号
            cert_patterns = [
                r'执业证号[：:]\s*([^\s\n]+)',
                r'证书编号[：:]\s*([^\s\n]+)',
                r'执业编号[：:]\s*([^\s\n]+)',
                r'证号[：:]\s*([^\s\n]+)'
            ]
            
            for pattern in cert_patterns:
                match = re.search(pattern, text_content)
                if match:
                    extracted_info['certificate_number'] = match.group(1).strip()
                    break
            
            # 提取律师事务所
            firm_patterns = [
                r'律师事务所[：:]\s*([^\s\n]+)',
                r'所在机构[：:]\s*([^\s\n]+)',
                r'执业机构[：:]\s*([^\s\n]+)',
                r'工作单位[：:]\s*([^\s\n]+)'
            ]
            
            for pattern in firm_patterns:
                match = re.search(pattern, text_content)
                if match:
                    extracted_info['law_firm'] = match.group(1).strip()
                    break
            
            # 提取颁发机构
            issuer_patterns = [
                r'颁发机构[：:]\s*([^\s\n]+)',
                r'发证机关[：:]\s*([^\s\n]+)',
                r'司法局',
                r'司法厅',
                r'司法部'
            ]
            
            for pattern in issuer_patterns:
                match = re.search(pattern, text_content)
                if match:
                    extracted_info['issuing_authority'] = match.group(0).strip()
                    break
            
            # 提取发证日期
            date_patterns = [
                r'发证日期[：:]\s*(\d{4}[年-]\d{1,2}[月-]\d{1,2})',
                r'颁发日期[：:]\s*(\d{4}[年-]\d{1,2}[月-]\d{1,2})',
                r'签发日期[：:]\s*(\d{4}[年-]\d{1,2}[月-]\d{1,2})'
            ]
            
            for pattern in date_patterns:
                match = re.search(pattern, text_content)
                if match:
                    extracted_info['issue_date'] = match.group(1).strip()
                    break
            
            logger.info(f"律师证信息提取完成: {extracted_info}")
            return extracted_info
            
        except Exception as e:
            logger.error(f"提取律师证信息失败: {str(e)}")
            return {}

    def _extract_lawyer_entities(self, text_content: str) -> Dict[str, str]:
        """提取律师证关键实体"""
        try:
            import re
            entities = {}
            
            # 提取持有人姓名
            name_patterns = [
                r'姓\s*名[：:]\s*([^\s\n]+)',
                r'律师姓名[：:]\s*([^\s\n]+)',
                r'执业者[：:]\s*([^\s\n]+)',
                r'持有人[：:]\s*([^\s\n]+)'
            ]
            
            for pattern in name_patterns:
                match = re.search(pattern, text_content)
                if match:
                    entities['holder_name'] = match.group(1).strip()
                    break
            
            # 提取证书编号
            cert_patterns = [
                r'执业证号[：:]\s*([^\s\n]+)',
                r'证书编号[：:]\s*([^\s\n]+)',
                r'执业编号[：:]\s*([^\s\n]+)'
            ]
            
            for pattern in cert_patterns:
                match = re.search(pattern, text_content)
                if match:
                    entities['certificate_number'] = match.group(1).strip()
                    break
            
            # 提取律师事务所
            firm_patterns = [
                r'律师事务所[：:]\s*([^\s\n]+)',
                r'执业机构[：:]\s*([^\s\n]+)',
                r'所在机构[：:]\s*([^\s\n]+)'
            ]
            
            for pattern in firm_patterns:
                match = re.search(pattern, text_content)
                if match:
                    entities['law_firm'] = match.group(1).strip()
                    break
            
            # 提取颁发机构
            if re.search(r'司法局|司法厅|司法部', text_content):
                entities['issuer'] = re.search(r'[^\s]*司法[局厅部][^\s]*', text_content).group(0)
            
            return entities
            
        except Exception as e:
            logger.error(f"提取律师证实体失败: {str(e)}")
            return {}

    def _extract_performance_entities(self, text_content: str) -> Dict[str, str]:
        """提取业绩合同关键实体"""
        try:
            import re
            entities = {}
            
            # 提取项目名称
            project_patterns = [
                r'项目名称[：:]\s*([^\s\n]+)',
                r'案件名称[：:]\s*([^\s\n]+)',
                r'合同名称[：:]\s*([^\s\n]+)',
                r'委托事项[：:]\s*([^\s\n]+)'
            ]
            
            for pattern in project_patterns:
                match = re.search(pattern, text_content)
                if match:
                    entities['project_name'] = match.group(1).strip()
                    break
            
            # 提取客户名称
            client_patterns = [
                r'甲方[：:]\s*([^\s\n]+)',
                r'委托方[：:]\s*([^\s\n]+)',
                r'客户[：:]\s*([^\s\n]+)',
                r'委托人[：:]\s*([^\s\n]+)'
            ]
            
            for pattern in client_patterns:
                match = re.search(pattern, text_content)
                if match:
                    entities['client_name'] = match.group(1).strip()
                    break
            
            # 提取金额
            amount_patterns = [
                r'金额[：:]\s*([0-9,，.万元]+)',
                r'费用[：:]\s*([0-9,，.万元]+)',
                r'律师费[：:]\s*([0-9,，.万元]+)'
            ]
            
            for pattern in amount_patterns:
                match = re.search(pattern, text_content)
                if match:
                    entities['amount'] = match.group(1).strip()
                    break
            
            return entities
            
        except Exception as e:
            logger.error(f"提取业绩实体失败: {str(e)}")
            return {}

    def _extract_award_entities(self, text_content: str) -> Dict[str, str]:
        """提取奖项关键实体"""
        try:
            import re
            entities = {}
            
            # 提取奖项名称
            award_patterns = [
                r'奖项[：:]\s*([^\s\n]+)',
                r'荣誉[：:]\s*([^\s\n]+)',
                r'表彰[：:]\s*([^\s\n]+)'
            ]
            
            for pattern in award_patterns:
                match = re.search(pattern, text_content)
                if match:
                    entities['award_name'] = match.group(1).strip()
                    break
            
            # 提取颁发机构
            issuer_patterns = [
                r'颁发机构[：:]\s*([^\s\n]+)',
                r'主办方[：:]\s*([^\s\n]+)',
                r'组织方[：:]\s*([^\s\n]+)'
            ]
            
            for pattern in issuer_patterns:
                match = re.search(pattern, text_content)
                if match:
                    entities['issuer'] = match.group(1).strip()
                    break
            
            return entities
            
        except Exception as e:
            logger.error(f"提取奖项实体失败: {str(e)}")
            return {}

    async def _integrate_analysis_results(self, text_content: str, ai_text_analysis: Dict, vision_analysis: Dict, file_path: str) -> Dict[str, Any]:
        """整合OCR、AI文本分析和视觉分析的结果"""
        try:
            # 初始化结果
            integrated_result = {
                "category": "other",
                "confidence": 0.0,
                "description": "未知文档类型",
                "key_entities": {},
                "analysis_sources": []
            }
            
            confidences = []
            categories = []
            
            # 1. 处理AI文本分析结果
            if ai_text_analysis:
                if ai_text_analysis.get("category"):
                    categories.append(ai_text_analysis["category"])
                if ai_text_analysis.get("confidence"):
                    confidences.append(ai_text_analysis["confidence"])
                if ai_text_analysis.get("key_entities"):
                    integrated_result["key_entities"].update(ai_text_analysis["key_entities"])
                if ai_text_analysis.get("description"):
                    integrated_result["description"] = ai_text_analysis["description"]
                integrated_result["analysis_sources"].append("ai_text")
            
            # 2. 处理视觉分析结果
            if vision_analysis:
                if vision_analysis.get("category"):
                    categories.append(vision_analysis["category"])
                if vision_analysis.get("confidence"):
                    confidences.append(vision_analysis["confidence"])
                if vision_analysis.get("key_entities"):
                    # 视觉分析的实体优先级更高
                    for key, value in vision_analysis["key_entities"].items():
                        if value and value != "unknown":
                            integrated_result["key_entities"][key] = value
                if vision_analysis.get("description") and not integrated_result.get("description"):
                    integrated_result["description"] = vision_analysis["description"]
                integrated_result["analysis_sources"].append("vision")
            
            # 3. 使用基础关键词分析作为兜底
            keyword_analysis = await self._classify_content(text_content, file_path)
            if keyword_analysis:
                categories.append(keyword_analysis["category"])
                confidences.append(keyword_analysis["confidence"])
                integrated_result["analysis_sources"].append("keyword")
            
            # 4. 确定最终分类
            if categories:
                # 选择最常见的分类
                category_counts = {}
                for cat in categories:
                    category_counts[cat] = category_counts.get(cat, 0) + 1
                integrated_result["category"] = max(category_counts, key=category_counts.get)
            
            # 5. 计算综合置信度
            if confidences:
                integrated_result["confidence"] = sum(confidences) / len(confidences)
            
            # 6. 根据最终分类补充信息
            if integrated_result["category"] == "lawyer_certificate":
                # 补充律师证特有信息
                if not integrated_result["key_entities"].get("holder_name"):
                    # 使用正则表达式从文本中提取
                    lawyer_entities = self._extract_lawyer_entities(text_content)
                    integrated_result["key_entities"].update(lawyer_entities)
                
                # 增强描述
                holder_name = integrated_result["key_entities"].get("holder_name")
                if holder_name and integrated_result["description"] == "未知文档类型":
                    integrated_result["description"] = f"律师执业证书 - {holder_name}"
                
                # 检查职位
                if "合伙人" in text_content:
                    integrated_result["key_entities"]["position"] = "合伙人"
                    if holder_name:
                        integrated_result["description"] = f"律师执业证书 - {holder_name}（合伙人）"
            
            elif integrated_result["category"] == "performance_contract":
                # 补充业绩合同信息
                performance_info = self._extract_performance_entities(text_content)
                integrated_result["performance_info"] = performance_info
                if performance_info.get("project_name") and integrated_result["description"] == "未知文档类型":
                    integrated_result["description"] = f"法律服务合同 - {performance_info['project_name']}"
            
            elif integrated_result["category"] == "award_certificate":
                # 补充奖项信息
                award_info = self._extract_award_entities(text_content)
                integrated_result["award_info"] = award_info
                if award_info.get("award_name") and integrated_result["description"] == "未知文档类型":
                    integrated_result["description"] = f"获奖证书 - {award_info['award_name']}"
            
            # 7. 最终置信度调整
            source_count = len(integrated_result["analysis_sources"])
            if source_count >= 2:
                integrated_result["confidence"] = min(0.95, integrated_result["confidence"] + 0.1)
            
            return integrated_result
            
        except Exception as e:
            logger.error(f"整合分析结果失败: {str(e)}")
            # 返回基础关键词分析结果
            return await self._classify_content(text_content, file_path)

    async def _classify_content(self, text_content: str, file_path: str) -> Dict[str, Any]:
        """基于内容分类文档 - 使用动态配置"""
        try:
            # 获取文档类型配置
            doc_types = self.config_manager.get_document_types()
            
            if not doc_types:
                # 回退到硬编码分类
                return self._classify_content_fallback(text_content, file_path)
            
            # 计算每种文档类型的匹配分数
            type_scores = {}
            text_lower = text_content.lower()
            
            for type_code, type_info in doc_types.items():
                keywords = type_info.get("keywords", [])
                matched_keywords = []
                
                for keyword in keywords:
                    if keyword.lower() in text_lower:
                        matched_keywords.append(keyword)
                
                # 计算匹配分数
                if keywords:
                    score = len(matched_keywords) / len(keywords)
                    type_scores[type_code] = {
                        "score": score,
                        "matched_keywords": matched_keywords,
                        "name": type_info.get("name", ""),
                        "confidence_threshold": type_info.get("confidence_threshold", 0.7)
                    }
            
            # 找到最佳匹配
            if not type_scores:
                return {
                    "category": "other",
                    "confidence": 0.3,
                    "description": "无法确定文档类型",
                    "keyword_scores": {}
                }
            
            best_type = max(type_scores.keys(), key=lambda k: type_scores[k]["score"])
            best_info = type_scores[best_type]
            
            # 计算置信度
            base_score = best_info["score"]
            if base_score == 0:
                category = "other"
                confidence = 0.3
                description = "无法确定文档类型"
            else:
                category = best_type
                # 基于匹配分数和阈值计算置信度
                threshold = best_info["confidence_threshold"]
                confidence = min(0.95, threshold + base_score * (1 - threshold))
                description = best_info["name"]
            
            return {
                "category": category,
                "confidence": confidence,
                "description": description,
                "keyword_scores": {k: v["score"] for k, v in type_scores.items()},
                "matched_keywords": best_info.get("matched_keywords", []),
                "classification_method": "dynamic_config"
            }
            
        except Exception as e:
            logger.error(f"动态配置分类失败: {str(e)}")
            # 回退到硬编码分类
            return self._classify_content_fallback(text_content, file_path)
    
    def _classify_content_fallback(self, text_content: str, file_path: str) -> Dict[str, Any]:
        """回退的硬编码分类方法"""
        try:
            # 律师证关键词
            lawyer_cert_keywords = ['执业证', '律师执业', '执业律师', '执业证书', '律师证', '执业编号', '执业证号']
            
            # 业绩合同关键词
            performance_keywords = ['合同', '委托书', '协议书', '法律服务', '甲方', '乙方', '委托方', '受托方']
            
            # 获奖证书关键词
            award_keywords = ['获奖', '奖项', '证书', '表彰', '荣誉', '颁发', '奖励', '评选']
            
            # 资质证照关键词（新增）
            qualification_keywords = ['执业许可证', '营业执照', '律师事务所', '机构证照', '资质证书']
            
            # 计算关键词匹配度
            lawyer_cert_score = sum(1 for keyword in lawyer_cert_keywords if keyword in text_content)
            performance_score = sum(1 for keyword in performance_keywords if keyword in text_content)
            award_score = sum(1 for keyword in award_keywords if keyword in text_content)
            qualification_score = sum(1 for keyword in qualification_keywords if keyword in text_content)
            
            # 确定分类
            scores = {
                "lawyer_certificate": lawyer_cert_score,
                "performance": performance_score,
                "award": award_score,
                "qualification_certificate": qualification_score
            }
            
            max_score = max(scores.values())
            
            if max_score == 0:
                category = "other"
                confidence = 0.3
                description = "无法确定文档类型"
            else:
                # 找到得分最高的类型
                category = max(scores.keys(), key=lambda k: scores[k])
                
                if category == "lawyer_certificate":
                    confidence = min(0.9, 0.5 + lawyer_cert_score * 0.1)
                    description = "律师执业证书"
                elif category == "performance":
                    confidence = min(0.8, 0.4 + performance_score * 0.1)
                    description = "法律服务合同/委托书"
                elif category == "award":
                    confidence = min(0.8, 0.4 + award_score * 0.1)
                    description = "获奖证书/表彰文件"
                elif category == "qualification_certificate":
                    confidence = min(0.85, 0.5 + qualification_score * 0.1)
                    description = "资质证照/机构许可证"
                else:
                    confidence = 0.3
                    description = "其他文档类型"
            
            return {
                "category": category,
                "confidence": confidence,
                "description": description,
                "keyword_scores": scores,
                "classification_method": "fallback_hardcoded"
            }
            
        except Exception as e:
            logger.error(f"硬编码分类失败: {str(e)}")
            return {
                "category": "other",
                "confidence": 0.1,
                "description": "分类失败",
                "error": str(e)
            }

    def _get_ai_api_key(self) -> str:
        """获取AI API密钥"""
        if self.ai_provider == "openai":
            return self._get_setting_value("openai_api_key", os.getenv("OPENAI_API_KEY", ""))
        elif self.ai_provider == "azure":
            return self._get_setting_value("azure_openai_api_key", os.getenv("AZURE_OPENAI_API_KEY", ""))
        elif self.ai_provider == "anthropic":
            return self._get_setting_value("anthropic_api_key", os.getenv("ANTHROPIC_API_KEY", ""))
        elif self.ai_provider == "custom":
            # 优先使用通用的ai_api_key，然后回退到custom_ai_api_key
            api_key = self._get_setting_value("ai_api_key", "")
            if not api_key:
                api_key = self._get_setting_value("custom_ai_api_key", os.getenv("CUSTOM_AI_API_KEY", ""))
            return api_key
        else:
            return ""

    def _get_ai_base_url(self) -> str:
        """获取AI API基础URL"""
        if self.ai_provider == "openai":
            return self._get_setting_value("openai_base_url", os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"))
        elif self.ai_provider == "azure":
            endpoint = self._get_setting_value("azure_openai_endpoint", os.getenv("AZURE_OPENAI_ENDPOINT", ""))
            return endpoint.rstrip("/") + "/openai/deployments" if endpoint else ""
        elif self.ai_provider == "custom":
            # 优先使用通用的ai_base_url，然后回退到custom_ai_base_url
            base_url = self._get_setting_value("ai_base_url", "")
            if not base_url:
                base_url = self._get_setting_value("custom_ai_base_url", os.getenv("CUSTOM_AI_BASE_URL", ""))
            return base_url
        else:
            return ""

    def _get_ai_model(self) -> str:
        """获取AI模型名称"""
        if self.ai_provider == "openai":
            return self._get_setting_value("openai_model", os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"))
        elif self.ai_provider == "azure":
            return self._get_setting_value("azure_openai_deployment_name", os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", ""))
        elif self.ai_provider == "anthropic":
            return self._get_setting_value("anthropic_model", os.getenv("ANTHROPIC_MODEL", "claude-3-sonnet-20240229"))
        elif self.ai_provider == "custom":
            # 优先使用通用的ai_text_model，然后回退到custom_ai_model
            model = self._get_setting_value("ai_text_model", "")
            if not model:
                model = self._get_setting_value("custom_ai_model", os.getenv("CUSTOM_AI_MODEL", "gpt-3.5-turbo"))
            return model
        else:
            return "gpt-3.5-turbo"

    def _get_ai_vision_model(self) -> str:
        """获取AI视觉模型名称"""
        # 首先检查是否有独立的视觉服务配置
        vision_provider = self._get_setting_value("vision_provider", "")
        if vision_provider:
            if vision_provider == "ollama":
                return self._get_setting_value("ai_vision_model", "llava:latest")
            elif vision_provider == "openai":
                return self._get_setting_value("ai_vision_model", "gpt-4-vision-preview")
            elif vision_provider == "azure":
                return self._get_setting_value("ai_vision_model", "")
            elif vision_provider == "custom":
                return self._get_setting_value("ai_vision_model", "gpt-4-vision-preview")
        
        # 回退到原始逻辑（基于主AI provider）
        if self.ai_provider == "openai":
            return self._get_setting_value("openai_vision_model", os.getenv("OPENAI_VISION_MODEL", "gpt-4-vision-preview"))
        elif self.ai_provider == "azure":
            return self._get_setting_value("azure_openai_vision_deployment_name", os.getenv("AZURE_OPENAI_VISION_DEPLOYMENT_NAME", ""))
        elif self.ai_provider == "custom":
            # 优先使用通用的ai_vision_model，然后回退到custom_ai_vision_model
            vision_model = self._get_setting_value("ai_vision_model", "")
            if not vision_model:
                vision_model = self._get_setting_value("custom_ai_vision_model", os.getenv("CUSTOM_AI_VISION_MODEL", "gpt-4-vision-preview"))
            return vision_model
        else:
            return "gpt-4-vision-preview"

    async def chat_with_tools(
        self, 
        user_message: str, 
        system_prompt: str = "", 
        tools: List[Dict] = None, 
        tool_executor=None
    ) -> Dict[str, Any]:
        """调用AI进行对话，支持工具调用"""
        try:
            if not self.enable_ai or not self.ai_api_key:
                return {
                    "success": False,
                    "error": "AI服务未配置或未启用",
                    "response": "抱歉，AI服务当前不可用。请联系管理员配置AI服务。"
                }
            
            # 构建消息
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": user_message})
            
            # 调用AI API
            ai_response = await self._call_ai_api(
                messages=messages,
                model=self.ai_model,
                tools=tools
            )
            
            if not ai_response.get("success"):
                return ai_response
            
            response_data = ai_response["response"]
            ai_message = response_data.get("choices", [{}])[0].get("message", {})
            
            # 处理工具调用
            tools_used = []
            if ai_message.get("tool_calls") and tool_executor:
                for tool_call in ai_message["tool_calls"]:
                    try:
                        tool_name = tool_call["function"]["name"]
                        tool_args = json.loads(tool_call["function"]["arguments"])
                        
                        # 执行工具
                        if tool_name.startswith('mcp_') and self.mcp_client.is_available():
                            # 调用MCP工具
                            mcp_tool_name = tool_name[4:]
                            tool_result = await self.mcp_client.call_tool(mcp_tool_name, **tool_args)
                        else:
                            # 调用本地工具
                            tool_result = await tool_executor(tool_name, tool_args)
                        tools_used.append({
                            "tool_name": tool_name,
                            "arguments": tool_args,
                            "result": tool_result
                        })
                        
                        # 将工具结果加入对话
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call["id"],
                            "content": json.dumps(tool_result, ensure_ascii=False)
                        })
                        
                    except Exception as tool_err:
                        logger.warning(f"工具调用失败: {tool_err}")
                        tools_used.append({
                            "tool_name": tool_call["function"]["name"],
                            "error": str(tool_err)
                        })
                
                # 如果有工具调用，再次调用AI获取最终回复
                if tools_used:
                    final_response = await self._call_ai_api(
                        messages=messages,
                        model=self.ai_model
                    )
                    if final_response.get("success"):
                        final_message = final_response["response"].get("choices", [{}])[0].get("message", {})
                        ai_message = final_message
            
            return {
                "success": True,
                "response": ai_message.get("content", "抱歉，我无法理解您的请求。"),
                "tools_used": tools_used,
                "model": self.ai_model,
                "provider": self.ai_provider
            }
                    
        except Exception as e:
            logger.error(f"AI对话失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "response": "抱歉，AI服务暂时不可用。"
            }

    async def analyze_text(self, prompt: str, model: str = None) -> Dict[str, Any]:
        """调用AI进行文本分析"""
        try:
            if not self.enable_ai or not self.ai_api_key:
                return {
                    "success": False,
                    "error": "AI服务未配置或未启用"
                }
            
            use_model = model or self.ai_model
            
            messages = [
                {
                    "role": "system",
                    "content": "你是一个专业的法律文档分析助手。请仔细分析用户提供的内容，并按照要求提取相关信息。回复必须是JSON格式。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
            ai_response = await self._call_ai_api(
                messages=messages,
                model=use_model
            )
            
            if not ai_response.get("success"):
                return ai_response
            
            response_data = ai_response["response"]
            ai_message = response_data.get("choices", [{}])[0].get("message", {})
            content = ai_message.get("content", "")
            
            # 尝试解析JSON回复
            try:
                result = json.loads(content)
                return {
                    "success": True,
                    "result": result,
                    "raw_content": content,
                    "model": use_model,
                    "provider": self.ai_provider
                }
            except json.JSONDecodeError:
                # 如果不是JSON，返回原始内容
                return {
                    "success": True,
                    "result": {"content": content},
                    "raw_content": content,
                    "model": use_model,
                    "provider": self.ai_provider
                }
            
        except Exception as e:
            logger.error(f"AI文本分析失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def analyze_vision(self, image_path: str, prompt: str) -> Dict[str, Any]:
        """调用AI进行图像分析"""
        try:
            # 检查是否有独立的视觉服务配置
            vision_provider = self._get_setting_value("vision_provider", "")
            
            if vision_provider:
                # 使用独立的视觉服务配置
                vision_base_url = self._get_setting_value("vision_base_url", "")
                vision_api_key = self._get_setting_value("vision_api_key", "")
                
                # 如果没有设置视觉专用的API密钥，使用主AI的API密钥
                if not vision_api_key:
                    vision_api_key = self.ai_api_key
                
                # 如果没有设置视觉专用的base_url，使用主AI的base_url
                if not vision_base_url:
                    vision_base_url = self.ai_base_url
                
                logger.info(f"使用独立视觉服务: provider={vision_provider}, model={self.ai_vision_model}, url={vision_base_url}")
            else:
                # 使用主AI服务的配置
                vision_base_url = self.ai_base_url
                vision_api_key = self.ai_api_key
                vision_provider = self.ai_provider
                logger.info(f"使用主AI服务进行视觉分析: provider={vision_provider}, model={self.ai_vision_model}")
            
            if not vision_api_key and vision_provider != "ollama":
                return {
                    "success": False,
                    "error": "视觉分析服务未配置API密钥"
                }
            
            # 检查文件类型，如果是PDF需要转换为图片
            file_ext = os.path.splitext(image_path)[1].lower()
            actual_image_path = image_path
            
            if file_ext == '.pdf':
                try:
                    # 将PDF转换为图片
                    import fitz  # PyMuPDF
                    import tempfile
                    
                    doc = fitz.open(image_path)
                    page = doc.load_page(0)  # 只分析第一页
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 提高分辨率
                    
                    # 创建临时图片文件
                    temp_dir = tempfile.gettempdir()
                    temp_image_path = os.path.join(temp_dir, f"temp_vision_{os.getpid()}_{hash(image_path)}.png")
                    pix.save(temp_image_path)
                    
                    actual_image_path = temp_image_path
                    doc.close()
                    
                    logger.info(f"PDF转换为图片成功: {temp_image_path}")
                    
                except Exception as e:
                    logger.error(f"PDF转图片失败: {e}")
                    return {
                        "success": False,
                        "error": f"PDF转图片失败: {e}"
                    }
            
            elif file_ext not in ['.jpg', '.jpeg', '.png', '.bmp', '.gif']:
                return {
                    "success": False,
                    "error": f"不支持的图片格式: {file_ext}"
                }
            
            # 读取图像并转换为base64
            import base64
            with open(actual_image_path, "rb") as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')
            
            # 清理临时文件
            if file_ext == '.pdf' and actual_image_path != image_path:
                try:
                    os.remove(actual_image_path)
                except:
                    pass
            
            messages = [
                {
                    "role": "system",
                    "content": "你是一个专业的法律文档图像分析助手。请仔细分析图像内容，并按照要求提取相关信息。"
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_data}"
                            }
                        }
                    ]
                }
            ]
            
            # 构建请求数据
            request_data = {
                "model": self.ai_vision_model,
                "messages": messages,
                "max_tokens": 4000,
                "temperature": 0.1
            }
            
            # 构建请求头
            headers = {
                "Content-Type": "application/json"
            }
            
            # 根据视觉服务提供商设置认证和URL
            if vision_provider == "ollama":
                # Ollama通常不需要API密钥
                url = f"{vision_base_url}/chat/completions"
            elif vision_provider in ["openai", "custom"]:
                headers["Authorization"] = f"Bearer {vision_api_key}"
                url = f"{vision_base_url}/chat/completions"
            elif vision_provider == "azure":
                headers["api-key"] = vision_api_key
                url = f"{vision_base_url}/{self.ai_vision_model}/chat/completions?api-version=2024-02-01"
            else:
                return {
                    "success": False,
                    "error": f"不支持的视觉服务提供商: {vision_provider}"
                }
            
            # 发送请求 - 增加超时时间为600秒（10分钟）
            timeout = aiohttp.ClientTimeout(total=600)  # 增加到10分钟
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, json=request_data, headers=headers) as response:
                    if response.status == 200:
                        response_data = await response.json()
                        ai_message = response_data.get("choices", [{}])[0].get("message", {})
                        content = ai_message.get("content", "")
                        
                        logger.info(f"视觉分析成功: {len(content)} 字符")
                        
                        return {
                            "success": True,
                            "result": content,
                            "raw_content": content,
                            "model": self.ai_vision_model,
                            "provider": vision_provider
                        }
                    else:
                        error_text = await response.text()
                        logger.error(f"视觉分析API调用失败: {response.status} - {error_text}")
                        return {
                            "success": False,
                            "error": f"视觉分析API调用失败: {response.status}",
                            "details": error_text
                        }
            
        except asyncio.TimeoutError:
            logger.error(f"视觉分析超时: 处理时间超过180秒")
            return {
                "success": False,
                "error": "视觉分析超时: 处理时间超过180秒"
            }
        except Exception as e:
            logger.error(f"AI图像分析失败: {str(e)}")
            import traceback
            logger.error(f"AI图像分析异常详情: {traceback.format_exc()}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _call_ai_api(
        self, 
        messages: List[Dict], 
        model: str, 
        tools: List[Dict] = None,
        max_tokens: int = 4000,
        temperature: float = 0.1
    ) -> Dict[str, Any]:
        """调用AI API的底层方法"""
        try:
            # 构建请求数据
            request_data = {
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature
            }
            
            if tools:
                request_data["tools"] = tools
                request_data["tool_choice"] = "auto"
            
            # 构建请求头
            headers = {
                "Content-Type": "application/json"
            }
            
            # 根据提供商设置认证头
            if self.ai_provider == "openai":
                headers["Authorization"] = f"Bearer {self.ai_api_key}"
                url = f"{self.ai_base_url}/chat/completions"
            elif self.ai_provider == "azure":
                headers["api-key"] = self.ai_api_key
                url = f"{self.ai_base_url}/{model}/chat/completions?api-version=2024-02-01"
            elif self.ai_provider == "anthropic":
                headers["x-api-key"] = self.ai_api_key
                headers["anthropic-version"] = "2023-06-01"
                url = f"https://api.anthropic.com/v1/messages"
                # Anthropic API格式不同，需要转换
                request_data = self._convert_to_anthropic_format(request_data)
            elif self.ai_provider == "custom":
                headers["Authorization"] = f"Bearer {self.ai_api_key}"
                url = f"{self.ai_base_url}/chat/completions"
            else:
                return {
                    "success": False,
                    "error": f"不支持的AI提供商: {self.ai_provider}"
                }
            
            # 发送请求
            timeout = aiohttp.ClientTimeout(total=60)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, json=request_data, headers=headers) as response:
                    if response.status == 200:
                        response_data = await response.json()
                        return {
                            "success": True,
                            "response": response_data
                        }
                    else:
                        error_text = await response.text()
                        logger.error(f"AI API调用失败: {response.status} - {error_text}")
                        return {
                            "success": False,
                            "error": f"AI API调用失败: {response.status}",
                            "details": error_text
                        }
                        
        except Exception as e:
            logger.error(f"AI API调用异常: {str(e)}")
            import traceback
            logger.error(f"AI API调用异常详情: {traceback.format_exc()}")
            return {
                "success": False,
                "error": str(e)
            }

    def _convert_to_anthropic_format(self, openai_data: Dict) -> Dict:
        """将OpenAI格式转换为Anthropic格式"""
        # Anthropic API格式转换逻辑
        messages = []
        system_message = ""
        
        for msg in openai_data["messages"]:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                messages.append(msg)
        
        result = {
            "model": openai_data["model"],
            "max_tokens": openai_data.get("max_tokens", 4000),
            "messages": messages
        }
        
        if system_message:
            result["system"] = system_message
        
        return result

    def _load_business_fields(self) -> list:
        """从配置管理器加载业务领域列表"""
        try:
            fields = config_manager.get_business_fields()
            business_fields = [field.get("name") for field in fields if field.get("is_active", True)]
            
            # 如果配置中没有业务领域，使用默认值
            if not business_fields:
                business_fields = [
                    "并购重组", "资本市场", "银行金融", "知识产权", "争议解决", 
                    "合规监管", "房地产", "劳动法", "税务", "能源矿产"
                ]
                logger.info("使用默认业务领域列表")
            else:
                logger.info(f"从配置管理器加载了 {len(business_fields)} 个业务领域")
            
            return business_fields
            
        except Exception as e:
            logger.warning(f"加载业务领域失败，使用默认值: {str(e)}")
            return [
                "并购重组", "资本市场", "银行金融", "知识产权", "争议解决", 
                "合规监管", "房地产", "劳动法", "税务", "能源矿产"
            ]

    async def extract_text_with_docling(self, file_path: str) -> Dict[str, Any]:
        """使用DoclingService提取文本"""
        try:
            if not self.docling_service:
                return {
                    "success": False,
                    "error": "DoclingService未就绪"
                }
            
            if not os.path.exists(file_path):
                return {
                    "success": False,
                    "error": "文件不存在"
                }
            
            # 使用统一的DoclingService
            result = await self.docling_service.convert_document(file_path)
            
            if result.get("success"):
                return {
                    "success": True,
                    "text_content": result.get("text", ""),
                    "document_info": result.get("metadata", {})
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error", "DoclingService转换失败")
                }
            
        except Exception as e:
            logger.error(f"DoclingService文本提取失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def extract_document_tags(self, file_path: str, existing_tags: List[str] = None) -> Dict[str, Any]:
        """提取文档标签"""
        try:
            if existing_tags is None:
                existing_tags = []
            
            # 使用智能文档分析获取文本内容
            analysis_result = await self.smart_document_analysis(file_path, enable_vision=False, enable_ocr=True)
            
            if not analysis_result.get("success"):
                return {
                    "success": False,
                    "error": "无法提取文档内容"
                }
            
            text_content = analysis_result.get("results", {}).get("text_extraction_result", {}).get("text", "")
            
            # 基于内容提取标签
            suggested_tags = await self._extract_tags_from_content(text_content)
            
            # 合并现有标签和建议标签
            all_tags = list(set(existing_tags + suggested_tags))
            
            return {
                "success": True,
                "suggested_tags": suggested_tags,
                "all_tags": all_tags,
                "existing_tags": existing_tags
            }
            
        except Exception as e:
            logger.error(f"提取文档标签失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _extract_tags_from_content(self, text_content: str) -> List[str]:
        """从内容中提取标签"""
        try:
            tags = []
            
            # 业务领域标签
            business_fields = {
                '并购': ['并购', '收购', '重组', 'M&A'],
                '资本市场': ['IPO', '上市', '证券', '股票', '债券'],
                '银行金融': ['银行', '金融', '贷款', '融资', '信贷'],
                '知识产权': ['专利', '商标', '版权', '著作权', '知识产权'],
                '争议解决': ['仲裁', '诉讼', '调解', '争议', '纠纷'],
                '合规监管': ['合规', '监管', '反腐', '反洗钱', '数据保护'],
                '房地产': ['房地产', '土地', '建筑', '物业', '房产'],
                '劳动法': ['劳动', '人力资源', '员工', '雇佣', '薪酬'],
                '税务': ['税务', '税收', '纳税', '税法', '税务筹划'],
                '能源矿产': ['能源', '矿产', '石油', '天然气', '煤炭']
            }
            
            for field, keywords in business_fields.items():
                if any(keyword in text_content for keyword in keywords):
                    tags.append(field)
            
            # 文档类型标签
            if '合同' in text_content:
                tags.append('合同')
            if '协议' in text_content:
                tags.append('协议')
            if '证书' in text_content:
                tags.append('证书')
            if '报告' in text_content:
                tags.append('报告')
            
            return list(set(tags))
            
        except Exception as e:
            logger.error(f"从内容提取标签失败: {str(e)}")
            return []

    def get_ai_models_status(self) -> Dict[str, Any]:
        """获取AI服务状态"""
        try:
            return {
                "ai_service_configured": bool(self.ai_api_key),
                "ai_provider": self.ai_provider,
                "ai_model": self.ai_model,
                "ai_vision_model": self.ai_vision_model,
                "ai_base_url": self.ai_base_url,
                "docling_service_available": self.docling_service is not None,
                "features": {
                    "ocr": self.docling_service is not None,
                    "text_analysis": bool(self.ai_api_key),
                    "vision_analysis": bool(self.ai_api_key),
                    "document_classification": bool(self.ai_api_key)
                }
            }
        except Exception as e:
            logger.error(f"获取AI服务状态失败: {e}")
            return {
                "ai_service_configured": False,
                "docling_service_available": False,
                "error": str(e)
            }

    def record_user_correction(self, learning_data: Dict[str, Any]):
        """记录用户修正数据供AI学习"""
        try:
            config_manager = ConfigManager()
            config_manager.add_learning_data("user_corrections", learning_data)
            
            logger.info(f"AI学习数据已记录: {learning_data.get('original_classification')} -> {learning_data.get('user_correction')}")
            
        except Exception as e:
            logger.error(f"记录AI学习数据失败: {e}")

    def get_user_corrections_for_learning(self) -> List[Dict[str, Any]]:
        """获取用户修正数据用于改进AI分类"""
        try:
            config_manager = ConfigManager()
            return config_manager.get_learning_data("user_corrections")
            
        except Exception as e:
            logger.error(f"获取AI学习数据失败: {e}")
            return []

    def improve_classification_with_learning(self, prompt: str) -> str:
        """基于用户修正数据改进分类提示词"""
        try:
            corrections = self.get_user_corrections_for_learning()
            
            if not corrections:
                return prompt
            
            # 构建学习改进提示
            learning_notes = []
            
            for correction in corrections[-10:]:  # 只使用最近10条学习数据
                if correction.get("specific_correction") == "law_firm_license_vs_personal_certificate":
                    learning_notes.append(
                        "重要提醒：律师事务所执业许可证应归类为qualification_certificate（资质证照），"
                        "而非lawyer_certificate（个人律师证）。机构资质与个人证书要严格区分。"
                    )
                
                original = correction.get("original_classification")
                corrected = correction.get("user_correction")
                if original and corrected:
                    learning_notes.append(
                        f"学习案例：{original} 类型文档被用户修正为 {corrected}"
                    )
            
            if learning_notes:
                learning_section = "\n\n基于用户反馈的重要改进提醒：\n" + "\n".join(learning_notes)
                prompt = prompt + learning_section
            
            return prompt
            
        except Exception as e:
            logger.error(f"改进分类提示词失败: {e}")
            return prompt

# AI任务管理辅助函数
def create_ai_task(db, file_id: int, file_type: str) -> int:
    """创建AI分析任务，返回任务ID"""
    try:
        from database import get_db
        task = AITask(file_id=file_id, file_type=file_type, status="pending")
        db.add(task)
        db.commit()
        db.refresh(task)
        return task.id
    except Exception as e:
        logger.error(f"创建AI任务失败: {e}")
        return None

def update_ai_task(db, task_id: int, status: str, result: dict = None, error: str = None):
    """更新AI分析任务状态和结果"""
    try:
        task = db.query(AITask).filter(AITask.id == task_id).first()
        if not task:
            logger.warning(f"AI任务不存在: {task_id}")
            return
        
        task.status = status
        if result is not None:
            task.result_snapshot = result
        if error is not None:
            task.error_message = error
        
        db.commit()
        logger.info(f"AI任务更新: {task_id} -> {status}")
    except Exception as e:
        logger.error(f"更新AI任务失败: {e}")

def get_ai_task_status(db, task_id: int) -> dict:
    """获取AI任务状态"""
    try:
        task = db.query(AITask).filter(AITask.id == task_id).first()
        if not task:
            return {"error": "任务不存在"}
        
        return {
            "id": task.id,
            "file_id": task.file_id,
            "file_type": task.file_type,
            "status": task.status,
            "result_snapshot": task.result_snapshot,
            "error_message": task.error_message,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "updated_at": task.updated_at.isoformat() if task.updated_at else None
        }
    except Exception as e:
        logger.error(f"获取AI任务状态失败: {e}")
        return {"error": str(e)}

# 创建全局可导入实例
ai_service = AIService()
