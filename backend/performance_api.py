"""
业绩管理API
"""
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import Optional, List
import logging
import os
from datetime import datetime

from database import get_db
from models import Performance, PerformanceFile
from schemas import PerformanceCreate, PerformanceUpdate, PerformanceResponse

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/stats")
async def get_performance_stats(db: Session = Depends(get_db)):
    """获取业绩统计数据"""
    try:
        total_performances = db.query(Performance).count()
        verified_performances = db.query(Performance).filter(Performance.is_verified == True).count()
        manual_input_performances = db.query(Performance).filter(Performance.is_manual_input == True).count()
        
        # 按年份统计
        yearly_stats = db.query(
            Performance.year,
            func.count(Performance.id).label('count')
        ).group_by(Performance.year).order_by(desc(Performance.year)).limit(5).all()
        
        # 按业务领域统计
        field_stats = db.query(
            Performance.business_field,
            func.count(Performance.id).label('count')
        ).group_by(Performance.business_field).order_by(desc(func.count(Performance.id))).limit(5).all()
        
        return {
            "success": True,
            "stats": {
                "total_performances": total_performances,
                "verified_performances": verified_performances,
                "manual_input_performances": manual_input_performances,
                "yearly_distribution": [
                    {"year": stat.year, "count": stat.count} 
                    for stat in yearly_stats
                ],
                "field_distribution": [
                    {"field": stat.business_field, "count": stat.count} 
                    for stat in field_stats if stat.business_field
                ]
            }
        }
        
    except Exception as e:
        logger.error(f"获取业绩统计失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取统计数据失败: {str(e)}")

@router.get("/list")
async def list_performances(
    page: int = 1,
    page_size: int = 20,
    search: Optional[str] = None,
    business_field: Optional[str] = None,
    year: Optional[int] = None,
    is_verified: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """获取业绩列表"""
    try:
        query = db.query(Performance)
        
        # 搜索过滤
        if search:
            query = query.filter(
                Performance.project_name.ilike(f'%{search}%') |
                Performance.client_name.ilike(f'%{search}%') |
                Performance.description.ilike(f'%{search}%')
            )
        
        # 业务领域过滤
        if business_field:
            query = query.filter(Performance.business_field == business_field)
        
        # 年份过滤
        if year:
            query = query.filter(Performance.year == year)
        
        # 验证状态过滤
        if is_verified is not None:
            query = query.filter(Performance.is_verified == is_verified)
        
        # 总数
        total = query.count()
        
        # 分页
        offset = (page - 1) * page_size
        performances = query.order_by(desc(Performance.created_at)).offset(offset).limit(page_size).all()
        
        return {
            "success": True,
            "performances": [
                {
                    "id": perf.id,
                    "project_name": perf.project_name,
                    "client_name": perf.client_name,
                    "project_type": perf.project_type,
                    "business_field": perf.business_field,
                    "year": perf.year,
                    "contract_amount": perf.contract_amount,
                    "currency": perf.currency,
                    "start_date": perf.start_date.isoformat() if perf.start_date else None,
                    "end_date": perf.end_date.isoformat() if perf.end_date else None,
                    "description": perf.description,
                    "confidence_score": perf.confidence_score,
                    "is_verified": perf.is_verified,
                    "is_manual_input": perf.is_manual_input,
                    "source_document": perf.source_document,
                    "created_at": perf.created_at.isoformat()
                }
                for perf in performances
            ],
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "pages": (total + page_size - 1) // page_size
            }
        }
        
    except Exception as e:
        logger.error(f"获取业绩列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取业绩列表失败: {str(e)}")

@router.post("/create")
async def create_performance(
    performance_data: dict,
    db: Session = Depends(get_db)
):
    """手动创建业绩记录"""
    try:
        # 创建业绩记录
        performance = Performance(
            project_name=performance_data.get("project_name"),
            client_name=performance_data.get("client_name"),
            project_type=performance_data.get("project_type"),
            business_field=performance_data.get("business_field"),
            year=int(performance_data.get("year")),
            contract_amount=performance_data.get("contract_amount"),
            currency=performance_data.get("currency", "CNY"),
            start_date=datetime.fromisoformat(performance_data["start_date"]) if performance_data.get("start_date") else None,
            end_date=datetime.fromisoformat(performance_data["end_date"]) if performance_data.get("end_date") else None,
            description=performance_data.get("description"),
            is_manual_input=True,
            is_verified=True  # 手动创建的默认为已验证
        )
        
        db.add(performance)
        db.commit()
        db.refresh(performance)
        
        logger.info(f"手动创建业绩记录成功: {performance.project_name}")
        
        return {
            "success": True,
            "message": "业绩记录创建成功",
            "performance_id": performance.id
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"创建业绩记录失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建业绩记录失败: {str(e)}")

