#!/usr/bin/env python3
"""
高级功能初始化脚本
用于初始化智能章节管理、AI自动检索奖项等高级功能的基础数据
"""

import sys
import os
from datetime import datetime

# 添加当前目录到sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from models import (
    SectionType, DataSource, RecommendationRule,
    Brand, BusinessField
)

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

def main():
    """主函数"""
    print("开始初始化高级功能数据...")
    print("=" * 50)
    
    init_section_types()
    init_data_sources()
    init_recommendation_rules()
    init_advanced_brands()
    init_advanced_business_fields()
    
    print("=" * 50)
    print("高级功能数据初始化完成！")

if __name__ == "__main__":
    main() 