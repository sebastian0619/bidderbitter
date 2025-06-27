#!/usr/bin/env python3
"""
高级功能初始化脚本
用于初始化智能章节管理、AI自动检索奖项等高级功能的基础数据
"""

import sys
import os
from datetime import datetime
import asyncio

# 添加当前目录到sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal, get_db, engine
from models import (
    Base, SectionType, DataSource, RecommendationRule,
    Brand, BusinessField, SystemSettings
)
from sqlalchemy.orm import Session

def init_section_types():
    """初始化章节类型"""
    db = SessionLocal()
    try:
        # 检查是否已有章节类型数据
        if db.query(SectionType).count() > 0:
            print("章节类型已存在，跳过初始化")
            return
        
        section_types = [
            {
                "name": "honor_awards",
                "display_name": "荣誉奖项",
                "description": "律师事务所获得的各类荣誉和奖项",
                "icon": "Trophy",
                "color": "#FFD700",
                "related_award_types": ["chambers", "legal500", "iflr1000"],
                "related_performance_types": []
            },
            {
                "name": "performance_cases",
                "display_name": "业绩案例",
                "description": "律师事务所完成的重要项目和案例",
                "icon": "Briefcase",
                "color": "#409EFF",
                "related_award_types": [],
                "related_performance_types": ["merger_acquisition", "ipo", "litigation", "compliance"]
            },
            {
                "name": "team_introduction",
                "display_name": "团队介绍",
                "description": "律师事务所团队成员的介绍和背景",
                "icon": "User",
                "color": "#67C23A",
                "related_award_types": [],
                "related_performance_types": []
            },
            {
                "name": "service_areas",
                "display_name": "服务领域",
                "description": "律师事务所提供的法律服务领域",
                "icon": "Grid",
                "color": "#E6A23C",
                "related_award_types": [],
                "related_performance_types": []
            },
            {
                "name": "client_references",
                "display_name": "客户推荐",
                "description": "客户对律师事务所的评价和推荐",
                "icon": "ChatDotRound",
                "color": "#F56C6C",
                "related_award_types": [],
                "related_performance_types": []
            }
        ]
        
        for type_data in section_types:
            section_type = SectionType(**type_data)
            db.add(section_type)
        
        db.commit()
        print(f"已初始化 {len(section_types)} 个章节类型")
        
    except Exception as e:
        print(f"初始化章节类型失败: {str(e)}")
        db.rollback()
    finally:
        db.close()

def init_data_sources():
    """初始化数据源"""
    db = SessionLocal()
    try:
        # 检查是否已有数据源
        if db.query(DataSource).count() > 0:
            print("数据源已存在，跳过初始化")
            return
        
        data_sources = [
            {
                "name": "Chambers",
                "type": "chambers",
                "base_url": "https://chambers.com",
                "description": "钱伯斯法律评级，全球权威的法律服务评级机构",
                "crawler_config": {
                    "search_url": "https://chambers.com/legal-guide/search",
                    "firm_page_pattern": "https://chambers.com/legal-guide/firm/*",
                    "wait_time": 2,
                    "max_retries": 3
                },
                "selectors": {
                    "firm_list": ".firm-item",
                    "firm_name": ".firm-name",
                    "award_list": ".award-item",
                    "award_name": ".award-name",
                    "award_year": ".award-year",
                    "business_field": ".business-field",
                    "ranking": ".ranking"
                },
                "rate_limit": 2
            },
            {
                "name": "Legal 500",
                "type": "legal500",
                "base_url": "https://www.legal500.com",
                "description": "Legal 500法律评级，全球领先的法律服务指南",
                "crawler_config": {
                    "search_url": "https://www.legal500.com/search",
                    "firm_page_pattern": "https://www.legal500.com/firms/*",
                    "wait_time": 3,
                    "max_retries": 3
                },
                "selectors": {
                    "firm_list": ".firm-listing",
                    "firm_name": ".firm-title",
                    "award_list": ".ranking-item",
                    "award_name": ".ranking-title",
                    "award_year": ".ranking-year",
                    "business_field": ".practice-area",
                    "ranking": ".tier-ranking"
                },
                "rate_limit": 3
            },
            {
                "name": "IFLR1000",
                "type": "iflr1000",
                "base_url": "https://www.iflr1000.com",
                "description": "IFLR1000金融法律评级，专注于金融法律领域",
                "crawler_config": {
                    "search_url": "https://www.iflr1000.com/search",
                    "firm_page_pattern": "https://www.iflr1000.com/firms/*",
                    "wait_time": 2,
                    "max_retries": 3
                },
                "selectors": {
                    "firm_list": ".firm-result",
                    "firm_name": ".firm-name",
                    "award_list": ".award-entry",
                    "award_name": ".award-title",
                    "award_year": ".award-year",
                    "business_field": ".practice-area",
                    "ranking": ".tier-level"
                },
                "rate_limit": 2
            }
        ]
        
        for source_data in data_sources:
            data_source = DataSource(**source_data)
            db.add(data_source)
        
        db.commit()
        print(f"已初始化 {len(data_sources)} 个数据源")
        
    except Exception as e:
        print(f"初始化数据源失败: {str(e)}")
        db.rollback()
    finally:
        db.close()

