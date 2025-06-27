from fastapi import APIRouter, Depends, HTTPException, Query, Form, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc, func
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import os
import logging

from database import get_db
from models import LawyerCertificate, LawyerCertificateFile, ManagedFile

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/lawyer-certificates", tags=["律师证管理"])

@router.get("/list")
async def list_lawyer_certificates(
    search: Optional[str] = Query(None, description="搜索关键词（律师姓名、执业证号、事务所）"),
    law_firm: Optional[str] = Query(None, description="律师事务所名称"),
    position: Optional[str] = Query(None, description="职位筛选"),
    position_tags: Optional[str] = Query(None, description="职位标签筛选（逗号分隔）"),
    business_field_tags: Optional[str] = Query(None, description="业务领域标签筛选（逗号分隔）"),
    is_verified: Optional[bool] = Query(None, description="验证状态筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    sort_by: str = Query("created_at", description="排序字段"),
    sort_order: str = Query("desc", description="排序方向（asc/desc）"),
    db: Session = Depends(get_db)
):
    """获取律师证列表"""
    try:
        # 构建查询
        query = db.query(LawyerCertificate)
        
        # 搜索过滤
        if search:
            search_filter = or_(
                LawyerCertificate.lawyer_name.ilike(f"%{search}%"),
                LawyerCertificate.certificate_number.ilike(f"%{search}%"),
                LawyerCertificate.law_firm.ilike(f"%{search}%"),
                LawyerCertificate.issuing_authority.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)
        
        # 律师事务所过滤
        if law_firm:
            query = query.filter(LawyerCertificate.law_firm.ilike(f"%{law_firm}%"))
        
        # 职位过滤
        if position:
            query = query.filter(LawyerCertificate.position == position)
        
        # 职位标签过滤
        if position_tags:
            tag_list = [tag.strip() for tag in position_tags.split(",")]
            for tag in tag_list:
                query = query.filter(LawyerCertificate.position_tags.contains([tag]))
        
        # 业务领域标签过滤
        if business_field_tags:
            tag_list = [tag.strip() for tag in business_field_tags.split(",")]
            for tag in tag_list:
                query = query.filter(LawyerCertificate.business_field_tags.contains([tag]))
        
        # 验证状态过滤
        if is_verified is not None:
            query = query.filter(LawyerCertificate.is_verified == is_verified)
        
        # 排序
        sort_column = getattr(LawyerCertificate, sort_by, LawyerCertificate.created_at)
        if sort_order.lower() == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))
        
        # 分页
        total = query.count()
        offset = (page - 1) * page_size
        certificates = query.offset(offset).limit(page_size).all()
        
        # 格式化结果
        result_certs = []
        for cert in certificates:
            cert_info = {
                "id": cert.id,
                "lawyer_name": cert.lawyer_name,
                "certificate_number": cert.certificate_number,
                "law_firm": cert.law_firm,
                "issuing_authority": cert.issuing_authority,
                "age": cert.age,
                "id_number": cert.id_number,
                "issue_date": cert.issue_date.isoformat() if cert.issue_date else None,
                "position": cert.position,
                "position_tags": cert.position_tags or [],
                "business_field_tags": cert.business_field_tags or [],
                "custom_tags": cert.custom_tags or [],
                "confidence_score": cert.confidence_score,
                "is_verified": cert.is_verified,
                "is_manual_input": cert.is_manual_input,
                "verification_notes": cert.verification_notes,
                "created_at": cert.created_at.isoformat(),
                "updated_at": cert.updated_at.isoformat(),
                "files_count": len(cert.files) if cert.files else 0
            }
            result_certs.append(cert_info)
        
        return {
            "success": True,
            "certificates": result_certs,
            "pagination": {
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size
            }
        }
        
    except Exception as e:
        logger.error(f"获取律师证列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取列表失败: {str(e)}")