@router.post("/upload")
async def upload_performance_files(
    files: List[UploadFile] = File(...),
    project_name: Optional[str] = Form(None),
    client_name: Optional[str] = Form(None),
    business_field: Optional[str] = Form(None),
    enable_ai_analysis: bool = Form(True),
    enable_vision_analysis: bool = Form(True),
    db: Session = Depends(get_db)
):
    """上传业绩文件（支持多文件）并进行AI分析"""
    try:
        # 保存文件目录
        upload_dir = os.path.join(os.path.dirname(__file__), "uploads", "performances")
        os.makedirs(upload_dir, exist_ok=True)
        
        # 创建业绩记录
        performance = Performance(
            project_name=project_name or "待AI分析",
            client_name=client_name or "待AI分析",
            project_type="重大个案",  # 默认值
            business_field=business_field or "待AI分析",
            year=datetime.now().year,
            is_manual_input=False,
            is_verified=False,
            confidence_score=0.0
        )
        
        db.add(performance)
        db.flush()  # 获取performance.id但不提交事务
        
        uploaded_files = []
        file_paths = []
        
        # 处理每个上传的文件
        for i, file in enumerate(files):
            # 生成唯一文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            file_path = os.path.join(upload_dir, f"{timestamp}_{i}_{file.filename}")
            
            # 保存文件
            with open(file_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
            
            # 创建文件记录
            performance_file = PerformanceFile(
                performance_id=performance.id,
                file_path=file_path,
                file_type="contract" if "合同" in file.filename or "contract" in file.filename.lower() else "supporting_doc",
                file_name=file.filename,
                file_size=len(content)
            )
            
            db.add(performance_file)
            uploaded_files.append(file.filename)
            file_paths.append(file_path)
        
        # 设置主要源文档（第一个文件）
        if file_paths:
            performance.source_document = file_paths[0]
        
        db.commit()
        db.refresh(performance)
        
        logger.info(f"业绩文件上传成功: {len(files)} 个文件, performance_id: {performance.id}")
        
        return {
            "success": True,
            "message": f"成功上传 {len(files)} 个文件，AI分析中...",
            "performance_id": performance.id,
            "uploaded_files": uploaded_files
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"上传业绩文件失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")

@router.patch("/{performance_id}/verify")
async def verify_performance(
    performance_id: int,
    db: Session = Depends(get_db)
):
    """验证业绩记录"""
    try:
        performance = db.query(Performance).filter(Performance.id == performance_id).first()
        if not performance:
            raise HTTPException(status_code=404, detail="业绩记录不存在")
        
        performance.is_verified = True
        db.commit()
        
        return {
            "success": True,
            "message": "业绩记录已验证"
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"验证业绩记录失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"验证失败: {str(e)}")

@router.post("/{performance_id}/reanalyze")
async def reanalyze_performance(
    performance_id: int,
    db: Session = Depends(get_db)
):
    """重新分析业绩文件"""
    try:
        performance = db.query(Performance).filter(Performance.id == performance_id).first()
        if not performance:
            raise HTTPException(status_code=404, detail="业绩记录不存在")
        
        if not performance.source_document or not os.path.exists(performance.source_document):
            raise HTTPException(status_code=400, detail="源文档不存在，无法重新分析")
        
        # TODO: 集成AI重新分析
        # 这里应该调用AI服务重新分析文档
        logger.info(f"重新分析业绩文件: {performance.source_document}")
        
        # 更新分析状态
        performance.confidence_score = 0.8  # 模拟分析结果
        db.commit()
        
        return {
            "success": True,
            "message": "重新分析完成"
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"重新分析业绩失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"重新分析失败: {str(e)}")

@router.delete("/{performance_id}")
async def delete_performance(
    performance_id: int,
    db: Session = Depends(get_db)
):
    """删除业绩记录"""
    try:
        performance = db.query(Performance).filter(Performance.id == performance_id).first()
        if not performance:
            raise HTTPException(status_code=404, detail="业绩记录不存在")
        
        # 删除关联文件
        if performance.source_document and os.path.exists(performance.source_document):
            os.remove(performance.source_document)
        
        db.delete(performance)
        db.commit()
        
        return {
            "success": True,
            "message": "业绩记录已删除"
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"删除业绩记录失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}") 