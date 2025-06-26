from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import List, Optional, Dict, Any
import json
from datetime import datetime

from database import get_db
from models import (
    ProjectSection, SectionType, SectionDataMapping, 
    Award, Performance, Project, DataSimilarity
)
from schemas import (
    SectionTypeCreate, SectionTypeUpdate, SectionTypeResponse,
    SectionDataMappingCreate, SectionDataMappingUpdate, SectionDataMappingResponse,
    SectionRecommendationRequest, SectionRecommendationResponse
)

router = APIRouter(prefix="/api/sections", tags=["智能章节管理"])

# 章节类型管理
@router.get("/types", response_model=List[SectionTypeResponse])
async def get_section_types(db: Session = Depends(get_db)):
    """获取所有章节类型"""
    types = db.query(SectionType).filter(SectionType.is_active == True).all()
    return types

@router.post("/types", response_model=SectionTypeResponse)
async def create_section_type(
    section_type: SectionTypeCreate, 
    db: Session = Depends(get_db)
):
    """创建章节类型"""
    db_section_type = SectionType(**section_type.dict())
    db.add(db_section_type)
    db.commit()
    db.refresh(db_section_type)
    return db_section_type

@router.put("/types/{type_id}", response_model=SectionTypeResponse)
async def update_section_type(
    type_id: int,
    section_type: SectionTypeUpdate,
    db: Session = Depends(get_db)
):
    """更新章节类型"""
    db_section_type = db.query(SectionType).filter(SectionType.id == type_id).first()
    if not db_section_type:
        raise HTTPException(status_code=404, detail="章节类型不存在")
    
    for key, value in section_type.dict(exclude_unset=True).items():
        setattr(db_section_type, key, value)
    
    db.commit()
    db.refresh(db_section_type)
    return db_section_type

# 章节数据映射管理
@router.get("/{section_id}/mappings", response_model=List[SectionDataMappingResponse])
async def get_section_mappings(
    section_id: int,
    db: Session = Depends(get_db)
):
    """获取章节的数据映射"""
    mappings = db.query(SectionDataMapping).filter(
        SectionDataMapping.section_id == section_id
    ).order_by(SectionDataMapping.display_order).all()
    return mappings

@router.post("/{section_id}/mappings", response_model=SectionDataMappingResponse)
async def create_section_mapping(
    section_id: int,
    mapping: SectionDataMappingCreate,
    db: Session = Depends(get_db)
):
    """为章节创建数据映射"""
    # 验证章节是否存在
    section = db.query(ProjectSection).filter(ProjectSection.id == section_id).first()
    if not section:
        raise HTTPException(status_code=404, detail="章节不存在")
    
    # 验证数据是否存在
    if mapping.data_type == "award":
        data_exists = db.query(Award).filter(Award.id == mapping.data_id).first()
    elif mapping.data_type == "performance":
        data_exists = db.query(Performance).filter(Performance.id == mapping.data_id).first()
    else:
        raise HTTPException(status_code=400, detail="不支持的数据类型")
    
    if not data_exists:
        raise HTTPException(status_code=404, detail="指定的数据不存在")
    
    db_mapping = SectionDataMapping(
        section_id=section_id,
        **mapping.dict()
    )
    db.add(db_mapping)
    db.commit()
    db.refresh(db_mapping)
    return db_mapping

@router.put("/mappings/{mapping_id}", response_model=SectionDataMappingResponse)
async def update_section_mapping(
    mapping_id: int,
    mapping: SectionDataMappingUpdate,
    db: Session = Depends(get_db)
):
    """更新章节数据映射"""
    db_mapping = db.query(SectionDataMapping).filter(
        SectionDataMapping.id == mapping_id
    ).first()
    if not db_mapping:
        raise HTTPException(status_code=404, detail="数据映射不存在")
    
    for key, value in mapping.dict(exclude_unset=True).items():
        setattr(db_mapping, key, value)
    
    db.commit()
    db.refresh(db_mapping)
    return db_mapping

@router.delete("/mappings/{mapping_id}")
async def delete_section_mapping(
    mapping_id: int,
    db: Session = Depends(get_db)
):
    """删除章节数据映射"""
    db_mapping = db.query(SectionDataMapping).filter(
        SectionDataMapping.id == mapping_id
    ).first()
    if not db_mapping:
        raise HTTPException(status_code=404, detail="数据映射不存在")
    
    db.delete(db_mapping)
    db.commit()
    return {"message": "数据映射已删除"}

