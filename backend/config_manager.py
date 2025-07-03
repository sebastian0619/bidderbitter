"""
配置管理器
用于管理业绩类型、业务领域等JSON配置文件，支持动态重载
"""
import json
import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
        # 配置文件路径
        self.performance_types_file = self.config_dir / "performance_types.json"
        self.business_fields_file = self.config_dir / "business_fields.json"
        self.ai_learning_file = self.config_dir / "ai_learning.json"
        self.ai_analysis_config_file = self.config_dir / "ai_analysis_config.json"
        
        # 缓存
        self._performance_types_cache = None
        self._business_fields_cache = None
        self._ai_learning_cache = None
        self._ai_analysis_config_cache = None
        self._cache_timestamps = {}
        
        # 初始化配置文件
        self._init_config_files()
    
    def _init_config_files(self):
        """初始化配置文件"""
        # 初始化业绩类型配置
        if not self.performance_types_file.exists():
            default_performance_types = {
                "performance_types": [
                    {
                        "code": "long_term_consultant",
                        "name": "长期顾问",
                        "description": "长期法律顾问服务",
                        "keywords": ["长期顾问", "常年法律顾问", "法律顾问", "顾问服务"],
                        "is_active": True,
                        "sort_order": 1
                    },
                    {
                        "code": "major_case",
                        "name": "重大个案",
                        "description": "重大专项法律服务项目",
                        "keywords": ["重大个案", "专项服务", "重大项目", "个案服务"],
                        "is_active": True,
                        "sort_order": 2
                    }
                ],
                "last_updated": datetime.now().isoformat(),
                "version": "1.0"
            }
            self._save_json(self.performance_types_file, default_performance_types)
        
        # 初始化业务领域配置
        if not self.business_fields_file.exists():
            default_business_fields = {
                "business_fields": [
                    {
                        "code": "merger_acquisition",
                        "name": "并购重组",
                        "description": "企业并购、重组、投资等公司法律事务",
                        "keywords": ["并购", "重组", "收购", "合并", "M&A", "投资"],
                        "is_active": True,
                        "sort_order": 1
                    },
                    {
                        "code": "capital_market",
                        "name": "资本市场",
                        "description": "IPO、债券发行、证券监管等资本市场法律事务",
                        "keywords": ["IPO", "上市", "债券", "证券", "资本市场", "发行"],
                        "is_active": True,
                        "sort_order": 2
                    }
                ],
                "last_updated": datetime.now().isoformat(),
                "version": "1.0"
            }
            self._save_json(self.business_fields_file, default_business_fields)
        
        # 初始化AI学习配置
        if not self.ai_learning_file.exists():
            default_ai_learning = {
                "user_feedback": [],
                "correction_patterns": [],
                "learning_rules": [],
                "last_updated": datetime.now().isoformat(),
                "version": "1.0"
            }
            self._save_json(self.ai_learning_file, default_ai_learning)
    
    def _load_json(self, file_path: Path) -> Dict[str, Any]:
        """加载JSON文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载配置文件失败 {file_path}: {e}")
            return {}
    
    def _save_json(self, file_path: Path, data: Dict[str, Any]):
        """保存JSON文件"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"配置文件已保存: {file_path}")
        except Exception as e:
            logger.error(f"保存配置文件失败 {file_path}: {e}")
    
    def _is_cache_valid(self, file_path: Path) -> bool:
        """检查缓存是否有效"""
        if not file_path.exists():
            return False
        
        file_mtime = file_path.stat().st_mtime
        cache_mtime = self._cache_timestamps.get(str(file_path), 0)
        
        return file_mtime <= cache_mtime
    
    def get_performance_types(self, force_reload: bool = False) -> List[Dict[str, Any]]:
        """获取业绩类型列表"""
        if not force_reload and self._performance_types_cache and self._is_cache_valid(self.performance_types_file):
            return self._performance_types_cache
        
        data = self._load_json(self.performance_types_file)
        self._performance_types_cache = data.get("performance_types", [])
        self._cache_timestamps[str(self.performance_types_file)] = datetime.now().timestamp()
        
        return self._performance_types_cache
    
    def get_business_fields(self, force_reload: bool = False) -> List[Dict[str, Any]]:
        """获取业务领域列表"""
        if not force_reload and self._business_fields_cache and self._is_cache_valid(self.business_fields_file):
            return self._business_fields_cache
        
        data = self._load_json(self.business_fields_file)
        self._business_fields_cache = data.get("business_fields", [])
        self._cache_timestamps[str(self.business_fields_file)] = datetime.now().timestamp()
        
        return self._business_fields_cache
    
    def get_ai_learning_data(self, force_reload: bool = False) -> Dict[str, Any]:
        """获取AI学习数据"""
        if not force_reload and self._ai_learning_cache and self._is_cache_valid(self.ai_learning_file):
            return self._ai_learning_cache
        
        data = self._load_json(self.ai_learning_file)
        self._ai_learning_cache = data
        self._cache_timestamps[str(self.ai_learning_file)] = datetime.now().timestamp()
        
        return self._ai_learning_cache
    
    def get_ai_analysis_config(self, force_reload: bool = False) -> Dict[str, Any]:
        """获取AI分析配置"""
        if not force_reload and self._ai_analysis_config_cache and self._is_cache_valid(self.ai_analysis_config_file):
            return self._ai_analysis_config_cache
        
        data = self._load_json(self.ai_analysis_config_file)
        self._ai_analysis_config_cache = data
        self._cache_timestamps[str(self.ai_analysis_config_file)] = datetime.now().timestamp()
        
        return self._ai_analysis_config_cache
    
    def get_document_types(self) -> Dict[str, Dict[str, Any]]:
        """获取文档类型分类配置"""
        config = self.get_ai_analysis_config()
        return config.get("document_classification", {})
    
    def get_business_field_classifications(self) -> Dict[str, Dict[str, Any]]:
        """获取业务领域分类配置"""
        config = self.get_ai_analysis_config()
        return config.get("business_fields", {})
    
    def get_prompt_template(self, prompt_type: str) -> Dict[str, str]:
        """获取指定类型的prompt模板"""
        config = self.get_ai_analysis_config()
        prompts = config.get("prompts", {})
        return prompts.get(prompt_type, {})
    
    def get_analysis_settings(self) -> Dict[str, Any]:
        """获取分析设置"""
        config = self.get_ai_analysis_config()
        return config.get("analysis_settings", {})
    
    def format_document_types_for_prompt(self) -> str:
        """格式化文档类型信息用于prompt"""
        doc_types = self.get_document_types()
        formatted = []
        for code, info in doc_types.items():
            keywords = ", ".join(info.get("keywords", []))
            formatted.append(f"- {code}: {info.get('name', '')} - {info.get('description', '')} (关键词: {keywords})")
        return "\n".join(formatted)
    
    def format_business_fields_for_prompt(self) -> str:
        """格式化业务领域信息用于prompt"""
        fields = self.get_business_field_classifications()
        formatted = []
        for code, info in fields.items():
            keywords = ", ".join(info.get("keywords", []))
            formatted.append(f"- {code}: {info.get('name', '')} - {info.get('description', '')} (关键词: {keywords})")
        return "\n".join(formatted)
    
    def build_prompt(self, prompt_type: str, **kwargs) -> tuple[str, str]:
        """构建完整的prompt"""
        template = self.get_prompt_template(prompt_type)
        if not template:
            return "", ""
        
        system_prompt = template.get("system", "")
        user_template = template.get("user_template", "")
        
        # 根据prompt类型添加特定的格式化数据
        if prompt_type == "document_classification":
            kwargs["document_types"] = self.format_document_types_for_prompt()
        elif prompt_type == "business_field_classification":
            kwargs["business_fields"] = self.format_business_fields_for_prompt()
        
        # 格式化用户prompt
        try:
            user_prompt = user_template.format(**kwargs)
        except KeyError as e:
            logger.warning(f"格式化prompt失败，缺少参数: {e}")
            user_prompt = user_template
        
        return system_prompt, user_prompt
    
    def get_confidence_threshold(self, analysis_type: str) -> float:
        """获取指定分析类型的置信度阈值"""
        settings = self.get_analysis_settings()
        thresholds = settings.get("confidence_thresholds", {})
        return thresholds.get(analysis_type, 0.7)
    
    def classify_business_field_by_keywords(self, text: str) -> Optional[tuple[str, str, float]]:
        """根据关键词分类业务领域"""
        fields = self.get_business_field_classifications()
        text_lower = text.lower()
        
        best_match = None
        best_score = 0
        
        for code, info in fields.items():
            keywords = info.get("keywords", [])
            matched_keywords = []
            
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    matched_keywords.append(keyword)
            
            if matched_keywords:
                # 计算匹配分数（匹配关键词数量 / 总关键词数量）
                score = len(matched_keywords) / len(keywords)
                if score > best_score:
                    best_score = score
                    best_match = (code, info.get("name", ""), score)
        
        return best_match
    
    def classify_document_type_by_keywords(self, text: str) -> Optional[tuple[str, str, float]]:
        """根据关键词分类文档类型"""
        doc_types = self.get_document_types()
        text_lower = text.lower()
        
        best_match = None
        best_score = 0
        
        for code, info in doc_types.items():
            keywords = info.get("keywords", [])
            matched_keywords = []
            
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    matched_keywords.append(keyword)
            
            if matched_keywords:
                # 计算匹配分数（匹配关键词数量 / 总关键词数量）
                score = len(matched_keywords) / len(keywords)
                if score > best_score:
                    best_score = score
                    best_match = (code, info.get("name", ""), score)
        
        return best_match
    
    def update_performance_types(self, performance_types: List[Dict[str, Any]]):
        """更新业绩类型配置"""
        data = {
            "performance_types": performance_types,
            "last_updated": datetime.now().isoformat(),
            "version": "1.0"
        }
        self._save_json(self.performance_types_file, data)
        self._performance_types_cache = performance_types
        self._cache_timestamps[str(self.performance_types_file)] = datetime.now().timestamp()
        logger.info("业绩类型配置已更新")
    
    def update_business_fields(self, business_fields: List[Dict[str, Any]]):
        """更新业务领域配置"""
        data = {
            "business_fields": business_fields,
            "last_updated": datetime.now().isoformat(),
            "version": "1.0"
        }
        self._save_json(self.business_fields_file, data)
        self._business_fields_cache = business_fields
        self._cache_timestamps[str(self.business_fields_file)] = datetime.now().timestamp()
        logger.info("业务领域配置已更新")
    
    def add_user_feedback(self, feedback: Dict[str, Any]):
        """添加用户反馈数据"""
        data = self.get_ai_learning_data()
        feedback["timestamp"] = datetime.now().isoformat()
        feedback["id"] = len(data.get("user_feedback", [])) + 1
        
        if "user_feedback" not in data:
            data["user_feedback"] = []
        
        data["user_feedback"].append(feedback)
        data["last_updated"] = datetime.now().isoformat()
        
        self._save_json(self.ai_learning_file, data)
        self._ai_learning_cache = data
        self._cache_timestamps[str(self.ai_learning_file)] = datetime.now().timestamp()
        
        logger.info(f"用户反馈已记录: {feedback.get('type', 'unknown')}")
    
    def add_correction_pattern(self, pattern: Dict[str, Any]):
        """添加修正模式"""
        data = self.get_ai_learning_data()
        pattern["timestamp"] = datetime.now().isoformat()
        pattern["id"] = len(data.get("correction_patterns", [])) + 1
        
        if "correction_patterns" not in data:
            data["correction_patterns"] = []
        
        data["correction_patterns"].append(pattern)
        data["last_updated"] = datetime.now().isoformat()
        
        self._save_json(self.ai_learning_file, data)
        self._ai_learning_cache = data
        self._cache_timestamps[str(self.ai_learning_file)] = datetime.now().timestamp()
        
        logger.info(f"修正模式已记录: {pattern.get('field', 'unknown')}")
    
    def get_performance_type_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """根据名称获取业绩类型"""
        types = self.get_performance_types()
        for type_info in types:
            if type_info.get("name") == name:
                return type_info
        return None
    
    def get_business_field_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """根据名称获取业务领域"""
        fields = self.get_business_fields()
        for field_info in fields:
            if field_info.get("name") == name:
                return field_info
        return None
    
    def suggest_performance_type(self, text: str) -> Optional[str]:
        """根据文本建议业绩类型"""
        types = self.get_performance_types()
        text_lower = text.lower()
        
        for type_info in types:
            if not type_info.get("is_active", True):
                continue
            
            # 检查关键词匹配
            keywords = type_info.get("keywords", [])
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    return type_info.get("name")
        
        return None
    
    def suggest_business_field(self, text: str) -> Optional[str]:
        """根据文本建议业务领域"""
        fields = self.get_business_fields()
        text_lower = text.lower()
        
        for field_info in fields:
            if not field_info.get("is_active", True):
                continue
            
            # 检查关键词匹配
            keywords = field_info.get("keywords", [])
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    return field_info.get("name")
        
        return None
    
    def add_learning_data(self, data_type: str, learning_data: Dict[str, Any]):
        """添加学习数据到指定类型"""
        data = self.get_ai_learning_data()
        learning_data["timestamp"] = datetime.now().isoformat()
        learning_data["id"] = len(data.get(data_type, [])) + 1
        
        if data_type not in data:
            data[data_type] = []
        
        data[data_type].append(learning_data)
        data["last_updated"] = datetime.now().isoformat()
        
        self._save_json(self.ai_learning_file, data)
        self._ai_learning_cache = data
        self._cache_timestamps[str(self.ai_learning_file)] = datetime.now().timestamp()
        
        logger.info(f"学习数据已记录到 {data_type}: {learning_data.get('original_classification', 'unknown')}")
    
    def get_learning_data(self, data_type: str) -> List[Dict[str, Any]]:
        """获取指定类型的学习数据"""
        data = self.get_ai_learning_data()
        return data.get(data_type, [])
    
    def update_ai_analysis_config(self, config: Dict[str, Any]):
        """更新AI分析配置"""
        config["last_updated"] = datetime.now().isoformat()
        self._save_json(self.ai_analysis_config_file, config)
        self._ai_analysis_config_cache = config
        self._cache_timestamps[str(self.ai_analysis_config_file)] = datetime.now().timestamp()
        logger.info("AI分析配置已更新")
    
    def reload_all_configs(self):
        """重新加载所有配置"""
        logger.info("重新加载所有配置文件...")
        self.get_performance_types(force_reload=True)
        self.get_business_fields(force_reload=True)
        self.get_ai_learning_data(force_reload=True)
        self.get_ai_analysis_config(force_reload=True)
        logger.info("所有配置文件重新加载完成")

# 全局配置管理器实例
config_manager = ConfigManager() 