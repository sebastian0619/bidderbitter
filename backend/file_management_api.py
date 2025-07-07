#!/usr/bin/env python3
"""文件管理API"""

from fastapi import APIRouter, Depends, File, UploadFile, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, asc, func
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import os
import hashlib
import shutil
import json
import mimetypes
import pytz

from database import get_db
from models import ManagedFile, FileVersion, FileUsage, FileCategory, LawyerCertificate, LawyerCertificateFile, SystemSettings, AITask
from schemas import *
import logging
from ai_service import create_ai_task, update_ai_task

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/files", tags=["file_management"])

# 文件存储路径配置
TEMP_FILES_PATH = "/app/uploads/temp"
PERMANENT_FILES_PATH = "/app/uploads/permanent"
PROCESSED_FILES_PATH = "/app/uploads/processed"

# 确保目录存在
for path in [TEMP_FILES_PATH, PERMANENT_FILES_PATH, PROCESSED_FILES_PATH]:
    os.makedirs(path, exist_ok=True)

# ============ 辅助函数 ============

def calculate_file_hash(file_path: str) -> str:
    """计算文件MD5哈希值"""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def get_file_type_from_mime(mime_type: str) -> str:
    """根据MIME类型确定文件类型"""
    if mime_type.startswith('image/'):
        return 'image'
    elif mime_type == 'application/pdf':
        return 'pdf'
    elif mime_type.startswith('text/'):
        return 'text'
    elif 'word' in mime_type or 'document' in mime_type:
        return 'document'
    elif 'spreadsheet' in mime_type or 'excel' in mime_type:
        return 'spreadsheet'
    elif 'presentation' in mime_type or 'powerpoint' in mime_type:
        return 'presentation'
    else:
        return 'other'

def cleanup_expired_files(db: Session):
    """清理过期的临时文件"""
    try:
        # 清理过期的上传临时文件（30天）
        expired_upload_files = db.query(ManagedFile).filter(
            and_(
                ManagedFile.file_category == "temporary_upload",
                ManagedFile.expires_at < datetime.now(),
                ManagedFile.is_archived == False
            )
        ).all()
        
        # 清理过期的生成文件（180天）
        expired_generated_files = db.query(ManagedFile).filter(
            and_(
                ManagedFile.file_category == "temporary_generated",
                ManagedFile.expires_at < datetime.now(),
                ManagedFile.is_archived == False
            )
        ).all()
        
        expired_files = expired_upload_files + expired_generated_files
        
        for file in expired_files:
            try:
                # 删除物理文件
                if os.path.exists(file.storage_path):
                    os.remove(file.storage_path)
                if file.processed_path and os.path.exists(file.processed_path):
                    os.remove(file.processed_path)
                
                # 标记为已归档
                file.is_archived = True
                file.archived_at = datetime.now()
                
            except Exception as e:
                logger.error(f"清理文件失败 {file.id}: {e}")
        
        db.commit()
        logger.info(f"清理了 {len(expired_files)} 个过期临时文件")
        
    except Exception as e:
        logger.error(f"清理过期文件失败: {e}")
        db.rollback()

# ============ API端点 ============

@router.post("/upload/temporary")
async def upload_temporary_file(
    file: UploadFile = File(...),
    category: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),  # JSON字符串
    expires_hours: int = Form(24),  # 默认24小时过期
    db: Session = Depends(get_db)
):
    """上传临时文件（单文件）"""
    try:
        # 检查文件大小
        content = await file.read()
        file_size = len(content)
        
        if file_size > 100 * 1024 * 1024:  # 100MB限制
            raise HTTPException(status_code=413, detail="文件大小超过限制(100MB)")
        
        # 重置文件指针
        await file.seek(0)
        
        # 计算文件哈希
        file_hash = hashlib.md5(content).hexdigest()
        
        # 检查是否已存在相同文件
        existing_file = db.query(ManagedFile).filter(
            and_(
                ManagedFile.file_hash == file_hash,
                ManagedFile.is_archived == False
            )
        ).first()
        
        if existing_file:
            # 更新访问时间
            existing_file.access_count += 1
            existing_file.last_accessed = datetime.now()
            db.commit()
            
            return {
                "success": True,
                "message": "文件已存在，返回现有文件信息",
                "file_id": existing_file.id,
                "is_duplicate": True
            }
        
        # 生成存储路径
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename_base = os.path.splitext(file.filename)[0]
        file_ext = os.path.splitext(file.filename)[1]
        storage_filename = f"temp_{timestamp}_{file_hash[:8]}{file_ext}"
        storage_path = os.path.join(TEMP_FILES_PATH, storage_filename)
        
        # 保存文件
        with open(storage_path, "wb") as f:
            await file.seek(0)
            shutil.copyfileobj(file.file, f)
        
        # 获取MIME类型
        mime_type, _ = mimetypes.guess_type(file.filename)
        if not mime_type:
            mime_type = "application/octet-stream"
        
        # 解析标签
        tags_list = []
        if tags:
            try:
                tags_list = json.loads(tags)
            except:
                tags_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
        
        # 创建数据库记录
        db_file = ManagedFile(
            original_filename=file.filename,
            display_name=file.filename,
            storage_path=storage_path,
            file_type=get_file_type_from_mime(mime_type),
            mime_type=mime_type,
            file_size=file_size,
            file_hash=file_hash,
            file_category="temporary_upload",  # 上传的临时文件
            category=category,
            tags=tags_list,
            description=description,
            expires_at=datetime.now() + timedelta(days=30),  # 30天过期
            access_count=1,
            last_accessed=datetime.now()
        )
        
        db.add(db_file)
        db.commit()
        db.refresh(db_file)
        
        logger.info(f"临时文件上传成功: {file.filename} -> {storage_path}")
        
        return {
            "success": True,
            "message": "临时文件上传成功",
            "file_id": db_file.id,
            "filename": db_file.original_filename,
            "file_size": db_file.file_size,
            "expires_at": db_file.expires_at.isoformat(),
            "is_duplicate": False
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"上传临时文件失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")