# 智能推荐系统
@router.post("/recommendations", response_model=SectionRecommendationResponse)
async def get_section_recommendations(
    request: SectionRecommendationRequest,
    db: Session = Depends(get_db)
):
    """获取章节内容推荐"""
    recommendations = {
        "awards": [],
        "performances": [],
        "similar_sections": []
    }
    
    # 基于章节标题和描述推荐奖项
    if request.section_title and "荣誉" in request.section_title or "奖项" in request.section_title:
        awards = db.query(Award).filter(
            and_(
                Award.is_verified == True,
                Award.year >= request.search_year - 2 if request.search_year else 2020
            )
        ).order_by(Award.year.desc()).limit(10).all()
        recommendations["awards"] = awards
    
    # 基于业务领域推荐业绩
    if request.business_field:
        performances = db.query(Performance).filter(
            and_(
                Performance.business_field.contains(request.business_field),
                Performance.year >= request.search_year - 2 if request.search_year else 2020
            )
        ).order_by(Performance.year.desc()).limit(10).all()
        recommendations["performances"] = performances
    
    # 基于相似度推荐相似章节
    if request.project_id:
        similar_sections = db.query(ProjectSection).filter(
            and_(
                ProjectSection.project_id != request.project_id,
                ProjectSection.title.contains(request.section_title) if request.section_title else True
            )
        ).limit(5).all()
        recommendations["similar_sections"] = similar_sections
    
    return recommendations

# 批量操作
@router.post("/{section_id}/batch-mapping")
async def batch_mapping_section(
    section_id: int,
    mappings: List[SectionDataMappingCreate],
    db: Session = Depends(get_db)
):
    """批量创建章节数据映射"""
    # 验证章节是否存在
    section = db.query(ProjectSection).filter(ProjectSection.id == section_id).first()
    if not section:
        raise HTTPException(status_code=404, detail="章节不存在")
    
    created_mappings = []
    for mapping_data in mappings:
        # 验证数据是否存在
        if mapping_data.data_type == "award":
            data_exists = db.query(Award).filter(Award.id == mapping_data.data_id).first()
        elif mapping_data.data_type == "performance":
            data_exists = db.query(Performance).filter(Performance.id == mapping_data.data_id).first()
        else:
            continue
        
        if data_exists:
            db_mapping = SectionDataMapping(
                section_id=section_id,
                **mapping_data.dict()
            )
            db.add(db_mapping)
            created_mappings.append(db_mapping)
    
    db.commit()
    return {"message": f"成功创建 {len(created_mappings)} 个数据映射"}

# 章节内容生成
@router.get("/{section_id}/content")
async def generate_section_content(
    section_id: int,
    include_files: bool = Query(True, description="是否包含文件信息"),
    db: Session = Depends(get_db)
):
    """生成章节内容"""
    section = db.query(ProjectSection).filter(ProjectSection.id == section_id).first()
    if not section:
        raise HTTPException(status_code=404, detail="章节不存在")
    
    # 获取章节的数据映射
    mappings = db.query(SectionDataMapping).filter(
        SectionDataMapping.section_id == section_id,
        SectionDataMapping.is_visible == True
    ).order_by(SectionDataMapping.display_order).all()
    
    content = {
        "section": {
            "id": section.id,
            "title": section.title,
            "description": section.description
        },
        "mappings": []
    }
    
    for mapping in mappings:
        mapping_data = {
            "id": mapping.id,
            "data_type": mapping.data_type,
            "data_id": mapping.data_id,
            "display_order": mapping.display_order,
            "custom_title": mapping.custom_title,
            "custom_description": mapping.custom_description,
            "data": None
        }
        
        # 获取具体数据
        if mapping.data_type == "award":
            award = db.query(Award).filter(Award.id == mapping.data_id).first()
            if award:
                mapping_data["data"] = {
                    "title": award.title,
                    "brand": award.brand,
                    "year": award.year,
                    "business_type": award.business_type,
                    "description": award.description,
                    "files": [{"file_name": f.file_name, "file_path": f.file_path} for f in award.files] if include_files else []
                }
        elif mapping.data_type == "performance":
            performance = db.query(Performance).filter(Performance.id == mapping.data_id).first()
            if performance:
                mapping_data["data"] = {
                    "client_name": performance.client_name,
                    "project_name": performance.project_name,
                    "project_type": performance.project_type,
                    "business_field": performance.business_field,
                    "year": performance.year,
                    "contract_amount": performance.contract_amount,
                    "description": performance.description,
                    "files": [{"file_name": f.file_name, "file_path": f.file_path} for f in performance.files] if include_files else []
                }
        
        content["mappings"].append(mapping_data)
    
    return content

# 数据相似度分析
@router.get("/similarity-analysis")
async def analyze_data_similarity(
    data_type: str = Query(..., description="数据类型: award, performance"),
    data_id: int = Query(..., description="数据ID"),
    threshold: float = Query(0.7, description="相似度阈值"),
    db: Session = Depends(get_db)
):
    """分析数据相似度"""
    similarities = db.query(DataSimilarity).filter(
        and_(
            or_(
                and_(DataSimilarity.data_type_1 == data_type, DataSimilarity.data_id_1 == data_id),
                and_(DataSimilarity.data_type_2 == data_type, DataSimilarity.data_id_2 == data_id)
            ),
            DataSimilarity.similarity_score >= threshold
        )
    ).order_by(DataSimilarity.similarity_score.desc()).limit(10).all()
    
    return {
        "data_type": data_type,
        "data_id": data_id,
        "similarities": similarities
    } 