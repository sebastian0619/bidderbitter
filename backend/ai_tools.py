#!/usr/bin/env python3
"""
AI工具系统
提供网页读取、数据库操作、文档处理等工具供AI调用
"""

import asyncio
import json
import logging
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import aiohttp
from sqlalchemy import text
from sqlalchemy.orm import Session
from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.datamodel.accelerator_options import AcceleratorDevice, AcceleratorOptions
import requests
from bs4 import BeautifulSoup
import re
import os

from database import SessionLocal
from models import Award, Performance, Project, SearchTask, SearchResult

logger = logging.getLogger(__name__)

class WebReader:
    """网页读取工具"""
    
    def __init__(self):
        self.session = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(headers=self.headers)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def read_webpage(self, url: str, timeout: int = 30) -> Dict[str, Any]:
        """读取网页内容"""
        try:
            async with self.session.get(url, timeout=timeout) as response:
                if response.status == 200:
                    content = await response.text()
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    # 提取关键信息
                    title = soup.find('title')
                    title_text = title.get_text() if title else ""
                    
                    # 提取正文内容
                    body = soup.find('body')
                    if body:
                        # 移除脚本和样式
                        for script in body(["script", "style"]):
                            script.decompose()
                        
                        # 获取文本内容
                        text_content = body.get_text()
                        # 清理文本
                        text_content = re.sub(r'\s+', ' ', text_content).strip()
                    else:
                        text_content = ""
                    
                    # 提取链接
                    links = []
                    for link in soup.find_all('a', href=True):
                        links.append({
                            'text': link.get_text().strip(),
                            'url': link['href']
                        })
                    
                    # 提取表格数据
                    tables = []
                    for table in soup.find_all('table'):
                        table_data = []
                        for row in table.find_all('tr'):
                            row_data = []
                            for cell in row.find_all(['td', 'th']):
                                row_data.append(cell.get_text().strip())
                            if row_data:
                                table_data.append(row_data)
                        if table_data:
                            tables.append(table_data)
                    
                    return {
                        'success': True,
                        'url': url,
                        'title': title_text,
                        'content': text_content,
                        'links': links,
                        'tables': tables,
                        'status_code': response.status
                    }
                else:
                    return {
                        'success': False,
                        'url': url,
                        'error': f'HTTP {response.status}',
                        'status_code': response.status
                    }
        except Exception as e:
            logger.error(f"读取网页失败 {url}: {str(e)}")
            return {
                'success': False,
                'url': url,
                'error': str(e)
            }
    
    async def search_legal_awards(self, law_firm: str, year: int, source: str = "chambers") -> List[Dict[str, Any]]:
        """搜索法律奖项信息"""
        results = []
        
        if source.lower() == "chambers":
            # 构建Chambers搜索URL
            search_url = f"https://chambers.com/legal-guide/search?q={law_firm}"
            webpage_data = await self.read_webpage(search_url)
            
            if webpage_data['success']:
                # 解析搜索结果
                content = webpage_data['content']
                
                # 使用正则表达式查找奖项信息
                award_patterns = [
                    r'(\d{4})\s*([A-Z][^.]*?)\s*(?:Tier\s*(\d+))?',
                    r'([A-Z][^.]*?)\s*(\d{4})\s*(?:Tier\s*(\d+))?',
                ]
                
                for pattern in award_patterns:
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        if str(year) in match.group(0):
                            results.append({
                                'law_firm': law_firm,
                                'award_name': match.group(2) if match.group(1).isdigit() else match.group(1),
                                'year': int(match.group(1)) if match.group(1).isdigit() else int(match.group(2)),
                                'tier': match.group(3) if match.group(3) else None,
                                'source': source,
                                'confidence': 0.8
                            })
        
        return results

