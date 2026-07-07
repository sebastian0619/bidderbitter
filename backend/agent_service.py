"""Agent 服务 - 内置智能代理

不是简单的 API 调用，而是完整的 Agent 系统：
- 观察 (Observe): 读取文件、查询数据库
- 思考 (Think): 分析任务、制定计划
- 行动 (Act): 执行操作、调用工具
- 反思 (Reflect): 评估结果、调整策略

基于 Hermes Agent 架构设计。
"""
import os
import json
import logging
import asyncio
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class AgentContext:
    """Agent 上下文"""
    task_id: str
    user_id: Optional[int] = None
    project_id: Optional[int] = None
    files: List[Dict] = field(default_factory=list)
    memory: List[Dict] = field(default_factory=list)
    tools_used: List[str] = field(default_factory=list)


@dataclass
class AgentStep:
    """Agent 执行步骤"""
    thought: str  # 思考过程
    action: str  # 执行的动作
    action_input: Dict  # 动作参数
    observation: str  # 观察结果
    timestamp: datetime = field(default_factory=datetime.now)


class AgentTool:
    """Agent 工具基类"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    async def execute(self, **kwargs) -> Dict:
        raise NotImplementedError


class FileReadTool(AgentTool):
    """读取文件内容"""
    
    def __init__(self):
        super().__init__("read_file", "读取文件内容")
    
    async def execute(self, file_path: str = None, file_id: int = None, **kwargs) -> Dict:
        try:
            if file_id:
                # 从数据库获取文件路径
                from models import get_db, ManagedFile
                db = next(get_db())
                file = db.query(ManagedFile).filter(ManagedFile.id == file_id).first()
                if not file:
                    return {"success": False, "error": "文件不存在"}
                file_path = file.storage_path
            
            if not file_path or not os.path.exists(file_path):
                return {"success": False, "error": "文件路径无效"}
            
            # 根据文件类型读取
            ext = Path(file_path).suffix.lower()
            
            if ext == '.pdf':
                import fitz
                doc = fitz.open(file_path)
                text = ""
                for page in doc[:10]:  # 最多读10页
                    text += page.get_text()
                doc.close()
                return {"success": True, "content": text[:5000], "pages": len(doc)}
            
            elif ext in ['.docx', '.doc']:
                from docx import Document
                doc = Document(file_path)
                text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
                return {"success": True, "content": text[:5000]}
            
            elif ext in ['.txt', '.md']:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return {"success": True, "content": f.read()[:5000]}
            
            else:
                return {"success": False, "error": f"不支持的文件类型: {ext}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}


class DatabaseQueryTool(AgentTool):
    """查询数据库"""
    
    def __init__(self):
        super().__init__("query_db", "查询数据库获取文件、项目、标签等信息")
    
    async def execute(self, query_type: str, filters: Dict = None, **kwargs) -> Dict:
        try:
            from models import get_db, ManagedFile, Project, Tag
            db = next(get_db())
            
            if query_type == "files":
                q = db.query(ManagedFile)
                if filters:
                    if filters.get("category"):
                        q = q.filter(ManagedFile.ai_category == filters["category"])
                    if filters.get("is_shared"):
                        q = q.filter(ManagedFile.is_shared == True)
                files = q.limit(50).all()
                return {
                    "success": True,
                    "results": [
                        {
                            "id": f.id,
                            "filename": f.original_filename,
                            "category": f.ai_category or f.category,
                            "tags": [t.name for t in f.tags]
                        }
                        for f in files
                    ]
                }
            
            elif query_type == "projects":
                projects = db.query(Project).limit(20).all()
                return {
                    "success": True,
                    "results": [
                        {"id": p.id, "name": p.name, "status": p.status}
                        for p in projects
                    ]
                }
            
            elif query_type == "tags":
                tags = db.query(Tag).all()
                return {
                    "success": True,
                    "results": [{"id": t.id, "name": t.name, "color": t.color} for t in tags]
                }
            
            else:
                return {"success": False, "error": f"未知查询类型: {query_type}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}


class SearchTool(AgentTool):
    """搜索文件"""
    
    def __init__(self):
        super().__init__("search_files", "搜索文件库中的文件")
    
    async def execute(self, keyword: str, category: str = None, **kwargs) -> Dict:
        try:
            from models import get_db, ManagedFile
            db = next(get_db())
            
            q = db.query(ManagedFile)
            if keyword:
                q = q.filter(
                    (ManagedFile.original_filename.contains(keyword)) |
                    (ManagedFile.description.contains(keyword)) |
                    (ManagedFile.keywords.contains(keyword))
                )
            if category:
                q = q.filter(ManagedFile.ai_category == category)
            
            files = q.limit(20).all()
            return {
                "success": True,
                "results": [
                    {
                        "id": f.id,
                        "filename": f.original_filename,
                        "category": f.ai_category or f.category,
                        "relevance": 1.0  # 简单实现
                    }
                    for f in files
                ]
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


class ClassifyTool(AgentTool):
    """分类文件"""
    
    def __init__(self):
        super().__init__("classify_file", "使用 AI 对文件进行分类")
    
    async def execute(self, filename: str, content: str = "", **kwargs) -> Dict:
        try:
            # 使用 MiMo API 进行分类
            import aiohttp
            
            prompt = f'分类：{filename}。类别：业绩/资质证照/奖项荣誉/财务资料/团队资料/公司资料/投标文件/其他。只回复JSON：{{"category":"类别"}}'
            
            headers = {
                'Authorization': f'Bearer {os.getenv("MIMO_API_KEY")}',
                'Content-Type': 'application/json'
            }
            
            body = {
                'model': os.getenv('MIMO_MODEL', 'mimo-v2.5'),
                'messages': [{'role': 'user', 'content': prompt}],
                'temperature': 0.1,
                'max_tokens': 1000
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f'{os.getenv("MIMO_BASE_URL")}/chat/completions',
                    headers=headers,
                    json=body,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        content = data['choices'][0]['message']['content']
                        
                        if content:
                            import re
                            json_match = re.search(r'\{.*\}', content, re.DOTALL)
                            if json_match:
                                result = json.loads(json_match.group())
                                return {"success": True, "category": result.get("category", "其他")}
            
            return {"success": False, "error": "分类失败"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}


class PlannerTool(AgentTool):
    """任务规划"""
    
    def __init__(self):
        super().__init__("plan_task", "规划多步骤任务")
    
    async def execute(self, task_description: str, context: Dict = None, **kwargs) -> Dict:
        try:
            import aiohttp
            
            prompt = f"""你是一个任务规划专家。请将以下任务分解为可执行的步骤。