def init_recommendation_rules():
    """初始化推荐规则"""
    db = SessionLocal()
    try:
        # 检查是否已有推荐规则
        if db.query(RecommendationRule).count() > 0:
            print("推荐规则已存在，跳过初始化")
            return
        
        recommendation_rules = [
            {
                "name": "同领域奖项推荐",
                "description": "基于业务领域推荐相关奖项",
                "rule_type": "field_based",
                "conditions": {
                    "trigger": "section_creation",
                    "field_match": True,
                    "year_range": 3
                },
                "actions": {
                    "recommend_awards": True,
                    "recommend_performances": False,
                    "max_recommendations": 10,
                    "sort_by": "year_desc"
                },
                "priority": 1
            },
            {
                "name": "时间相关性推荐",
                "description": "基于时间相关性推荐奖项和业绩",
                "rule_type": "time_based",
                "conditions": {
                    "trigger": "section_creation",
                    "year_match": True,
                    "recent_years": 2
                },
                "actions": {
                    "recommend_awards": True,
                    "recommend_performances": True,
                    "max_recommendations": 15,
                    "sort_by": "relevance"
                },
                "priority": 2
            },
            {
                "name": "相似项目推荐",
                "description": "基于相似项目推荐相关数据",
                "rule_type": "similarity_based",
                "conditions": {
                    "trigger": "section_creation",
                    "similarity_threshold": 0.7,
                    "max_similar_items": 5
                },
                "actions": {
                    "recommend_awards": True,
                    "recommend_performances": True,
                    "max_recommendations": 8,
                    "sort_by": "similarity_desc"
                },
                "priority": 3
            }
        ]
        
        for rule_data in recommendation_rules:
            recommendation_rule = RecommendationRule(**rule_data)
            db.add(recommendation_rule)
        
        db.commit()
        print(f"已初始化 {len(recommendation_rules)} 个推荐规则")
        
    except Exception as e:
        print(f"初始化推荐规则失败: {str(e)}")
        db.rollback()
    finally:
        db.close()

