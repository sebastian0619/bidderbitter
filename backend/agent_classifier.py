"""Agent 文件分类服务

支持两种模式:
1. 规则引擎 - 基于关键词快速分类（无需 LLM）
2. LLM Agent - 调用大模型进行深度分析（更准确）

设计目标：
- 上传文件后自动触发分类
- 分类结果包含：类别、置信度、标签、摘要
- 支持批量分类
- 分类结果可人工修正（反馈学习）
"""
import os
import json
import logging
import hashlib
import re
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


# ==================== 分类规则引擎 ====================

CATEGORY_RULES = {
    "业绩": {
        "keywords": [
            "业绩", "合同", "服务协议", "法律顾问协议", "委托协议", "聘用合同",
            "常年顾问", "专项服务", "项目合同", "中标通知书", "法律服务",
            "代理协议", "委托代理", "仲裁代理", "诉讼代理"
        ],
        "tags": ["业绩", "合同"],
        "color": "#409EFF",
        "description": "法律服务合同、项目协议等业绩证明材料"
    },
    "资质证照": {
        "keywords": [
            "律师证", "执业证", "营业执照", "资质证书", "许可证", "资格证",
            "组织机构代码", "税务登记", "开户许可", "律所执业许可",
            "执业许可", "事务所执业证", "年检"
        ],
        "tags": ["资质", "证照"],
        "color": "#67C23A",
        "description": "律师执业证、律所资质、营业执照等"
    },
    "奖项荣誉": {
        "keywords": [
            "奖项", "获奖", "荣誉", "排名", "chambers", "legal500", "alb",
            "legalband", "iflr", "钱伯斯", "亚洲法律", "商法",
            "benchmark", "dawkins", "who's who"
        ],
        "tags": ["奖项", "荣誉"],
        "color": "#E6A23C",
        "description": "法律评级机构排名、行业奖项等"
    },
    "财务资料": {
        "keywords": [
            "审计报告", "财务报表", "资产负债表", "利润表", "纳税证明",
            "社保缴纳", "完税证明", "银行资信", "财务状况", "年度审计"
        ],
        "tags": ["财务"],
        "color": "#F56C6C",
        "description": "审计报告、纳税证明、社保缴纳等财务材料"
    },
    "团队资料": {
        "keywords": [
            "律师简历", "团队介绍", "人员名单", "学历证明", "学位证",
            "培训证书", "合伙人", "执业律师", "律师名册", "团队情况"
        ],
        "tags": ["团队", "人员"],
        "color": "#909399",
        "description": "律师简历、团队介绍、学历证书等"
    },
    "公司资料": {
        "keywords": [
            "公司简介", "律所简介", "组织架构", "办公场所", "分支机构",
            "企业文化", "发展历程", "律所介绍", "基本情况"
        ],
        "tags": ["公司"],
        "color": "#00BCD4",
        "description": "律所简介、组织架构、办公场所等"
    },
    "投标文件": {
        "keywords": [
            "投标函", "投标文件", "投标书", "报价", "商务标", "技术标",
            "资格预审", "投标保证金", "开标一览表"
        ],
        "tags": ["投标"],
        "color": "#FF9800",
        "description": "投标函、投标文件等"
    }
}


