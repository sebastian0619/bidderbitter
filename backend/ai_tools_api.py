from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Body
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import json
import logging
from datetime import datetime
import re

from database import get_db
from ai_tools import tool_manager, WebReader, DatabaseTool
from ai_service import ai_service
from config_manager import config_manager

class AIAssistantRequest(BaseModel):
    user_message: str
    context: Optional[Dict[str, Any]] = None

class DocumentClassificationRequest(BaseModel):
    content: str
    classification_type: str = "both"  # document_type, business_field, both

router = APIRouter(prefix="/api/ai-tools", tags=["AI工具"])

logger = logging.getLogger(__name__)

@router.get("/tools")
async def get_available_tools():
    """获取可用工具列表"""
    try:
        tools = await tool_manager.get_tools()
        return {
            "success": True,
            "tools": tools
        }
    except Exception as e:
        logger.error(f"获取工具列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/execute")
async def execute_tool(
    tool_name: str,
    parameters: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """执行工具"""
    try:
        result = await tool_manager.execute_tool(tool_name, parameters)
        return {
            "success": True,
            "tool_name": tool_name,
            "parameters": parameters,
            "result": result
        }
    except Exception as e:
        logger.error(f"执行工具 {tool_name} 失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ai-assistant")
async def ai_assistant_with_tools(
    request: AIAssistantRequest,
    db: Session = Depends(get_db)
):
    """AI助手（支持工具调用）"""
    try:
        # 获取可用工具
        tools = await tool_manager.get_tools()
        
        # 构建系统提示词
        system_prompt = f"""
你是一个专业的法律行业投标助手，拥有以下工具可以使用：

可用工具：
{json.dumps(tools, ensure_ascii=False, indent=2)}

使用规则：
1. 当用户询问需要获取外部信息时，优先使用工具
2. 当需要查询数据库信息时，使用相应的数据库工具
3. 当需要处理文档时，使用文档处理工具
4. 工具调用格式：{{"tool_name": "工具名称", "parameters": {{"参数名": "参数值"}}}}
5. 可以连续调用多个工具来完成复杂任务
6. 始终用中文回复用户

当前上下文：{json.dumps(request.context or {}, ensure_ascii=False)}

请根据用户的问题，选择合适的工具来帮助用户。
"""

        # 调用AI服务
        response = await ai_service.chat_with_tools(
            user_message=request.user_message,
            system_prompt=system_prompt,
            tools=tools,
            tool_executor=tool_manager.execute_tool
        )
        
        return {
            "success": True,
            "response": response,
            "tools_used": response.get("tools_used", [])
        }
        
    except Exception as e:
        logger.error(f"AI助手调用失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/batch-execute")
async def batch_execute_tools(
    tool_calls: List[Dict[str, Any]],
    db: Session = Depends(get_db)
):
    """批量执行工具"""
    try:
        results = []
        for tool_call in tool_calls:
            tool_name = tool_call.get("tool_name")
            parameters = tool_call.get("parameters", {})
            
            if not tool_name:
                results.append({
                    "success": False,
                    "error": "缺少工具名称"
                })
                continue
            
            result = await tool_manager.execute_tool(tool_name, parameters)
            results.append({
                "tool_name": tool_name,
                "parameters": parameters,
                "result": result
            })
        
        return {
            "success": True,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"批量执行工具失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/smart-search")
async def smart_search_awards(
    law_firm: str,
    year: int,
    business_field: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """智能搜索奖项（结合多个工具）"""
    try:
        results = []
        
        # 1. 从数据库搜索
        with tool_manager.db_tool or DatabaseTool() as db_tool:
            db_results = db_tool.get_awards_by_firm(law_firm, year)
            results.extend([{"source": "database", "data": item} for item in db_results])
        
        # 2. 从网页搜索
        async with WebReader() as web_reader:
            web_results = await web_reader.search_legal_awards(law_firm, year, "chambers")
            results.extend([{"source": "web", "data": item} for item in web_results])
        
        # 3. 搜索相似奖项
        if business_field:
            with tool_manager.db_tool or DatabaseTool() as db_tool:
                similar_results = db_tool.search_similar_awards(law_firm, business_field)
                results.extend([{"source": "similar", "data": item} for item in similar_results])
        
        return {
            "success": True,
            "law_firm": law_firm,
            "year": year,
            "business_field": business_field,
            "total_results": len(results),
            "results": results
        }
        
    except Exception as e:
        logger.error(f"智能搜索失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/document-analysis")
async def analyze_document_with_ai(
    file_path: str,
    analysis_type: str = "general",  # general, awards, performance
    db: Session = Depends(get_db)
):
    """使用AI分析文档"""
    try:
        # 1. 使用Docling处理文档
        doc_result = await tool_manager.doc_processor.process_document(file_path)
        
        if not doc_result.get("success"):
            raise HTTPException(status_code=400, detail=f"文档处理失败: {doc_result.get('error')}")
        
        # 2. 根据分析类型构建AI提示词
        if analysis_type == "awards":
            analysis_prompt = f"""
请分析以下法律文档，提取奖项相关信息：

文档内容：
{doc_result.get('content', '')}

请提取以下信息：
1. 奖项名称
2. 颁发机构
3. 获奖年份
4. 业务领域
5. 奖项描述
6. 相关律师事务所

请以JSON格式返回结果。
"""
        elif analysis_type == "performance":
            analysis_prompt = f"""
请分析以下法律文档，提取业绩相关信息：

文档内容：
{doc_result.get('content', '')}

请提取以下信息：
1. 项目名称
2. 客户名称
3. 项目类型
4. 业务领域
5. 项目金额
6. 完成时间
7. 项目描述

请以JSON格式返回结果。
"""
        else:
            analysis_prompt = f"""
请分析以下法律文档，提取关键信息：

文档内容：
{doc_result.get('content', '')}

请提取以下信息：
1. 文档类型
2. 主要内容
3. 关键实体（律师事务所、客户、项目等）
4. 时间信息
5. 金额信息
6. 重要数据

请以JSON格式返回结果。
"""
        
        # 3. 调用AI进行分析
        ai_result = await ai_service.analyze_text(analysis_prompt)
        
        return {
            "success": True,
            "file_path": file_path,
            "analysis_type": analysis_type,
            "document_info": doc_result,
            "ai_analysis": ai_result
        }
        
    except Exception as e:
        logger.error(f"文档AI分析失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tool-status")
async def get_tool_status():
    """获取工具状态"""
    try:
        # 测试各个工具的状态
        status = {
            "web_reader": "available",
            "database_tool": "available", 
            "document_processor": "available",
            "ai_service": "available"
        }
        
        # 测试数据库连接
        try:
            with DatabaseTool() as db_tool:
                stats = db_tool.get_statistics()
                status["database_connection"] = "connected"
                status["database_stats"] = stats
        except Exception as e:
            status["database_connection"] = "error"
            status["database_error"] = str(e)
        
        return {
            "success": True,
            "status": status,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"获取工具状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/classify-document")
async def classify_document_with_ai(
    request: DocumentClassificationRequest,
    db: Session = Depends(get_db)
):
    """使用AI和动态配置分类文档"""
    try:
        results = {}
        
        # 1. 文档类型分类
        if request.classification_type in ["document_type", "both"]:
            try:
                system_prompt, user_prompt = config_manager.build_prompt(
                    "document_classification",
                    content=request.content
                )
                
                if system_prompt and user_prompt:
                    # 使用动态配置的prompt进行分类
                    classification_result = await ai_service.analyze_text(user_prompt)
                    
                    if classification_result.get("success"):
                        # 解析分类结果
                        try:
                            classification_content = classification_result.get("raw_content", "")
                            json_match = re.search(r'\{.*\}', classification_content, re.DOTALL)
                            if json_match:
                                import re
                                classification_data = json.loads(json_match.group())
                                results["document_type"] = {
                                    "type": classification_data.get("type", "unknown"),
                                    "name": classification_data.get("name", ""),
                                    "confidence": classification_data.get("confidence", 0.0),
                                    "reason": classification_data.get("reason", ""),
                                    "method": "dynamic_config_ai"
                                }
                            else:
                                # 回退到关键词分类
                                keyword_result = config_manager.classify_document_type_by_keywords(request.content)
                                if keyword_result:
                                    code, name, score = keyword_result
                                    results["document_type"] = {
                                        "type": code,
                                        "name": name,
                                        "confidence": score,
                                        "reason": "基于关键词匹配",
                                        "method": "keyword_fallback"
                                    }
                        except json.JSONDecodeError:
                            # 回退到关键词分类
                            keyword_result = config_manager.classify_document_type_by_keywords(request.content)
                            if keyword_result:
                                code, name, score = keyword_result
                                results["document_type"] = {
                                    "type": code,
                                    "name": name,
                                    "confidence": score,
                                    "reason": "AI解析失败，使用关键词匹配",
                                    "method": "keyword_fallback"
                                }
                else:
                    # 回退到关键词分类
                    keyword_result = config_manager.classify_document_type_by_keywords(request.content)
                    if keyword_result:
                        code, name, score = keyword_result
                        results["document_type"] = {
                            "type": code,
                            "name": name,
                            "confidence": score,
                            "reason": "未配置动态prompt，使用关键词匹配",
                            "method": "keyword_fallback"
                        }
            except Exception as e:
                logger.error(f"文档类型分类失败: {e}")
                results["document_type"] = {
                    "type": "unknown",
                    "name": "分类失败",
                    "confidence": 0.0,
                    "reason": f"分类异常: {str(e)}",
                    "method": "error"
                }
        
        # 2. 业务领域分类
        if request.classification_type in ["business_field", "both"]:
            try:
                system_prompt, user_prompt = config_manager.build_prompt(
                    "business_field_classification",
                    content=request.content
                )
                
                if system_prompt and user_prompt:
                    # 使用动态配置的prompt进行分类
                    business_result = await ai_service.analyze_text(user_prompt)
                    
                    if business_result.get("success"):
                        try:
                            business_content = business_result.get("raw_content", "")
                            import re
                            json_match = re.search(r'\{.*\}', business_content, re.DOTALL)
                            if json_match:
                                business_data = json.loads(json_match.group())
                                results["business_field"] = {
                                    "field": business_data.get("business_field", "unknown"),
                                    "name": business_data.get("name", "未识别"),
                                    "confidence": business_data.get("confidence", 0.0),
                                    "reason": business_data.get("reason", ""),
                                    "keywords_found": business_data.get("keywords_found", []),
                                    "method": "dynamic_config_ai"
                                }
                            else:
                                # 回退到关键词分类
                                keyword_result = config_manager.classify_business_field_by_keywords(request.content)
                                if keyword_result:
                                    code, name, score = keyword_result
                                    results["business_field"] = {
                                        "field": code,
                                        "name": name,
                                        "confidence": score,
                                        "reason": "AI解析失败，使用关键词匹配",
                                        "keywords_found": [],
                                        "method": "keyword_fallback"
                                    }
                        except json.JSONDecodeError:
                            # 回退到关键词分类
                            keyword_result = config_manager.classify_business_field_by_keywords(request.content)
                            if keyword_result:
                                code, name, score = keyword_result
                                results["business_field"] = {
                                    "field": code,
                                    "name": name,
                                    "confidence": score,
                                    "reason": "AI JSON解析失败，使用关键词匹配",
                                    "keywords_found": [],
                                    "method": "keyword_fallback"
                                }
                else:
                    # 回退到关键词分类
                    keyword_result = config_manager.classify_business_field_by_keywords(request.content)
                    if keyword_result:
                        code, name, score = keyword_result
                        results["business_field"] = {
                            "field": code,
                            "name": name,
                            "confidence": score,
                            "reason": "未配置动态prompt，使用关键词匹配",
                            "keywords_found": [],
                            "method": "keyword_fallback"
                        }
            except Exception as e:
                logger.error(f"业务领域分类失败: {e}")
                results["business_field"] = {
                    "field": "unknown",
                    "name": "分类失败",
                    "confidence": 0.0,
                    "reason": f"分类异常: {str(e)}",
                    "keywords_found": [],
                    "method": "error"
                }
        
        return {
            "success": True,
            "content_length": len(request.content),
            "classification_type": request.classification_type,
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"文档分类失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 