def init_advanced_brands():
    """初始化高级厂牌数据"""
    db = SessionLocal()
    try:
        # 添加更多权威评级机构
        advanced_brands = [
            {
                "name": "Chambers",
                "full_name": "Chambers and Partners",
                "description": "全球权威的法律服务评级机构，提供详细的法律市场分析和排名",
                "website": "https://chambers.com",
                "is_active": True
            },
            {
                "name": "Legal 500",
                "full_name": "The Legal 500",
                "description": "全球领先的法律服务指南，提供全面的法律市场研究",
                "website": "https://www.legal500.com",
                "is_active": True
            },
            {
                "name": "IFLR1000",
                "full_name": "IFLR1000 Financial and Corporate Guide",
                "description": "专注于金融法律领域的权威评级机构",
                "website": "https://www.iflr1000.com",
                "is_active": True
            },
            {
                "name": "Who's Who Legal",
                "full_name": "Who's Who Legal",
                "description": "全球领先的律师和法律专家指南",
                "website": "https://whoswholegal.com",
                "is_active": True
            },
            {
                "name": "Benchmark Litigation",
                "full_name": "Benchmark Litigation",
                "description": "专注于诉讼领域的法律评级机构",
                "website": "https://benchmarklitigation.com",
                "is_active": True
            }
        ]
        
        for brand_data in advanced_brands:
            # 检查是否已存在
            existing_brand = db.query(Brand).filter(Brand.name == brand_data["name"]).first()
            if not existing_brand:
                brand = Brand(**brand_data)
                db.add(brand)
        
        db.commit()
        print("已初始化高级厂牌数据")
        
    except Exception as e:
        print(f"初始化高级厂牌数据失败: {str(e)}")
        db.rollback()
    finally:
        db.close()

def init_advanced_business_fields():
    """初始化高级业务领域数据"""
    db = SessionLocal()
    try:
        # 添加更多法律业务领域
        advanced_fields = [
            {
                "name": "公司并购",
                "description": "企业并购、重组、投资等公司法律事务"
            },
            {
                "name": "资本市场",
                "description": "IPO、债券发行、证券监管等资本市场法律事务"
            },
            {
                "name": "银行金融",
                "description": "银行监管、金融产品、支付系统等金融法律事务"
            },
            {
                "name": "知识产权",
                "description": "专利、商标、版权、商业秘密等知识产权法律事务"
            },
            {
                "name": "争议解决",
                "description": "诉讼、仲裁、调解等争议解决法律事务"
            },
            {
                "name": "合规监管",
                "description": "反垄断、数据保护、环境法等合规监管事务"
            },
            {
                "name": "房地产",
                "description": "房地产开发、投资、租赁等房地产法律事务"
            },
            {
                "name": "劳动法",
                "description": "雇佣关系、劳动纠纷、人力资源等劳动法律事务"
            },
            {
                "name": "税务",
                "description": "税务筹划、税务争议、国际税务等税务法律事务"
            },
            {
                "name": "能源矿产",
                "description": "能源开发、矿产投资、环保等能源矿产法律事务"
            }
        ]
        
        for field_data in advanced_fields:
            # 检查是否已存在
            existing_field = db.query(BusinessField).filter(BusinessField.name == field_data["name"]).first()
            if not existing_field:
                business_field = BusinessField(**field_data)
                db.add(business_field)
        
        db.commit()
        print("已初始化高级业务领域数据")
        
    except Exception as e:
        print(f"初始化高级业务领域数据失败: {str(e)}")
        db.rollback()
    finally:
        db.close()