class DatabaseTool:
    """数据库操作工具"""
    
    def __init__(self):
        self.db = SessionLocal()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db.close()
    
    def execute_query(self, query: str, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """执行SQL查询"""
        try:
            result = self.db.execute(text(query), params or {})
            columns = result.keys()
            return [dict(zip(columns, row)) for row in result.fetchall()]
        except Exception as e:
            logger.error(f"数据库查询失败: {str(e)}")
            return []
    
    def get_awards_by_firm(self, law_firm: str, year: int = None) -> List[Dict[str, Any]]:
        """根据律师事务所获取奖项"""
        query = """
        SELECT id, title, brand, year, business_type, description, is_verified
        FROM awards 
        WHERE title ILIKE :firm_pattern
        """
        params = {'firm_pattern': f'%{law_firm}%'}
        
        if year:
            query += " AND year = :year"
            params['year'] = year
        
        query += " ORDER BY year DESC"
        
        return self.execute_query(query, params)
    
    def get_performances_by_firm(self, law_firm: str, year: int = None) -> List[Dict[str, Any]]:
        """根据律师事务所获取业绩"""
        query = """
        SELECT id, client_name, project_name, business_field, year, contract_amount, description
        FROM performances 
        WHERE client_name ILIKE :firm_pattern OR project_name ILIKE :firm_pattern
        """
        params = {'firm_pattern': f'%{law_firm}%'}
        
        if year:
            query += " AND year = :year"
            params['year'] = year
        
        query += " ORDER BY year DESC"
        
        return self.execute_query(query, params)
    
    def search_similar_awards(self, award_title: str, business_field: str = None) -> List[Dict[str, Any]]:
        """搜索相似奖项"""
        query = """
        SELECT id, title, brand, year, business_type, description
        FROM awards 
        WHERE (title ILIKE :title_pattern OR business_type ILIKE :field_pattern)
        AND is_verified = true
        ORDER BY year DESC
        LIMIT 10
        """
        params = {
            'title_pattern': f'%{award_title}%',
            'field_pattern': f'%{business_field}%' if business_field else f'%{award_title}%'
        }
        
        return self.execute_query(query, params)
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计数据"""
        queries = {
            'total_awards': "SELECT COUNT(*) as count FROM awards",
            'verified_awards': "SELECT COUNT(*) as count FROM awards WHERE is_verified = true",
            'total_performances': "SELECT COUNT(*) as count FROM performances",
            'verified_performances': "SELECT COUNT(*) as count FROM performances WHERE is_verified = true",
            'awards_by_year': """
                SELECT year, COUNT(*) as count 
                FROM awards 
                GROUP BY year 
                ORDER BY year DESC 
                LIMIT 5
            """,
            'top_brands': """
                SELECT brand, COUNT(*) as count 
                FROM awards 
                GROUP BY brand 
                ORDER BY count DESC 
                LIMIT 5
            """
        }
        
        stats = {}
        for key, query in queries.items():
            result = self.execute_query(query)
            if result:
                stats[key] = result[0]['count'] if 'count' in result[0] else result
        
        return stats

class DocumentProcessor:
    """文档处理工具，使用Docling"""
    
    def __init__(self):
        """初始化Docling处理器"""
        try:
            # 配置PDF处理选项 - 根据Docling文档规范
            pipeline_options = PdfPipelineOptions(
                do_ocr=True,
                do_table_structure=True,
                generate_page_images=False,
                generate_picture_images=False,
                generate_parsed_pages=True,
                generate_table_images=False,
                force_backend_text=False
            )
            
            # 配置加速选项
            pipeline_options.accelerator_options = AcceleratorOptions(
                num_threads=4, 
                device=AcceleratorDevice.CPU
            )
            
            # 创建转换器
            self.converter = DocumentConverter(
                format_options={
                    InputFormat.PDF: pipeline_options
                }
            )
            logger.info("Docling转换器创建成功")
        except Exception as e:
            logger.error(f"创建Docling转换器失败: {e}")
            self.converter = None

    async def process_document(self, file_path: str) -> Dict[str, Any]:
        """使用Docling处理文档"""
        try:
            if not os.path.exists(file_path):
                return {"success": False, "error": f"文件未找到: {file_path}"}
            
            if not self.converter:
                return {"success": False, "error": "Docling转换器未初始化"}
            
            # 使用Docling解析文档
            conv_result = self.converter.convert(file_path)
            document = conv_result.document
            
            # 提取信息
            title = self._extract_title(document)
            content = document.export_to_text()
            tables = self._extract_tables(document)
            images = self._extract_images(document)
            metadata = self._extract_metadata(document)
            
            return {
                "success": True,
                "file_path": file_path,
                "title": title,
                "content": content,
                "tables": tables,
                "images": images,
                "metadata": metadata
            }
        except Exception as e:
            logger.error(f"使用Docling处理文档失败 {file_path}: {str(e)}")
            return {"success": False, "error": str(e)}

    def _extract_title(self, document) -> str:
        """从文档中提取标题"""
        try:
            # 使用Docling的文本导出功能
            text_content = document.export_to_text()
            if text_content:
                lines = text_content.split('\n')
                for line in lines:
                    if line.strip():
                        return line.strip()
            return "无标题"
        except Exception as e:
            logger.error(f"提取标题失败: {e}")
            return "无标题"

    def _extract_tables(self, document) -> List[Dict[str, Any]]:
        """从文档中提取表格"""
        try:
            # 使用Docling的表格导出功能
            extracted_tables = []
            # 这里需要根据实际的Docling API来提取表格
            # 暂时返回空列表
            return extracted_tables
        except Exception as e:
            logger.error(f"提取表格失败: {e}")
            return []

    def _extract_images(self, document) -> List[Dict[str, Any]]:
        """从文档中提取图片"""
        try:
            # 使用Docling的图片导出功能
            extracted_images = []
            # 这里需要根据实际的Docling API来提取图片
            # 暂时返回空列表
            return extracted_images
        except Exception as e:
            logger.error(f"提取图片失败: {e}")
            return []

    def _extract_metadata(self, document) -> Dict[str, Any]:
        """提取文档元数据"""
        try:
            # 使用Docling的元数据导出功能
            metadata = {}
            # 这里需要根据实际的Docling API来提取元数据
            # 暂时返回空字典
            return metadata
        except Exception as e:
            logger.error(f"提取元数据失败: {e}")
            return {}

class AIToolManager:
    """AI工具管理器"""
    
    def __init__(self):
        self.web_reader = None
        self.db_tool = None
        self.doc_processor = DocumentProcessor()
    
    async def get_tools(self) -> List[Dict[str, Any]]:
        """获取可用工具列表"""
        return [
            {
                "name": "read_webpage",
                "description": "读取网页内容，提取文本、链接、表格等信息",
                "parameters": {
                    "url": {"type": "string", "description": "要读取的网页URL"},
                    "timeout": {"type": "integer", "description": "超时时间（秒）", "default": 30}
                }
            },
            {
                "name": "search_legal_awards",
                "description": "在法律评级网站搜索律师事务所的奖项信息",
                "parameters": {
                    "law_firm": {"type": "string", "description": "律师事务所名称"},
                    "year": {"type": "integer", "description": "搜索年份"},
                    "source": {"type": "string", "description": "数据源（chambers/legal500）", "default": "chambers"}
                }
            },
            {
                "name": "execute_database_query",
                "description": "执行SQL查询，获取数据库中的信息",
                "parameters": {
                    "query": {"type": "string", "description": "SQL查询语句"},
                    "params": {"type": "object", "description": "查询参数", "default": {}}
                }
            },
            {
                "name": "get_awards_by_firm",
                "description": "根据律师事务所名称获取奖项信息",
                "parameters": {
                    "law_firm": {"type": "string", "description": "律师事务所名称"},
                    "year": {"type": "integer", "description": "年份（可选）"}
                }
            },
            {
                "name": "get_performances_by_firm",
                "description": "根据律师事务所名称获取业绩信息",
                "parameters": {
                    "law_firm": {"type": "string", "description": "律师事务所名称"},
                    "year": {"type": "integer", "description": "年份（可选）"}
                }
            },
            {
                "name": "search_similar_awards",
                "description": "搜索相似的奖项信息",
                "parameters": {
                    "award_title": {"type": "string", "description": "奖项标题"},
                    "business_field": {"type": "string", "description": "业务领域（可选）"}
                }
            },
            {
                "name": "get_database_statistics",
                "description": "获取数据库统计信息",
                "parameters": {}
            },
            {
                "name": "process_document",
                "description": "使用Docling处理文档，提取结构化信息",
                "parameters": {
                    "file_path": {"type": "string", "description": "文档文件路径"}
                }
            }
        ]
    
    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """执行工具"""
        try:
            if tool_name == "read_webpage":
                async with WebReader() as reader:
                    return await reader.read_webpage(
                        parameters["url"], 
                        parameters.get("timeout", 30)
                    )
            
            elif tool_name == "search_legal_awards":
                async with WebReader() as reader:
                    return await reader.search_legal_awards(
                        parameters["law_firm"],
                        parameters["year"],
                        parameters.get("source", "chambers")
                    )
            
            elif tool_name == "execute_database_query":
                with DatabaseTool() as db:
                    return db.execute_query(
                        parameters["query"],
                        parameters.get("params", {})
                    )
            
            elif tool_name == "get_awards_by_firm":
                with DatabaseTool() as db:
                    return db.get_awards_by_firm(
                        parameters["law_firm"],
                        parameters.get("year")
                    )
            
            elif tool_name == "get_performances_by_firm":
                with DatabaseTool() as db:
                    return db.get_performances_by_firm(
                        parameters["law_firm"],
                        parameters.get("year")
                    )
            
            elif tool_name == "search_similar_awards":
                with DatabaseTool() as db:
                    return db.search_similar_awards(
                        parameters["award_title"],
                        parameters.get("business_field")
                    )
            
            elif tool_name == "get_database_statistics":
                with DatabaseTool() as db:
                    return db.get_statistics()
            
            elif tool_name == "process_document":
                return await self.doc_processor.process_document(
                    parameters["file_path"]
                )
            
            else:
                return {
                    "success": False,
                    "error": f"未知工具: {tool_name}"
                }
                
        except Exception as e:
            logger.error(f"执行工具 {tool_name} 失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

# 全局工具管理器实例
tool_manager = AIToolManager() 