@router.get("/stats")
async def get_lawyer_certificate_stats(db: Session = Depends(get_db)):
    """获取律师证统计信息"""
    try:
        # 基础统计
        total_certificates = db.query(LawyerCertificate).count()
        verified_certificates = db.query(LawyerCertificate).filter(LawyerCertificate.is_verified == True).count()
        manual_certificates = db.query(LawyerCertificate).filter(LawyerCertificate.is_manual_input == True).count()
        
        # 职位统计
        position_stats = db.query(
            LawyerCertificate.position,
            func.count(LawyerCertificate.id).label('count')
        ).group_by(LawyerCertificate.position).all()
        
        # 律师事务所统计（Top 10）
        law_firm_stats = db.query(
            LawyerCertificate.law_firm,
            func.count(LawyerCertificate.id).label('count')
        ).group_by(LawyerCertificate.law_firm).order_by(desc(func.count(LawyerCertificate.id))).limit(10).all()
        
        return {
            "success": True,
            "stats": {
                "total_certificates": total_certificates,
                "verified_certificates": verified_certificates,
                "manual_certificates": manual_certificates,
                "verification_rate": round(verified_certificates / total_certificates * 100, 2) if total_certificates > 0 else 0,
                "position_distribution": [
                    {"position": stat.position or "未知", "count": stat.count}
                    for stat in position_stats
                ],
                "top_law_firms": [
                    {"law_firm": stat.law_firm, "count": stat.count}
                    for stat in law_firm_stats
                ]
            }
        }
        
    except Exception as e:
        logger.error(f"获取律师证统计失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取统计失败: {str(e)}")

@router.get("/tags/suggestions")
async def get_tag_suggestions():
    """获取标签建议"""
    try:
        from ai_service import ai_service
        
        return {
            "success": True,
            "tag_suggestions": {
                "position_tags": ["合伙人", "律师", "高级律师", "资深律师", "首席律师"],
                "business_field_tags": ai_service.business_fields,
                "common_custom_tags": ["资深", "专家", "顾问", "特殊资质", "外语能力"]
            }
        }
        
    except Exception as e:
        logger.error(f"获取标签建议失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取建议失败: {str(e)}")