def init_classification_prompts(db: Session):
    """初始化文档分类提示词设置"""
    
    # 视觉模型分类提示词
    vision_classification_prompt = '''你是一个专业的法律文档分类专家。请分析这份文档图片，判断文档类型并提取关键信息。

文档类型分类（请仔细判断）：
1. performance_contract - 业绩合同：法律服务合同、委托协议、顾问协议等
2. award_certificate - 荣誉奖项：Chambers、Legal 500、Best Lawyers等法律行业奖项证书、排名认证等
3. qualification_certificate - 资质证照：
   - 律师执业证书（个人执业资格）
   - 律师事务所执业许可证（机构执业资格）
   - 营业执照、组织机构代码证
   - 各种行业认证、资质证明
   - 会员证书、从业资格证书
4. other - 其他杂项：不属于以上类别的其他文档

重点识别标准：
- **律师执业证**：标题含"律师执业证"、"执业证书"，个人姓名，执业证号，发证机关（司法部门）
- **事务所执业许可证**：标题含"律师事务所执业许可证"、"执业许可"，事务所名称，许可证号，发证机关
- **营业执照**：标题含"营业执照"，统一社会信用代码，注册资本，经营范围
- **获奖证书**：含奖项名称、获奖方、颁奖机构（如Chambers、Legal 500等）、年份
- **服务合同**：含甲方乙方、服务内容、服务费用、合同期限等

请按照以下JSON格式返回结果：
{
    "category": "文档类型代码",
    "category_name": "文档类型中文名称",
    "business_field": "业务领域（如果适用）",
    "year": 年份,
    "keywords": ["关键词1", "关键词2", "关键词3"],
    "confidence": 置信度(0-1),
    "description": "文档描述和分类依据",
    "specific_type": "具体类型（如：律师执业证、事务所许可证、Chambers排名等）"
}

分析要点：
1. **优先识别标题和文档头部**：这是判断文档类型的关键
2. **查找关键标识**：执业证号、许可证号、奖项年份、合同编号等
3. **识别发证/颁奖机构**：司法部门、评级机构、客户单位等
4. **观察格式特征**：证书格式、合同格式、官方印章等
5. **提取关键实体**：人名、机构名、金额、日期等
6. **置信度评估**：根据关键信息的清晰度和完整性评分

特别注意：律师事务所的执业许可证应归类为 qualification_certificate（资质证照），而非其他类别！'''

    # 文本综合分类提示词
    text_classification_prompt = '''你是一个专业的法律文档分类专家。请基于提供的文档内容进行分类分析。

文档类型分类（请仔细判断）：
1. performance_contract - 业绩合同：法律服务合同、委托协议、顾问协议、服务协议等
2. award_certificate - 荣誉奖项：Chambers、Legal 500、Best Lawyers、IFLR、Who's Who Legal等法律行业奖项证书、排名认证等
3. qualification_certificate - 资质证照：
   - 律师执业证书（个人执业资格证明）
   - 律师事务所执业许可证（机构执业资格证明）
   - 营业执照、组织机构代码证、统一社会信用代码证
   - 各种行业认证证书、资质证明文件
   - 专业会员证书、从业资格证书
4. other - 其他杂项：不属于以上类别的其他文档

关键词识别标准（优先级排序）：
**资质证照类**（最高优先级）：
- "律师执业证"、"执业证书"、"执业许可证"、"律师事务所执业许可证"
- "营业执照"、"统一社会信用代码"、"组织机构代码"
- "资质证明"、"认证证书"、"从业资格"、"会员证书"
- "司法局"、"司法厅"、"司法部"、"市场监督管理局"（发证机关）
- "证号"、"许可证号"、"执业证号"、"信用代码"

**荣誉奖项类**：
- "Chambers"、"Legal 500"、"Best Lawyers"、"IFLR"、"Who's Who Legal"
- "排名"、"评级"、"奖项"、"荣誉"、"认证"、"推荐律师"
- "Ranked"、"Recommended"、"Leading"、"Notable"、"Rising Star"

**业绩合同类**：
- "合同"、"协议"、"委托书"、"服务协议"、"顾问协议"
- "甲方"、"乙方"、"委托方"、"受托方"
- "服务费"、"律师费"、"顾问费"、"合同金额"
- "服务期限"、"合同期限"、"委托期间"

请按照以下JSON格式返回结果：
{
    "category": "文档类型代码",
    "category_name": "文档类型中文名称", 
    "business_field": "业务领域（如果适用）",
    "year": 年份,
    "keywords": ["关键词1", "关键词2", "关键词3"],
    "confidence": 置信度(0-1),
    "description": "分类依据和文档描述",
    "specific_type": "具体类型（如：律师执业证、事务所许可证、Chambers排名等）",
    "key_entities": {
        "holder_name": "持证人/获奖方名称",
        "issuer": "颁发/发证机构",
        "certificate_number": "证书/许可证号（如果是资质证照）",
        "award_name": "奖项名称（如果是获奖）",
        "client_name": "客户名称（如果是合同）",
        "amount": "合同金额（如果是合同）",
        "date_issued": "颁发/签署日期"
    }
}

分析优先级：
1. **首先查找资质证照关键词**：如发现"执业证"、"许可证"、"营业执照"等，优先分类为 qualification_certificate
2. **其次查找奖项关键词**：如发现"Chambers"、"Legal 500"、"排名"等，分类为 award_certificate  
3. **最后查找合同关键词**：如发现"合同"、"协议"、"甲方乙方"等，分类为 performance_contract
4. **提取关键实体信息**：机构名称、个人姓名、证书号码、日期等
5. **评估置信度**：根据关键信息的数量和清晰度打分

特别强调：
- 律师事务所执业许可证必须归类为 qualification_certificate（资质证照）
- 个人律师执业证也必须归类为 qualification_certificate（资质证照）
- 营业执照、组织机构代码证等均为 qualification_certificate（资质证照）
- 只有真正的法律行业排名和奖项才归类为 award_certificate'''

    # 添加分类提示词设置
    classification_settings = [
        {
            "setting_key": "classification_vision_prompt",
            "setting_value": vision_classification_prompt,
            "setting_type": "longtext",
            "category": "ai_classification",
            "description": "视觉模型文档分类提示词",
            "is_editable": True,
            "requires_restart": False
        },
        {
            "setting_key": "classification_text_prompt", 
            "setting_value": text_classification_prompt,
            "setting_type": "longtext",
            "category": "ai_classification",
            "description": "文本综合分类提示词",
            "is_editable": True,
            "requires_restart": False
        },
        # Docling OCR配置
        {
            "setting_key": "docling_enable_ocr",
            "setting_value": "true",
            "setting_type": "boolean",
            "category": "ocr",
            "description": "是否启用Docling OCR功能",
            "is_editable": True,
            "requires_restart": True
        },
        {
            "setting_key": "docling_use_gpu",
            "setting_value": "false",
            "setting_type": "boolean",
            "category": "ocr",
            "description": "Docling OCR是否使用GPU加速",
            "is_editable": True,
            "requires_restart": True
        },
        {
            "setting_key": "docling_ocr_languages",
            "setting_value": '["zh-cn", "en"]',
            "setting_type": "json",
            "category": "ocr",
            "description": "Docling OCR支持的语言列表",
            "is_editable": True,
            "requires_restart": True
        },
        {
            "setting_key": "docling_confidence_threshold",
            "setting_value": "0.5",
            "setting_type": "number",
            "category": "ocr",
            "description": "OCR识别置信度阈值",
            "is_editable": True,
            "requires_restart": False
        },
        {
            "setting_key": "docling_bitmap_area_threshold", 
            "setting_value": "0.05",
            "setting_type": "number",
            "category": "ocr",
            "description": "OCR识别位图区域阈值",
            "is_editable": True,
            "requires_restart": False
        }
    ]
    
    # 检查并添加设置
    for setting_data in classification_settings:
        existing = db.query(SystemSettings).filter(
            SystemSettings.setting_key == setting_data["setting_key"]
        ).first()
        
        if not existing:
            setting = SystemSettings(**setting_data)
            db.add(setting)
            print(f"✅ 添加设置: {setting_data['setting_key']}")
        else:
            print(f"⚠️  设置已存在: {setting_data['setting_key']}")
    
    db.commit()

def init_advanced_data():
    """初始化高级功能数据"""
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    print("✅ 数据库表创建完成")
    
    db = next(get_db())
    try:
        # 初始化分类提示词
        print("\n🔧 初始化文档分类提示词设置...")
        init_classification_prompts(db)
        
        init_section_types()
        init_data_sources()
        init_recommendation_rules()
        init_advanced_brands()
        init_advanced_business_fields()
        
        print("\n✅ 高级功能数据初始化完成！")
        
    except Exception as e:
        print(f"❌ 初始化失败: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    init_advanced_data() 