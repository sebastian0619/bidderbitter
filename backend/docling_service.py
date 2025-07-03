#!/usr/bin/env python3
"""
统一Docling服务模块

整合所有Docling相关功能，提供统一的接口和配置管理。
包括文档转换、OCR、文本提取、网页预览等功能。

作者: AI Assistant
日期: 2024-12-30
版本: 1.0
"""

import os
import logging
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
import asyncio
from concurrent.futures import ThreadPoolExecutor
import json
import subprocess

# 设置日志
logger = logging.getLogger(__name__)

# Docling相关导入
try:
    from docling.document_converter import (
        DocumentConverter, 
        StandardPdfPipeline,
        PdfFormatOption, 
        WordFormatOption, 
        ImageFormatOption
    )
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import (
        PdfPipelineOptions, 
        PipelineOptions, 
        EasyOcrOptions
    )
    from docling.datamodel.accelerator_options import AcceleratorOptions, AcceleratorDevice
    DOCLING_AVAILABLE = True
    logger.info("Docling模块可用")
except ImportError as e:
    DOCLING_AVAILABLE = False
    logger.warning(f"Docling模块不可用: {e}")

# EasyOCR检查
try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError as e:
    EASYOCR_AVAILABLE = False
    logger.warning(f"EasyOCR模块不可用: {e}")


class DoclingConfig:
    """Docling配置管理类"""
    
    def __init__(self):
        # 基础路径配置 - 修复Docker环境中的路径问题
        if os.path.exists("/app"):
            # 在Docker容器中，使用/app作为基础路径
            self.project_root = Path("/app")
            self.easyocr_models_path = self.project_root / "easyocr_models"
        else:
            # 本地开发环境，使用相对路径
            self.project_root = Path(__file__).parent.parent
            self.easyocr_models_path = self.project_root / "easyocr_models"
        
        # 确保EasyOCR目录存在
        self.easyocr_models_path.mkdir(exist_ok=True)
        
        # OCR基础配置
        self.enable_ocr = self._get_setting_value("docling_enable_ocr", "true").lower() == "true"
        self.use_gpu = self._get_setting_value("docling_use_gpu", "false").lower() == "true"
        # 修正语言代码 - 参考GitHub讨论中的建议
        self.ocr_languages = self._get_setting_value("docling_ocr_languages", '["ch_sim", "en"]')
        if isinstance(self.ocr_languages, str):
            try:
                self.ocr_languages = json.loads(self.ocr_languages)
            except:
                self.ocr_languages = ["ch_sim", "en"]
        
        # EasyOCR高级配置 - 从数据库读取
        self.confidence_threshold = float(self._get_setting_value("docling_confidence_threshold", "0.5"))
        self.bitmap_area_threshold = float(self._get_setting_value("docling_bitmap_area_threshold", "0.05"))
        self.force_full_page_ocr = self._get_setting_value("docling_force_full_page_ocr", "false").lower() == "true"
        self.recog_network = self._get_setting_value("docling_recog_network", "standard")
        self.download_enabled = self._get_env_bool("DOCLING_DOWNLOAD_ENABLED", True)
        
        # AI分析功能开关 - 从数据库读取
        self.enable_table_structure = self._get_setting_value("ai_analysis_enable_table_structure", "false").lower() == "true"
        self.enable_picture_classification = self._get_setting_value("ai_analysis_enable_picture_classification", "false").lower() == "true"
        self.enable_picture_description = self._get_setting_value("ai_analysis_enable_picture_description", "false").lower() == "true"
        
        # 图像处理配置 - 从数据库读取
        self.images_scale = float(self._get_setting_value("docling_images_scale", "2.0"))
        self.generate_page_images = self._get_setting_value("ai_analysis_generate_page_images", "false").lower() == "true"
        self.generate_picture_images = self._get_setting_value("ai_analysis_generate_picture_images", "false").lower() == "true"
        
        # 视觉模型配置 - 从数据库读取用户配置的AI模型
        self.vision_provider = self._get_setting_value("vision_provider", self._get_setting_value("ai_provider", "openai"))
        self.vision_model = self._get_setting_value("ai_vision_model", "gpt-4-vision-preview")
        self.vision_api_key = self._get_setting_value("vision_api_key", self._get_setting_value("ai_api_key", ""))
        self.vision_base_url = self._get_setting_value("vision_base_url", self._get_setting_value("ai_base_url", "https://api.openai.com/v1"))
        self.ollama_vision_base_url = self._get_setting_value("ollama_vision_base_url", "http://localhost:11434/v1")
        
        # 图片描述prompt - 可配置
        self.picture_description_prompt = self._get_setting_value("picture_description_prompt", "请详细描述这张图片的内容，包括文字、图表、结构等信息。")
        
        logger.info(f"Docling配置初始化完成:")
        logger.info(f"  - 运行环境: {'Docker容器' if os.path.exists('/app') else '本地开发'}")
        logger.info(f"  - 项目根目录: {self.project_root}")
        logger.info(f"  - OCR启用: {self.enable_ocr}")
        logger.info(f"  - GPU使用: {self.use_gpu}")
        logger.info(f"  - OCR语言: {self.ocr_languages}")
        logger.info(f"  - 置信度阈值: {self.confidence_threshold}")
        logger.info(f"  - 位图阈值: {self.bitmap_area_threshold}")
        logger.info(f"  - 全页OCR: {self.force_full_page_ocr}")
        logger.info(f"  - 识别网络: {self.recog_network}")
        logger.info(f"  - 图像缩放: {self.images_scale}")
        logger.info(f"  - 表格结构: {self.enable_table_structure}")
        logger.info(f"  - 图片分类: {self.enable_picture_classification}")
        logger.info(f"  - 图片描述: {self.enable_picture_description}")
        logger.info(f"  - 生成页面图片: {self.generate_page_images}")
        logger.info(f"  - 生成图片文件: {self.generate_picture_images}")
        logger.info(f"  - EasyOCR模型路径: {self.easyocr_models_path}")
        logger.info(f"  - Docling模型: 由系统自动管理")
        logger.info(f"  - 视觉模型提供商: {self.vision_provider}")
        logger.info(f"  - 视觉模型: {self.vision_model}")
        logger.info(f"  - 视觉模型URL: {self.vision_base_url if self.vision_provider != 'ollama' else self.ollama_vision_base_url}")
        logger.info(f"  - 图片描述Prompt: {self.picture_description_prompt[:50]}...")
    
    def _get_env_bool(self, key: str, default: bool) -> bool:
        """获取环境变量布尔值"""
        return os.getenv(key, str(default)).lower() in ("true", "1", "yes", "on")
    
    def _get_env_list(self, key: str, default: List[str]) -> List[str]:
        """获取环境变量列表"""
        value = os.getenv(key)
        if value:
            return [item.strip() for item in value.split(",")]
        return default
    
    def _get_setting_value(self, key: str, default: str = "") -> str:
        """从数据库获取设置值"""
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
        
        return default


