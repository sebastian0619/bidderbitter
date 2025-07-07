from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form, Query, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional, Dict, Any
import os
import shutil
from datetime import datetime
import logging
import uuid
import asyncio
import json
from pydantic import BaseModel

from database import get_db
from models import Project, ProjectSection, SectionDocument, Template, TemplateField, TemplateMapping, GeneratedDocument
from document_processor import document_processor

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(prefix="/api/projects", tags=["projects"])

# 上传目录
UPLOAD_DIR = os.environ.get("UPLOAD_PATH", "/app/uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ============ 数据模型 ============

class ProjectBase(BaseModel):
    name: str
    tender_agency: Optional[str] = None
    tender_company: Optional[str] = None
    bidder_name: Optional[str] = None
    deadline: Optional[datetime] = None
    description: Optional[str] = None

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(ProjectBase):
    status: Optional[str] = None

class ProjectResponse(ProjectBase):
    id: int
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class SectionBase(BaseModel):
    title: str
    description: Optional[str] = None
    order: Optional[int] = 0

class SectionCreate(SectionBase):
    pass

class SectionUpdate(SectionBase):
    pass

class SectionResponse(SectionBase):
    id: int
    project_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class DocumentBase(BaseModel):
    original_filename: str
    file_type: str
    order: Optional[int] = 0

class DocumentResponse(DocumentBase):
    id: int
    section_id: int
    storage_path: str
    converted_path: Optional[str] = None
    page_count: Optional[int] = None
    file_size: Optional[int] = None
    is_processed: bool
    processing_status: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class ReorderItem(BaseModel):
    id: int
    order: int

# ============ API端点 ============

# 项目管理
@router.post("", response_model=ProjectResponse)
async def create_project(project: ProjectCreate, db: Session = Depends(get_db)):
    """创建新项目"""
    try:
        # 创建项目记录
        db_project = Project(**project.dict())
        db.add(db_project)
        db.commit()
        db.refresh(db_project)
        
        return db_project
        
    except Exception as e:
        logger.error(f"创建项目失败: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建项目失败: {str(e)}")

@router.get("", response_model=List[ProjectResponse])
async def get_projects(
    status: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """获取项目列表"""
    try:
        query = db.query(Project)
        
        if status:
            query = query.filter(Project.status == status)
        
        # 按更新时间降序排列
        query = query.order_by(desc(Project.updated_at))
        
        return query.offset(skip).limit(limit).all()
        
    except Exception as e:
        logger.error(f"获取项目列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取项目列表失败: {str(e)}")

@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: int, db: Session = Depends(get_db)):
    """获取项目详情"""
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
            
        return project
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取项目详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取项目详情失败: {str(e)}")

@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    project_data: ProjectUpdate,
    db: Session = Depends(get_db)
):
    """更新项目"""
    try:
        # 检查项目是否存在
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        # 更新字段
        for key, value in project_data.dict(exclude_unset=True).items():
            setattr(project, key, value)
        
        project.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(project)
        
        return project
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新项目失败: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新项目失败: {str(e)}")

@router.delete("/{project_id}")
async def delete_project(project_id: int, db: Session = Depends(get_db)):
    """删除项目"""
    try:
        # 检查项目是否存在
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        # 删除项目(关联的章节、文档会通过cascade自动删除)
        db.delete(project)
        db.commit()
        
        return {"message": "项目删除成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除项目失败: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除项目失败: {str(e)}")

# 章节管理
@router.post("/{project_id}/sections", response_model=SectionResponse)
async def create_section(
    project_id: int,
    section_data: SectionCreate,
    db: Session = Depends(get_db)
):
    """创建项目章节"""
    try:
        # 检查项目是否存在
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        # 创建章节
        section = ProjectSection(project_id=project_id, **section_data.dict())
        db.add(section)
        db.commit()
        db.refresh(section)
        
        return section
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建章节失败: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建章节失败: {str(e)}")

@router.get("/{project_id}/sections", response_model=List[SectionResponse])
async def get_sections(project_id: int, db: Session = Depends(get_db)):
    """获取项目的章节列表"""
    try:
        # 检查项目是否存在
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        # 获取章节列表，按order排序
        sections = db.query(ProjectSection).filter(
            ProjectSection.project_id == project_id
        ).order_by(ProjectSection.order).all()
        
        return sections
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取章节列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取章节列表失败: {str(e)}")

