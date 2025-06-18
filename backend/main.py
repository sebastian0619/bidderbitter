from fastapi import FastAPI, File, UploadFile, Depends, HTTPException, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any, Union
import os
import shutil
import asyncio
import logging
from datetime import datetime
import json
from docx import Document
from PIL import Image

from database import get_db, init_db
from models import *
from ai_service import ai_service
from screenshot_service import screenshot_service
from document_generator import document_generator
import schemas

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="投标软件系统",
    description="法律行业投标资料管理和生成系统",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://frontend:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件
app.mount("/screenshots", StaticFiles(directory="/app/screenshots"), name="screenshots")
app.mount("/uploads", StaticFiles(directory="/app/uploads"), name="uploads")
app.mount("/generated", StaticFiles(directory="/app/generated_docs"), name="generated")

# 创建必要的目录
os.makedirs("/app/uploads", exist_ok=True)
os.makedirs("/app/screenshots", exist_ok=True)
os.makedirs("/app/generated_docs", exist_ok=True)

@app.on_event("startup")
async def startup_event():
    """应用启动时初始化数据库"""
    try:
        init_db()
        logger.info("数据库初始化完成")
        
        # 初始化基础数据
        await init_base_data()
        
    except Exception as e:
        logger.error(f"应用启动失败: {str(e)}")