@router.post("/upload/permanent")
async def upload_permanent_file(
    file: UploadFile = File(...),
    display_name: str = Form(...),
    category: str = Form(None),  # 可选，如果不提供将使用AI分类
    description: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),  # JSON字符串
    keywords: Optional[str] = Form(None),
    is_public: bool = Form(True),
    enable_ai_classification: bool = Form(True),  # 是否启用AI分类
    enable_vision_analysis: bool = Form(True),  # 是否启用视觉分析
    db: Session = Depends(get_db)
):
    """上传常驻文件"""
    try:
        # 检查文件大小
        content = await file.read()
        file_size = len(content)
        
        if file_size > 200 * 1024 * 1024:  # 200MB限制
            raise HTTPException(status_code=413, detail="文件大小超过限制(200MB)")
        
        # 计算文件哈希
        file_hash = hashlib.md5(content).hexdigest()
        
        # 检查是否已存在相同文件
        existing_file = db.query(ManagedFile).filter(
            and_(
                ManagedFile.file_hash == file_hash,
                ManagedFile.file_category == "permanent",
                ManagedFile.is_archived == False
            )
        ).first()
        
        if existing_file:
            # 更新访问时间和计数，返回现有文件信息而不是抛出错误
            existing_file.access_count += 1
            existing_file.last_accessed = datetime.now()
            db.commit()
            
            return {
                "success": True,
                "message": "相同文件已存在，返回现有文件信息",
                "file_id": existing_file.id,
                "display_name": existing_file.display_name,
                "file_size": existing_file.file_size,
                "category": existing_file.category,
                "tags": existing_file.tags or [],
                "is_duplicate": True
            }
        
        # 生成存储路径
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_ext = os.path.splitext(file.filename)[1]
        storage_filename = f"perm_{timestamp}_{file_hash[:8]}{file_ext}"
        storage_path = os.path.join(PERMANENT_FILES_PATH, storage_filename)
        
        # 保存文件
        with open(storage_path, "wb") as f:
            f.write(content)
        
        # 获取MIME类型
        mime_type, _ = mimetypes.guess_type(file.filename)
        if not mime_type:
            mime_type = "application/octet-stream"
        
        # 解析标签
        tags_list = []
        if tags:
            try:
                tags_list = json.loads(tags)
            except:
                tags_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
        
        # 确定初始分类（如果用户未指定，使用默认值）
        final_category = category if category else "other"
        final_tags = tags_list.copy()
        
        # 创建数据库记录
        db_file = ManagedFile(
            original_filename=file.filename,
            display_name=display_name,
            storage_path=storage_path,
            file_type=get_file_type_from_mime(mime_type),
            mime_type=mime_type,
            file_size=file_size,
            file_hash=file_hash,
            file_category="permanent",
            category=final_category,
            tags=final_tags,
            description=description,
            keywords=keywords,
            is_public=is_public,
            access_count=0,
            last_accessed=datetime.now()
        )
        
        db.add(db_file)
        db.commit()
        db.refresh(db_file)
        
        # 创建AI分析任务
        task_id = None
        if enable_ai_classification:
            task_id = create_ai_task(db, db_file.id, "permanent_file")
            logger.info(f"📋 常驻文件AI任务已创建: 任务ID={task_id}, 文件ID={db_file.id}")
            
            # 启动异步后台AI分析
            import asyncio
            asyncio.create_task(
                analyze_permanent_file_in_background(
                    db_file.id,
                    enable_vision_analysis,
                    task_id,
                    user_category=category  # 传递用户指定的分类
                )
            )
            logger.info(f"🤖 已启动后台AI分析任务，文件ID={db_file.id}")
        
        logger.info(f"常驻文件上传成功: {display_name} -> {storage_path}")
        
        return {
            "success": True,
            "message": "常驻文件上传成功",
            "file_id": db_file.id,
            "display_name": db_file.display_name,
            "file_size": db_file.file_size,
            "category": final_category,
            "tags": final_tags,
            "ai_analysis": {
                "enabled": enable_ai_classification,
                "status": "background_processing" if enable_ai_classification else "disabled",
                "task_id": task_id
            },
            "task_id": task_id  # 返回任务ID
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"上传常驻文件失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")

