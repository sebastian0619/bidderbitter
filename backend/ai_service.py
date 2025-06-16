import os
import json
import time
import base64
import logging
from typing import Dict, List, Optional, Tuple
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
        self.openai_client = openai.OpenAI(
            api_key=os.getenv("OPENAI_API_KEY", "")
        )
        
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
        try:
            start_time = time.time()
            
            prompt = self._get_award_analysis_prompt()
            
            response = await self._call_openai_api(
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
        try:
            start_time = time.time()
            
            prompt = self._get_performance_analysis_prompt()
            
            response = await self._call_openai_api(
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
        try:
            start_time = time.time()
            
            # 转换图像为base64
            with open(image_path, "rb") as image_file:
                image_base64 = base64.b64encode(image_file.read()).decode('utf-8')
            
            # 使用GPT-4V分析图像
            response = await self._call_openai_vision_api(image_base64)
            
            processing_time = time.time() - start_time
            
            return {
                "description": response,
                "processing_time": processing_time,
                "method": "gpt-4-vision"
            }
            
        except Exception as e:
            logger.error(f"图像分析失败: {str(e)}")
            return {
                "description": "",
                "processing_time": 0,
                "error": str(e)
            }
    
    async def _call_openai_api(self, prompt: str, content: str, max_tokens: int = 1000) -> str:
        """调用OpenAI API"""
        try:
            response = await self.openai_client.chat.completions.acreate(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": content}
                ],
                max_tokens=max_tokens,
                temperature=0.3
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API调用失败: {str(e)}")
            raise e
    
    async def _call_openai_vision_api(self, image_base64: str) -> str:
        """调用OpenAI Vision API"""
        try:
            response = await self.openai_client.chat.completions.acreate(
                model="gpt-4-vision-preview",
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
            logger.error(f"OpenAI Vision API调用失败: {str(e)}")
            raise e
    
    def _get_award_analysis_prompt(self) -> str:
        """获取获奖分析提示词"""
        return """
你是一个专业的法律行业获奖信息分析专家。请分析以下文档内容，提取获奖相关信息。

请按照以下JSON格式返回结果：
{
    "awards": [
        {
            "title": "奖项名称",
            "brand": "厂牌名称（如Chambers, Legal Band等）",
            "year": 年份,
            "business_type": "业务类型（如银行与金融、资本市场等）",
            "description": "获奖描述",
            "url": "相关链接（如果有）",
            "confidence": 置信度(0-1)
        }
    ],
    "confidence": 整体置信度(0-1)
}

注意：
1. 如果文档中包含多个奖项，请全部提取
2. 厂牌名称请标准化（如Chambers and Partners写作Chambers）
3. 业务类型请使用标准分类
4. 如果某些信息不确定，请在confidence中体现
"""
    
    def _get_performance_analysis_prompt(self) -> str:
        """获取业绩分析提示词"""
        return """
你是一个专业的法律服务业绩信息分析专家。请分析以下文档内容，提取业绩相关信息。

请按照以下JSON格式返回结果：
{
    "performances": [
        {
            "client_name": "客户名称",
            "project_name": "项目名称",
            "project_type": "项目类型（长期顾问/重大个案）",
            "business_field": "业务领域",
            "start_date": "开始日期（YYYY-MM-DD格式）",
            "end_date": "结束日期（YYYY-MM-DD格式）",
            "year": 年份,
            "contract_amount": 合同金额,
            "currency": "货币单位",
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

# 创建全局AI服务实例
ai_service = AIService() 