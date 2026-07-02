"""AI 分类服务 - 基于规则和 LLM 的文件分类"""
import os
import logging
import json
import hashlib
from typing import Dict, List, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


class AIClassificationService:
    """AI 文件分类服务
    
    支持两种模式:
    1. 规则引擎 - 基于文件名关键词快速分类
    2. LLM 分析 - 调用大模型进行深度分析
    """
    
    # 分类规则
    RULES = {
        "业绩": {
            "keywords": ["业绩", "合同", "服务协议", "法律顾问协议", "委托协议", "聘用合同", 
                        "常年顾问", "专项服务", "项目合同", "中标通知书"],
            "tags": ["业绩", "合同"],
            "color": "#409EFF"
        },
        "资质证照": {
            "keywords": ["律师证", "执业证", "营业执照", "资质证书", "许可证", "资格证",
                        "组织机构代码", "税务登记", "开户许可", "律所执业许可"],
            "tags": ["资质", "证照"],
            "color": "#67C23A"
        },
        "奖项荣誉": {
            "keywords": ["奖项", "获奖", "荣誉", "排名", "chambers", "legal500", "alb",
                        "legalband", "iflr", "钱伯斯", "亚洲法律", "商法"],
            "tags": ["奖项", "荣誉"],
            "color": "#E6A23C"
        },
        "财务资料": {
            "keywords": ["审计报告", "财务报表", "资产负债表", "利润表", "纳税证明",
                        "社保缴纳", "完税证明", "银行资信"],
            "tags": ["财务"],
            "color": "#F56C6C"
        },
        "团队资料": {
            "keywords": ["律师简历", "团队介绍", "人员名单", "学历证明", "学位证",
                        "培训证书", "合伙人", "执业律师"],
            "tags": ["团队", "人员"],
            "color": "#909399"
        },
        "公司资料": {
            "keywords": ["公司简介", "律所简介", "组织架构", "办公场所", "分支机构",
                        "企业文化", "发展历程"],
            "tags": ["公司"],
            "color": "#00BCD4"
        }
    }
    
    def __init__(self, llm_client=None):
        """初始化分类服务
        
        Args:
            llm_client: LLM 客户端 (可选，用于深度分析)
        """
        self.llm_client = llm_client
    
    def classify_by_rules(self, filename: str, content_preview: str = "") -> Dict:
        """基于规则的分类
        
        Args:
            filename: 文件名
            content_preview: 内容预览 (可选)
        
        Returns:
            分类结果
        """
        text = (filename + " " + content_preview).lower()
        
        # 按优先级匹配规则
        best_match = None
        best_score = 0
        
        for category, rule in self.RULES.items():
            score = 0
            matched_keywords = []
            
            for keyword in rule["keywords"]:
                if keyword.lower() in text:
                    score += 1
                    matched_keywords.append(keyword)
            
            if score > best_score:
                best_score = score
                best_match = {
                    "category": category,
                    "confidence": min(0.5 + score * 0.15, 0.95),
                    "tags": rule["tags"],
                    "color": rule["color"],
                    "matched_keywords": matched_keywords,
                    "method": "rules"
                }
        
        # 如果没有匹配，返回默认分类
        if not best_match:
            best_match = {
                "category": "其他",
                "confidence": 0.3,
                "tags": [],
                "color": "#909399",
                "matched_keywords": [],
                "method": "rules"
            }
        
        return best_match
    
    async def classify_with_llm(self, filename: str, content: str, 
                                 llm_provider: str = "openai") -> Dict:
        """基于 LLM 的分类
        
        Args:
            filename: 文件名
            content: 文件内容
            llm_provider: LLM 提供商
        
        Returns:
            分类结果
        """
        if not self.llm_client:
            return self.classify_by_rules(filename, content)
        
        prompt = f"""你是一个法律文档分类专家。请分析以下文件，判断其类别。

文件名: {filename}
内容预览: {content[:2000]}

请从以下类别中选择最合适的一个:
1. 业绩 - 法律服务合同、项目协议等
2. 资质证照 - 律师证、营业执照、资质证书等
3. 奖项荣誉 - 获奖证书、排名证明等
4. 财务资料 - 审计报告、纳税证明等
5. 团队资料 - 律师简历、团队介绍等
6. 公司资料 - 公司简介、组织架构等
7. 其他

请以JSON格式返回:
{{
    "category": "类别名称",
    "confidence": 0.0-1.0,
    "reason": "判断理由",
    "tags": ["标签1", "标签2"]
}}"""
        
        try:
            # 调用 LLM
            response = await self.llm_client.chat(prompt)
            result = json.loads(response)
            result["method"] = "llm"
            return result
        except Exception as e:
            logger.error(f"LLM 分类失败: {e}")
            return self.classify_by_rules(filename, content)
    
    def classify_batch(self, files: List[Dict]) -> List[Dict]:
        """批量分类
        
        Args:
            files: 文件列表 [{"id": int, "filename": str, "content": str}]
        
        Returns:
            分类结果列表
        """
        results = []
        for file in files:
            result = self.classify_by_rules(file["filename"], file.get("content", ""))
            result["file_id"] = file["id"]
            results.append(result)
        return results


# 全局实例
ai_classifier = AIClassificationService()
