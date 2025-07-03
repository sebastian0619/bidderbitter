from fastapi import APIRouter, Depends, HTTPException, Query, Form, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc, func
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import os
import logging

from database import get_db, Base
from models import LawyerCertificate, LawyerCertificateFile, ManagedFile, SystemSettings, AITask
from schemas import LawyerCertificateResponse, LawyerCertificateCreate, LawyerCertificateUpdate
from ai_service import create_ai_task, update_ai_task

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

@router.post("/create-from-file")
async def create_lawyer_certificate_from_file(
    file: UploadFile = File(...),
    lawyer_name: Optional[str] = Form(None),
    certificate_number: Optional[str] = Form(None), 
    law_firm: Optional[str] = Form(None),
    issuing_authority: Optional[str] = Form(None),
    age: Optional[int] = Form(None),
    id_number: Optional[str] = Form(None),
    issue_date: Optional[str] = Form(None),
    position: Optional[str] = Form(None),
    position_tags: Optional[str] = Form(None),
    business_field_tags: Optional[str] = Form(None),
    custom_tags: Optional[str] = Form(None),
    verification_notes: Optional[str] = Form(None),
    enable_ai_analysis: bool = Form(True),
    enable_vision_analysis: bool = Form(True),
    auto_verify: bool = Form(False),
    skip_duplicates: bool = Form(True),
    db: Session = Depends(get_db)
):
    """从文件创建律师证记录（支持AI分析）"""
    try:
        from ai_service import ai_service
        
        # 保存上传的文件
        try:
            from file_management_api import PERMANENT_FILES_PATH
        except ImportError:
            PERMANENT_FILES_PATH = "/app/uploads"
            os.makedirs(PERMANENT_FILES_PATH, exist_ok=True)
        
        # 检查文件类型
        if not file.filename:
            raise HTTPException(status_code=400, detail="文件名不能为空")
        
        allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx']
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in allowed_extensions:
            raise HTTPException(status_code=400, detail="不支持的文件格式")
        
        # 保存文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        storage_filename = f"lawyer_cert_upload_{timestamp}{file_ext}"
        storage_path = os.path.join(PERMANENT_FILES_PATH, storage_filename)
        
        content = await file.read()
        with open(storage_path, "wb") as f:
            f.write(content)
        
        logger.info(f"文件保存成功: {storage_path}")
        
        # AI分析文件
        ai_result = None
        extracted_info = {}
        confidence_score = 0.0
        
        if enable_ai_analysis and ai_service.enable_ai:
            try:
                logger.info("开始AI分析律师证文件...")
                ai_result = await ai_service.smart_document_analysis(
                    storage_path,
                    enable_vision=enable_vision_analysis,
                    enable_ocr=True
                )
                
                if ai_result and ai_result.get("success"):
                    results = ai_result.get("results", {})
                    classification = results.get("final_classification", {})
                    confidence_score = classification.get("confidence", 0.0)
                    
                    # 提取律师证信息
                    if classification.get("category") == "lawyer_certificate":
                        # 从分类结果中提取结构化信息
                        extracted_info = classification.get("key_entities", {})
                        logger.info(f"AI提取律师证信息: {extracted_info}")
                    else:
                        # 如果AI分类不是律师证，尝试从文本中提取
                        text_content = results.get("text_extraction_result", {}).get("text", "")
                        if text_content:
                            # 检查是否包含律师证关键词
                            lawyer_keywords = ['执业证', '律师执业', '执业律师', '执业证书', '律师证']
                            if any(keyword in text_content for keyword in lawyer_keywords):
                                extracted_info = ai_service._extract_lawyer_entities(text_content)
                                confidence_score = 0.6  # 基于关键词的置信度
                                logger.info(f"基于关键词提取律师证信息: {extracted_info}")
                
                logger.info(f"AI分析完成，置信度: {confidence_score}")
                
            except Exception as e:
                logger.warning(f"AI分析失败，将使用手动信息: {str(e)}")
        
        # 合并手动输入信息和AI提取信息
        final_info = {}
        
        # 优先使用手动输入的信息，如果没有则使用AI提取的信息
        fields_mapping = {
            'lawyer_name': lawyer_name,
            'certificate_number': certificate_number,
            'law_firm': law_firm,
            'issuing_authority': issuing_authority,
            'age': age,
            'id_number': id_number,
            'position': position
        }
        
        for field, manual_value in fields_mapping.items():
            if manual_value:
                final_info[field] = manual_value
            elif field in extracted_info:
                final_info[field] = extracted_info[field]
        
        # 检查必填字段
        if not final_info.get('lawyer_name'):
            raise HTTPException(status_code=400, detail="律师姓名不能为空（手动输入或AI未能识别）")
        
        if not final_info.get('certificate_number'):
            raise HTTPException(status_code=400, detail="执业证号不能为空（手动输入或AI未能识别）")
        
        # 检查重复
        if skip_duplicates:
            existing = db.query(LawyerCertificate).filter(
                LawyerCertificate.certificate_number == final_info['certificate_number']
            ).first()
            if existing:
                return {
                    "success": False,
                    "skipped": True,
                    "message": f"执业证号 {final_info['certificate_number']} 已存在，已跳过"
                }
        
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
        issue_date_to_use = issue_date or extracted_info.get('issue_date')
        if issue_date_to_use:
            try:
                issue_date_obj = datetime.fromisoformat(str(issue_date_to_use).replace('Z', '+00:00'))
            except:
                pass
        
        # 决定是否自动验证
        is_verified = False
        if auto_verify and confidence_score >= 0.8:  # 高置信度自动验证
            is_verified = True
        
        # 创建律师证记录
        cert = LawyerCertificate(
            lawyer_name=final_info['lawyer_name'],
            certificate_number=final_info['certificate_number'],
            law_firm=final_info.get('law_firm', ''),
            issuing_authority=final_info.get('issuing_authority'),
            age=final_info.get('age'),
            id_number=final_info.get('id_number'),
            issue_date=issue_date_obj,
            position=final_info.get('position', '律师'),
            position_tags=position_tags_list,
            business_field_tags=business_field_tags_list,
            custom_tags=custom_tags_list,
            source_document=file.filename,
            ai_analysis=ai_result,
            confidence_score=confidence_score,
            extracted_text=ai_result.get('text_extraction_result', {}).get('text', '') if ai_result else '',
            verification_notes=verification_notes,
            is_verified=is_verified,
            is_manual_input=False
        )
        
        db.add(cert)
        db.flush()  # 获取ID
        
        # 创建AI分析任务
        task_id = None
        if enable_ai_analysis:
            task_id = create_ai_task(db, cert.id, "lawyer_certificate")
            logger.info(f"📋 律师证AI任务已创建: 任务ID={task_id}, 律师证ID={cert.id}")
        
        # 创建文件记录
        cert_file = LawyerCertificateFile(
            certificate_id=cert.id,
            file_path=storage_path,
            file_type="uploaded_document",
            file_name=file.filename,
            file_size=len(content)
        )
        
        db.add(cert_file)
        db.commit()
        
        # 更新AI任务状态为成功（如果AI分析成功）
        if task_id and ai_result and ai_result.get("success"):
            update_ai_task(db, task_id, "success", result={
                "analysis_result": ai_result,
                "extracted_info": extracted_info,
                "confidence_score": confidence_score,
                "final_info": final_info
            })
        elif task_id:
            # AI分析失败或未启用，标记任务完成但无结果
            update_ai_task(db, task_id, "completed", result={
                "extracted_info": extracted_info,
                "confidence_score": confidence_score,
                "final_info": final_info
            })
        
        logger.info(f"从文件创建律师证成功: {final_info['lawyer_name']} ({final_info['certificate_number']})")
        
        return {
            "success": True,
            "message": f"律师证创建成功",
            "certificate": {
                "id": cert.id,
                "lawyer_name": cert.lawyer_name,
                "certificate_number": cert.certificate_number,
                "law_firm": cert.law_firm,
                "confidence_score": confidence_score,
                "is_verified": is_verified
            },
            "ai_analysis": {
                "confidence": confidence_score,
                "auto_verified": is_verified,
                "extracted_fields": list(extracted_info.keys()) if extracted_info else []
            },
            "task_id": task_id  # 返回任务ID
        }
        
    except HTTPException:
        # 清理上传的文件
        try:
            if 'storage_path' in locals() and os.path.exists(storage_path):
                os.remove(storage_path)
        except:
            pass
        raise
    except Exception as e:
        # 清理上传的文件
        try:
            if 'storage_path' in locals() and os.path.exists(storage_path):
                os.remove(storage_path)
        except:
            pass
        
        logger.error(f"从文件创建律师证失败: {str(e)}")
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