任务：{task_description}

上下文：{json.dumps(context or {}, ensure_ascii=False)}

请返回JSON格式的计划：
{{"steps": ["步骤1", "步骤2", ...], "estimated_time": "预计时间"}}"""
            
            headers = {
                'Authorization': f'Bearer {os.getenv("MIMO_API_KEY")}',
                'Content-Type': 'application/json'
            }
            
            body = {
                'model': os.getenv('MIMO_MODEL', 'mimo-v2.5'),
                'messages': [{'role': 'user', 'content': prompt}],
                'temperature': 0.1,
                'max_tokens': 1500
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f'{os.getenv("MIMO_BASE_URL")}/chat/completions',
                    headers=headers,
                    json=body,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        content = data['choices'][0]['message']['content']
                        
                        if content:
                            import re
                            json_match = re.search(r'\{.*\}', content, re.DOTALL)
                            if json_match:
                                return {"success": True, "plan": json.loads(json_match.group())}
            
            return {"success": False, "error": "规划失败"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}


class Agent:
    """内置智能代理
    
    核心循环: Observe → Think → Act → Reflect
    """
    
    def __init__(self):
        self.tools: Dict[str, AgentTool] = {}
        self._register_default_tools()
    
    def _register_default_tools(self):
        """注册默认工具"""
        self.tools["read_file"] = FileReadTool()
        self.tools["query_db"] = DatabaseQueryTool()
        self.tools["search_files"] = SearchTool()
        self.tools["classify_file"] = ClassifyTool()
        self.tools["plan_task"] = PlannerTool()
    
    def register_tool(self, tool: AgentTool):
        """注册新工具"""
        self.tools[tool.name] = tool
    
    async def run(self, task: str, context: AgentContext = None) -> Dict:
        """执行任务
        
        Args:
            task: 任务描述
            context: Agent 上下文
        
        Returns:
            执行结果
        """
        if context is None:
            context = AgentContext(task_id=f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        
        steps = []
        max_steps = 10
        
        for step_num in range(max_steps):
            logger.info(f"Step {step_num + 1}: {task}")
            
            # 1. Think - 分析任务，决定下一步
            thought = await self._think(task, context, steps)
            
            # 2. Act - 执行动作
            action_result = await self._act(thought, context)
            
            # 3. Record - 记录步骤
            step = AgentStep(
                thought=thought.get("reasoning", ""),
                action=thought.get("action", "none"),
                action_input=thought.get("action_input", {}),
                observation=str(action_result.get("result", ""))
            )
            steps.append(step)
            context.memory.append({
                "step": step_num + 1,
                "thought": step.thought,
                "action": step.action,
                "result": step.observation[:200]
            })
            
            # 4. Check - 检查是否完成
            if action_result.get("completed", False):
                return {
                    "success": True,
                    "result": action_result.get("result"),
                    "steps": len(steps),
                    "context": context.memory
                }
            
            # 5. Update task for next iteration
            task = action_result.get("next_task", task)
        
        return {
            "success": False,
            "error": "达到最大步骤数限制",
            "steps": len(steps),
            "context": context.memory
        }
    
    async def _think(self, task: str, context: AgentContext, history: List[AgentStep]) -> Dict:
        """思考阶段 - 分析任务，决定下一步动作"""
        import aiohttp
        
        # 构建思考 prompt
        history_text = "\n".join([
            f"Step {i+1}: {s.thought} -> {s.action} -> {s.observation[:100]}"
            for i, s in enumerate(history[-3:])  # 只保留最近3步
        ])
        
        tools_desc = "\n".join([
            f"- {t.name}: {t.description}"
            for t in self.tools.values()
        ])
        
        prompt = f"""你是一个智能代理，正在执行任务。