@router.post("/upload/temporary/batch")
async def upload_temporary_files_batch(
    files: List[UploadFile] = File(...),
    category: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),  # JSON字符串
    expires_hours: int = Form(24),  # 默认24小时过期
    db: Session = Depends(get_db)
):
    """批量上传临时文件"""
    try:
        uploaded_files = []
        failed_files = []
        
        # 解析标签
        tags_list = []
        if tags:
            try:
                tags_list = json.loads(tags)
            except:
                tags_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
        
        for i, file in enumerate(files):
            try:
                # 检查文件大小
                content = await file.read()
                file_size = len(content)
                
                if file_size > 100 * 1024 * 1024:  # 100MB限制
                    failed_files.append({
                        "filename": file.filename,
                        "error": "文件大小超过限制(100MB)"
                    })
                    continue
                
                # 计算文件哈希
                file_hash = hashlib.md5(content).hexdigest()
                
                # 检查是否已存在相同文件
                existing_file = db.query(ManagedFile).filter(
                    and_(
                        ManagedFile.file_hash == file_hash,
                        ManagedFile.is_archived == False
                    )
                ).first()
                
                if existing_file:
                    # 更新访问时间
                    existing_file.access_count += 1
                    existing_file.last_accessed = datetime.now()
                    uploaded_files.append({
                        "file_id": existing_file.id,
                        "filename": file.filename,
                        "file_size": file_size,
                        "is_duplicate": True,
                        "message": "文件已存在"
                    })
                    continue
                
                # 生成存储路径
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                file_ext = os.path.splitext(file.filename)[1]
                storage_filename = f"temp_{timestamp}_{i}_{file_hash[:8]}{file_ext}"
                storage_path = os.path.join(TEMP_FILES_PATH, storage_filename)
                
                # 保存文件
                with open(storage_path, "wb") as f:
                    f.write(content)
                
                # 获取MIME类型
                mime_type, _ = mimetypes.guess_type(file.filename)
                if not mime_type:
                    mime_type = "application/octet-stream"
                
                # 创建数据库记录
                db_file = ManagedFile(
                    original_filename=file.filename,
                    display_name=file.filename,
                    storage_path=storage_path,
                    file_type=get_file_type_from_mime(mime_type),
                    mime_type=mime_type,
                    file_size=file_size,
                    file_hash=file_hash,
                    file_category="temporary_upload",
                    category=category,
                    tags=tags_list,
                    description=description,
                    expires_at=datetime.now() + timedelta(hours=expires_hours),
                    access_count=1,
                    last_accessed=datetime.now()
                )
                
                db.add(db_file)
                db.flush()  # 获取ID但不提交
                
                uploaded_files.append({
                    "file_id": db_file.id,
                    "filename": file.filename,
                    "file_size": file_size,
                    "is_duplicate": False,
                    "expires_at": db_file.expires_at.isoformat()
                })
                
                logger.info(f"批量临时文件上传成功: {file.filename}")
                
            except Exception as file_err:
                failed_files.append({
                    "filename": file.filename,
                    "error": str(file_err)
                })
                logger.error(f"上传文件失败 {file.filename}: {file_err}")
        
        db.commit()
        
        return {
            "success": True,
            "message": f"批量上传完成: {len(uploaded_files)} 成功, {len(failed_files)} 失败",
            "uploaded_files": uploaded_files,
            "failed_files": failed_files,
            "summary": {
                "total": len(files),
                "success": len(uploaded_files),
                "failed": len(failed_files)
            }
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"批量上传临时文件失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"批量上传失败: {str(e)}")

@router.post("/upload/permanent/batch")
async def upload_permanent_files_batch(
    files: List[UploadFile] = File(...),
    display_names: Optional[str] = Form(None),  # JSON数组，每个文件的显示名称
    category: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),  # JSON字符串
    keywords: Optional[str] = Form(None),
    is_public: bool = Form(True),
    enable_ai_classification: bool = Form(True),
    enable_vision_analysis: bool = Form(True),
    db: Session = Depends(get_db)
):
    """批量上传常驻文件"""
    try:
        uploaded_files = []
        failed_files = []
        ai_tasks = []
        
        # 解析显示名称
        display_names_list = []
        if display_names:
            try:
                display_names_list = json.loads(display_names)
            except:
                display_names_list = []
        
        # 解析标签
        tags_list = []
        if tags:
            try:
                tags_list = json.loads(tags)
            except:
                tags_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
        
        for i, file in enumerate(files):
            try:
                # 检查文件大小
                content = await file.read()
                file_size = len(content)
                
                if file_size > 200 * 1024 * 1024:  # 200MB限制
                    failed_files.append({
                        "filename": file.filename,
                        "error": "文件大小超过限制(200MB)"
                    })
                    continue
                
                # 计算文件哈希
                file_hash = hashlib.md5(content).hexdigest()
                
                # 检查是否已存在相同文件
                existing_file = db.query(ManagedFile).filter(
                    and_(
                        ManagedFile.file_hash == file_hash,
                        ManagedFile.file_category == "permanent",
                        ManagedFile.is_archived == False
                    )
                ).first()
                
                if existing_file:
                    existing_file.access_count += 1
                    existing_file.last_accessed = datetime.now()
                    uploaded_files.append({
                        "file_id": existing_file.id,
                        "filename": file.filename,
                        "display_name": existing_file.display_name,
                        "file_size": file_size,
                        "is_duplicate": True,
                        "message": "文件已存在"
                    })
                    continue
                
                # 确定显示名称
                display_name = display_names_list[i] if i < len(display_names_list) else file.filename
                
                # 生成存储路径
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                file_ext = os.path.splitext(file.filename)[1]
                storage_filename = f"perm_{timestamp}_{i}_{file_hash[:8]}{file_ext}"
                storage_path = os.path.join(PERMANENT_FILES_PATH, storage_filename)
                
                # 保存文件
                with open(storage_path, "wb") as f:
                    f.write(content)
                
                # 获取MIME类型
                mime_type, _ = mimetypes.guess_type(file.filename)
                if not mime_type:
                    mime_type = "application/octet-stream"
                
                # 确定初始分类
                final_category = category if category else "other"
                
                # 创建数据库记录
                db_file = ManagedFile(
                    original_filename=file.filename,
                    display_name=display_name,
                    storage_path=storage_path,
                    file_type=get_file_type_from_mime(mime_type),
                    mime_type=mime_type,
                    file_size=file_size,
                    file_hash=file_hash,
                    file_category="permanent",
                    category=final_category,
                    tags=tags_list.copy(),
                    description=description,
                    keywords=keywords,
                    is_public=is_public,
                    access_count=0,
                    last_accessed=datetime.now()
                )
                
                db.add(db_file)
                db.flush()  # 获取ID但不提交
                
                # 创建AI分析任务
                task_id = None
                if enable_ai_classification:
                    task_id = create_ai_task(db, db_file.id, "permanent_file")
                    ai_tasks.append({
                        "file_id": db_file.id,
                        "task_id": task_id,
                        "filename": file.filename
                    })
                
                uploaded_files.append({
                    "file_id": db_file.id,
                    "filename": file.filename,
                    "display_name": display_name,
                    "file_size": file_size,
                    "category": final_category,
                    "is_duplicate": False,
                    "task_id": task_id
                })
                
                logger.info(f"批量常驻文件上传成功: {display_name}")
                
            except Exception as file_err:
                failed_files.append({
                    "filename": file.filename,
                    "error": str(file_err)
                })
                logger.error(f"上传文件失败 {file.filename}: {file_err}")
        
        db.commit()
        
        # 启动异步AI分析任务
        if enable_ai_classification and ai_tasks:
            import asyncio
            for task in ai_tasks:
                asyncio.create_task(
                    analyze_permanent_file_in_background(
                        task["file_id"],
                        enable_vision_analysis,
                        task["task_id"],
                        user_category=category
                    )
                )
            logger.info(f"🤖 已启动 {len(ai_tasks)} 个后台AI分析任务")
        
        return {
            "success": True,
            "message": f"批量上传完成: {len(uploaded_files)} 成功, {len(failed_files)} 失败",
            "uploaded_files": uploaded_files,
            "failed_files": failed_files,
            "ai_analysis": {
                "enabled": enable_ai_classification,
                "tasks_created": len(ai_tasks),
                "status": "background_processing" if ai_tasks else "disabled"
            },
            "summary": {
                "total": len(files),
                "success": len(uploaded_files),
                "failed": len(failed_files)
            }
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"批量上传常驻文件失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"批量上传失败: {str(e)}")

@router.get("/list")
async def list_files(
    file_category: Optional[str] = None,  # temporary, permanent
    category: Optional[str] = None,
    search: Optional[str] = None,
    tags: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    include_archived: bool = False,
    db: Session = Depends(get_db)
):
    """获取文件列表"""
    try:
        # 清理过期文件
        if file_category in ["temporary_upload", "temporary_generated", "temporary"] or file_category is None:
            cleanup_expired_files(db)
        
        # 构建查询
        query = db.query(ManagedFile)
        
        # 基础过滤
        if not include_archived:
            query = query.filter(ManagedFile.is_archived == False)
        
        if file_category:
            if file_category == "temporary":
                # 查询所有临时文件类型
                query = query.filter(
                    or_(
                        ManagedFile.file_category == "temporary",
                        ManagedFile.file_category == "temporary_upload",
                        ManagedFile.file_category == "temporary_generated"
                    )
                )
            else:
                query = query.filter(ManagedFile.file_category == file_category)
        
        if category:
            query = query.filter(ManagedFile.category == category)
        
        # 搜索
        if search:
            search_filter = or_(
                ManagedFile.display_name.ilike(f"%{search}%"),
                ManagedFile.original_filename.ilike(f"%{search}%"),
                ManagedFile.description.ilike(f"%{search}%"),
                ManagedFile.keywords.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)
        
        # 标签过滤
        if tags:
            tag_list = [tag.strip() for tag in tags.split(",")]
            for tag in tag_list:
                query = query.filter(ManagedFile.tags.contains([tag]))
        
        # 排序
        sort_column = getattr(ManagedFile, sort_by, ManagedFile.created_at)
        if sort_order.lower() == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))
        
        # 分页
        total = query.count()
        offset = (page - 1) * page_size
        files = query.offset(offset).limit(page_size).all()
        
        # 格式化结果
        result_files = []
        for file in files:
            china_tz = pytz.timezone('Asia/Shanghai')
            
            file_info = {
                "id": file.id,
                "display_name": file.display_name,
                "original_filename": file.original_filename,
                "file_type": file.file_type,
                "file_size": file.file_size,
                "file_category": file.file_category,
                "category": file.category,
                "tags": file.tags or [],
                "description": file.description,
                "keywords": file.keywords,
                "is_public": file.is_public,
                "access_count": file.access_count,
                "created_at": file.created_at.replace(tzinfo=pytz.UTC).astimezone(china_tz).strftime('%Y-%m-%d %H:%M:%S'),
                "last_accessed": file.last_accessed.replace(tzinfo=pytz.UTC).astimezone(china_tz).strftime('%Y-%m-%d %H:%M:%S') if file.last_accessed else None,
                "is_archived": file.is_archived
            }
            
            # 临时文件显示过期时间
            if file.file_category in ["temporary_upload", "temporary_generated", "temporary"] and file.expires_at:
                file_info["expires_at"] = file.expires_at.replace(tzinfo=pytz.UTC).astimezone(china_tz).strftime('%Y-%m-%d %H:%M:%S')
                file_info["is_expired"] = file.expires_at < datetime.now()
            
            result_files.append(file_info)
        
        return {
            "success": True,
            "files": result_files,
            "pagination": {
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size
            }
        }
        
    except Exception as e:
        logger.error(f"获取文件列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取文件列表失败: {str(e)}")

# 具体路径路由必须在参数路由之前定义

@router.get("/stats")
async def get_file_stats(db: Session = Depends(get_db)):
    """获取文件统计信息"""
    try:
        # 清理过期文件
        cleanup_expired_files(db)
        
        # 统计信息
        total_files = db.query(ManagedFile).filter(ManagedFile.is_archived == False).count()
        temp_files = db.query(ManagedFile).filter(
            and_(
                or_(
                    ManagedFile.file_category == "temporary",
                    ManagedFile.file_category == "temporary_upload",
                    ManagedFile.file_category == "temporary_generated"
                ),
                ManagedFile.is_archived == False
            )
        ).count()
        permanent_files = db.query(ManagedFile).filter(
            and_(ManagedFile.file_category == "permanent", ManagedFile.is_archived == False)
        ).count()
        
        # 存储大小统计
        total_size = db.query(func.sum(ManagedFile.file_size)).filter(ManagedFile.is_archived == False).scalar() or 0
        temp_size = db.query(func.sum(ManagedFile.file_size)).filter(
            and_(
                or_(
                    ManagedFile.file_category == "temporary",
                    ManagedFile.file_category == "temporary_upload",
                    ManagedFile.file_category == "temporary_generated"
                ),
                ManagedFile.is_archived == False
            )
        ).scalar() or 0
        permanent_size = db.query(func.sum(ManagedFile.file_size)).filter(
            and_(ManagedFile.file_category == "permanent", ManagedFile.is_archived == False)
        ).scalar() or 0
        
        # 文件类型统计
        type_stats = db.query(
            ManagedFile.file_type,
            func.count(ManagedFile.id).label('count'),
            func.sum(ManagedFile.file_size).label('size')
        ).filter(ManagedFile.is_archived == False).group_by(ManagedFile.file_type).all()
        
        return {
            "success": True,
            "stats": {
                "total_files": total_files,
                "temporary_files": temp_files,
                "permanent_files": permanent_files,
                "total_size": total_size,
                "temporary_size": temp_size,
                "permanent_size": permanent_size,
                "file_types": [
                    {
                        "type": stat.file_type,
                        "count": stat.count,
                        "size": stat.size or 0
                    }
                    for stat in type_stats
                ]
            }
        }
        
    except Exception as e:
        logger.error(f"获取统计信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")