class DoclingService:
    """统一Docling服务类 - 管理所有Docling相关功能"""
    
    def __init__(self, config: Optional[DoclingConfig] = None):
        self.config = config or DoclingConfig()
        self.converter: Optional[DocumentConverter] = None
        self.is_initialized = False
        self._executor = ThreadPoolExecutor(max_workers=2)
        
        # 初始化转换器
        self._initialize_converter()
    
    def _initialize_converter(self) -> bool:
        """初始化Docling转换器"""
        if not DOCLING_AVAILABLE:
            logger.warning("Docling不可用，跳过初始化")
            return False
        
        try:
            # 预下载模型
            self._download_models()
            
            # 创建转换器
            self.converter = self._create_converter()
            self.is_initialized = True
            
            logger.info("Docling转换器初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"Docling转换器初始化失败: {e}")
            self.converter = None
            self.is_initialized = False
            return False
    
    def _download_models(self):
        """下载Docling模型 - 优化下载策略，优先使用已有模型"""
        try:
            # 设置完整的HuggingFace镜像环境变量
            import os
            import subprocess
            
            # 使用HuggingFace镜像网址
            hf_endpoint = "https://hf-mirror.com"
            os.environ["HF_ENDPOINT"] = hf_endpoint
            os.environ["HUGGINGFACE_HUB_URL"] = hf_endpoint
            
            # 设置HuggingFace相关环境变量
            os.environ["HF_HOME"] = "/root/.cache/huggingface"
            os.environ["TRANSFORMERS_CACHE"] = "/root/.cache/huggingface/transformers"
            os.environ["HF_HUB_CACHE"] = "/root/.cache/huggingface/hub"
            
            # 网络优化配置
            os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "1"  # 启用hf_transfer加速
            os.environ["HUGGINGFACE_HUB_VERBOSITY"] = "info"  # 启用详细日志
            
            # 创建缓存目录
            hf_cache_dir = "/root/.cache/huggingface"
            docling_cache_dir = "/root/.cache/docling/models"
            os.makedirs(hf_cache_dir, exist_ok=True)
            os.makedirs("/root/.cache/huggingface/transformers", exist_ok=True)
            os.makedirs("/root/.cache/huggingface/hub", exist_ok=True)
            os.makedirs(docling_cache_dir, exist_ok=True)
            
            logger.info(f"Docling网络配置完成:")
            logger.info(f"  - HF镜像: {hf_endpoint}")
            logger.info(f"  - HF缓存: {hf_cache_dir}")
            logger.info(f"  - Docling缓存: {docling_cache_dir}")
            logger.info(f"  - HF_TRANSFER: 启用 (加速下载)")
            
            # 检查已有模型
            layout_exists = os.path.exists(f"{docling_cache_dir}/layout")
            tableformer_exists = os.path.exists(f"{docling_cache_dir}/tableformer")
            
            logger.info(f"模型状态检查:")
            logger.info(f"  - Layout模型: {'✅ 已存在' if layout_exists else '❌ 缺失'}")
            logger.info(f"  - TableFormer模型: {'✅ 已存在' if tableformer_exists else '❌ 缺失'}")
            
            # 只下载缺失的核心模型
            if not layout_exists or not tableformer_exists:
                try:
                    logger.info("下载核心PDF处理模型...")
                    
                    models_to_download = []
                    if not layout_exists:
                        models_to_download.append("layout")
                    if not tableformer_exists:
                        models_to_download.append("tableformer")
                    
                    result = subprocess.run(
                        ["docling-tools", "models", "download"] + models_to_download,
                        capture_output=True,
                        text=True,
                        timeout=300,  # 5分钟超时，只下载核心模型
                        env=os.environ.copy()
                    )
                    
                    if result.returncode == 0:
                        logger.info(f"✅ 核心模型下载成功: {models_to_download}")
                        logger.info(f"输出: {result.stdout}")
                    else:
                        logger.warning(f"⚠️  核心模型下载失败，使用备用方法")
                        logger.warning(f"错误: {result.stderr}")
                        
                        # 备用方法：使用旧的下载方式但跳过OCR
                        logger.info("使用备用下载方法...")
                        # 这里不调用会触发OCR下载的方法
                        
                except subprocess.TimeoutExpired:
                    logger.warning("⏰ 核心模型下载超时，跳过预下载")
                except Exception as download_error:
                    logger.warning(f"📦 核心模型下载失败: {download_error}")
            else:
                logger.info("✅ 核心模型已存在，跳过下载")
            
            # OCR模型单独处理
            if self.config.enable_ocr:
                easyocr_exists = os.path.exists(f"{docling_cache_dir}/easyocr")
                if not easyocr_exists:
                    logger.info("⚠️  OCR模型缺失，建议后台下载或使用Tesseract替代")
                    logger.info("提示：可以稍后手动运行 'docling-tools models download easyocr'")
                else:
                    logger.info("✅ OCR模型已存在")
                
        except Exception as e:
            logger.warning(f"模型配置失败，但不影响基础功能: {e}")
    
    def _create_converter(self) -> Optional[object]:
        """创建Docling文档转换器 - 使用HF镜像配置并优化EasyOCR"""
        # 确保HF镜像环境变量在转换器创建时也有效
        import os
        hf_endpoint = "https://hf-mirror.com"
        os.environ["HF_ENDPOINT"] = hf_endpoint
        os.environ["HUGGINGFACE_HUB_URL"] = hf_endpoint
        
        # 配置EasyOCR选项
        ocr_options = None
        accelerator_options = AcceleratorOptions(device=AcceleratorDevice.CPU)
        
        if self.config.enable_ocr and EASYOCR_AVAILABLE:
            try:
                # 优化EasyOCR选项 - 基于官方文档和GitHub讨论
                ocr_options = EasyOcrOptions(
                    # 必需参数 - 语言支持
                    lang=self.config.ocr_languages,  # ['ch_sim', 'en'] 中英文支持
                    
                    # OCR控制参数 - 从数据库配置读取
                    force_full_page_ocr=self.config.force_full_page_ocr,  # 从数据库读取
                    bitmap_area_threshold=self.config.bitmap_area_threshold,  # 从数据库读取
                    confidence_threshold=self.config.confidence_threshold,  # 从数据库读取
                    
                    # 模型管理 - 关键优化
                    model_storage_directory=str(self.config.easyocr_models_path),  # 统一模型存储
                    download_enabled=True,  # 启用自动下载
                    
                    # 网络配置 - 从数据库读取
                    recog_network=self.config.recog_network,  # 从数据库读取
                    
                    # GPU配置 - 从数据库读取
                    use_gpu=self.config.use_gpu  # 从数据库读取
                )
                
                # 设置加速器选项
                if self.config.use_gpu:
                    accelerator_options = AcceleratorOptions(device=AcceleratorDevice.CUDA)
                else:
                    accelerator_options = AcceleratorOptions(device=AcceleratorDevice.CPU)
                    
                logger.info(f"EasyOCR优化配置完成:")
                logger.info(f"  - 语言支持: {self.config.ocr_languages}")
                logger.info(f"  - 计算设备: {accelerator_options.device.value}")
                logger.info(f"  - 置信度阈值: {self.config.confidence_threshold}")
                logger.info(f"  - 位图阈值: {self.config.bitmap_area_threshold}")
                logger.info(f"  - 全页OCR: {self.config.force_full_page_ocr}")
                logger.info(f"  - 识别网络: {self.config.recog_network}")
                logger.info(f"  - 模型路径: {self.config.easyocr_models_path}")
                logger.info(f"  - HF镜像: {hf_endpoint}")
                
            except Exception as e:
                logger.error(f"EasyOCR配置失败: {e}")
                ocr_options = None
                accelerator_options = AcceleratorOptions(device=AcceleratorDevice.CPU)
        
        # 配置图片描述选项 - 使用用户配置的视觉模型
        picture_description_options = None
        if self.config.enable_picture_description and self.config.vision_api_key:
            try:
                from docling.datamodel.pipeline_options import PictureDescriptionApiOptions
                
                # 根据视觉提供商配置API选项
                if self.config.vision_provider == "ollama":
                    # Ollama配置
                    picture_description_options = PictureDescriptionApiOptions(
                        url=f"{self.config.ollama_vision_base_url}/chat/completions",
                        headers={
                            "Content-Type": "application/json"
                        },
                        params={
                            "model": self.config.vision_model
                        },
                        prompt=self.config.picture_description_prompt,
                        timeout=60,
                        picture_area_threshold=0.05,
                        scale=2.0
                    )
                    logger.info(f"Docling图片描述配置(Ollama): {self.config.vision_model}")
                else:
                    # OpenAI兼容API配置 (OpenAI, Azure, Custom)
                    headers = {
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.config.vision_api_key}"
                    }
                    
                    # 根据不同提供商配置模型参数
                    if self.config.vision_provider == "azure":
                        # Azure OpenAI特殊配置
                        api_url = f"{self.config.vision_base_url}/openai/deployments/{self.config.vision_model}/chat/completions"
                        headers["api-key"] = self.config.vision_api_key
                        del headers["Authorization"]  # Azure使用api-key而不是Authorization
                    else:
                        # OpenAI或Custom API
                        api_url = f"{self.config.vision_base_url}/chat/completions"
                    
                    picture_description_options = PictureDescriptionApiOptions(
                        url=api_url,
                        headers=headers,
                        params={
                            "model": self.config.vision_model,
                            "max_tokens": 1000,
                            "temperature": 0.1
                        },
                        prompt=self.config.picture_description_prompt,
                        timeout=60,
                        picture_area_threshold=0.05,
                        scale=2.0
                    )
                    logger.info(f"Docling图片描述配置({self.config.vision_provider}): {self.config.vision_model}")
                    logger.info(f"  - API URL: {api_url}")
                    logger.info(f"  - Prompt: {self.config.picture_description_prompt[:50]}...")
                
            except ImportError as e:
                logger.warning(f"PictureDescriptionApiOptions不可用: {e}")
                picture_description_options = None
            except Exception as e:
                logger.error(f"图片描述配置失败: {e}")
                picture_description_options = None
        
        # 配置PDF处理选项
        pdf_options_dict = {
            "do_ocr": self.config.enable_ocr,
            "do_table_structure": self.config.enable_table_structure,  # 从数据库读取
            "do_picture_classification": self.config.enable_picture_classification,  # 从数据库读取
            "do_picture_description": self.config.enable_picture_description,  # 从数据库读取
            "ocr_options": ocr_options,
            "accelerator_options": accelerator_options,  # 关键：设置加速器选项
            "images_scale": self.config.images_scale,
            "generate_page_images": self.config.generate_page_images,  # 从数据库读取
            "generate_picture_images": self.config.generate_picture_images,  # 从数据库读取
            "generate_parsed_pages": True,
            "generate_table_images": False,
            "enable_remote_services": (picture_description_options is not None)  # 如果配置了图片描述，则启用远程服务
        }
        
        # 只有在配置了图片描述选项时才添加
        if picture_description_options is not None:
            pdf_options_dict["picture_description_options"] = picture_description_options
            logger.info("✅ Docling图片描述选项已配置，将使用用户配置的视觉模型")
        else:
            logger.info("ℹ️  未配置Docling图片描述选项，将使用独立视觉分析")
        
        pdf_options = PdfPipelineOptions(**pdf_options_dict)
        
        # 配置图片处理选项 - 修复API兼容性问题
        # 对于图片处理，我们不需要单独的PipelineOptions
        
        # 创建转换器
        try:
            converter = DocumentConverter(
                format_options={
                    InputFormat.PDF: PdfFormatOption(pipeline_options=pdf_options),
                    InputFormat.DOCX: WordFormatOption(),
                    InputFormat.PPTX: WordFormatOption(),
                    InputFormat.HTML: WordFormatOption(),
                    InputFormat.MD: WordFormatOption(),
                    InputFormat.IMAGE: ImageFormatOption(),  # 简化图片配置，不传递pipeline_options
                }
            )
            
            logger.info("Docling转换器创建成功")
            return converter
            
        except Exception as e:
            logger.error(f"Docling转换器创建失败: {e}")
            return None
    
    # ========== 核心转换功能 ==========
    
    async def convert_document(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """通用文档转换"""
        if not self.is_initialized:
            return {"success": False, "error": "Docling服务未初始化"}
        
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                return {"success": False, "error": f"文件不存在: {file_path}"}
            
            # 在线程池中执行转换
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self._executor, 
                self.converter.convert, 
                str(file_path)
            )
            
            return {
                "success": True,
                "document": result.document,
                "conversion_result": result,
                "file_path": str(file_path)
            }
            
        except Exception as e:
            logger.error(f"文档转换失败 {file_path}: {e}")
            return {"success": False, "error": str(e)}
    
    async def extract_text(self, file_path: Union[str, Path], format: str = "markdown") -> Dict[str, Any]:
        """文本提取"""
        convert_result = await self.convert_document(file_path)
        if not convert_result["success"]:
            return convert_result
        
        try:
            doc = convert_result["document"]
            
            # 添加详细的调试信息
            logger.info(f"Docling文档信息:")
            logger.info(f"  - 页数: {doc.num_pages()}")
            logger.info(f"  - 文本元素数量: {len(doc.texts)}")
            logger.info(f"  - 表格数量: {len(doc.tables)}")
            logger.info(f"  - 图片数量: {len(doc.pictures)}")
            
            # 检查文本元素
            if len(doc.texts) > 0:
                logger.info(f"  - 前3个文本元素:")
                for i, text in enumerate(doc.texts[:3]):
                    logger.info(f"    文本{i+1}: {text.text[:100]}..." if len(text.text) > 100 else f"    文本{i+1}: {text.text}")
            else:
                logger.warning("  - 没有找到文本元素")
            
            # 根据格式提取文本
            if format.lower() == "markdown":
                text_content = doc.export_to_markdown()
            elif format.lower() == "html":
                text_content = doc.export_to_html()
            elif format.lower() == "text":
                text_content = doc.export_to_text()
            elif format.lower() == "json":
                text_content = json.dumps(doc.export_to_dict(), ensure_ascii=False, indent=2)
            else:
                text_content = doc.export_to_text()
            
            logger.info(f"提取的文本长度: {len(text_content)} 字符")
            if len(text_content) > 0:
                logger.info(f"文本预览: {text_content[:200]}...")
            else:
                logger.warning("提取的文本为空")
            
            return {
                "success": True,
                "text_content": text_content,
                "format": format,
                "metadata": {
                    "pages": doc.num_pages(),
                    "pictures": len(doc.pictures),
                    "tables": len(doc.tables),
                    "texts": len(doc.texts)
                }
            }
            
        except Exception as e:
            logger.error(f"文本提取失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_document_preview(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """获取文档网页预览数据 - 支持实时预览"""
        convert_result = await self.convert_document(file_path)
        if not convert_result["success"]:
            return convert_result
        
        try:
            doc = convert_result["document"]
            
            # 获取预览数据
            preview_data = {
                # HTML预览内容 - 主要用于网页显示
                "html_content": doc.export_to_html(),
                
                # Markdown格式（备选）
                "markdown_content": doc.export_to_markdown(),
                
                # 可视化数据 - 如果需要图形化预览
                "visualization": None,  # doc.get_visualization() 如果API支持
                
                # 文档元数据
                "metadata": {
                    "filename": Path(file_path).name,
                    "pages": doc.num_pages(),
                    "pictures": len(doc.pictures),
                    "tables": len(doc.tables),
                    "texts": len(doc.texts),
                    "origin": {
                        "filename": doc.origin.filename if doc.origin else None,
                        "mimetype": doc.origin.mimetype if doc.origin else None
                    }
                },
                
                # 分页预览数据
                "pages": []
            }
            
            # 提取每页内容（用于分页预览）
            try:
                for i, page in enumerate(doc.pages, 1):
                    page_info = {
                        "page_num": i,
                        "size": page.size.as_tuple() if hasattr(page, 'size') else None,
                        # 页面内容预览
                        "has_content": bool(page),
                        "content_summary": f"第{i}页包含 {len([item for item in page.children])} 个元素" if hasattr(page, 'children') else f"第{i}页"
                    }
                    preview_data["pages"].append(page_info)
            except Exception as page_error:
                logger.warning(f"页面信息提取失败: {page_error}")
            
            return {
                "success": True,
                "preview_data": preview_data
            }
            
        except Exception as e:
            logger.error(f"预览数据生成失败: {e}")
            return {"success": False, "error": str(e)}
    
    # ========== 分析功能 ==========
    
    async def analyze_document(self, file_path: Union[str, Path], analysis_type: str = "full") -> Dict[str, Any]:
        """文档智能分析"""
        convert_result = await self.convert_document(file_path)
        if not convert_result["success"]:
            return convert_result
        
        try:
            doc = convert_result["document"]
            
            analysis_result = {
                "basic_info": {
                    "pages": doc.num_pages(),
                    "pictures": len(doc.pictures),
                    "tables": len(doc.tables),
                    "texts": len(doc.texts)
                }
            }
            
            if analysis_type in ("full", "text"):
                # 文本分析
                text_content = doc.export_to_text()
                analysis_result["text_analysis"] = {
                    "char_count": len(text_content),
                    "word_count": len(text_content.split()),
                    "line_count": len(text_content.split('\n')),
                    "preview": text_content[:500] + "..." if len(text_content) > 500 else text_content
                }
            
            if analysis_type in ("full", "structure"):
                # 结构分析
                analysis_result["structure_analysis"] = {
                    "has_tables": len(doc.tables) > 0,
                    "has_pictures": len(doc.pictures) > 0,
                    "content_types": list(set([text.label for text in doc.texts if hasattr(text, 'label')]))
                }
            
            return {
                "success": True,
                "analysis": analysis_result
            }
            
        except Exception as e:
            logger.error(f"文档分析失败: {e}")
            return {"success": False, "error": str(e)}
    
    # ========== 工具方法 ==========
    
    def get_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        return {
            "docling_available": DOCLING_AVAILABLE,
            "easyocr_available": EASYOCR_AVAILABLE,
            "initialized": self.is_initialized,
            "converter_ready": self.converter is not None,
            "config": {
                # 基础OCR配置
                "enable_ocr": self.config.enable_ocr,
                "use_gpu": self.config.use_gpu,
                "ocr_languages": self.config.ocr_languages,
                
                # EasyOCR高级配置
                "confidence_threshold": self.config.confidence_threshold,
                "bitmap_area_threshold": self.config.bitmap_area_threshold,
                "force_full_page_ocr": self.config.force_full_page_ocr,
                "recog_network": self.config.recog_network,
                "download_enabled": self.config.download_enabled,
                
                # 路径配置
                "easyocr_models_path": str(self.config.easyocr_models_path),
                "docling_models": "由系统自动管理",
                
                # 功能配置
                "enable_table_structure": self.config.enable_table_structure,
                "enable_picture_classification": self.config.enable_picture_classification,
                "enable_picture_description": self.config.enable_picture_description,
                
                # 图像处理配置
                "images_scale": self.config.images_scale,
                "generate_page_images": self.config.generate_page_images,
                "generate_picture_images": self.config.generate_picture_images,
                
                # 视觉模型配置
                "vision_provider": self.config.vision_provider,
                "vision_model": self.config.vision_model,
                "vision_api_key": self.config.vision_api_key,
                "vision_base_url": self.config.vision_base_url if self.config.vision_provider != 'ollama' else self.config.ollama_vision_base_url,
                "picture_description_prompt": self.config.picture_description_prompt[:50] + "..."
            }
        }
    
    def get_supported_formats(self) -> List[str]:
        """获取支持的文件格式"""
        if not self.is_initialized:
            return []
        
        return [
            ".pdf", ".docx", ".pptx", ".html", ".md", 
            ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff"
        ]
    
    async def download_models(self, force: bool = False) -> Dict[str, Any]:
        """手动下载模型 - 使用官方推荐的新方法"""
        try:
            if not DOCLING_AVAILABLE:
                return {"success": False, "error": "Docling不可用"}
            
            logger.info("开始手动下载Docling模型...")
            loop = asyncio.get_event_loop()
            
            # 使用新的官方推荐方法
            try:
                from docling.utils.models_downloader import download_all
                logger.info("✅ 使用 docling.utils.models_downloader.download_all() 方法")
                model_path = await loop.run_in_executor(self._executor, download_all)
                
                return {
                    "success": True,
                    "model_path": str(model_path),
                    "message": "模型下载完成 (新方法)",
                    "method": "docling.utils.models_downloader.download_all"
                }
                
            except ImportError:
                logger.info("⚠️  新方法不可用，使用旧方法...")
                model_path = await loop.run_in_executor(
                    self._executor,
                    StandardPdfPipeline.download_models_hf,
                    force
                )
                
                return {
                    "success": True,
                    "model_path": str(model_path),
                    "message": "模型下载完成 (旧方法)",
                    "method": "StandardPdfPipeline.download_models_hf"
                }
            
        except Exception as e:
            logger.error(f"模型下载失败: {e}")
            return {"success": False, "error": str(e)}
    
    def __del__(self):
        """清理资源"""
        if hasattr(self, '_executor'):
            self._executor.shutdown(wait=False)

    async def extract_text_ocr_only(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """仅OCR文本提取 - 避免完整文档转换，提高性能"""
        if not self.is_initialized:
            return {"success": False, "error": "Docling服务未初始化"}
        
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                return {"success": False, "error": f"文件不存在: {file_path}"}
            
            # 检查文件格式
            file_ext = file_path.suffix.lower()
            
            # 对于纯文本文件，直接读取
            if file_ext in ['.txt', '.md']:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        text_content = f.read()
                    logger.info(f"直接读取文本文件: {len(text_content)} 字符")
                    return {
                        "success": True,
                        "text_content": text_content,
                        "format": "text",
                        "method": "direct_read",
                        "metadata": {
                            "pages": 1,
                            "pictures": 0,
                            "tables": 0,
                            "texts": 1
                        }
                    }
                except Exception as e:
                    logger.warning(f"直接读取文本文件失败: {e}")
            
            # 对于支持的文档格式，使用简化的OCR转换
            if file_ext in ['.pdf', '.docx', '.pptx', '.html', '.jpg', '.jpeg', '.png']:
                try:
                    # 创建简化的OCR配置 - 只做文本提取
                    simplified_pdf_options = PdfPipelineOptions(
                        do_ocr=True,  # 启用OCR
                        do_table_structure=self.config.enable_table_structure,  # 从数据库读取
                        do_picture_classification=self.config.enable_picture_classification,  # 从数据库读取
                        do_picture_description=self.config.enable_picture_description,  # 从数据库读取
                        generate_page_images=self.config.generate_page_images,  # 从数据库读取
                        generate_picture_images=self.config.generate_picture_images,  # 从数据库读取
                        generate_parsed_pages=True,  # 必须为True，避免Pydantic校验错误
                        generate_table_images=False,  # 禁用表格图片
                        enable_remote_services=False,  # 保持离线
                        ocr_options=self._get_ocr_options(),  # 使用OCR选项
                        accelerator_options=AcceleratorOptions(device=AcceleratorDevice.CUDA if self.config.use_gpu else AcceleratorDevice.CPU),  # 从数据库读取
                        images_scale=self.config.images_scale  # 从数据库读取
                    )
                    
                    # 创建简化的转换器
                    simplified_converter = DocumentConverter(
                        format_options={
                            InputFormat.PDF: PdfFormatOption(pipeline_options=simplified_pdf_options),
                            InputFormat.DOCX: WordFormatOption(),
                            InputFormat.PPTX: WordFormatOption(),
                            InputFormat.HTML: WordFormatOption(),
                            InputFormat.IMAGE: ImageFormatOption(),  # 移除pipeline_options避免API错误
                        }
                    )
                    
                    # 执行简化的转换
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(
                        self._executor, 
                        simplified_converter.convert, 
                        str(file_path)
                    )
                    
                    doc = result.document
                    text_content = doc.export_to_text()
                    
                    logger.info(f"OCR文本提取完成: {len(text_content)} 字符")
                    
                    return {
                        "success": True,
                        "text_content": text_content,
                        "format": "text",
                        "method": "ocr_only",
                        "metadata": {
                            "pages": doc.num_pages(),
                            "pictures": len(doc.pictures),
                            "tables": len(doc.tables),
                            "texts": len(doc.texts)
                        }
                    }
                    
                except Exception as e:
                    logger.error(f"OCR文本提取失败: {e}")
                    return {"success": False, "error": f"OCR提取失败: {str(e)}"}
            else:
                return {"success": False, "error": f"不支持的文件格式: {file_ext}"}
                
        except Exception as e:
            logger.error(f"文本提取失败: {e}")
            return {"success": False, "error": str(e)}
    
    def _get_ocr_options(self):
        """获取OCR选项"""
        if not self.config.enable_ocr or not EASYOCR_AVAILABLE:
            return None
            
        try:
            return EasyOcrOptions(
                lang=self.config.ocr_languages,
                force_full_page_ocr=self.config.force_full_page_ocr,  # 从数据库读取
                bitmap_area_threshold=self.config.bitmap_area_threshold,  # 从数据库读取
                confidence_threshold=self.config.confidence_threshold,  # 从数据库读取
                model_storage_directory=str(self.config.easyocr_models_path),
                download_enabled=True,
                recog_network=self.config.recog_network,  # 从数据库读取
                use_gpu=self.config.use_gpu  # 从数据库读取
            )
        except Exception as e:
            logger.error(f"OCR选项创建失败: {e}")
            return None


# 全局实例
docling_service = DoclingService()


# ========== 便捷函数 ==========

async def convert_document(file_path: Union[str, Path]) -> Dict[str, Any]:
    """便捷函数：转换文档"""
    return await docling_service.convert_document(file_path)

async def extract_text(file_path: Union[str, Path], format: str = "markdown") -> Dict[str, Any]:
    """便捷函数：提取文本"""
    return await docling_service.extract_text(file_path, format)

async def get_document_preview(file_path: Union[str, Path]) -> Dict[str, Any]:
    """便捷函数：获取网页预览"""
    return await docling_service.get_document_preview(file_path)

async def analyze_document(file_path: Union[str, Path]) -> Dict[str, Any]:
    """便捷函数：分析文档"""
    return await docling_service.analyze_document(file_path)

def get_service_status() -> Dict[str, Any]:
    """便捷函数：获取服务状态"""
    return docling_service.get_status() 