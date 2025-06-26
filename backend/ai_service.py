import os
import json
import time
import base64
import logging
from typing import Dict, List, Optional, Tuple, Any, Callable
from datetime import datetime
import openai
import pytesseract
import cv2
import numpy as np
from PIL import Image
import pdfplumber
import docx
from io import BytesIO
import httpx

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIService:
    """AI服务类，提供各种AI能力"""
    
    def __init__(self):
        self.ai_provider = os.getenv("AI_PROVIDER", "openai").lower()
        self.enable_ai = os.getenv("ENABLE_AI", "true").lower() == "true"
        
        # 初始化AI客户端
        self.ai_client = None
        if self.enable_ai:
            self._init_ai_client()
    
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
            
            # 如果数据库中没有，尝试从环境变量获取
            env_mapping = {
                "ai_provider": "AI_PROVIDER",
                "ai_text_model": f"{self.ai_provider.upper()}_MODEL" if hasattr(self, 'ai_provider') else "OPENAI_MODEL",
                "ai_vision_model": f"{self.ai_provider.upper()}_VISION_MODEL" if hasattr(self, 'ai_provider') else "OPENAI_VISION_MODEL",
                "ai_api_key": f"{self.ai_provider.upper()}_API_KEY" if hasattr(self, 'ai_provider') else "OPENAI_API_KEY",
                "ai_base_url": f"{self.ai_provider.upper()}_BASE_URL" if hasattr(self, 'ai_provider') else "OPENAI_BASE_URL"
            }
            
            env_key = env_mapping.get(key, key.upper())
            return os.getenv(env_key, default)
            
        except Exception as e:
            logger.warning(f"无法从数据库获取设置 {key}: {str(e)}")
            # 回退到环境变量
            return os.getenv(key.upper(), default)
        finally:
            try:
                db.close()
            except:
                pass
    
    def reload_config(self):
        """重新加载配置并重新初始化AI客户端"""
        try:
            logger.info("重新加载AI服务配置...")
            
            # 重新读取AI提供商设置
            self.ai_provider = self._get_setting_value("ai_provider", "openai").lower()
            self.enable_ai = self._get_setting_value("enable_ai", "true").lower() == "true"
            
            # 重新初始化AI客户端
            self.ai_client = None
            if self.enable_ai:
                self._init_ai_client()
                
            logger.info(f"AI服务配置重载完成，当前提供商: {self.ai_provider}")
            
        except Exception as e:
            logger.error(f"重新加载AI配置失败: {str(e)}")
    
    def _init_ai_client(self):
        """初始化AI客户端"""
        try:
            if self.ai_provider == "openai":
                self.ai_client = openai.OpenAI(
                    api_key=self._get_setting_value("ai_api_key", os.getenv("OPENAI_API_KEY", "")),
                    base_url=self._get_setting_value("ai_base_url", os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"))
                )
                self.model = self._get_setting_value("ai_text_model", os.getenv("OPENAI_MODEL", "gpt-4"))
                self.vision_model = self._get_setting_value("ai_vision_model", os.getenv("OPENAI_VISION_MODEL", "gpt-4-vision-preview"))
                
            elif self.ai_provider == "azure":
                from openai import AzureOpenAI
                self.ai_client = AzureOpenAI(
                    api_key=self._get_setting_value("ai_api_key", os.getenv("AZURE_OPENAI_API_KEY", "")),
                    api_version=self._get_setting_value("azure_api_version", os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01")),
                    azure_endpoint=self._get_setting_value("azure_endpoint", os.getenv("AZURE_OPENAI_ENDPOINT", ""))
                )
                self.model = self._get_setting_value("ai_text_model", os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4"))
                self.vision_model = self._get_setting_value("ai_vision_model", os.getenv("AZURE_OPENAI_VISION_DEPLOYMENT_NAME", "gpt-4-vision"))
                
            elif self.ai_provider == "custom":
                # 兼容OpenAI API的自定义服务
                self.ai_client = openai.OpenAI(
                    api_key=self._get_setting_value("ai_api_key", os.getenv("CUSTOM_AI_API_KEY", "")),
                    base_url=self._get_setting_value("ai_base_url", os.getenv("CUSTOM_AI_BASE_URL", ""))
                )
                self.model = self._get_setting_value("ai_text_model", os.getenv("CUSTOM_AI_MODEL", "gpt-4"))
                self.vision_model = self._get_setting_value("ai_vision_model", os.getenv("CUSTOM_AI_VISION_MODEL", "gpt-4-vision"))
                
            else:
                logger.warning(f"不支持的AI提供商: {self.ai_provider}，将禁用AI功能")
                self.enable_ai = False
            
            if self.ai_client:
                logger.info(f"AI客户端初始化成功 - 提供商: {self.ai_provider}, 文本模型: {self.model}, 视觉模型: {self.vision_model}")
                
        except Exception as e:
            logger.error(f"初始化AI客户端失败: {str(e)}")
            self.enable_ai = False
    
    async def extract_text_from_image(self, image_path: str) -> Dict:
        """从图片中提取文字"""
        try:
            start_time = time.time()
            
            # 使用Tesseract OCR
            image = cv2.imread(image_path)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # 图像预处理
            gray = cv2.medianBlur(gray, 3)
            gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
            
            # OCR识别
            text = pytesseract.image_to_string(gray, lang='chi_sim+eng')
            
            processing_time = time.time() - start_time
            
            return {
                "text": text,
                "confidence": 0.8,  # 默认置信度
                "processing_time": processing_time,
                "method": "tesseract"
            }
            
        except Exception as e:
            logger.error(f"OCR处理失败: {str(e)}")
            return {
                "text": "",
                "confidence": 0.0,
                "processing_time": 0,
                "error": str(e)
            }
    
    async def extract_text_from_pdf(self, pdf_path: str) -> Dict:
        """从PDF中提取文字"""
        try:
            start_time = time.time()
            text_content = []
            
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    text = page.extract_text()
                    if text:
                        text_content.append({
                            "page": page_num + 1,
                            "text": text
                        })
            
            processing_time = time.time() - start_time
            
            return {
                "content": text_content,
                "total_pages": len(text_content),
                "processing_time": processing_time,
                "method": "pdfplumber"
            }
            
        except Exception as e:
            logger.error(f"PDF文字提取失败: {str(e)}")
            return {
                "content": [],
                "total_pages": 0,
                "processing_time": 0,
                "error": str(e)
            }
    
    async def extract_text_from_docx(self, docx_path: str) -> Dict:
        """从Word文档中提取文字"""
        try:
            start_time = time.time()
            
            doc = docx.Document(docx_path)
            text_content = []
            
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_content.append(paragraph.text)
            
            processing_time = time.time() - start_time
            
            return {
                "content": text_content,
                "full_text": "\n".join(text_content),
                "processing_time": processing_time,
                "method": "python-docx"
            }
            
        except Exception as e:
            logger.error(f"Word文档提取失败: {str(e)}")
            return {
                "content": [],
                "full_text": "",
                "processing_time": 0,
                "error": str(e)
            }
    
    async def analyze_award_document(self, text: str) -> Dict:
        """分析获奖文档内容"""
        if not self.enable_ai or not self.ai_client:
            return {
                "analysis": {"awards": [], "confidence": 0.0},
                "confidence": 0.0,
                "processing_time": 0,
                "message": "AI功能未启用或配置错误"
            }
            
        try:
            start_time = time.time()
            
            prompt = self._get_award_analysis_prompt()
            
            response = await self._call_ai_api(
                prompt=prompt,
                content=text,
                max_tokens=1500
            )
            
            processing_time = time.time() - start_time
            
            # 解析AI返回的结构化数据
            try:
                analysis_result = json.loads(response)
            except json.JSONDecodeError:
                # 如果返回的不是JSON，尝试提取关键信息
                analysis_result = self._parse_award_response(response)
            
            return {
                "analysis": analysis_result,
                "confidence": analysis_result.get("confidence", 0.7),
                "processing_time": processing_time,
                "raw_response": response
            }
            
        except Exception as e:
            logger.error(f"获奖文档分析失败: {str(e)}")
            return {
                "analysis": {},
                "confidence": 0.0,
                "processing_time": 0,
                "error": str(e)
            }
    
    async def analyze_performance_document(self, text: str) -> Dict:
        """分析业绩文档内容"""
        if not self.enable_ai or not self.ai_client:
            return {
                "analysis": {"performances": [], "confidence": 0.0},
                "confidence": 0.0,
                "processing_time": 0,
                "message": "AI功能未启用或配置错误"
            }
            
        try:
            start_time = time.time()
            
            prompt = self._get_performance_analysis_prompt()
            
            response = await self._call_ai_api(
                prompt=prompt,
                content=text,
                max_tokens=1500
            )
            
            processing_time = time.time() - start_time
            
            # 解析AI返回的结构化数据
            try:
                analysis_result = json.loads(response)
            except json.JSONDecodeError:
                analysis_result = self._parse_performance_response(response)
            
            return {
                "analysis": analysis_result,
                "confidence": analysis_result.get("confidence", 0.7),
                "processing_time": processing_time,
                "raw_response": response
            }
            
        except Exception as e:
            logger.error(f"业绩文档分析失败: {str(e)}")
            return {
                "analysis": {},
                "confidence": 0.0,
                "processing_time": 0,
                "error": str(e)
            }
    
    async def analyze_image_content(self, image_path: str) -> Dict:
        """分析图像内容"""
        if not self.enable_ai or not self.ai_client:
            return {
                "description": "AI功能未启用或配置错误",
                "processing_time": 0,
                "method": "disabled"
            }
            
        try:
            start_time = time.time()
            
            # 转换图像为base64
            with open(image_path, "rb") as image_file:
                image_base64 = base64.b64encode(image_file.read()).decode('utf-8')
            
            # 使用Vision API分析图像
            response = await self._call_vision_api(image_base64)
            
            processing_time = time.time() - start_time
            
            return {
                "description": response,
                "processing_time": processing_time,
                "method": f"{self.ai_provider}-vision"
            }
            
        except Exception as e:
            logger.error(f"图像分析失败: {str(e)}")
            return {
                "description": "",
                "processing_time": 0,
                "error": str(e)
            }
    
    async def _call_ai_api(self, prompt: str, content: str, max_tokens: int = 1000) -> str:
        """调用AI API"""
        if not self.ai_client:
            raise Exception("AI客户端未初始化")
            
        try:
            response = await self.ai_client.chat.completions.acreate(
                model=self.model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": content}
                ],
                max_tokens=max_tokens,
                temperature=0.3
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"AI API调用失败: {str(e)}")
            raise e
    
    async def _call_vision_api(self, image_base64: str) -> str:
        """调用Vision API"""
        if not self.ai_client:
            raise Exception("AI客户端未初始化")
            
        try:
            response = await self.ai_client.chat.completions.acreate(
                model=self.vision_model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "请分析这张图片的内容，如果是获奖证书或法律行业相关文档，请详细描述奖项信息、获奖方、年份等关键信息。请用中文回答。"
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Vision API调用失败: {str(e)}")
            raise e
    
    def _get_award_analysis_prompt(self) -> str:
        """获取获奖分析提示词"""
        return """
你是一个专业的法律行业获奖信息分析专家。请分析以下文档内容，提取获奖相关信息。

支持的厂牌包括（请使用标准名称）：
- Chambers (Chambers and Partners)
- Legal 500 (The Legal 500)
- IFLR (International Financial Law Review)
- Who's Who Legal
- Best Lawyers
- ALB (Asian Legal Business)
- Legal Band
- Asialaw
- China Law & Practice
- IAM (Intellectual Asset Management)
- Global Arbitration Review
- Global Competition Review
- Benchmark Litigation
- China Business Law Journal
等知名法律评级机构

业务类型分类（请使用以下标准分类）：
- 公司法律服务：公司业务、并购重组、外商投资、私募股权/风险投资、公司治理、合规与监管
- 金融法律服务：银行与金融、资本市场、债券发行、资产证券化、基金与资产管理、保险法
- 争议解决：争议解决、国际仲裁、商事仲裁、诉讼代理、跨境争议
- 专业法律领域：知识产权、专利申请与保护、商标注册与维权、反不正当竞争
- 基础设施与能源：建设工程、基础设施、能源法、环境法、新能源
- 房地产：房地产、土地使用权、房地产开发、城市更新
- 国际贸易：国际贸易、航运海事、海关与贸易合规
- 税务财务：税法、税务争议、税务筹划、国际税务
- 新兴业务：医疗健康、互联网、人工智能、金融科技
- 跨境业务：跨境投资、境外上市、一带一路

请按照以下JSON格式返回结果：
{
    "awards": [
        {
            "title": "奖项名称",
            "brand": "厂牌名称（使用上述标准名称）",
            "year": 年份,
            "business_type": "业务类型（使用上述标准分类）",
            "description": "获奖描述",
            "url": "相关链接（如果有）",
            "confidence": 置信度(0-1)
        }
    ],
    "confidence": 整体置信度(0-1)
}

注意：
1. 如果文档中包含多个奖项，请全部提取
2. 厂牌名称必须使用上述标准名称，不要使用缩写或别名
3. 业务类型必须从上述分类中选择最匹配的类别
4. 如果某些信息不确定，请在confidence中体现
5. 年份应为4位数字格式
"""
    
    def _get_performance_analysis_prompt(self) -> str:
        """获取业绩分析提示词"""
        return """
你是一个专业的法律服务业绩信息分析专家。请分析以下文档内容，提取业绩相关信息。

业务领域标准分类（请使用以下分类）：
- 公司法律服务：公司业务、并购重组、外商投资、私募股权/风险投资、公司治理、合规与监管、反垄断与竞争法、数据保护与隐私、公司重组与破产
- 金融法律服务：银行与金融、资本市场、债券发行、资产证券化、基金与资产管理、保险法、融资租赁、金融科技、绿色金融、REITs
- 争议解决：争议解决、国际仲裁、商事仲裁、诉讼代理、调解服务、执行与保全、跨境争议、建设工程争议、金融争议
- 专业法律领域：知识产权、专利申请与保护、商标注册与维权、版权保护、商业秘密、反不正当竞争、娱乐法、体育法、网络法、电子商务法
- 基础设施与能源：建设工程、基础设施、能源法、石油天然气、电力法、新能源、环境法、碳中和与ESG、矿业法
- 房地产与土地：房地产、土地使用权、房地产开发、房地产投资、物业管理、城市更新、特色小镇、产业园区
- 国际贸易与海事：国际贸易、海关与贸易合规、反倾销与反补贴、自贸区业务、航运海事、船舶金融、货物运输、海事保险、港口法务
- 劳动与社会保障：劳动法、劳动争议、人力资源、社会保险、工伤赔偿、劳动合规、外籍员工、高管激励
- 税务与财务：税法、税务争议、税务筹划、国际税务、转让定价、关税与进出口税、增值税、企业所得税、个人所得税
- 新兴业务领域：医疗健康、生物医药、医疗器械、互联网、人工智能、区块链、虚拟货币、游戏法、教育法、食品药品
- 政府与公共事务：政府法律顾问、PPP项目、政府采购、行政法、刑事辩护、反腐败与职务犯罪、监察法、国家安全法
- 跨境业务：跨境投资、境外上市、QFII/QDII、外汇管理、国际制裁、一带一路、中美贸易、跨境数据传输、跨境电商
- 特殊行业：航空航天、汽车制造、化工医药、电信通信、传媒娱乐、金融科技、新零售、供应链金融、农业法、旅游法

项目类型分类：
- 长期顾问：为客户提供长期法律顾问服务
- 重大个案：为客户处理特定重大法律事务

请按照以下JSON格式返回结果：
{
    "performances": [
        {
            "client_name": "客户名称",
            "project_name": "项目名称",
            "project_type": "项目类型（长期顾问/重大个案）",
            "business_field": "业务领域（使用上述标准分类）",
            "start_date": "开始日期（YYYY-MM-DD格式）",
            "end_date": "结束日期（YYYY-MM-DD格式）",
            "year": 年份,
            "contract_amount": 合同金额,
            "currency": "货币单位（CNY/USD/EUR/HKD等）",
            "description": "项目描述",
            "confidence": 置信度(0-1)
        }
    ],
    "confidence": 整体置信度(0-1)
}

注意：
1. 如果是合同文档，重点提取合同金额、服务期限等信息
2. 如果是业绩汇总文档，提取所有项目信息
3. 日期格式请统一为YYYY-MM-DD
4. 金额请提取数字部分，货币单位单独标注
5. 业务领域必须从上述分类中选择最匹配的类别
6. 项目类型只能是"长期顾问"或"重大个案"
7. 年份应为4位数字格式
"""
    
    def _parse_award_response(self, response: str) -> Dict:
        """解析获奖分析响应（备用方法）"""
        # 简单的文本解析逻辑
        return {
            "awards": [],
            "confidence": 0.5,
            "raw_text": response
        }
    
    def _parse_performance_response(self, response: str) -> Dict:
        """解析业绩分析响应（备用方法）"""
        # 简单的文本解析逻辑
        return {
            "performances": [],
            "confidence": 0.5,
            "raw_text": response
        }

    async def chat_with_tools(
        self, 
        user_message: str, 
        system_prompt: str = "",
        tools: List[Dict[str, Any]] = None,
        tool_executor: Callable = None,
        max_tokens: int = 2000
    ) -> Dict[str, Any]:
        """支持工具调用的AI对话"""
        try:
            if not self.enable_ai or not self.ai_client:
                return {
                    "success": False,
                    "error": "AI服务未启用或未初始化"
                }
            
            # 构建消息历史
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            
            messages.append({"role": "user", "content": user_message})
            
            # 构建工具定义
            tool_definitions = []
            if tools:
                for tool in tools:
                    tool_definitions.append({
                        "type": "function",
                        "function": {
                            "name": tool["name"],
                            "description": tool["description"],
                            "parameters": {
                                "type": "object",
                                "properties": tool["parameters"],
                                "required": [k for k, v in tool["parameters"].items() if "default" not in v]
                            }
                        }
                    })
            
            # 调用AI API
            response = await self._call_ai_api_with_tools(
                messages=messages,
                tools=tool_definitions,
                max_tokens=max_tokens
            )
            
            # 处理工具调用
            tools_used = []
            if response.get("choices") and response["choices"][0].get("message", {}).get("tool_calls"):
                tool_calls = response["choices"][0]["message"]["tool_calls"]
                
                for tool_call in tool_calls:
                    tool_name = tool_call["function"]["name"]
                    tool_args = json.loads(tool_call["function"]["arguments"])
                    
                    # 执行工具
                    if tool_executor:
                        try:
                            tool_result = await tool_executor(tool_name, tool_args)
                            tools_used.append({
                                "tool_name": tool_name,
                                "arguments": tool_args,
                                "result": tool_result
                            })
                        except Exception as e:
                            logger.error(f"工具执行失败 {tool_name}: {str(e)}")
                            tools_used.append({
                                "tool_name": tool_name,
                                "arguments": tool_args,
                                "error": str(e)
                            })
            
            # 如果有工具调用结果，再次调用AI进行总结
            if tools_used:
                # 构建包含工具结果的用户消息
                tool_results_message = f"""
用户问题：{user_message}

已执行的工具和结果：
{json.dumps(tools_used, ensure_ascii=False, indent=2)}

请根据工具执行结果，为用户提供完整的回答。
"""
                
                messages.append({"role": "user", "content": tool_results_message})
                
                # 再次调用AI
                final_response = await self._call_ai_api_with_tools(
                    messages=messages,
                    tools=[],  # 不再需要工具调用
                    max_tokens=max_tokens
                )
                
                return {
                    "success": True,
                    "response": final_response["choices"][0]["message"]["content"],
                    "tools_used": tools_used,
                    "raw_response": final_response
                }
            else:
                return {
                    "success": True,
                    "response": response["choices"][0]["message"]["content"],
                    "tools_used": [],
                    "raw_response": response
                }
                
        except Exception as e:
            logger.error(f"AI工具对话失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def analyze_text(self, prompt: str, max_tokens: int = 2000) -> Dict[str, Any]:
        """分析文本内容"""
        try:
            if not self.enable_ai or not self.ai_client:
                return {
                    "success": False,
                    "error": "AI服务未启用或未初始化"
                }
            
            messages = [
                {"role": "system", "content": "你是一个专业的法律文档分析助手，请根据用户的要求分析文档内容。"},
                {"role": "user", "content": prompt}
            ]
            
            response = await self._call_ai_api_with_tools(
                messages=messages,
                tools=[],
                max_tokens=max_tokens
            )
            
            return {
                "success": True,
                "analysis": response["choices"][0]["message"]["content"],
                "raw_response": response
            }
            
        except Exception as e:
            logger.error(f"文本分析失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _call_ai_api_with_tools(
        self, 
        messages: List[Dict[str, Any]], 
        tools: List[Dict[str, Any]] = None,
        max_tokens: int = 2000
    ) -> Dict[str, Any]:
        """调用支持工具的AI API"""
        try:
            if self.ai_provider == "openai":
                kwargs = {
                    "model": self.model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": 0.7
                }
                
                if tools:
                    kwargs["tools"] = tools
                    kwargs["tool_choice"] = "auto"
                
                response = self.ai_client.chat.completions.create(**kwargs)
                return response.model_dump()
                
            elif self.ai_provider == "azure":
                kwargs = {
                    "model": self.model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": 0.7
                }
                
                if tools:
                    kwargs["tools"] = tools
                    kwargs["tool_choice"] = "auto"
                
                response = self.ai_client.chat.completions.create(**kwargs)
                return response.model_dump()
                
            elif self.ai_provider == "custom":
                kwargs = {
                    "model": self.model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": 0.7
                }
                
                if tools:
                    kwargs["tools"] = tools
                    kwargs["tool_choice"] = "auto"
                
                response = self.ai_client.chat.completions.create(**kwargs)
                return response.model_dump()
                
            else:
                raise ValueError(f"不支持的AI提供商: {self.ai_provider}")
                
        except Exception as e:
            logger.error(f"AI API调用失败: {str(e)}")
            raise e

# 创建全局AI服务实例
ai_service = AIService() 