@router.get("/categories/list")
async def list_categories(db: Session = Depends(get_db)):
    """获取分类列表"""
    try:
        categories = db.query(FileCategory).filter(FileCategory.is_active == True).order_by(FileCategory.sort_order).all()
        
        return {
            "success": True,
            "categories": [
                {
                    "id": cat.id,
                    "name": cat.name,
                    "display_name": cat.display_name,
                    "description": cat.description,
                    "parent_id": cat.parent_id,
                    "icon": cat.icon,
                    "color": cat.color,
                    "sort_order": cat.sort_order
                }
                for cat in categories
            ]
        }
        
    except Exception as e:
        logger.error(f"获取分类列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取分类列表失败: {str(e)}")

@router.get("/categories/suggestions")
async def get_category_suggestions():
    """获取文档分类建议"""
    try:
        from ai_service import ai_service
        
        return {
            "success": True,
            "categories": [
                {
                    "code": "performance_contract",
                    "name": "业绩合同",
                    "description": "法律服务合同、委托协议等"
                },
                {
                    "code": "award_certificate", 
                    "name": "荣誉奖项",
                    "description": "各种法律行业奖项证书、排名认证等"
                },
                {
                    "code": "qualification_certificate",
                    "name": "资质证照", 
                    "description": "律师事务所执业许可证、营业执照等机构资质证明"
                },
                {
                    "code": "lawyer_certificate",
                    "name": "律师证",
                    "description": "个人律师执业证书，包含律师姓名、执业证号等信息"
                },
                {
                    "code": "financial_data",
                    "name": "财务数据",
                    "description": "审计报告、财务报表、财务分析等财务相关文档"
                },
                {
                    "code": "other",
                    "name": "其他杂项",
                    "description": "不属于以上类别的其他文档"
                }
            ],
            "business_fields": ai_service.business_fields,
            "lawyer_certificate_tags": {
                "position": ["合伙人", "律师"],
                "business_fields": ai_service.business_fields
            }
        }
        
    except Exception as e:
        logger.error(f"获取分类建议失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取建议失败: {str(e)}")

# 参数路由必须在具体路径路由之后