@router.post("/{cert_id}/upload-file")
async def upload_lawyer_certificate_file(
    cert_id: int,
    file: UploadFile = File(...),
    replace_existing: bool = Form(True),  # 是否替换现有文件
    enable_ai_analysis: bool = Form(True),  # 是否启用AI分析
    enable_vision_analysis: bool = Form(True),  # 是否启用视觉分析
    db: Session = Depends(get_db)
):
    """上传律师证文件（支持替换）"""
    try:
        # 检查律师证是否存在
        cert = db.query(LawyerCertificate).filter(LawyerCertificate.id == cert_id).first()
        if not cert:
            raise HTTPException(status_code=404, detail="律师证不存在")
        
        if not file.filename:
            raise HTTPException(status_code=400, detail="文件名不能为空")
        
        # 读取文件内容
        content = await file.read()
        file_size = len(content)
        
        if file_size > 50 * 1024 * 1024:  # 50MB限制
            raise HTTPException(status_code=413, detail="文件大小超过限制(50MB)")
        
        try:
            from file_management_api import PERMANENT_FILES_PATH
        except ImportError:
            PERMANENT_FILES_PATH = "/app/uploads"
            os.makedirs(PERMANENT_FILES_PATH, exist_ok=True)
        
        # 如果是替换模式，删除现有文件
        if replace_existing:
            for existing_file in cert.files:
                try:
                    if os.path.exists(existing_file.file_path):
                        os.remove(existing_file.file_path)
                    db.delete(existing_file)
                except Exception as e:
                    logger.warning(f"删除旧文件失败: {existing_file.file_path}, 错误: {str(e)}")
        
        # 生成新文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_ext = os.path.splitext(file.filename)[1]
        storage_filename = f"lawyer_cert_{cert_id}_{timestamp}{file_ext}"
        storage_path = os.path.join(PERMANENT_FILES_PATH, storage_filename)
        
        # 保存文件
        with open(storage_path, "wb") as f:
            f.write(content)
        
        # 创建文件记录
        cert_file = LawyerCertificateFile(
            certificate_id=cert_id,
            file_path=storage_path,
            file_type="re_upload" if replace_existing else "additional_upload",
            file_name=file.filename,
            file_size=file_size
        )
        
        db.add(cert_file)
        db.flush()  # 获取文件ID
        
        # AI分析结果
        ai_analysis_result = None
        updated_fields = {}
        
        # 如果启用AI分析，进行文档分析
        if enable_ai_analysis:
            try:
                from ai_service import ai_service
                
                # 进行智能文档分析
                if enable_vision_analysis:
                    analysis_result = await ai_service.smart_document_analysis(
                        storage_path, 
                        enable_vision=True,
                        enable_ocr=True
                    )
                else:
                    analysis_result = await ai_service.smart_document_analysis(storage_path)
                
                if analysis_result.get("success"):
                    if enable_vision_analysis:
                        ai_classification = analysis_result["results"]["final_classification"]
                    else:
                        ai_classification = analysis_result.get("classification")
                    
                    if ai_classification and ai_classification.get("category") == "lawyer_certificate":
                        # 提取律师证信息
                        extracted_info = ai_classification.get("key_entities", {})
                        
                        # 更新律师证信息（保留原有信息，只更新AI识别的字段）
                        if extracted_info.get("holder_name") and not cert.lawyer_name:
                            cert.lawyer_name = extracted_info["holder_name"]
                            updated_fields["lawyer_name"] = extracted_info["holder_name"]
                        
                        if extracted_info.get("certificate_number") and not cert.certificate_number:
                            cert.certificate_number = extracted_info["certificate_number"]
                            updated_fields["certificate_number"] = extracted_info["certificate_number"]
                        
                        if extracted_info.get("law_firm") and not cert.law_firm:
                            cert.law_firm = extracted_info["law_firm"]
                            updated_fields["law_firm"] = extracted_info["law_firm"]
                        
                        if extracted_info.get("issuer") and not cert.issuing_authority:
                            cert.issuing_authority = extracted_info["issuer"]
                            updated_fields["issuing_authority"] = extracted_info["issuer"]
                        
                        # 更新AI分析结果
                        cert.ai_analysis = analysis_result
                        cert.confidence_score = ai_classification.get("confidence", 0.0)
                        
                        # 根据AI分析结果提取职位信息
                        description = ai_classification.get("description", "")
                        if "合伙人" in description and not cert.position:
                            cert.position = "合伙人"
                            updated_fields["position"] = "合伙人"
                        
                        ai_analysis_result = ai_classification
                
                logger.info(f"律师证文件AI分析完成: {cert_id}")
                
            except Exception as ai_err:
                logger.warning(f"AI分析失败，但文件上传成功: {ai_err}")
        
        db.commit()
        
        logger.info(f"律师证文件上传成功: {cert.lawyer_name} ({cert.certificate_number})")
        
        return {
            "success": True,
            "message": "文件上传成功",
            "file_info": {
                "id": cert_file.id,
                "filename": file.filename,
                "size": file_size,
                "type": cert_file.file_type
            },
            "ai_analysis": ai_analysis_result,
            "updated_fields": updated_fields,
            "replaced_existing": replace_existing and len(cert.files) > 1  # 实际是否替换了文件
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"上传律师证文件失败: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")