async def init_base_data():
    """初始化基础数据"""
    try:
        db = next(get_db())
        
        # 初始化厂牌数据
        brands = [
            # 国际知名法律评级机构
            {"name": "Chambers", "full_name": "Chambers and Partners", "website": "https://chambers.com", "description": "全球权威法律评级机构"},
            {"name": "Legal 500", "full_name": "The Legal 500", "website": "https://www.legal500.com", "description": "国际领先的法律目录"},
            {"name": "IFLR", "full_name": "International Financial Law Review", "website": "https://www.iflr.com", "description": "国际金融法律评级"},
            {"name": "Who's Who Legal", "full_name": "Who's Who Legal", "website": "https://whoswholegal.com", "description": "全球律师指南"},
            {"name": "Best Lawyers", "full_name": "Best Lawyers", "website": "https://www.bestlawyers.com", "description": "美国最佳律师评级"},
            
            # 亚太地区法律评级机构
            {"name": "ALB", "full_name": "Asian Legal Business", "website": "https://www.legalbusinessonline.com", "description": "亚洲法律商业杂志"},
            {"name": "Legal Band", "full_name": "Legal Band", "website": "https://legalband.com", "description": "中国法律评级机构"},
            {"name": "Asialaw", "full_name": "Asialaw Profiles", "website": "https://asialaw.com", "description": "亚洲法律评级"},
            {"name": "China Law & Practice", "full_name": "China Law & Practice", "website": "https://www.chinalawandpractice.com", "description": "中国法律实务"},
            {"name": "LEGALWEEK", "full_name": "LEGALWEEK", "website": "https://www.legalweek.com", "description": "法律周刊评级"},
            
            # 专业领域评级机构
            {"name": "IAM", "full_name": "Intellectual Asset Management", "website": "https://www.iam-media.com", "description": "知识产权领域专业评级"},
            {"name": "PLC Which Lawyer", "full_name": "PLC Which Lawyer", "website": "https://www.legal500.com", "description": "专业法律指南"},
            {"name": "Global Arbitration Review", "full_name": "Global Arbitration Review", "website": "https://globalarbitrationreview.com", "description": "国际仲裁评级"},
            {"name": "Global Competition Review", "full_name": "Global Competition Review", "website": "https://globalcompetitionreview.com", "description": "全球竞争法评级"},
            {"name": "IFLR1000", "full_name": "IFLR1000", "website": "https://www.iflr1000.com", "description": "金融法律评级"},
            
            # 其他重要评级
            {"name": "Benchmark Litigation", "full_name": "Benchmark Litigation", "website": "https://www.benchmarklitigation.com", "description": "诉讼律师评级"},
            {"name": "China Business Law Journal", "full_name": "China Business Law Journal", "website": "https://www.cblj.com", "description": "中国商法杂志"},
            {"name": "Korea Law", "full_name": "Korea Law", "website": "https://www.korealaw.com", "description": "韩国法律评级"},
            {"name": "Japan Law", "full_name": "Japan Law", "website": "https://www.japanlaw.com", "description": "日本法律评级"}
        ]
        
        for brand_data in brands:
            existing = db.query(Brand).filter(Brand.name == brand_data["name"]).first()
            if not existing:
                brand = Brand(**brand_data)
                db.add(brand)
        
        # 初始化业务领域数据
        business_fields = [
            # 公司法律服务
            "公司业务", "并购重组", "外商投资", "私募股权/风险投资", "公司治理",
            "合规与监管", "反垄断与竞争法", "数据保护与隐私", "公司重组与破产",
            
            # 金融法律服务
            "银行与金融", "资本市场", "债券发行", "资产证券化", "基金与资产管理",
            "保险法", "融资租赁", "金融科技", "绿色金融", "REITs",
            
            # 争议解决
            "争议解决", "国际仲裁", "商事仲裁", "诉讼代理", "调解服务",
            "执行与保全", "跨境争议", "建设工程争议", "金融争议",
            
            # 专业法律领域
            "知识产权", "专利申请与保护", "商标注册与维权", "版权保护", "商业秘密",
            "反不正当竞争", "娱乐法", "体育法", "网络法", "电子商务法",
            
            # 基础设施与能源
            "建设工程", "基础设施", "能源法", "石油天然气", "电力法",
            "新能源", "环境法", "碳中和与ESG", "矿业法",
            
            # 房地产与土地
            "房地产", "土地使用权", "房地产开发", "房地产投资", "物业管理",
            "城市更新", "特色小镇", "产业园区",
            
            # 国际贸易与海事
            "国际贸易", "海关与贸易合规", "反倾销与反补贴", "自贸区业务",
            "航运海事", "船舶金融", "货物运输", "海事保险", "港口法务",
            
            # 劳动与社会保障
            "劳动法", "劳动争议", "人力资源", "社会保险", "工伤赔偿",
            "劳动合规", "外籍员工", "高管激励",
            
            # 税务与财务
            "税法", "税务争议", "税务筹划", "国际税务", "转让定价",
            "关税与进出口税", "增值税", "企业所得税", "个人所得税",
            
            # 新兴业务领域
            "医疗健康", "生物医药", "医疗器械", "互联网", "人工智能",
            "区块链", "虚拟货币", "游戏法", "教育法", "食品药品",
            
            # 政府与公共事务
            "政府法律顾问", "PPP项目", "政府采购", "行政法", "刑事辩护",
            "反腐败与职务犯罪", "监察法", "国家安全法",
            
            # 跨境业务
            "跨境投资", "境外上市", "QFII/QDII", "外汇管理", "国际制裁",
            "一带一路", "中美贸易", "跨境数据传输", "跨境电商",
            
            # 特殊行业
            "航空航天", "汽车制造", "化工医药", "电信通信", "传媒娱乐",
            "金融科技", "新零售", "供应链金融", "农业法", "旅游法"
        ]
        
        for field_name in business_fields:
            existing = db.query(BusinessField).filter(BusinessField.name == field_name).first()
            if not existing:
                field = BusinessField(name=field_name)
                db.add(field)
        
        db.commit()
        logger.info("基础数据初始化完成")
        
    except Exception as e:
        logger.error(f"基础数据初始化失败: {str(e)}")
    finally:
        db.close()

# ==================== 文件上传和处理 ====================

