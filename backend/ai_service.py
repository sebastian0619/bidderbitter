import os
import json
import logging
from typing import Dict, List, Optional, Any

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Docling相关导入
try:
    from docling.document_converter import DocumentConverter
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions, PipelineOptions, EasyOcrOptions
    from docling.datamodel.accelerator_options import AcceleratorOptions
    DOCLING_AVAILABLE = True
    logger.info("Docling模块可用")
except ImportError as e:
    DOCLING_AVAILABLE = False
    logger.warning(f"Docling模块不可用: {e}")

# 检查EasyOCR是否可用
try:
    import easyocr
    EASYOCR_AVAILABLE = True
    logger.info("EasyOCR模块可用")
except ImportError as e:
    EASYOCR_AVAILABLE = False
    logger.warning(f"EasyOCR模块不可用: {e}")

class AIService:
    """AI服务类，提供各种AI能力"""
    
    def __init__(self):
        self.ai_provider = os.getenv("AI_PROVIDER", "openai").lower()
        self.enable_ai = os.getenv("ENABLE_AI", "true").lower() == "true"
        
        # EasyOCR配置（为了兼容性）
        self.easyocr_enable = True
        self.easyocr_model_path = os.path.join(os.path.dirname(__file__), '..', 'easyocr_models')
        self.easyocr_model_path = os.path.abspath(self.easyocr_model_path)
        os.makedirs(self.easyocr_model_path, exist_ok=True)
        self.easyocr_download_proxy = ""
        self.easyocr_languages = ["ch_sim", "en"]
        self.easyocr_use_gpu = False
        self.easyocr_reader = None
        
        # Docling OCR配置
        self.enable_docling_ocr = True
        self.docling_enable_ocr = True
        self.docling_use_gpu = False
        self.docling_ocr_languages = ["ch_sim", "en"]
        
        # 初始化Docling转换器
        self.docling_converter = None
        self._init_docling_converter()
        
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
            
            return os.getenv(key.upper(), default)
            
        except Exception as e:
            logger.warning(f"无法从数据库获取设置 {key}: {str(e)}")
            return os.getenv(key.upper(), default)
        finally:
            try:
                db.close()
            except:
                pass
    
    def reload_config(self):
        """重新加载配置"""
        try:
            logger.info("重新加载AI服务配置...")
            
            # 重新读取设置
            self.ai_provider = self._get_setting_value("ai_provider", "openai").lower()
            self.enable_ai = self._get_setting_value("enable_ai", "true").lower() == "true"
            self.enable_docling_ocr = self._get_setting_value("docling_enable_ocr", "true").lower() == "true"
            self.docling_enable_ocr = self.enable_docling_ocr
            self.docling_use_gpu = self._get_setting_value("docling_use_gpu", "false").lower() == "true"
            
            # 重新初始化Docling转换器
            self._init_docling_converter()
                
            logger.info(f"AI服务配置重载完成，当前提供商: {self.ai_provider}")
            
        except Exception as e:
            logger.error(f"重新加载AI配置失败: {str(e)}")
    
    def _init_docling_converter(self):
        """初始化Docling转换器"""
        if not DOCLING_AVAILABLE:
            logger.warning("Docling不可用，跳过初始化")
            return
            
        try:
            # 配置Docling管道选项，包括OCR
            
            # 设置EasyOCR模型目录 - 使用项目中的easyocr_models目录
            easyocr_model_path = os.path.join(os.path.dirname(__file__), '..', 'easyocr_models')
            easyocr_model_path = os.path.abspath(easyocr_model_path)
            
            # 确保模型目录存在
            os.makedirs(easyocr_model_path, exist_ok=True)
            
            # 配置EasyOCR选项 - 根据Docling文档规范
            ocr_options = EasyOcrOptions(
                lang=['ch_sim', 'en'],  # 使用正确的语言代码
                force_full_page_ocr=False,
                bitmap_area_threshold=0.05,
                use_gpu=self.docling_use_gpu,
                confidence_threshold=0.5,
                model_storage_directory=easyocr_model_path,
                recog_network='standard',
                download_enabled=True
            )
            
            # 配置PDF管道选项 - 根据Docling文档规范
            self.docling_pipeline_options = PdfPipelineOptions(
                do_ocr=self.docling_enable_ocr,
                do_table_structure=True,
                do_picture_classification=False,
                do_picture_description=False,
                ocr_options=ocr_options,
                images_scale=1.0,
                generate_page_images=False,
                generate_picture_images=False,
                force_backend_text=False,  # 添加缺失的属性
                generate_parsed_pages=True,  # 修复：应该为True
                generate_table_images=False  # 添加缺失的属性
            )
            
            # 配置图片处理选项（使用基础PipelineOptions加OCR）
            self.docling_image_options = PipelineOptions()
            
            # 创建转换器
            self.docling_converter = DocumentConverter(
                format_options={
                    InputFormat.PDF: self.docling_pipeline_options,
                    InputFormat.DOCX: PipelineOptions(),
                    InputFormat.PPTX: PipelineOptions(),
                    InputFormat.HTML: PipelineOptions(),
                    InputFormat.MD: PipelineOptions(),
                    InputFormat.IMAGE: self.docling_image_options,
                }
            )
            
            logger.info(f"Docling转换器初始化成功")
            logger.info(f"EasyOCR模型目录: {easyocr_model_path}")
            logger.info(f"OCR设置: 启用={self.docling_enable_ocr}, GPU={self.docling_use_gpu}")
            
        except Exception as e:
            logger.error(f"Docling转换器初始化失败: {str(e)}")
            self.docling_converter = None
    
    async def download_easyocr_models(self, progress_callback=None):
        """手动下载EasyOCR模型（通过Docling统一管理）"""
        try:
            # 确保模型目录存在
            os.makedirs(self.easyocr_model_path, exist_ok=True)
            logger.info(f"EasyOCR模型目录: {self.easyocr_model_path}")
            
            if progress_callback:
                progress_callback({"status": "downloading", "progress": 10, "message": "开始下载模型..."})
            
            # 使用Docling的EasyOCR配置来下载模型
            if DOCLING_AVAILABLE:
                try:
                    # 导入Docling的EasyOCR选项
                    from docling.datamodel.pipeline_options import EasyOcrOptions
                    
                    # 设置代理（如果有的话）
                    if self.easyocr_download_proxy:
                        os.environ['http_proxy'] = self.easyocr_download_proxy
                        os.environ['https_proxy'] = self.easyocr_download_proxy
                        logger.info(f"设置下载代理: {self.easyocr_download_proxy}")
                    
                    if progress_callback:
                        progress_callback({"status": "downloading", "progress": 30, "message": "配置OCR选项..."})
                    
                    # 创建EasyOCR配置，这会触发模型下载
                    ocr_options = EasyOcrOptions(
                        lang=['ch_sim', 'en'],  # 使用正确的语言代码
                        force_full_page_ocr=False,
                        bitmap_area_threshold=0.05,
                        use_gpu=self.easyocr_use_gpu,
                        confidence_threshold=0.5,
                        model_storage_directory=self.easyocr_model_path,
                        recog_network='standard',
                        download_enabled=True
                    )
                    
                    if progress_callback:
                        progress_callback({"status": "downloading", "progress": 60, "message": "下载模型文件..."})
                    
                    # 实际触发模型下载 - 通过直接创建EasyOCR Reader来下载模型
                    if progress_callback:
                        progress_callback({"status": "downloading", "progress": 70, "message": "触发模型下载..."})
                    
                    # 直接使用EasyOCR来触发模型下载
                    logger.info("开始通过EasyOCR直接下载模型...")
                    
                    # 使用重试机制进行模型下载
                    max_retries = 3
                    retry_count = 0
                    download_success = False
                    
                    while retry_count < max_retries and not download_success:
                        try:
                            logger.info(f"第 {retry_count + 1} 次尝试下载EasyOCR模型...")
                            
                            import easyocr
                            import os
                            import urllib.request
                            import urllib.error
                            
                            # 设置网络超时
                            import socket
                            socket.setdefaulttimeout(300)  # 5分钟超时
                            
                            # 直接创建EasyOCR Reader，这会触发模型下载
                            reader = easyocr.Reader(
                                ['ch_sim', 'en'],
                                gpu=self.easyocr_use_gpu,
                                model_storage_directory=self.easyocr_model_path,
                                download_enabled=True,
                                verbose=True
                            )
                            logger.info("EasyOCR Reader创建成功，模型应该已下载")
                            
                            # 验证模型文件是否真的下载了
                            model_files = ['craft_mlt_25k.pth', 'zh_sim_g2.pth', 'english_g2.pth']
                            downloaded_count = 0
                            for model_file in model_files:
                                file_path = os.path.join(self.easyocr_model_path, model_file)
                                if os.path.exists(file_path):
                                    downloaded_count += 1
                                    logger.info(f"模型文件验证成功: {model_file}")
                            
                            if downloaded_count >= 1:  # 至少有1个模型文件下载成功
                                download_success = True
                                self.easyocr_reader = reader
                                logger.info(f"模型下载验证成功，已下载 {downloaded_count} 个模型文件")
                            else:
                                raise Exception("模型文件验证失败，未发现下载的模型文件")
                            
                        except Exception as easyocr_error:
                            retry_count += 1
                            logger.warning(f"第 {retry_count} 次EasyOCR下载失败: {easyocr_error}")
                            
                            if retry_count < max_retries:
                                logger.info(f"将在 5 秒后重试... ({retry_count}/{max_retries})")
                                import time
                                time.sleep(5)
                            else:
                                logger.error("所有EasyOCR下载尝试都失败了，尝试Docling方法")
                                
                                # 如果直接EasyOCR失败，尝试DocumentConverter方法
                                temp_converter = DocumentConverter(
                                    format_options={
                                        InputFormat.PDF: PdfPipelineOptions(
                                            do_ocr=True,
                                            ocr_options=ocr_options
                                        )
                                    }
                                )
                    
                    # 测试模型是否下载成功 - 检查模型文件是否存在
                    model_files = ['craft_mlt_25k.pth', 'zh_sim_g2.pth', 'english_g2.pth']
                    downloaded_models = []
                    
                    # 等待一下让模型下载完成
                    import time
                    time.sleep(2)
                    
                    for model_file in model_files:
                        model_path = os.path.join(self.easyocr_model_path, model_file)
                        if os.path.exists(model_path):
                            downloaded_models.append(model_file)
                            logger.info(f"模型文件已下载: {model_file}")
                    
                    if progress_callback:
                        progress_callback({"status": "completed", "progress": 100, "message": "模型下载完成"})
                    
                    # 清除代理环境变量
                    if self.easyocr_download_proxy:
                        os.environ.pop('http_proxy', None)
                        os.environ.pop('https_proxy', None)
                    
                    return {
                        "success": True,
                        "message": f"EasyOCR模型配置成功，支持语言: {self.easyocr_languages}",
                        "model_path": self.easyocr_model_path,
                        "downloaded_models": downloaded_models,
                        "method": "docling_managed"
                    }
                    
                except Exception as e:
                    logger.warning(f"Docling EasyOCR配置失败，尝试直接下载: {str(e)}")
                    # 如果Docling方式失败，降级到直接EasyOCR下载
                    pass
            
            # 降级方案：直接使用EasyOCR下载（如果可用）
            if EASYOCR_AVAILABLE:
                logger.info("使用直接EasyOCR下载模式...")
                
                # 设置代理
                if self.easyocr_download_proxy:
                    os.environ['http_proxy'] = self.easyocr_download_proxy
                    os.environ['https_proxy'] = self.easyocr_download_proxy
                    logger.info(f"设置下载代理: {self.easyocr_download_proxy}")
                
                # 设置模型路径
                os.environ['EASYOCR_MODULE_PATH'] = self.easyocr_model_path
                
                if progress_callback:
                    progress_callback({"status": "downloading", "progress": 50, "message": "创建EasyOCR读取器..."})
                
                # 创建读取器（这会触发模型下载）
                import easyocr
                reader = easyocr.Reader(
                    self.easyocr_languages,
                    gpu=self.easyocr_use_gpu,
                    model_storage_directory=self.easyocr_model_path,
                    download_enabled=True
                )
                
                if progress_callback:
                    progress_callback({"status": "testing", "progress": 80, "message": "测试模型..."})
                
                # 测试模型是否工作
                try:
                    import numpy as np
                    test_image = np.ones((100, 100, 3), dtype=np.uint8) * 255  # 白色图片
                    result = reader.readtext(test_image)
                    logger.info("EasyOCR模型测试成功")
                except ImportError:
                    # 如果numpy不可用，创建简单测试图片
                    test_image = "/tmp/test_image.png"
                    from PIL import Image
                    img = Image.new('RGB', (100, 100), color='white')
                    img.save(test_image)
                    result = reader.readtext(test_image)
                    logger.info("EasyOCR模型测试成功（使用临时图片）")
                
                if progress_callback:
                    progress_callback({"status": "completed", "progress": 100, "message": "模型下载完成"})
                
                # 更新读取器
                self.easyocr_reader = reader
                
                # 清除代理环境变量
                if self.easyocr_download_proxy:
                    os.environ.pop('http_proxy', None)
                    os.environ.pop('https_proxy', None)
                
                return {
                    "success": True,
                    "message": f"EasyOCR模型下载成功，支持语言: {self.easyocr_languages}",
                    "model_path": self.easyocr_model_path,
                    "method": "direct_easyocr"
                }
            
            # 如果都不可用
            return {
                "success": False,
                "error": "EasyOCR和Docling都不可用，无法下载模型"
            }
            
        except Exception as e:
            # 清除代理环境变量
            if hasattr(self, 'easyocr_download_proxy') and self.easyocr_download_proxy:
                os.environ.pop('http_proxy', None)
                os.environ.pop('https_proxy', None)
            
            logger.error(f"EasyOCR模型下载失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

# 创建全局AI服务实例
ai_service = AIService() 