@router.put("/sections/{section_id}", response_model=SectionResponse)
async def update_section(
    section_id: int,
    section_data: SectionUpdate,
    db: Session = Depends(get_db)
):
    """更新章节"""
    try:
        # 检查章节是否存在
        section = db.query(ProjectSection).filter(ProjectSection.id == section_id).first()
        if not section:
            raise HTTPException(status_code=404, detail="章节不存在")
        
        # 更新字段
        for key, value in section_data.dict(exclude_unset=True).items():
            setattr(section, key, value)
        
        section.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(section)
        
        return section
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新章节失败: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新章节失败: {str(e)}")

@router.delete("/sections/{section_id}")
async def delete_section(section_id: int, db: Session = Depends(get_db)):
    """删除章节"""
    try:
        # 检查章节是否存在
        section = db.query(ProjectSection).filter(ProjectSection.id == section_id).first()
        if not section:
            raise HTTPException(status_code=404, detail="章节不存在")
        
        # 删除章节(关联的文档会通过cascade自动删除)
        db.delete(section)
        db.commit()
        
        return {"message": "章节删除成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除章节失败: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除章节失败: {str(e)}")

@router.put("/sections/reorder")
async def reorder_sections(
    items: List[ReorderItem],
    db: Session = Depends(get_db)
):
    """重新排序章节"""
    try:
        for item in items:
            section = db.query(ProjectSection).filter(ProjectSection.id == item.id).first()
            if section:
                section.order = item.order
                section.updated_at = datetime.utcnow()
        
        db.commit()
        return {"message": "章节重新排序成功"}
        
    except Exception as e:
        logger.error(f"重新排序章节失败: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"重新排序章节失败: {str(e)}")

# 文档管理
async def process_document_background(document_id: int, db_str: str):
    """后台处理文档"""
    try:
        # 创建新的数据库会话
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        
        # 创建引擎和会话
        engine = create_engine(db_str)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # 获取文档
        document = db.query(SectionDocument).filter(SectionDocument.id == document_id).first()
        if not document:
            logger.error(f"文档不存在: {document_id}")
            return
        
        # 更新处理状态
        document.processing_status = "processing"
        db.commit()
        
        try:
            # 处理文档
            if document.file_type.lower() in ['pdf', 'image', 'docx', 'doc']:
                # 转换为Word
                converted_path, page_count = await document_processor.convert_to_word(document.storage_path)
                
                document.converted_path = converted_path
                document.page_count = page_count
                document.is_processed = True
                document.processing_status = "completed"
            else:
                document.processing_status = "failed"
                document.error_message = "不支持的文件类型"
        
        except Exception as proc_err:
            document.processing_status = "failed"
            document.error_message = str(proc_err)
            logger.error(f"处理文档失败: {str(proc_err)}")
        
        # 更新文档状态
        document.updated_at = datetime.utcnow()
        db.commit()
        
    except Exception as e:
        logger.error(f"后台处理文档失败: {str(e)}")
    finally:
        db.close()

@router.post("/sections/{section_id}/documents", response_model=DocumentResponse)
async def upload_document(
    section_id: int,
    file: UploadFile = File(...),
    order: int = Form(0),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """上传文档到章节"""
    try:
        # 检查章节是否存在
        section = db.query(ProjectSection).filter(ProjectSection.id == section_id).first()
        if not section:
            raise HTTPException(status_code=404, detail="章节不存在")
        
        # 生成唯一文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        ext = os.path.splitext(file.filename)[1]
        new_filename = f"{timestamp}_{unique_id}{ext}"
        
        # 创建项目专属目录
        project_dir = os.path.join(UPLOAD_DIR, f"project_{section.project_id}")
        os.makedirs(project_dir, exist_ok=True)
        
        file_path = os.path.join(project_dir, new_filename)
        file_size = 0
        
        # 保存文件
        with open(file_path, "wb") as buffer:
            data = await file.read()
            buffer.write(data)
            file_size = len(data)
        
        # 检测文件类型
        file_ext = os.path.splitext(file.filename)[1].lower().replace('.', '')
        file_type = file_ext
        
        # 创建文档记录
        document = SectionDocument(
            section_id=section_id,
            original_filename=file.filename,
            storage_path=file_path,
            file_type=file_type,
            mime_type=file.content_type,
            order=order,
            file_size=file_size,
            is_processed=False,
            processing_status="pending"
        )
        
        db.add(document)
        db.commit()
        db.refresh(document)
        
        # 添加后台任务处理文档
        # 获取数据库连接字符串
        from database import DATABASE_URL
        background_tasks.add_task(process_document_background, document.id, DATABASE_URL)
        
        return document
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"上传文档失败: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"上传文档失败: {str(e)}")

@router.post("/sections/{section_id}/documents/batch")
async def upload_documents_batch(
    section_id: int,
    files: List[UploadFile] = File(...),
    orders: Optional[str] = Form(None),  # JSON数组，每个文件的顺序
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """批量上传文档到章节"""
    try:
        import json
        
        # 检查章节是否存在
        section = db.query(ProjectSection).filter(ProjectSection.id == section_id).first()
        if not section:
            raise HTTPException(status_code=404, detail="章节不存在")
        
        uploaded_documents = []
        failed_files = []
        
        # 解析顺序
        orders_list = []
        if orders:
            try:
                orders_list = json.loads(orders)
            except:
                orders_list = []
        
        # 创建项目专属目录
        project_dir = os.path.join(UPLOAD_DIR, f"project_{section.project_id}")
        os.makedirs(project_dir, exist_ok=True)
        
        for i, file in enumerate(files):
            try:
                if not file.filename:
                    failed_files.append({
                        "filename": "未知文件",
                        "error": "文件名不能为空"
                    })
                    continue
                
                # 检查文件大小
                content = await file.read()
                file_size = len(content)
                
                if file_size > 200 * 1024 * 1024:  # 200MB限制
                    failed_files.append({
                        "filename": file.filename,
                        "error": "文件大小超过限制(200MB)"
                    })
                    continue
                
                # 生成唯一文件名
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                unique_id = str(uuid.uuid4())[:8]
                ext = os.path.splitext(file.filename)[1]
                new_filename = f"{timestamp}_{i}_{unique_id}{ext}"
                
                file_path = os.path.join(project_dir, new_filename)
                
                # 保存文件
                with open(file_path, "wb") as buffer:
                    buffer.write(content)
                
                # 检测文件类型
                file_ext = os.path.splitext(file.filename)[1].lower().replace('.', '')
                file_type = file_ext
                
                # 确定顺序
                order = orders_list[i] if i < len(orders_list) else i
                
                # 创建文档记录
                document = SectionDocument(
                    section_id=section_id,
                    original_filename=file.filename,
                    storage_path=file_path,
                    file_type=file_type,
                    mime_type=file.content_type,
                    order=order,
                    file_size=file_size,
                    is_processed=False,
                    processing_status="pending"
                )
                
                db.add(document)
                db.flush()  # 获取ID但不提交
                
                uploaded_documents.append({
                    "id": document.id,
                    "filename": file.filename,
                    "file_size": file_size,
                    "order": order
                })
                
                # 添加后台任务处理文档
                from database import DATABASE_URL
                background_tasks.add_task(process_document_background, document.id, DATABASE_URL)
                
                logger.info(f"批量文档上传成功: {file.filename}")
                
            except Exception as file_err:
                failed_files.append({
                    "filename": file.filename,
                    "error": str(file_err)
                })
                logger.error(f"上传文档失败 {file.filename}: {file_err}")
        
        db.commit()
        
        return {
            "success": True,
            "message": f"批量上传完成: {len(uploaded_documents)} 成功, {len(failed_files)} 失败",
            "uploaded_documents": uploaded_documents,
            "failed_files": failed_files,
            "summary": {
                "total": len(files),
                "success": len(uploaded_documents),
                "failed": len(failed_files)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量上传文档失败: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"批量上传文档失败: {str(e)}")

@router.get("/sections/{section_id}/documents", response_model=List[DocumentResponse])
async def get_documents(section_id: int, db: Session = Depends(get_db)):
    """获取章节的文档列表"""
    try:
        # 检查章节是否存在
        section = db.query(ProjectSection).filter(ProjectSection.id == section_id).first()
        if not section:
            raise HTTPException(status_code=404, detail="章节不存在")
        
        # 获取文档列表，按order排序
        documents = db.query(SectionDocument).filter(
            SectionDocument.section_id == section_id
        ).order_by(SectionDocument.order).all()
        
        return documents
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文档列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取文档列表失败: {str(e)}")

@router.delete("/documents/{document_id}")
async def delete_document(document_id: int, db: Session = Depends(get_db)):
    """删除文档"""
    try:
        # 检查文档是否存在
        document = db.query(SectionDocument).filter(SectionDocument.id == document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        # 删除文件
        if document.storage_path and os.path.exists(document.storage_path):
            os.remove(document.storage_path)
        
        if document.converted_path and os.path.exists(document.converted_path):
            os.remove(document.converted_path)
        
        # 删除数据库记录
        db.delete(document)
        db.commit()
        
        return {"message": "文档删除成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除文档失败: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除文档失败: {str(e)}")

@router.put("/documents/reorder")
async def reorder_documents(
    items: List[ReorderItem],
    db: Session = Depends(get_db)
):
    """重新排序文档"""
    try:
        for item in items:
            document = db.query(SectionDocument).filter(SectionDocument.id == item.id).first()
            if document:
                document.order = item.order
                document.updated_at = datetime.utcnow()
        
        db.commit()
        return {"message": "文档重新排序成功"}
        
    except Exception as e:
        logger.error(f"重新排序文档失败: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"重新排序文档失败: {str(e)}")

# 文档生成
@router.post("/{project_id}/generate", response_model=Dict[str, Any])
async def generate_project_document(
    project_id: int,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """生成项目文档"""
    try:
        # 检查项目是否存在
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        # 查询所有章节及其文档
        sections = db.query(ProjectSection).filter(
            ProjectSection.project_id == project_id
        ).order_by(ProjectSection.order).all()
        
        # 收集已处理的文档
        document_paths = []
        section_info = []
        
        for section in sections:
            section_docs = []
            
            documents = db.query(SectionDocument).filter(
                SectionDocument.section_id == section.id,
                SectionDocument.is_processed == True,
                SectionDocument.processing_status == "completed"
            ).order_by(SectionDocument.order).all()
            
            for doc in documents:
                if doc.converted_path and os.path.exists(doc.converted_path):
                    document_paths.append(doc.converted_path)
                    section_docs.append({
                        "id": doc.id,
                        "filename": doc.original_filename,
                        "page_count": doc.page_count or 1
                    })
            
            if section_docs:
                section_info.append({
                    "id": section.id,
                    "title": section.title,
                    "documents": section_docs
                })
        
        if not document_paths:
            raise HTTPException(status_code=400, detail="没有已处理完成的文档")
        
        # 生成输出文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = project.name.replace(" ", "_").replace("/", "_")
        output_filename = f"{safe_name}_{timestamp}.docx"
        
        # 合并文档
        output_path, total_pages, processing_time = await document_processor.merge_documents(
            document_paths, output_filename
        )
        
        # 创建生成文档记录
        generated_doc = GeneratedDocument(
            project_id=project_id,
            filename=output_filename,
            file_path=output_path,
            file_size=os.path.getsize(output_path),
            page_count=total_pages,
            generation_time=processing_time
        )
        
        db.add(generated_doc)
        db.commit()
        db.refresh(generated_doc)
        
        # 构造下载URL
        download_url = f"/api/projects/download/{generated_doc.id}"
        
        return {
            "success": True,
            "message": "文档生成成功",
            "document_id": generated_doc.id,
            "filename": output_filename,
            "page_count": total_pages,
            "file_size": os.path.getsize(output_path),
            "processing_time": processing_time,
            "download_url": download_url,
            "sections": section_info
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"生成文档失败: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"生成文档失败: {str(e)}")

@router.get("/download/{document_id}")
async def download_generated_document(document_id: int, db: Session = Depends(get_db)):
    """下载生成的文档"""
    try:
        # 获取文档
        document = db.query(GeneratedDocument).filter(GeneratedDocument.id == document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        # 检查文件是否存在
        if not document.file_path or not os.path.exists(document.file_path):
            raise HTTPException(status_code=404, detail="文件不存在")
        
        return FileResponse(
            path=document.file_path,
            filename=document.filename,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"下载文档失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"下载文档失败: {str(e)}")

# 导出API路由器供main.py使用
def setup_router(app):
    app.include_router(router) 