@app.post("/api/upload/document")
async def upload_document(
    file: UploadFile = File(...),
    document_type: str = Form(...),  # "award" or "performance"
    db: Session = Depends(get_db)
):
    """上传文档并进行AI分析"""
    try:
        # 保存上传的文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{file.filename}"
        filepath = os.path.join("/app/uploads", filename)
        
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 根据文件类型进行处理
        if file.filename.lower().endswith('.pdf'):
            extracted_data = await ai_service.extract_text_from_pdf(filepath)
        elif file.filename.lower().endswith('.docx'):
            extracted_data = await ai_service.extract_text_from_docx(filepath)
        elif file.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            extracted_data = await ai_service.extract_text_from_image(filepath)
        else:
            raise HTTPException(status_code=400, detail="不支持的文件格式")
        
        if extracted_data.get("error"):
            raise HTTPException(status_code=500, detail=f"文件处理失败: {extracted_data['error']}")
        
        # AI分析文档内容
        if document_type == "award":
            text_content = extracted_data.get("full_text") or "\n".join([item.get("text", "") for item in extracted_data.get("content", [])])
            analysis_result = await ai_service.analyze_award_document(text_content)
        else:
            text_content = extracted_data.get("full_text") or "\n".join([item.get("text", "") for item in extracted_data.get("content", [])])
            analysis_result = await ai_service.analyze_performance_document(text_content)
        
        return {
            "success": True,
            "file_path": filepath,
            "extracted_data": extracted_data,
            "analysis_result": analysis_result,
            "document_type": document_type
        }
        
    except Exception as e:
        logger.error(f"文档上传处理失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/process/screenshot")