@router.get("/{cert_id}")
async def get_lawyer_certificate(cert_id: int, db: Session = Depends(get_db)):
    """获取律师证详细信息"""
    try:
        cert = db.query(LawyerCertificate).filter(LawyerCertificate.id == cert_id).first()
        if not cert:
            raise HTTPException(status_code=404, detail="律师证不存在")
        
        # 获取关联文件
        files_info = []
        for file in cert.files:
            files_info.append({
                "id": file.id,
                "file_path": file.file_path,
                "file_type": file.file_type,
                "file_name": file.file_name,
                "file_size": file.file_size,
                "page_number": file.page_number,
                "created_at": file.created_at.isoformat()
            })
        
        return {
            "success": True,
            "certificate": {
                "id": cert.id,
                "lawyer_name": cert.lawyer_name,
                "certificate_number": cert.certificate_number,
                "law_firm": cert.law_firm,
                "issuing_authority": cert.issuing_authority,
                "age": cert.age,
                "id_number": cert.id_number,
                "issue_date": cert.issue_date.isoformat() if cert.issue_date else None,
                "position": cert.position,
                "position_tags": cert.position_tags or [],
                "business_field_tags": cert.business_field_tags or [],
                "custom_tags": cert.custom_tags or [],
                "source_document": cert.source_document,
                "ai_analysis": cert.ai_analysis,
                "confidence_score": cert.confidence_score,
                "extracted_text": cert.extracted_text,
                "is_verified": cert.is_verified,
                "is_manual_input": cert.is_manual_input,
                "verification_notes": cert.verification_notes,
                "created_at": cert.created_at.isoformat(),
                "updated_at": cert.updated_at.isoformat(),
                "files": files_info
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取律师证详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取详情失败: {str(e)}")

@router.post("/create")
async def create_lawyer_certificate(
    lawyer_name: str = Form(...),
    certificate_number: str = Form(...),
    law_firm: str = Form(...),
    issuing_authority: Optional[str] = Form(None),
    age: Optional[int] = Form(None),
    id_number: Optional[str] = Form(None),
    issue_date: Optional[str] = Form(None),
    position: Optional[str] = Form("律师"),
    position_tags: Optional[str] = Form(None),  # JSON字符串
    business_field_tags: Optional[str] = Form(None),  # JSON字符串
    custom_tags: Optional[str] = Form(None),  # JSON字符串
    verification_notes: Optional[str] = Form(None),
    files: List[UploadFile] = File(default=[]),
    db: Session = Depends(get_db)
):
    """手动创建律师证记录"""
    try:
        # 检查证书号是否已存在
        existing = db.query(LawyerCertificate).filter(
            LawyerCertificate.certificate_number == certificate_number
        ).first()
        if existing:
            raise HTTPException(status_code=409, detail="执业证号已存在")
        
        # 解析标签
        position_tags_list = []
        business_field_tags_list = []
        custom_tags_list = []
        
        if position_tags:
            try:
                position_tags_list = json.loads(position_tags)
            except:
                position_tags_list = [tag.strip() for tag in position_tags.split(",") if tag.strip()]
        
        if business_field_tags:
            try:
                business_field_tags_list = json.loads(business_field_tags)
            except:
                business_field_tags_list = [tag.strip() for tag in business_field_tags.split(",") if tag.strip()]
        
        if custom_tags:
            try:
                custom_tags_list = json.loads(custom_tags)
            except:
                custom_tags_list = [tag.strip() for tag in custom_tags.split(",") if tag.strip()]
        
        # 解析日期
        issue_date_obj = None
        if issue_date:
            try:
                issue_date_obj = datetime.fromisoformat(issue_date.replace('Z', '+00:00'))
            except:
                pass
        
        # 创建律师证记录
        cert = LawyerCertificate(
            lawyer_name=lawyer_name,
            certificate_number=certificate_number,
            law_firm=law_firm,
            issuing_authority=issuing_authority,
            age=age,
            id_number=id_number,
            issue_date=issue_date_obj,
            position=position,
            position_tags=position_tags_list,
            business_field_tags=business_field_tags_list,
            custom_tags=custom_tags_list,
            verification_notes=verification_notes,
            is_verified=True,  # 手动创建默认已验证
            is_manual_input=True
        )
        
        db.add(cert)
        db.flush()  # 获取ID
        
        # 处理上传的文件
        uploaded_files = []
        if files:
            try:
                from file_management_api import PERMANENT_FILES_PATH
            except ImportError:
                PERMANENT_FILES_PATH = "/app/uploads"
                os.makedirs(PERMANENT_FILES_PATH, exist_ok=True)
            
            for file in files:
                if file.filename:
                    # 保存文件
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    file_ext = os.path.splitext(file.filename)[1]
                    storage_filename = f"lawyer_cert_{cert.id}_{timestamp}{file_ext}"
                    storage_path = os.path.join(PERMANENT_FILES_PATH, storage_filename)
                    
                    content = await file.read()
                    with open(storage_path, "wb") as f:
                        f.write(content)
                    
                    # 创建文件记录
                    cert_file = LawyerCertificateFile(
                        certificate_id=cert.id,
                        file_path=storage_path,
                        file_type="manual_upload",
                        file_name=file.filename,
                        file_size=len(content)
                    )
                    
                    db.add(cert_file)
                    uploaded_files.append({
                        "filename": file.filename,
                        "size": len(content)
                    })
        
        db.commit()
        
        logger.info(f"手动创建律师证成功: {lawyer_name} ({certificate_number})")
        
        return {
            "success": True,
            "message": "律师证创建成功",
            "certificate_id": cert.id,
            "uploaded_files": uploaded_files
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建律师证失败: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建失败: {str(e)}")

@router.put("/{cert_id}")
async def update_lawyer_certificate(
    cert_id: int,
    lawyer_name: str = Form(...),
    certificate_number: str = Form(...),
    law_firm: str = Form(...),
    issuing_authority: Optional[str] = Form(None),
    age: Optional[int] = Form(None),
    id_number: Optional[str] = Form(None),
    issue_date: Optional[str] = Form(None),
    position: Optional[str] = Form("律师"),
    position_tags: Optional[str] = Form(None),
    business_field_tags: Optional[str] = Form(None),
    custom_tags: Optional[str] = Form(None),
    verification_notes: Optional[str] = Form(None),
    is_verified: Optional[bool] = Form(None),
    db: Session = Depends(get_db)
):
    """更新律师证记录"""
    try:
        cert = db.query(LawyerCertificate).filter(LawyerCertificate.id == cert_id).first()
        if not cert:
            raise HTTPException(status_code=404, detail="律师证不存在")
        
        # 检查证书号是否与其他记录重复
        existing = db.query(LawyerCertificate).filter(
            LawyerCertificate.certificate_number == certificate_number,
            LawyerCertificate.id != cert_id
        ).first()
        if existing:
            raise HTTPException(status_code=409, detail="执业证号已存在")
        
        # 解析标签
        position_tags_list = []
        business_field_tags_list = []
        custom_tags_list = []
        
        if position_tags:
            try:
                position_tags_list = json.loads(position_tags)
            except:
                position_tags_list = [tag.strip() for tag in position_tags.split(",") if tag.strip()]
        
        if business_field_tags:
            try:
                business_field_tags_list = json.loads(business_field_tags)
            except:
                business_field_tags_list = [tag.strip() for tag in business_field_tags.split(",") if tag.strip()]
        
        if custom_tags:
            try:
                custom_tags_list = json.loads(custom_tags)
            except:
                custom_tags_list = [tag.strip() for tag in custom_tags.split(",") if tag.strip()]
        
        # 解析日期
        issue_date_obj = None
        if issue_date:
            try:
                issue_date_obj = datetime.fromisoformat(issue_date.replace('Z', '+00:00'))
            except:
                pass
        
        # 更新字段
        cert.lawyer_name = lawyer_name
        cert.certificate_number = certificate_number
        cert.law_firm = law_firm
        cert.issuing_authority = issuing_authority
        cert.age = age
        cert.id_number = id_number
        cert.issue_date = issue_date_obj
        cert.position = position
        cert.position_tags = position_tags_list
        cert.business_field_tags = business_field_tags_list
        cert.custom_tags = custom_tags_list
        cert.verification_notes = verification_notes
        if is_verified is not None:
            cert.is_verified = is_verified
        
        db.commit()
        
        logger.info(f"更新律师证成功: {lawyer_name} ({certificate_number})")
        
        return {
            "success": True,
            "message": "律师证更新成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新律师证失败: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")

@router.delete("/{cert_id}")
async def delete_lawyer_certificate(cert_id: int, db: Session = Depends(get_db)):
    """删除律师证记录"""
    try:
        cert = db.query(LawyerCertificate).filter(LawyerCertificate.id == cert_id).first()
        if not cert:
            raise HTTPException(status_code=404, detail="律师证不存在")
        
        # 删除关联的文件记录和实际文件
        for file in cert.files:
            try:
                if os.path.exists(file.file_path):
                    os.remove(file.file_path)
            except Exception as e:
                logger.warning(f"删除文件失败: {file.file_path}, 错误: {str(e)}")
            
            db.delete(file)
        
        # 删除律师证记录
        lawyer_name = cert.lawyer_name
        certificate_number = cert.certificate_number
        db.delete(cert)
        db.commit()
        
        logger.info(f"删除律师证成功: {lawyer_name} ({certificate_number})")
        
        return {
            "success": True,
            "message": "律师证删除成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除律师证失败: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")

def setup_router(app):
    """设置路由"""
    app.include_router(router) 