@router.get("/{file_id}")
async def get_file_info(file_id: int, db: Session = Depends(get_db)):
    """获取文件详细信息"""
    try:
        file = db.query(ManagedFile).filter(ManagedFile.id == file_id).first()
        if not file:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        # 更新访问统计
        file.access_count += 1
        file.last_accessed = datetime.now()
        db.commit()
        
        china_tz = pytz.timezone('Asia/Shanghai')
        
        return {
            "success": True,
            "file": {
                "id": file.id,
                "display_name": file.display_name,
                "original_filename": file.original_filename,
                "storage_path": file.storage_path,
                "file_type": file.file_type,
                "mime_type": file.mime_type,
                "file_size": file.file_size,
                "file_hash": file.file_hash,
                "file_category": file.file_category,
                "category": file.category,
                "tags": file.tags or [],
                "description": file.description,
                "keywords": file.keywords,
                "is_public": file.is_public,
                "access_count": file.access_count,
                "created_at": file.created_at.replace(tzinfo=pytz.UTC).astimezone(china_tz).strftime('%Y-%m-%d %H:%M:%S'),
                "last_accessed": file.last_accessed.replace(tzinfo=pytz.UTC).astimezone(china_tz).strftime('%Y-%m-%d %H:%M:%S'),
                "expires_at": file.expires_at.replace(tzinfo=pytz.UTC).astimezone(china_tz).strftime('%Y-%m-%d %H:%M:%S') if file.expires_at else None,
                "is_archived": file.is_archived
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文件信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取文件信息失败: {str(e)}")

@router.get("/{file_id}/download")
async def download_file(file_id: int, db: Session = Depends(get_db)):
    """下载文件"""
    try:
        file = db.query(ManagedFile).filter(ManagedFile.id == file_id).first()
        if not file:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        if not os.path.exists(file.storage_path):
            raise HTTPException(status_code=404, detail="物理文件不存在")
        
        # 更新访问统计
        file.access_count += 1
        file.last_accessed = datetime.now()
        db.commit()
        
        return FileResponse(
            path=file.storage_path,
            filename=file.original_filename,
            media_type=file.mime_type
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"下载文件失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"下载文件失败: {str(e)}")

@router.put("/{file_id}")
async def update_file_info(
    file_id: int,
    display_name: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    keywords: Optional[str] = Form(None),
    is_public: Optional[bool] = Form(None),
    enable_ai_reanalysis: bool = Form(False),  # 是否重新进行AI分析
    db: Session = Depends(get_db)
):
    """更新文件信息"""
    try:
        file = db.query(ManagedFile).filter(ManagedFile.id == file_id).first()
        if not file:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        # 记录更新前的信息
        old_info = {
            "display_name": file.display_name,
            "category": file.category,
            "description": file.description,
            "tags": file.tags,
            "keywords": file.keywords
        }
        
        # AI学习机制：当用户修改分类时，记录学习数据
        if category and category != old_info["category"]:
            try:
                from ai_service import ai_service
                
                # 记录用户的修正行为供AI学习
                learning_data = {
                    "file_path": file.storage_path,
                    "original_classification": old_info["category"],
                    "user_correction": category,
                    "file_type": file.file_type,
                    "file_size": file.file_size,
                    "correction_reason": "user_manual_edit",
                    "timestamp": datetime.now().isoformat()
                }
                
                # 如果是从"律师证"修正为"资质证照"，记录详细原因
                if old_info["category"] == "lawyer_certificate" and category == "qualification_certificate":
                    learning_data["specific_correction"] = "law_firm_license_vs_personal_certificate"
                    learning_data["learning_note"] = "律师事务所执业许可证应归类为资质证照，而非个人律师证"
                
                # 保存学习数据到配置管理器
                ai_service.record_user_correction(learning_data)
                
                logger.info(f"AI学习记录: 用户将 {old_info['category']} 修正为 {category}")
                
            except Exception as learn_err:
                logger.warning(f"AI学习记录失败，但不影响更新: {learn_err}")
        
        # 更新字段
        if display_name is not None:
            file.display_name = display_name
        if category is not None:
            file.category = category
        if description is not None:
            file.description = description
        if keywords is not None:
            file.keywords = keywords
        if is_public is not None:
            file.is_public = is_public
        
        # 更新标签
        if tags is not None:
            try:
                file.tags = json.loads(tags)
            except:
                file.tags = [tag.strip() for tag in tags.split(",") if tag.strip()]
        
        file.updated_at = datetime.now()
        
        # 如果启用AI重新分析
        ai_result = None
        if enable_ai_reanalysis and file.file_category == "permanent":
            try:
                from ai_service import ai_service
                analysis_result = await ai_service.smart_document_analysis(
                    file.storage_path, 
                    enable_vision=True
                )
                if analysis_result.get("success"):
                    ai_result = analysis_result["results"]["final_classification"]
                    
                    # 如果用户没有手动设置分类，使用AI分析结果
                    if category is None and ai_result.get("category"):
                        file.category = ai_result["category"]
                    
                    # 更新AI分析结果到处理结果中
                    if not file.processing_result:
                        file.processing_result = {}
                    file.processing_result["ai_analysis"] = ai_result
                    file.processing_result["last_analysis"] = datetime.now().isoformat()
                    
                    logger.info(f"文件 {file_id} AI重新分析完成: {ai_result.get('category')}")
            except Exception as ai_err:
                logger.warning(f"AI重新分析失败: {ai_err}")
        
        db.commit()
        
        return {
            "success": True, 
            "message": "文件信息更新成功",
            "ai_analysis": ai_result if enable_ai_reanalysis else None,
            "updated_fields": {
                "display_name": file.display_name,
                "category": file.category,
                "description": file.description,
                "tags": file.tags,
                "keywords": file.keywords
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新文件信息失败: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新文件信息失败: {str(e)}")

@router.delete("/{file_id}")
async def delete_file(file_id: int, force: bool = False, db: Session = Depends(get_db)):
    """删除文件"""
    try:
        file = db.query(ManagedFile).filter(ManagedFile.id == file_id).first()
        if not file:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        if force:
            # 物理删除
            try:
                if os.path.exists(file.storage_path):
                    os.remove(file.storage_path)
                if file.processed_path and os.path.exists(file.processed_path):
                    os.remove(file.processed_path)
            except Exception as e:
                logger.warning(f"删除物理文件失败: {e}")
            
            # 删除数据库记录
            db.delete(file)
        else:
            # 软删除（归档）
            file.is_archived = True
            file.archived_at = datetime.now()
        
        db.commit()
        
        return {
            "success": True,
            "message": "文件删除成功" if force else "文件已归档"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除文件失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除文件失败: {str(e)}")

@router.post("/categories")
async def create_category(
    name: str = Form(...),
    display_name: str = Form(...),
    description: Optional[str] = Form(None),
    parent_id: Optional[int] = Form(None),
    icon: Optional[str] = Form(None),
    color: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """创建文件分类"""
    try:
        # 检查分类名是否已存在
        existing = db.query(FileCategory).filter(FileCategory.name == name).first()
        if existing:
            raise HTTPException(status_code=409, detail="分类名称已存在")
        
        category = FileCategory(
            name=name,
            display_name=display_name,
            description=description,
            parent_id=parent_id,
            icon=icon,
            color=color
        )
        
        db.add(category)
        db.commit()
        db.refresh(category)
        
        return {
            "success": True,
            "message": "分类创建成功",
            "category_id": category.id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建分类失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建分类失败: {str(e)}")

# 导出路由器供main.py使用
@router.post("/analyze-document")
async def analyze_document_ai(
    file_id: int,
    enable_vision: bool = True,
    force_reanalyze: bool = False,
    db: Session = Depends(get_db)
):
    """对已上传的文档进行AI分析"""
    try:
        # 获取文件信息
        file_record = db.query(ManagedFile).filter(ManagedFile.id == file_id).first()
        if not file_record:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        if not os.path.exists(file_record.storage_path):
            raise HTTPException(status_code=404, detail="物理文件不存在")
        
        # 进行AI分析
        from ai_service import ai_service
        
        if enable_vision:
            analysis_result = await ai_service.smart_document_analysis(
                file_record.storage_path,
                enable_vision=True
            )
        else:
            analysis_result = await ai_service.smart_document_analysis(file_record.storage_path)
        
        if not analysis_result.get("success"):
            raise HTTPException(status_code=500, detail=f"AI分析失败: {analysis_result.get('error')}")
        
        # 提取分类信息
        if enable_vision:
            classification = analysis_result["results"]["final_classification"]
        else:
            classification = analysis_result.get("classification")
        
        # 提取标签建议
        tag_result = await ai_service.extract_document_tags(
            file_record.storage_path,
            existing_tags=file_record.tags or []
        )
        
        suggested_tags = tag_result.get("suggested_tags", []) if tag_result.get("success") else []
        
        # 处理律师证的特殊逻辑
        lawyer_cert_created = None
        if classification and classification.get("category") == "lawyer_certificate":
            try:
                lawyer_cert_created = await handle_lawyer_certificate_creation(
                    file_record, classification, analysis_result, db
                )
            except Exception as lawyer_err:
                logger.warning(f"创建律师证记录失败: {lawyer_err}")
        
        # 如果需要，更新文件记录
        if force_reanalyze and classification:
            # 修复分类字段访问 - 使用type而不是category
            new_category = classification.get("type", file_record.category)
            if new_category:
                file_record.category = new_category
                logger.info(f"更新文件分类: {file_record.id} -> {new_category}")
            
            if tag_result.get("success"):
                file_record.tags = tag_result.get("all_tags", file_record.tags)
            
            # 更新描述信息
            if classification.get("summary") and not file_record.description:
                file_record.description = classification["summary"]
            
            # 更新处理结果
            if not file_record.processing_result:
                file_record.processing_result = {}
            file_record.processing_result["ai_analysis"] = analysis_result
            file_record.processing_result["classification"] = classification
            
            db.commit()
            logger.info(f"文件记录已更新: 分类={new_category}, 标签={file_record.tags}")
        
        return {
            "success": True,
            "file_id": file_id,
            "analysis_result": analysis_result,
            "classification": classification,
            "suggested_tags": suggested_tags,
            "updated": force_reanalyze,
            "lawyer_certificate_created": lawyer_cert_created
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文档AI分析失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")

@router.post("/batch-analyze")
async def batch_analyze_documents(
    file_ids: List[int],
    enable_vision: bool = True,
    update_records: bool = False,
    db: Session = Depends(get_db)
):
    """批量分析文档"""
    try:
        results = []
        
        for file_id in file_ids:
            try:
                # 分析单个文档
                analysis_result = await analyze_document_ai(
                    file_id=file_id,
                    enable_vision=enable_vision,
                    force_reanalyze=update_records,
                    db=db
                )
                results.append({
                    "file_id": file_id,
                    "success": True,
                    "result": analysis_result
                })
            except Exception as e:
                results.append({
                    "file_id": file_id,
                    "success": False,
                    "error": str(e)
                })
        
        success_count = sum(1 for r in results if r["success"])
        
        return {
            "success": True,
            "total": len(file_ids),
            "success_count": success_count,
            "failed_count": len(file_ids) - success_count,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"批量分析失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"批量分析失败: {str(e)}")

async def handle_lawyer_certificate_creation(file_record, classification, analysis_result, db):
    """处理律师证的创建逻辑"""
    try:
        from models import LawyerCertificate, LawyerCertificateFile
        
        # 提取律师证信息
        lawyer_info = classification.get("lawyer_info", {})
        key_entities = classification.get("key_entities", {})
        
        # 必要字段检查
        lawyer_name = lawyer_info.get("name") or key_entities.get("holder_name")
        certificate_number = lawyer_info.get("certificate_number") or key_entities.get("certificate_number")
        law_firm = lawyer_info.get("law_firm") or classification.get("description", "")
        
        if not lawyer_name or not certificate_number:
            logger.warning("律师证信息不完整，跳过创建")
            return None
        
        # 检查是否已存在
        existing = db.query(LawyerCertificate).filter(
            LawyerCertificate.certificate_number == certificate_number
        ).first()
        
        if existing:
            logger.info(f"律师证已存在: {certificate_number}")
            return {"id": existing.id, "action": "exists"}
        
        # 创建律师证记录
        lawyer_cert = LawyerCertificate(
            lawyer_name=lawyer_name,
            certificate_number=certificate_number,
            law_firm=law_firm,
            issuing_authority=lawyer_info.get("issuing_authority"),
            age=lawyer_info.get("age"),
            id_number=lawyer_info.get("id_number"),
            source_document=file_record.storage_path,
            ai_analysis=analysis_result,
            confidence_score=classification.get("confidence", 0.0),
            extracted_text=analysis_result.get("results", {}).get("text_extraction_result", {}).get("extracted_content", {}).get("text", ""),
            is_verified=False,
            is_manual_input=False
        )
        
        # 处理职位标签
        position = "律师"  # 默认
        if "合伙人" in str(classification.get("description", "")):
            position = "合伙人"
        lawyer_cert.position = position
        lawyer_cert.position_tags = [position]
        
        # 处理业务领域标签
        business_field = classification.get("business_field")
        if business_field:
            lawyer_cert.business_field_tags = [business_field]
        
        db.add(lawyer_cert)
        db.flush()  # 获取ID
        
        # 创建文件关联
        cert_file = LawyerCertificateFile(
            certificate_id=lawyer_cert.id,
            file_path=file_record.storage_path,
            file_type="original",
            file_name=file_record.original_filename,
            file_size=file_record.file_size
        )
        
        db.add(cert_file)
        db.commit()
        
        logger.info(f"律师证创建成功: {lawyer_name} ({certificate_number})")
        
        return {
            "id": lawyer_cert.id,
            "action": "created",
            "lawyer_name": lawyer_name,
            "certificate_number": certificate_number,
            "law_firm": law_firm,
            "position": position
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"创建律师证记录失败: {str(e)}")
        raise e

@router.post("/{file_id}/create-lawyer-certificate")
async def create_lawyer_certificate_from_file(
    file_id: int,
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
    db: Session = Depends(get_db)
):
    """从文件管理创建律师证记录（双向管理）"""
    try:
        # 检查文件是否存在
        file_record = db.query(ManagedFile).filter(ManagedFile.id == file_id).first()
        if not file_record:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        # 检查证书号是否已存在
        from models import LawyerCertificate, LawyerCertificateFile
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
        lawyer_cert = LawyerCertificate(
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
            source_document=file_record.storage_path,
            is_verified=True,  # 手动创建默认已验证
            is_manual_input=True  # 从文件管理手动创建
        )
        
        db.add(lawyer_cert)
        db.flush()  # 获取ID
        
        # 创建文件关联
        cert_file = LawyerCertificateFile(
            certificate_id=lawyer_cert.id,
            file_path=file_record.storage_path,
            file_type="from_file_management",
            file_name=file_record.original_filename,
            file_size=file_record.file_size
        )
        
        db.add(cert_file)
        
        # 更新文件记录的分类
        file_record.category = "lawyer_certificate"
        if not file_record.description:
            file_record.description = f"律师证文档：{lawyer_name}（{certificate_number}）"
        
        db.commit()
        
        logger.info(f"从文件管理创建律师证成功: {lawyer_name} ({certificate_number})")
        
        return {
            "success": True,
            "message": "律师证创建成功",
            "certificate_id": lawyer_cert.id,
            "file_updated": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"从文件管理创建律师证失败: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建失败: {str(e)}")

@router.get("/{file_id}/lawyer-certificate")
async def get_related_lawyer_certificate(file_id: int, db: Session = Depends(get_db)):
    """查看文件关联的律师证信息"""
    try:
        # 检查文件是否存在
        file_record = db.query(ManagedFile).filter(ManagedFile.id == file_id).first()
        if not file_record:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        # 查找关联的律师证
        from models import LawyerCertificate, LawyerCertificateFile
        
        # 通过文件路径查找律师证
        cert_file = db.query(LawyerCertificateFile).filter(
            LawyerCertificateFile.file_path == file_record.storage_path
        ).first()
        
        if not cert_file:
            # 通过源文档查找
            cert = db.query(LawyerCertificate).filter(
                LawyerCertificate.source_document == file_record.storage_path
            ).first()
            
            if not cert:
                return {
                    "success": True,
                    "has_lawyer_certificate": False,
                    "message": "该文件未关联律师证"
                }
        else:
            cert = cert_file.certificate
        
        return {
            "success": True,
            "has_lawyer_certificate": True,
            "lawyer_certificate": {
                "id": cert.id,
                "lawyer_name": cert.lawyer_name,
                "certificate_number": cert.certificate_number,
                "law_firm": cert.law_firm,
                "position": cert.position,
                "is_verified": cert.is_verified,
                "created_at": cert.created_at.isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查看文件关联律师证失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查看失败: {str(e)}")

@router.get("/task/{task_id}/status")
async def get_ai_task_status(task_id: int, db: Session = Depends(get_db)):
    """查询AI任务状态"""
    try:
        task = db.query(AITask).filter(AITask.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        # 获取关联的文件信息
        file_record = None
        if task.file_type == "permanent_file":
            file_record = db.query(ManagedFile).filter(ManagedFile.id == task.file_id).first()
        
        return {
            "success": True,
            "task_id": task.id,
            "status": task.status,
            "file_id": task.file_id,
            "file_type": task.file_type,
            "result": task.result_snapshot,
            "error_message": task.error_message,
            "created_at": task.created_at.isoformat(),
            "updated_at": task.updated_at.isoformat(),
            "file_info": {
                "display_name": file_record.display_name if file_record else None,
                "category": file_record.category if file_record else None,
                "processing_status": file_record.processing_status if file_record else None
            } if file_record else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询AI任务状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")

@router.post("/{file_id}/reanalyze")
async def reanalyze_permanent_file(
    file_id: int,
    enable_vision_analysis: bool = Form(True),
    force_reclassify: bool = Form(True),
    db: Session = Depends(get_db)
):
    """重新分析常驻文件（智能分类 + 专业记录创建）"""
    try:
        # 检查文件是否存在
        file_record = db.query(ManagedFile).filter(ManagedFile.id == file_id).first()
        if not file_record:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        if file_record.file_category != "permanent":
            raise HTTPException(status_code=400, detail="只能重新分析常驻文件")
        
        # 创建新的AI任务
        task_id = create_ai_task(db, file_id, "permanent_file")
        logger.info(f"📋 重新分析任务已创建: 任务ID={task_id}, 文件ID={file_id}")
        
        # 启动异步后台AI分析
        import asyncio
        asyncio.create_task(
            analyze_permanent_file_in_background(
                file_id,
                enable_vision_analysis,
                task_id,
                user_category=None  # 让AI重新智能分类
            )
        )
        logger.info(f"🤖 已启动重新分析任务，文件ID={file_id}")
        
        return {
            "success": True,
            "message": "重新分析任务已启动",
            "task_id": task_id,
            "file_id": file_id,
            "analysis_options": {
                "vision_enabled": enable_vision_analysis,
                "force_reclassify": force_reclassify
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"重新分析文件失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"重新分析失败: {str(e)}")

async def analyze_permanent_file_in_background(file_id: int, enable_vision_analysis: bool, task_id: int = None, user_category: str = None):
    """后台异步分析常驻文件"""
    try:
        from database import get_db
        from ai_service import ai_service
        
        db = next(get_db())
        
        if not ai_service.enable_ai:
            logger.warning("AI服务未启用，跳过后台分析")
            if task_id:
                update_ai_task(db, task_id, "completed", result={
                    "ai_analysis": False,
                    "reason": "AI服务未启用"
                })
            db.close()
            return
        
        logger.info(f"🤖 开始后台AI分析，文件ID={file_id}")
        
        try:
            # 获取文件记录
            file_record = db.query(ManagedFile).filter(ManagedFile.id == file_id).first()
            
            if not file_record or not file_record.storage_path:
                logger.warning(f"⚠️ 文件记录或文件路径不存在: {file_id}")
                if task_id:
                    update_ai_task(db, task_id, "failed", result={
                        "error": "文件记录或文件路径不存在"
                    })
                db.close()
                return
            
            if not os.path.exists(file_record.storage_path):
                logger.warning(f"⚠️ 物理文件不存在: {file_record.storage_path}")
                if task_id:
                    update_ai_task(db, task_id, "failed", result={
                        "error": "物理文件不存在"
                    })
                db.close()
                return
            
            # 更新AI任务状态为正在处理
            if task_id:
                update_ai_task(db, task_id, "processing")
            
            # 更新文件处理状态
            file_record.processing_status = "processing"
            db.commit()
            
            logger.info(f"🔍 开始分析文件: {file_record.display_name}")
            
            # 进行AI智能分析
            if enable_vision_analysis:
                analysis_result = await ai_service.smart_document_analysis(
                    file_record.storage_path, 
                    enable_vision=True,
                    enable_ocr=True
                )
            else:
                analysis_result = await ai_service.smart_document_analysis(
                    file_record.storage_path,
                    enable_ocr=True
                )
            
            if analysis_result.get("success"):
                # 提取分类信息
                if enable_vision_analysis:
                    ai_classification = analysis_result["results"]["final_classification"]
                else:
                    ai_classification = analysis_result.get("classification")
                
                # 更新文件分类（仅当用户未指定分类时）
                if not user_category and ai_classification:
                    suggested_category = ai_classification.get("category", "other")
                    if suggested_category and suggested_category != "other":
                        file_record.category = suggested_category
                        logger.info(f"📋 AI建议分类: {suggested_category}")
                
                # 提取AI建议的标签
                if ai_classification:
                    try:
                        tag_result = await ai_service.extract_document_tags(
                            file_record.storage_path, 
                            existing_tags=file_record.tags or []
                        )
                        if tag_result.get("success"):
                            ai_tags = tag_result.get("suggested_tags", [])
                            if ai_tags:
                                # 合并现有标签和AI建议标签
                                existing_tags = set(file_record.tags or [])
                                new_tags = existing_tags.union(set(ai_tags))
                                file_record.tags = list(new_tags)
                                logger.info(f"🏷️ AI建议标签: {ai_tags}")
                    except Exception as tag_err:
                        logger.warning(f"提取标签失败: {tag_err}")
                
                # 保存AI分析结果到处理结果中
                if not file_record.processing_result:
                    file_record.processing_result = {}
                file_record.processing_result["ai_analysis"] = ai_classification
                file_record.processing_result["analysis_timestamp"] = datetime.now().isoformat()
                file_record.processing_result["vision_enabled"] = enable_vision_analysis
                
                # 智能分类和专业记录创建
                professional_record_created = None
                if ai_classification:
                    try:
                        professional_record_created = await create_professional_record_from_file(
                            db, file_record, ai_classification, analysis_result
                        )
                        if professional_record_created:
                            logger.info(f"🎯 自动创建专业记录成功: {professional_record_created}")
                    except Exception as prof_err:
                        logger.warning(f"自动创建专业记录失败: {prof_err}")
                        professional_record_created = {"error": str(prof_err)}
                
                # 更新处理状态
                file_record.processing_status = "completed"
                file_record.is_processed = True
                
                # 更新AI任务状态为成功
                if task_id:
                    update_ai_task(db, task_id, "success", result={
                        "ai_classification": ai_classification,
                        "category": file_record.category,
                        "tags": file_record.tags,
                        "analysis_enabled": True,
                        "vision_enabled": enable_vision_analysis,
                        "professional_record": professional_record_created
                    })
                
                logger.info(f"✅ 文件AI分析完成: {file_record.display_name}")
                
            else:
                # AI分析失败
                error_msg = analysis_result.get("error", "AI分析失败")
                logger.warning(f"⚠️ AI分析失败: {error_msg}")
                
                file_record.processing_status = "failed"
                if not file_record.processing_result:
                    file_record.processing_result = {}
                file_record.processing_result["error"] = error_msg
                file_record.processing_result["analysis_timestamp"] = datetime.now().isoformat()
                
                if task_id:
                    update_ai_task(db, task_id, "failed", result={
                        "error": error_msg,
                        "analysis_enabled": False
                    })
            
            db.commit()
            
        except Exception as process_err:
            logger.error(f"❌ 后台AI分析异常: {process_err}")
            
            # 更新处理状态
            try:
                file_record = db.query(ManagedFile).filter(ManagedFile.id == file_id).first()
                if file_record:
                    file_record.processing_status = "failed"
                    if not file_record.processing_result:
                        file_record.processing_result = {}
                    file_record.processing_result["error"] = str(process_err)
                    file_record.processing_result["analysis_timestamp"] = datetime.now().isoformat()
                
                if task_id:
                    update_ai_task(db, task_id, "failed", result={
                        "error": str(process_err)
                    })
                
                db.commit()
            except Exception as update_err:
                logger.error(f"更新失败状态出错: {update_err}")
        
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"❌ 后台AI分析失败: {e}")
        import traceback
        logger.error(f"异常详情: {traceback.format_exc()}")

async def create_professional_record_from_file(db, file_record, ai_classification, analysis_result):
    """根据AI分类结果创建对应的专业管理记录"""
    try:
        # 智能分类识别 - 优先使用category字段，然后使用type字段，最后使用document_type字段
        ai_category = ai_classification.get("category", "other")
        ai_type = ai_classification.get("type", "")
        document_type = ai_classification.get("document_type", "")
        
        # 基于AI识别的类型进行智能分类映射
        if ai_category == "other":
            # 优先使用document_type，然后使用type
            if document_type:
                ai_category = classify_document_by_ai_type(document_type, ai_classification)
            elif ai_type:
                ai_category = classify_document_by_ai_type(ai_type, ai_classification)
        
        professional_record = None
        
        logger.info(f"🎯 开始创建专业记录，AI类型: {ai_type}, 最终分类: {ai_category}")
        
        if ai_category == "lawyer_certificate":
            # 律师证分析和创建
            professional_record = await create_lawyer_certificate_from_analysis(
                db, file_record, ai_classification, analysis_result
            )
        elif ai_category == "performance_contract":
            # 业绩合同分析和创建
            professional_record = await create_performance_from_analysis(
                db, file_record, ai_classification, analysis_result
            )
        elif ai_category == "award_certificate":
            # 奖项证书分析和创建
            professional_record = await create_award_from_analysis(
                db, file_record, ai_classification, analysis_result
            )
        elif ai_category == "financial_data":
            # 财务数据分析（暂不创建具体记录，但记录分类）
            logger.info(f"💰 识别为财务数据: {file_record.display_name}")
            professional_record = {
                "type": "financial_data",
                "category": "财务数据",
                "description": "已识别为财务相关文档，暂存为常驻文件",
                "ai_type": ai_type
            }
            # 更新文件分类
            file_record.category = "financial_data"
        else:
            logger.info(f"📋 其他类型文档，AI类型: {ai_type}, 分类: {ai_category}")
            professional_record = {
                "type": "other",
                "category": ai_category,
                "ai_type": ai_type,
                "description": f"AI识别类型: {ai_type}, 分类为: {ai_category}"
            }
        
        return professional_record
        
    except Exception as e:
        logger.error(f"创建专业记录失败: {str(e)}")
        return {"error": str(e)}

def classify_document_by_ai_type(ai_type, ai_classification):
    """根据AI识别的类型进行智能分类映射"""
    try:
        ai_type_lower = ai_type.lower()
        summary = ai_classification.get("summary", "").lower()
        entities = ai_classification.get("entities", {})
        
        # 优先检查AI返回的type字段
        if ai_type and ai_type != "unknown":
            # 基于AI返回的type进行智能映射
            if ai_type in ["报告", "审计报告", "财务报告", "audit_report", "financial_report"]:
                return "financial_data"
            elif ai_type in ["合同", "协议", "contract", "agreement"]:
                return "performance_contract"
            elif ai_type in ["证书", "律师证", "执业证", "certificate", "lawyer_certificate"]:
                return "lawyer_certificate"
            elif ai_type in ["奖项", "奖状", "award", "prize", "honor"]:
                return "award_certificate"
        
        # 基于关键词的备用分类逻辑
        # 财务数据相关（优先级最高）
        if any(keyword in ai_type_lower for keyword in ["报告", "审计", "财务", "会计", "financial", "audit", "report"]):
            return "financial_data"
        
        # 律师证相关
        if any(keyword in ai_type_lower for keyword in ["律师证", "执业证", "lawyer", "certificate"]):
            return "lawyer_certificate"
        
        # 业绩合同相关  
        if any(keyword in ai_type_lower for keyword in ["合同", "协议", "contract", "agreement"]):
            return "performance_contract"
        
        # 奖项证书相关
        if any(keyword in ai_type_lower for keyword in ["奖项", "证书", "award", "prize", "honor"]):
            return "award_certificate"
        
        # 基于摘要内容进一步判断
        if "审计" in summary or "财务" in summary or "会计" in summary:
            return "financial_data"
            
        if "合同" in summary or "协议" in summary:
            return "performance_contract"
            
        if "奖" in summary or "证书" in summary:
            return "award_certificate"
            
        if "律师" in summary or "执业" in summary:
            return "lawyer_certificate"
        
        return "other"
        
    except Exception as e:
        logger.error(f"AI类型分类映射失败: {str(e)}")
        return "other"

async def create_lawyer_certificate_from_analysis(db, file_record, ai_classification, analysis_result):
    """从AI分析结果创建律师证记录"""
    try:
        from models import LawyerCertificate, LawyerCertificateFile
        
        # 提取律师证信息
        lawyer_info = ai_classification.get("lawyer_info", {})
        key_entities = ai_classification.get("key_entities", {})
        
        extracted_info = {
            "lawyer_name": lawyer_info.get("name") or key_entities.get("holder_name"),
            "certificate_number": lawyer_info.get("certificate_number") or key_entities.get("certificate_number"),
            "law_firm": lawyer_info.get("law_firm") or ai_classification.get("description", ""),
            "issuing_authority": lawyer_info.get("issuing_authority") or key_entities.get("issuer"),
            "age": lawyer_info.get("age"),
            "id_number": lawyer_info.get("id_number"),
            "position": "合伙人" if "合伙人" in str(ai_classification.get("description", "")) else "律师"
        }
        
        # 检查必要字段
        if not (extracted_info.get("lawyer_name") and extracted_info.get("certificate_number")):
            logger.warning("律师证信息不完整，跳过创建记录")
            return {"error": "律师证信息不完整"}
        
        # 检查是否已存在
        existing = db.query(LawyerCertificate).filter(
            LawyerCertificate.certificate_number == extracted_info["certificate_number"]
        ).first()
        
        if existing:
            # 关联到现有记录
            cert_file = LawyerCertificateFile(
                certificate_id=existing.id,
                file_path=file_record.storage_path,
                file_type="auto_detected_from_permanent_file",
                file_name=file_record.original_filename,
                file_size=file_record.file_size
            )
            db.add(cert_file)
            
            logger.info(f"👥 律师证已存在，添加文件关联: {existing.lawyer_name}")
            return {
                "type": "lawyer_certificate",
                "action": "linked_to_existing",
                "certificate_id": existing.id,
                "lawyer_name": existing.lawyer_name
            }
        else:
            # 创建新记录
            cert = LawyerCertificate(
                lawyer_name=extracted_info["lawyer_name"],
                certificate_number=extracted_info["certificate_number"],
                law_firm=extracted_info["law_firm"] or "",
                issuing_authority=extracted_info.get("issuing_authority"),
                age=extracted_info.get("age"),
                id_number=extracted_info.get("id_number"),
                position=extracted_info.get("position", "律师"),
                position_tags=[extracted_info.get("position", "律师")],
                source_document=file_record.original_filename,
                ai_analysis=analysis_result,
                confidence_score=ai_classification.get("confidence", 0.0),
                extracted_text=analysis_result.get('text_extraction_result', {}).get('text', ''),
                is_verified=False,
                is_manual_input=False
            )
            
            db.add(cert)
            db.flush()  # 获取ID
            
            # 创建文件关联
            cert_file = LawyerCertificateFile(
                certificate_id=cert.id,
                file_path=file_record.storage_path,
                file_type="auto_detected_from_permanent_file",
                file_name=file_record.original_filename,
                file_size=file_record.file_size
            )
            
            db.add(cert_file)
            
            logger.info(f"✅ 自动创建律师证记录: {cert.lawyer_name} ({cert.certificate_number})")
            return {
                "type": "lawyer_certificate",
                "action": "created_new",
                "certificate_id": cert.id,
                "lawyer_name": cert.lawyer_name,
                "certificate_number": cert.certificate_number
            }
        
    except Exception as e:
        logger.error(f"创建律师证记录失败: {str(e)}")
        return {"error": str(e)}

async def create_performance_from_analysis(db, file_record, ai_classification, analysis_result):
    """从AI分析结果创建业绩记录"""
    try:
        from models import Performance, PerformanceFile
        
        # 提取业绩信息
        performance_info = ai_classification.get("performance_info", {})
        key_entities = ai_classification.get("key_entities", {})
        
        extracted_info = {
            "project_name": performance_info.get("project_name") or key_entities.get("project_name") or file_record.display_name,
            "client_name": performance_info.get("client_name") or key_entities.get("client_name") or "待完善",
            "business_field": performance_info.get("business_field") or ai_classification.get("business_field", "待AI分析"),
            "description": ai_classification.get("description", f"从文件 '{file_record.original_filename}' 自动识别")
        }
        
        # 创建业绩记录
        performance = Performance(
            project_name=extracted_info["project_name"],
            client_name=extracted_info["client_name"],
            project_type="重大个案(非诉)",
            business_field=extracted_info["business_field"],
            year=datetime.now().year,
            is_manual_input=False,
            is_verified=False,
            confidence_score=ai_classification.get("confidence", 0.0),
            description=extracted_info["description"],
            source_document=file_record.storage_path,
            ai_analysis_status="completed",
            extracted_text=analysis_result.get('text_extraction_result', {}).get('text', '')
        )
        
        db.add(performance)
        db.flush()  # 获取ID
        
        # 创建文件关联
        perf_file = PerformanceFile(
            performance_id=performance.id,
            file_path=file_record.storage_path,
            file_type="auto_detected_from_permanent_file",
            file_name=file_record.original_filename,
            file_size=file_record.file_size
        )
        
        db.add(perf_file)
        
        logger.info(f"✅ 自动创建业绩记录: {performance.project_name}")
        return {
            "type": "performance_contract",
            "action": "created_new",
            "performance_id": performance.id,
            "project_name": performance.project_name,
            "client_name": performance.client_name
        }
        
    except Exception as e:
        logger.error(f"创建业绩记录失败: {str(e)}")
        return {"error": str(e)}

async def create_award_from_analysis(db, file_record, ai_classification, analysis_result):
    """从AI分析结果创建奖项记录"""
    try:
        from models import Award
        
        # 提取奖项信息
        award_info = ai_classification.get("award_info", {})
        key_entities = ai_classification.get("key_entities", {})
        
        extracted_info = {
            "title": award_info.get("title") or key_entities.get("title") or file_record.display_name,
            "brand": award_info.get("brand") or key_entities.get("brand") or "待AI分析",
            "year": award_info.get("year") or datetime.now().year,
            "business_type": award_info.get("business_type") or ai_classification.get("business_field", "待AI分析"),
            "description": ai_classification.get("description", f"从文件 '{file_record.original_filename}' 自动识别")
        }
        
        # 创建奖项记录
        award = Award(
            title=extracted_info["title"],
            brand=extracted_info["brand"],
            year=extracted_info["year"],
            business_type=extracted_info["business_type"],
            description=extracted_info["description"],
            is_verified=False,
            source_document=file_record.storage_path,
            confidence_score=ai_classification.get("confidence", 0.0)
        )
        
        db.add(award)
        db.flush()  # 获取ID
        
        logger.info(f"✅ 自动创建奖项记录: {award.title}")
        return {
            "type": "award_certificate",
            "action": "created_new",
            "award_id": award.id,
            "title": award.title,
            "brand": award.brand
        }
        
    except Exception as e:
        logger.error(f"创建奖项记录失败: {str(e)}")
        return {"error": str(e)}

def setup_router(app):
    app.include_router(router) 