async def process_screenshot(
    urls: List[str],
    award_id: Optional[int] = None
):
    """处理网页截图"""
    try:
        if not urls:
            raise HTTPException(status_code=400, detail="URL列表不能为空")
        
        # 批量截图
        results = await screenshot_service.capture_award_pages(urls, award_id)
        
        return {
            "success": True,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"网页截图处理失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== 获奖信息管理 ====================

@app.post("/api/awards")
async def create_award(award_data: Dict[str, Any], db: Session = Depends(get_db)):
    """创建获奖记录"""
    try:
        award = Award(
            title=award_data.get("title"),
            brand=award_data.get("brand"),
            year=award_data.get("year"),
            business_type=award_data.get("business_type"),
            description=award_data.get("description"),
            source_document=award_data.get("source_document"),
            source_url=award_data.get("source_url"),
            screenshot_path=award_data.get("screenshot_path"),
            screenshot_pages=award_data.get("screenshot_pages"),
            ai_analysis=award_data.get("ai_analysis"),
            confidence_score=award_data.get("confidence_score", 0.0),
            is_manual_input=award_data.get("is_manual_input", False)
        )
        
        db.add(award)
        db.commit()
        db.refresh(award)
        
        return {"success": True, "award_id": award.id}
        
    except Exception as e:
        logger.error(f"创建获奖记录失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/awards")
async def get_awards(
    brand: Optional[str] = Query(None),
    business_type: Optional[str] = Query(None),
    year: Optional[int] = Query(None),
    verified_only: bool = Query(False),
    skip: int = Query(0),
    limit: int = Query(100),
    db: Session = Depends(get_db)
):
    """获取获奖记录列表"""
    try:
        query = db.query(Award)
        
        if brand:
            query = query.filter(Award.brand == brand)
        if business_type:
            query = query.filter(Award.business_type == business_type)
        if year:
            query = query.filter(Award.year == year)
        if verified_only:
            query = query.filter(Award.is_verified == True)
        
        total = query.count()
        awards = query.offset(skip).limit(limit).all()
        
        return {
            "success": True,
            "total": total,
            "awards": [
                {
                    "id": award.id,
                    "title": award.title,
                    "brand": award.brand,
                    "year": award.year,
                    "business_type": award.business_type,
                    "description": award.description,
                    "is_verified": award.is_verified,
                    "confidence_score": award.confidence_score,
                    "screenshot_pages": award.screenshot_pages,
                    "created_at": award.created_at.isoformat()
                }
                for award in awards
            ]
        }
        
    except Exception as e:
        logger.error(f"获取获奖记录失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/awards/{award_id}")
async def update_award(
    award_id: int,
    award_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """更新获奖记录"""
    try:
        award = db.query(Award).filter(Award.id == award_id).first()
        if not award:
            raise HTTPException(status_code=404, detail="获奖记录不存在")
        
        # 更新字段
        for key, value in award_data.items():
            if hasattr(award, key):
                setattr(award, key, value)
        
        award.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(award)
        
        return {"success": True, "message": "获奖记录更新成功"}
        
    except Exception as e:
        logger.error(f"更新获奖记录失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/awards/{award_id}")
async def delete_award(award_id: int, db: Session = Depends(get_db)):
    """删除获奖记录"""
    try:
        award = db.query(Award).filter(Award.id == award_id).first()
        if not award:
            raise HTTPException(status_code=404, detail="获奖记录不存在")
        
        db.delete(award)
        db.commit()
        
        return {"success": True, "message": "获奖记录删除成功"}
        
    except Exception as e:
        logger.error(f"删除获奖记录失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== 业绩信息管理 ====================

@app.post("/api/performances")
async def create_performance(performance_data: Dict[str, Any], db: Session = Depends(get_db)):
    """创建业绩记录"""
    try:
        performance = Performance(
            client_name=performance_data.get("client_name"),
            project_name=performance_data.get("project_name"),
            project_type=performance_data.get("project_type"),
            business_field=performance_data.get("business_field"),
            start_date=datetime.fromisoformat(performance_data["start_date"]) if performance_data.get("start_date") else None,
            end_date=datetime.fromisoformat(performance_data["end_date"]) if performance_data.get("end_date") else None,
            year=performance_data.get("year"),
            contract_amount=performance_data.get("contract_amount"),
            currency=performance_data.get("currency", "CNY"),
            description=performance_data.get("description"),
            source_document=performance_data.get("source_document"),
            contract_file=performance_data.get("contract_file"),
            ai_analysis=performance_data.get("ai_analysis"),
            confidence_score=performance_data.get("confidence_score", 0.0),
            is_manual_input=performance_data.get("is_manual_input", False)
        )
        
        db.add(performance)
        db.commit()
        db.refresh(performance)
        
        return {"success": True, "performance_id": performance.id}
        
    except Exception as e:
        logger.error(f"创建业绩记录失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/performances")
async def get_performances(
    business_field: Optional[str] = Query(None),
    project_type: Optional[str] = Query(None),
    year: Optional[int] = Query(None),
    verified_only: bool = Query(False),
    skip: int = Query(0),
    limit: int = Query(100),
    db: Session = Depends(get_db)
):
    """获取业绩记录列表"""
    try:
        query = db.query(Performance)
        
        if business_field:
            query = query.filter(Performance.business_field == business_field)
        if project_type:
            query = query.filter(Performance.project_type == project_type)
        if year:
            query = query.filter(Performance.year == year)
        if verified_only:
            query = query.filter(Performance.is_verified == True)
        
        total = query.count()
        performances = query.offset(skip).limit(limit).all()
        
        return {
            "success": True,
            "total": total,
            "performances": [
                {
                    "id": perf.id,
                    "client_name": perf.client_name,
                    "project_name": perf.project_name,
                    "project_type": perf.project_type,
                    "business_field": perf.business_field,
                    "year": perf.year,
                    "contract_amount": perf.contract_amount,
                    "currency": perf.currency,
                    "description": perf.description,
                    "is_verified": perf.is_verified,
                    "confidence_score": perf.confidence_score,
                    "created_at": perf.created_at.isoformat()
                }
                for perf in performances
            ]
        }
        
    except Exception as e:
        logger.error(f"获取业绩记录失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== 文档生成 ====================

@app.post("/api/generate/document")
async def generate_document(
    request_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """生成Word文档"""
    try:
        doc_type = request_data.get("type", "combined")  # "award", "performance", "combined"
        filters = request_data.get("filters", {})
        
        # 构建查询
        award_query = db.query(Award)
        performance_query = db.query(Performance)
        
        # 应用筛选条件
        if filters.get("brands"):
            award_query = award_query.filter(Award.brand.in_(filters["brands"]))
        
        if filters.get("business_fields"):
            award_query = award_query.filter(Award.business_type.in_(filters["business_fields"]))
            performance_query = performance_query.filter(Performance.business_field.in_(filters["business_fields"]))
        
        if filters.get("years"):
            award_query = award_query.filter(Award.year.in_(filters["years"]))
            performance_query = performance_query.filter(Performance.year.in_(filters["years"]))
        
        # 获取数据
        awards = []
        performances = []
        
        if doc_type in ["award", "combined"]:
            awards = award_query.all()
            awards = [
                {
                    "id": award.id,
                    "title": award.title,
                    "brand": award.brand,
                    "year": award.year,
                    "business_type": award.business_type,
                    "description": award.description,
                    "screenshot_pages": award.screenshot_pages or []
                }
                for award in awards
            ]
        
        if doc_type in ["performance", "combined"]:
            performances = performance_query.all()
            performances = [
                {
                    "id": perf.id,
                    "client_name": perf.client_name,
                    "project_name": perf.project_name,
                    "project_type": perf.project_type,
                    "business_field": perf.business_field,
                    "year": perf.year,
                    "contract_amount": perf.contract_amount,
                    "currency": perf.currency,
                    "description": perf.description,
                    "start_date": perf.start_date.strftime("%Y-%m-%d") if perf.start_date else None,
                    "end_date": perf.end_date.strftime("%Y-%m-%d") if perf.end_date else None,
                    "files": []  # TODO: 添加文件关联
                }
                for perf in performances
            ]
        
        # 生成文档
        if doc_type == "award":
            filepath = document_generator.generate_award_document(awards, filters)
        elif doc_type == "performance":
            filepath = document_generator.generate_performance_document(performances, filters)
        else:
            filepath = document_generator.generate_combined_document(awards, performances, filters)
        
        # 返回文件下载链接
        filename = os.path.basename(filepath)
        return {
            "success": True,
            "download_url": f"/api/download/{filename}",
            "filename": filename
        }
        
    except Exception as e:
        logger.error(f"文档生成失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/download/{filename}")
async def download_file(filename: str):
    """下载生成的文档"""
    filepath = os.path.join("/app/generated_docs", filename)
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="文件不存在")
    
    return FileResponse(
        path=filepath,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

# ==================== 配置管理 ====================

@app.get("/api/config/brands")
async def get_brands(db: Session = Depends(get_db)):
    """获取厂牌列表"""
    brands = db.query(Brand).filter(Brand.is_active == True).all()
    return {
        "success": True,
        "brands": [
            {
                "id": brand.id,
                "name": brand.name,
                "full_name": brand.full_name,
                "website": brand.website
            }
            for brand in brands
        ]
    }

@app.get("/api/config/business-fields")
async def get_business_fields(db: Session = Depends(get_db)):
    """获取业务领域列表"""
    fields = db.query(BusinessField).filter(BusinessField.is_active == True).all()
    return {
        "success": True,
        "business_fields": [
            {
                "id": field.id,
                "name": field.name,
                "description": field.description,
                "parent_id": field.parent_id
            }
            for field in fields
        ]
    }

# ==================== 健康检查 ====================

@app.get("/api/health")
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

# ==================== 系统设置管理 ====================

@app.get("/api/settings")
async def get_settings(category: Optional[str] = None, db: Session = Depends(get_db)):
    """获取系统设置"""
    try:
        query = db.query(SystemSettings)
        if category:
            query = query.filter(SystemSettings.category == category)
        
        settings = query.all()
        
        # 将设置转换为字典格式
        settings_dict = {}
        for setting in settings:
            # 敏感信息进行脱敏处理
            value = setting.setting_value
            if setting.is_sensitive and value:
                value = "******" if len(value) > 6 else "*" * len(value)
            
            settings_dict[setting.setting_key] = {
                "value": value,
                "type": setting.setting_type,
                "category": setting.category,
                "description": setting.description,
                "is_sensitive": setting.is_sensitive
            }
        
        return {
            "success": True,
            "settings": settings_dict
        }
        
    except Exception as e:
        logger.error(f"获取设置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/settings")
async def update_settings(
    settings_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """更新系统设置"""
    try:
        updated_settings = []
        
        for key, value in settings_data.items():
            # 查找现有设置
            existing_setting = db.query(SystemSettings).filter(
                SystemSettings.setting_key == key
            ).first()
            
            if existing_setting:
                # 更新现有设置
                existing_setting.setting_value = str(value)
                existing_setting.updated_at = datetime.utcnow()
            else:
                # 创建新设置（根据键名推断分类）
                category = "general"
                if key.startswith("ai_") or "model" in key.lower():
                    category = "ai"
                elif key.startswith("upload_"):
                    category = "upload"
                elif key.startswith("screenshot_"):
                    category = "screenshot"
                
                new_setting = SystemSettings(
                    setting_key=key,
                    setting_value=str(value),
                    category=category,
                    is_sensitive="api_key" in key.lower() or "secret" in key.lower()
                )
                db.add(new_setting)
            
            updated_settings.append(key)
        
        db.commit()
        
        # 重新初始化AI服务以应用新的模型配置
        if any("model" in key.lower() or "ai_" in key for key in updated_settings):
            ai_service.reload_config()
        
        return {
            "success": True,
            "message": f"已更新 {len(updated_settings)} 个设置",
            "updated_settings": updated_settings
        }
        
    except Exception as e:
        logger.error(f"更新设置失败: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/settings/init-defaults")
async def init_default_settings(db: Session = Depends(get_db)):
    """初始化默认设置"""
    try:
        default_settings = [
            # AI模型设置
            {
                "key": "ai_provider",
                "value": "openai",
                "category": "ai",
                "description": "AI服务提供商 (openai/azure/custom)"
            },
            {
                "key": "ai_text_model",
                "value": "gpt-4",
                "category": "ai",
                "description": "文本分析模型"
            },
            {
                "key": "ai_vision_model",
                "value": "gpt-4-vision-preview",
                "category": "ai",
                "description": "图像分析模型"
            },
            {
                "key": "ai_api_key",
                "value": "",
                "category": "ai",
                "description": "AI API密钥",
                "is_sensitive": True
            },
            {
                "key": "ai_base_url",
                "value": "https://api.openai.com/v1",
                "category": "ai",
                "description": "AI API基础URL"
            },
            # 上传设置
            {
                "key": "upload_max_file_size",
                "value": "52428800",
                "category": "upload",
                "description": "最大文件大小（字节）"
            },
            {
                "key": "upload_allowed_types",
                "value": "pdf,docx,doc,png,jpg,jpeg",
                "category": "upload",
                "description": "允许的文件类型"
            },
            # 截图设置
            {
                "key": "screenshot_timeout",
                "value": "30",
                "category": "screenshot",
                "description": "截图超时时间（秒）"
            },
            {
                "key": "screenshot_max_pages",
                "value": "20",
                "category": "screenshot",
                "description": "最大截图页数"
            }
        ]
        
        created_count = 0
        for setting_info in default_settings:
            # 检查设置是否已存在
            existing = db.query(SystemSettings).filter(
                SystemSettings.setting_key == setting_info["key"]
            ).first()
            
            if not existing:
                new_setting = SystemSettings(
                    setting_key=setting_info["key"],
                    setting_value=setting_info["value"],
                    category=setting_info["category"],
                    description=setting_info["description"],
                    is_sensitive=setting_info.get("is_sensitive", False)
                )
                db.add(new_setting)
                created_count += 1
        
        db.commit()
        
        return {
            "success": True,
            "message": f"已初始化 {created_count} 个默认设置"
        }
        
    except Exception as e:
        logger.error(f"初始化默认设置失败: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/convert-to-word")
async def convert_files_to_word(
    files: List[UploadFile] = File(...),
    document_title: str = Form(default="转换文档")
):
    """
    将上传的PDF和图片文件转换为Word文档
    """
    try:
        # 创建临时目录
        temp_dir = "temp_conversions"
        os.makedirs(temp_dir, exist_ok=True)
        
        # 创建Word文档
        doc = Document()
        doc.add_heading(document_title, 0)
        
        processed_files = []
        
        for file in files:
            # 保存上传的文件
            file_path = os.path.join(temp_dir, file.filename)
            with open(file_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
            
            file_ext = os.path.splitext(file.filename)[1].lower()
            
            if file_ext == '.pdf':
                # PDF转图片再插入Word
                await process_pdf_to_word(doc, file_path, file.filename)
                processed_files.append(f"PDF: {file.filename}")
            elif file_ext in ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff']:
                # 图片直接插入Word
                await process_image_to_word(doc, file_path, file.filename)
                processed_files.append(f"图片: {file.filename}")
            else:
                processed_files.append(f"不支持的格式: {file.filename}")
        
        # 保存Word文档
        output_filename = f"{document_title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
        output_path = os.path.join("uploads", output_filename)
        doc.save(output_path)
        
        # 清理临时文件
        import shutil
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        
        return {
            "success": True,
            "message": "文件转换完成",
            "output_file": output_filename,
            "processed_files": processed_files,
            "download_url": f"/api/download/{output_filename}"
        }
        
    except Exception as e:
        logger.error(f"文件转换失败: {str(e)}")
        return {"success": False, "message": f"转换失败: {str(e)}"}

async def process_pdf_to_word(doc, pdf_path, filename):
    """将PDF转换为图片并插入Word"""
    try:
        import fitz  # PyMuPDF
        
        doc.add_heading(f"来源文件: {filename}", level=1)
        
        # 打开PDF
        pdf_document = fitz.open(pdf_path)
        
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            
            # 将页面转换为图片
            mat = fitz.Matrix(2.0, 2.0)  # 提高分辨率
            pix = page.get_pixmap(matrix=mat)
            
            # 保存为临时图片
            temp_image_path = f"temp_page_{page_num + 1}.png"
            pix.save(temp_image_path)
            
            # 添加页面标题
            doc.add_heading(f"第 {page_num + 1} 页", level=2)
            
            # 插入图片到Word
            try:
                from docx.shared import Inches
                doc.add_picture(temp_image_path, width=Inches(6))
                doc.add_page_break()
            except Exception as e:
                doc.add_paragraph(f"图片插入失败: {str(e)}")
            
            # 删除临时图片
            if os.path.exists(temp_image_path):
                os.remove(temp_image_path)
        
        pdf_document.close()
        
    except Exception as e:
        doc.add_paragraph(f"PDF处理失败 ({filename}): {str(e)}")

async def process_image_to_word(doc, image_path, filename):
    """将图片直接插入Word"""
    try:
        from docx.shared import Inches
        
        doc.add_heading(f"图片: {filename}", level=1)
        
        # 获取图片信息
        with Image.open(image_path) as img:
            width, height = img.size
            doc.add_paragraph(f"尺寸: {width} x {height} 像素")
        
        # 插入图片
        doc.add_picture(image_path, width=Inches(6))
        doc.add_page_break()
        
    except Exception as e:
        doc.add_paragraph(f"图片处理失败 ({filename}): {str(e)}")

@app.get("/api/download/{filename}")
async def download_file(filename: str):
    """下载生成的Word文档"""
    file_path = os.path.join("uploads", filename)
    if os.path.exists(file_path):
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
    else:
        raise HTTPException(status_code=404, detail="文件不存在")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 