@router.post("/{cert_id}/reanalyze")
async def reanalyze_lawyer_certificate(
    cert_id: int,
    enable_vision_analysis: bool = Form(True),
    enable_ocr: bool = Form(True),
    update_fields: bool = Form(False),  # 是否使用AI结果更新字段
    db: Session = Depends(get_db)
):
    """重新分析律师证文件"""
    try:
        # 检查律师证是否存在
        cert = db.query(LawyerCertificate).filter(LawyerCertificate.id == cert_id).first()
        if not cert:
            raise HTTPException(status_code=404, detail="律师证不存在")
        
        if not cert.files:
            raise HTTPException(status_code=400, detail="该律师证没有关联文件")
        
        # 使用最新的文件进行分析
        latest_file = sorted(cert.files, key=lambda x: x.created_at, reverse=True)[0]
        
        if not os.path.exists(latest_file.file_path):
            raise HTTPException(status_code=404, detail="文件不存在")
        
        # 进行AI分析
        try:
            from ai_service import ai_service
            
            # 进行智能文档分析
            if enable_vision_analysis:
                analysis_result = await ai_service.smart_document_analysis(
                    latest_file.file_path, 
                    enable_vision=True,
                    enable_ocr=enable_ocr
                )
            else:
                analysis_result = await ai_service.smart_document_analysis(latest_file.file_path)
            
            if not analysis_result.get("success"):
                raise HTTPException(status_code=500, detail=f"AI分析失败: {analysis_result.get('error')}")
            
            # 提取分类信息
            if enable_vision_analysis:
                ai_classification = analysis_result["results"]["final_classification"]
            else:
                ai_classification = analysis_result.get("classification")
            
            updated_fields = {}
            
            # 如果启用字段更新，使用AI结果更新律师证信息
            if update_fields and ai_classification:
                extracted_info = ai_classification.get("key_entities", {})
                
                if extracted_info.get("holder_name"):
                    cert.lawyer_name = extracted_info["holder_name"]
                    updated_fields["lawyer_name"] = extracted_info["holder_name"]
                
                if extracted_info.get("certificate_number"):
                    cert.certificate_number = extracted_info["certificate_number"]
                    updated_fields["certificate_number"] = extracted_info["certificate_number"]
                
                if extracted_info.get("law_firm"):
                    cert.law_firm = extracted_info["law_firm"]
                    updated_fields["law_firm"] = extracted_info["law_firm"]
                
                if extracted_info.get("issuer"):
                    cert.issuing_authority = extracted_info["issuer"]
                    updated_fields["issuing_authority"] = extracted_info["issuer"]
                
                # 根据AI分析结果提取职位信息
                description = ai_classification.get("description", "")
                if "合伙人" in description:
                    cert.position = "合伙人"
                    updated_fields["position"] = "合伙人"
            
            # 更新AI分析结果
            cert.ai_analysis = analysis_result
            cert.confidence_score = ai_classification.get("confidence", 0.0) if ai_classification else 0.0
            
            db.commit()
            
            logger.info(f"律师证重新分析完成: {cert_id}")
            
            return {
                "success": True,
                "message": "重新分析完成",
                "analysis_result": analysis_result,
                "classification": ai_classification,
                "updated_fields": updated_fields,
                "confidence_score": cert.confidence_score
            }
            
        except Exception as ai_err:
            logger.error(f"AI分析失败: {str(ai_err)}")
            raise HTTPException(status_code=500, detail=f"AI分析失败: {str(ai_err)}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"重新分析律师证失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"重新分析失败: {str(e)}")

def setup_router(app):
    """设置路由"""
    app.include_router(router) 