任务: {task}

可用工具:
{tools_desc}

历史步骤:
{history_text or "无"}

请决定下一步动作。返回JSON格式:
{{"reasoning": "思考过程", "action": "工具名称", "action_input": {{参数}}, "completed": false}}

如果任务已完成，返回:
{{"reasoning": "完成原因", "action": "none", "action_input": {{}}, "completed": true, "result": "最终结果"}}"""
        
        headers = {
            'Authorization': f'Bearer {os.getenv("MIMO_API_KEY")}',
            'Content-Type': 'application/json'
        }
        
        body = {
            'model': os.getenv('MIMO_MODEL', 'mimo-v2.5'),
            'messages': [{'role': 'user', 'content': prompt}],
            'temperature': 0.1,
            'max_tokens': 2000
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f'{os.getenv("MIMO_BASE_URL")}/chat/completions',
                    headers=headers,
                    json=body,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        content = data['choices'][0]['message']['content']
                        
                        if content:
                            import re
                            json_match = re.search(r'\{.*\}', content, re.DOTALL)
                            if json_match:
                                return json.loads(json_match.group())
        except Exception as e:
            logger.error(f"Think error: {e}")
        
        # Fallback
        return {"reasoning": "无法分析", "action": "none", "action_input": {}, "completed": True, "result": "Agent 思考失败"}
    
    async def _act(self, thought: Dict, context: AgentContext) -> Dict:
        """行动阶段 - 执行工具调用"""
        action = thought.get("action", "none")
        action_input = thought.get("action_input", {})
        
        if action == "none" or thought.get("completed", False):
            return {"completed": True, "result": thought.get("result", "任务完成")}
        
        tool = self.tools.get(action)
        if not tool:
            return {"completed": False, "result": f"未知工具: {action}"}
        
        try:
            result = await tool.execute(**action_input)
            context.tools_used.append(action)
            return {"completed": False, "result": result}
        except Exception as e:
            return {"completed": False, "result": f"工具执行失败: {str(e)}"}


# 全局 Agent 实例
agent = Agent()