class AgentClassifier:
    """Agent 文件分类器"""
    
    def __init__(self, llm_provider=None, llm_api_key=None, llm_base_url=None):
        """初始化分类器
        
        Args:
            llm_provider: LLM 提供商 (openai/azure/custom)
            llm_api_key: API Key
            llm_base_url: API Base URL
        """
        self.llm_provider = llm_provider or os.getenv("AI_PROVIDER", "openai")
        self.llm_api_key = llm_api_key or os.getenv("OPENAI_API_KEY")
        self.llm_base_url = llm_base_url or os.getenv("OPENAI_BASE_URL")
    
    def classify_by_rules(self, filename: str, content_preview: str = "") -> Dict:
        """基于规则的快速分类
        
        Args:
            filename: 文件名
            content_preview: 内容预览（可选）
        
        Returns:
            分类结果
        """
        text = (filename + " " + content_preview).lower()
        
        best_match = None
        best_score = 0
        all_matches = []
        
        for category, rule in CATEGORY_RULES.items():
            score = 0
            matched_keywords = []
            
            for keyword in rule["keywords"]:
                if keyword.lower() in text:
                    score += 1
                    matched_keywords.append(keyword)
            
            if score > 0:
                all_matches.append({
                    "category": category,
                    "score": score,
                    "keywords": matched_keywords
                })
            
            if score > best_score:
                best_score = score
                best_match = {
                    "category": category,
                    "confidence": min(0.5 + score * 0.12, 0.95),
                    "tags": rule["tags"],
                    "color": rule["color"],
                    "description": rule["description"],
                    "matched_keywords": matched_keywords,
                    "method": "rules"
                }
        
        # 无匹配时返回默认
        if not best_match:
            best_match = {
                "category": "其他",
                "confidence": 0.3,
                "tags": [],
                "color": "#909399",
                "description": "未分类文件",
                "matched_keywords": [],
                "method": "rules"
            }
        
        # 附加所有匹配结果供参考
        best_match["all_matches"] = sorted(all_matches, key=lambda x: x["score"], reverse=True)
        
        return best_match
    
    async def classify_with_llm(self, filename: str, content: str = "") -> Dict:
        """基于 LLM 的深度分类
        
        Args:
            filename: 文件名
            content: 文件内容
        
        Returns:
            分类结果
        """
        if not self.llm_api_key:
            logger.warning("未配置 LLM API Key，回退到规则分类")
            return self.classify_by_rules(filename, content)
        
        try:
            import aiohttp
            
            prompt = f"""你是一个法律文档分类专家。请分析以下文件，判断其类别。

文件名: {filename}
{f"内容预览: {content[:2000]}" if content else ""}

请从以下类别中选择最合适的一个:
1. 业绩 - 法律服务合同、项目协议等
2. 资质证照 - 律师证、营业执照、资质证书等
3. 奖项荣誉 - 获奖证书、排名证明等
4. 财务资料 - 审计报告、纳税证明等
5. 团队资料 - 律师简历、团队介绍等
6. 公司资料 - 公司简介、组织架构等
7. 投标文件 - 投标函、投标书等
8. 其他

请以JSON格式返回:
{{
    "category": "类别名称",
    "confidence": 0.0-1.0,
    "reason": "判断理由",
    "tags": ["标签1", "标签2"],
    "summary": "文件内容摘要（50字以内）"
}}"""
            
            # 调用 LLM API
            headers = {
                "Authorization": f"Bearer {self.llm_api_key}",
                "Content-Type": "application/json"
            }
            
            body = {
                "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                "messages": [
                    {"role": "system", "content": "你是一个专业的法律文档分类助手。请始终以JSON格式回复。"},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1,
                "max_tokens": 500
            }
            
            base_url = self.llm_base_url or "https://api.openai.com/v1"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{base_url}/chat/completions",
                    headers=headers,
                    json=body,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        content = data["choices"][0]["message"]["content"]
                        
                        # 提取 JSON
                        json_match = re.search(r'\{.*\}', content, re.DOTALL)
                        if json_match:
                            result = json.loads(json_match.group())
                            result["method"] = "llm"
                            return result
            
            # LLM 调用失败，回退到规则
            return self.classify_by_rules(filename, content)
            
        except Exception as e:
            logger.error(f"LLM 分类失败: {e}")
            return self.classify_by_rules(filename, content)
    
    def classify_batch(self, files: List[Dict]) -> List[Dict]:
        """批量分类
        
        Args:
            files: [{"id": int, "filename": str, "content": str}]
        
        Returns:
            分类结果列表
        """
        results = []
        for file in files:
            result = self.classify_by_rules(file["filename"], file.get("content", ""))
            result["file_id"] = file["id"]
            results.append(result)
        return results
    
    def get_tags_for_category(self, category: str) -> List[str]:
        """获取分类对应的标签"""
        rule = CATEGORY_RULES.get(category, {})
        return rule.get("tags", [])
    
    def get_all_categories(self) -> Dict:
        """获取所有分类定义"""
        return {
            cat: {
                "description": rule["description"],
                "tags": rule["tags"],
                "color": rule["color"],
                "keyword_count": len(rule["keywords"])
            }
            for cat, rule in CATEGORY_RULES.items()
        }


# 全局实例
agent_classifier = AgentClassifier()
