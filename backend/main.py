"""FastAPI 主应用"""
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import shutil
import hashlib
import os
from pathlib import Path
from datetime import datetime

# 设置 MiMo API 环境变量
os.environ.setdefault("MIMO_API_KEY", "tp-cvbdchboz3viy5gwd59qrnnli6s9mnsgexbuavd8mo25no2b")
os.environ.setdefault("MIMO_BASE_URL", "https://token-plan-cn.xiaomimimo.com/v1")
os.environ.setdefault("MIMO_MODEL", "mimo-v2.5")

from models import get_db, init_db, ManagedFile, Tag, file_tags, Project, ProjectSection, SectionDocument, project_files, User
from agent_classifier import agent_classifier
from tender_analyzer import tender_analyzer
from agent_service import agent, AgentContext

app = FastAPI(title="BidTool API", version="0.1.0")

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 文件存储目录
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

@app.on_event("startup")
def startup():
    init_db()

# ==================== 文件 API ====================

@app.post("/api/files")
async def upload_file(
    file: UploadFile = File(...),
    category: Optional[str] = None,
    description: Optional[str] = None,
    save_to_manager: bool = True,
    not_shared: bool = False,
    db: Session = Depends(get_db)
):
    """上传文件
    
    Args:
        save_to_manager: 是否存入文件管理，默认为 True
        not_shared: 是否不共享，默认为 False（即默认共享）
    """
    # 共享逻辑：默认共享，除非明确勾选不共享
    is_shared = not not_shared
    # 计算文件哈希
    content = await file.read()
    file_hash = hashlib.md5(content).hexdigest()
    
    # 检查是否已存在
    existing = db.query(ManagedFile).filter(ManagedFile.file_hash == file_hash).first()
    if existing:
        # 如果已存在且需要存入管理，返回已有文件
        if save_to_manager:
            return {"id": existing.id, "filename": existing.original_filename, "size": existing.file_size}
        # 如果不需要存入管理，直接返回临时文件信息
        return {"id": existing.id, "filename": existing.original_filename, "size": existing.file_size, "temp": True}
    
    # 保存文件
    today = datetime.now()
    rel_path = f"{today.year}/{today.month:02d}/{today.day:02d}"
    save_dir = UPLOAD_DIR / rel_path
    save_dir.mkdir(parents=True, exist_ok=True)
    
    ext = Path(file.filename).suffix
    new_filename = f"{file_hash[:8]}_{file.filename}"
    file_path = save_dir / new_filename
    
    with open(file_path, "wb") as f:
        f.write(content)
    
    # 确定文件类型
    file_type = "document"
    if ext.lower() in [".jpg", ".jpeg", ".png", ".gif", ".bmp"]:
        file_type = "image"
    elif ext.lower() == ".pdf":
        file_type = "pdf"
    
    # 根据 save_to_manager 决定是否创建数据库记录
    if save_to_manager:
        # 判断是否为参考资料（业绩/证照等），默认标记为参考资料
        is_reference = category in ["业绩", "资质证照", "奖项荣誉", "合同", None]
        
        db_file = ManagedFile(
            original_filename=file.filename,
            display_name=file.filename,
            storage_path=str(file_path),
            file_type=file_type,
            mime_type=file.content_type,
            file_size=len(content),
            file_hash=file_hash,
            category=category or "uploaded",
            description=description,
            is_shared=is_shared,  # 默认共享，除非明确不共享
            is_reference=is_reference,
        )
        db.add(db_file)
        db.commit()
        db.refresh(db_file)
        return {"id": db_file.id, "filename": db_file.original_filename, "size": db_file.file_size, "is_shared": is_shared}
    else:
        # 临时文件，返回文件路径作为 ID
        return {"id": f"temp_{file_hash[:8]}", "filename": file.filename, "size": len(content), "temp": True, "path": str(file_path)}

@app.get("/api/files")
async def list_files(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    file_type: Optional[str] = None,
    tag_id: Optional[int] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取文件列表"""
    query = db.query(ManagedFile)
    
    if category:
        query = query.filter(ManagedFile.category == category)
    if file_type:
        query = query.filter(ManagedFile.file_type == file_type)
    if tag_id:
        query = query.filter(ManagedFile.tags.any(Tag.id == tag_id))
    if search:
        query = query.filter(
            (ManagedFile.original_filename.contains(search)) |
            (ManagedFile.description.contains(search))
        )
    
    total = query.count()
    files = query.offset((page - 1) * page_size).limit(page_size).all()
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "files": [
            {
                "id": f.id,
                "filename": f.original_filename,
                "display_name": f.display_name,
                "file_type": f.file_type,
                "file_size": f.file_size,
                "category": f.category,
                "tags": [{"id": t.id, "name": t.name, "color": t.color} for t in f.tags],
                "created_at": f.created_at.isoformat() if f.created_at else None,
            }
            for f in files
        ]
    }

@app.get("/api/files/{file_id}")
async def get_file(file_id: int, db: Session = Depends(get_db)):
    """获取文件详情"""
    file = db.query(ManagedFile).filter(ManagedFile.id == file_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="文件不存在")
    
    return {
        "id": file.id,
        "filename": file.original_filename,
        "display_name": file.display_name,
        "file_type": file.file_type,
        "mime_type": file.mime_type,
        "file_size": file.file_size,
        "file_hash": file.file_hash,
        "category": file.category,
        "description": file.description,
        "tags": [{"id": t.id, "name": t.name, "color": t.color} for t in file.tags],
        "created_at": file.created_at.isoformat() if file.created_at else None,
        "updated_at": file.updated_at.isoformat() if file.updated_at else None,
    }

@app.get("/api/files/{file_id}/download")
async def download_file(file_id: int, db: Session = Depends(get_db)):
    """下载文件"""
    file = db.query(ManagedFile).filter(ManagedFile.id == file_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="文件不存在")
    
    file_path = Path(file.storage_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    
    return FileResponse(
        path=str(file_path),
        filename=file.original_filename,
        media_type=file.mime_type
    )

@app.put("/api/files/{file_id}")
async def update_file(
    file_id: int,
    display_name: Optional[str] = None,
    category: Optional[str] = None,
    description: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """更新文件信息"""
    file = db.query(ManagedFile).filter(ManagedFile.id == file_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="文件不存在")
    
    if display_name:
        file.display_name = display_name
    if category:
        file.category = category
    if description:
        file.description = description
    
    db.commit()
    return {"message": "更新成功"}

@app.delete("/api/files/{file_id}")
async def delete_file(file_id: int, db: Session = Depends(get_db)):
    """删除文件"""
    file = db.query(ManagedFile).filter(ManagedFile.id == file_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="文件不存在")
    
    # 删除物理文件
    file_path = Path(file.storage_path)
    if file_path.exists():
        file_path.unlink()
    
    db.delete(file)
    db.commit()
    return {"message": "删除成功"}

# ==================== 标签 API ====================

@app.get("/api/tags")
async def list_tags(db: Session = Depends(get_db)):
    """获取所有标签"""
    tags = db.query(Tag).all()
    return [
        {"id": t.id, "name": t.name, "color": t.color, "category": t.category}
        for t in tags
    ]

@app.post("/api/tags")
async def create_tag(
    name: str,
    color: str = "#409EFF",
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """创建标签"""
    existing = db.query(Tag).filter(Tag.name == name).first()
    if existing:
        raise HTTPException(status_code=409, detail="标签已存在")
    
    tag = Tag(name=name, color=color, category=category)
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return {"id": tag.id, "name": tag.name, "color": tag.color}

@app.put("/api/tags/{tag_id}")
async def update_tag(
    tag_id: int,
    name: Optional[str] = None,
    color: Optional[str] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """更新标签"""
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="标签不存在")
    
    if name:
        tag.name = name
    if color:
        tag.color = color
    if category:
        tag.category = category
    
    db.commit()
    return {"message": "更新成功"}

@app.delete("/api/tags/{tag_id}")
async def delete_tag(tag_id: int, db: Session = Depends(get_db)):
    """删除标签"""
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="标签不存在")
    
    db.delete(tag)
    db.commit()
    return {"message": "删除成功"}

@app.post("/api/files/{file_id}/tags")
async def add_tags_to_file(
    file_id: int,
    tag_ids: List[int],
    db: Session = Depends(get_db)
):
    """为文件添加标签"""
    file = db.query(ManagedFile).filter(ManagedFile.id == file_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="文件不存在")
    
    tags = db.query(Tag).filter(Tag.id.in_(tag_ids)).all()
    file.tags.extend(tags)
    db.commit()
    return {"message": "标签添加成功"}

@app.delete("/api/files/{file_id}/tags/{tag_id}")
async def remove_tag_from_file(
    file_id: int,
    tag_id: int,
    db: Session = Depends(get_db)
):
    """移除文件标签"""
    file = db.query(ManagedFile).filter(ManagedFile.id == file_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="文件不存在")
    
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if tag in file.tags:
        file.tags.remove(tag)
        db.commit()
    
    return {"message": "标签移除成功"}

# ==================== PDF 处理 API ====================

@app.post("/api/pdf/merge")
async def merge_pdfs(
    files: List[int],
    output_name: str = "merged.pdf",
    db: Session = Depends(get_db)
):
    """合并多个 PDF"""
    import fitz
    
    # 获取文件路径
    db_files = db.query(ManagedFile).filter(ManagedFile.id.in_(files)).all()
    if len(db_files) != len(files):
        raise HTTPException(status_code=404, detail="部分文件不存在")
    
    # 合并 PDF
    doc = fitz.open()
    for f in db_files:
        src = fitz.open(f.storage_path)
        doc.insert_pdf(src)
        src.close()
    
    # 保存结果
    today = datetime.now()
    rel_path = f"{today.year}/{today.month:02d}/{today.day:02d}"
    save_dir = UPLOAD_DIR / rel_path
    save_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = save_dir / output_name
    doc.save(str(output_path))
    doc.close()
    
    # 创建数据库记录
    file_hash = hashlib.md5(output_path.read_bytes()).hexdigest()
    db_file = ManagedFile(
        original_filename=output_name,
        display_name=output_name,
        storage_path=str(output_path),
        file_type="pdf",
        mime_type="application/pdf",
        file_size=output_path.stat().st_size,
        file_hash=file_hash,
        category="generated",
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    
    return {"id": db_file.id, "filename": output_name}

@app.post("/api/pdf/extract-images")
async def extract_images_from_pdf(
    file_id: int,
    db: Session = Depends(get_db)
):
    """从 PDF 提取图片"""
    import fitz
    
    file = db.query(ManagedFile).filter(ManagedFile.id == file_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="文件不存在")
    
    doc = fitz.open(file.storage_path)
    extracted = []
    
    today = datetime.now()
    rel_path = f"{today.year}/{today.month:02d}/{today.day:02d}"
    save_dir = UPLOAD_DIR / rel_path / "extracted"
    save_dir.mkdir(parents=True, exist_ok=True)
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        images = page.get_images(full=True)
        for img_idx, img_info in enumerate(images):
            xref = img_info[0]
            try:
                pix = fitz.Pixmap(doc, xref)
                if pix.width < 100 or pix.height < 100:
                    continue
                if pix.n > 4:
                    pix = fitz.Pixmap(fitz.csRGB, pix)
                ext = "png" if pix.alpha else "jpg"
                out_path = save_dir / f"page{page_num+1}_img{img_idx+1}.{ext}"
                pix.save(str(out_path))
                extracted.append(str(out_path))
            except Exception:
                continue
    doc.close()
    
    return {"extracted_count": len(extracted), "output_dir": str(save_dir)}

@app.post("/api/image/to-pdf")
async def images_to_pdf(
    file_ids: List[int],
    output_name: str = "output.pdf",
    db: Session = Depends(get_db)
):
    """图片转 PDF"""
    from PIL import Image
    
    db_files = db.query(ManagedFile).filter(ManagedFile.id.in_(file_ids)).all()
    if len(db_files) != len(file_ids):
        raise HTTPException(status_code=404, detail="部分文件不存在")
    
    img_list = []
    for f in db_files:
        img = Image.open(f.storage_path)
        if img.mode != "RGB":
            img = img.convert("RGB")
        img_list.append(img)
    
    if not img_list:
        raise HTTPException(status_code=400, detail="没有有效图片")
    
    today = datetime.now()
    rel_path = f"{today.year}/{today.month:02d}/{today.day:02d}"
    save_dir = UPLOAD_DIR / rel_path
    save_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = save_dir / output_name
    first = img_list[0]
    if len(img_list) > 1:
        first.save(str(output_path), save_all=True, append_images=img_list[1:])
    else:
        first.save(str(output_path))
    
    # 创建数据库记录
    file_hash = hashlib.md5(output_path.read_bytes()).hexdigest()
    db_file = ManagedFile(
        original_filename=output_name,
        display_name=output_name,
        storage_path=str(output_path),
        file_type="pdf",
        mime_type="application/pdf",
        file_size=output_path.stat().st_size,
        file_hash=file_hash,
        category="generated",
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    
    return {"id": db_file.id, "filename": output_name}

# ==================== 投标项目 API ====================

@app.get("/api/projects")
async def list_projects(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取项目列表"""
    query = db.query(Project)
    
    if status:
        query = query.filter(Project.status == status)
    if search:
        query = query.filter(
            (Project.name.contains(search)) |
            (Project.tender_company.contains(search))
        )
    
    total = query.count()
    projects = query.order_by(Project.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "projects": [
            {
                "id": p.id,
                "name": p.name,
                "tender_agency": p.tender_agency,
                "tender_company": p.tender_company,
                "bidder_name": p.bidder_name,
                "deadline": p.deadline.isoformat() if p.deadline else None,
                "status": p.status,
                "description": p.description,
                 "file_count": len(p.managed_files),
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in projects
        ]
    }

@app.post("/api/projects")
async def create_project(
    name: str,
    tender_agency: Optional[str] = None,
    tender_company: Optional[str] = None,
    bidder_name: Optional[str] = None,
    deadline: Optional[str] = None,
    description: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """创建项目"""
    project = Project(
        name=name,
        tender_agency=tender_agency,
        tender_company=tender_company,
        bidder_name=bidder_name,
        deadline=datetime.fromisoformat(deadline) if deadline else None,
        description=description,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    
    return {"id": project.id, "name": project.name}

@app.get("/api/projects/{project_id}")
async def get_project(project_id: int, db: Session = Depends(get_db)):
    """获取项目详情"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    return {
        "id": project.id,
        "name": project.name,
        "tender_agency": project.tender_agency,
        "tender_company": project.tender_company,
        "bidder_name": project.bidder_name,
        "deadline": project.deadline.isoformat() if project.deadline else None,
        "status": project.status,
        "description": project.description,
        "files": [
            {
                "id": f.id,
                "filename": f.original_filename,
                "file_type": f.file_type,
                "category": f.category,
            }
            for f in project.managed_files
        ],
        "sections": [
            {
                "id": s.id,
                "title": s.title,
                "section_type": s.section_type,
                "order": s.order,
            }
            for s in project.sections
        ],
        "created_at": project.created_at.isoformat() if project.created_at else None,
    }

@app.put("/api/projects/{project_id}")
async def update_project(
    project_id: int,
    name: Optional[str] = None,
    tender_agency: Optional[str] = None,
    tender_company: Optional[str] = None,
    bidder_name: Optional[str] = None,
    deadline: Optional[str] = None,
    status: Optional[str] = None,
    description: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """更新项目"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    if name is not None:
        project.name = name
    if tender_agency is not None:
        project.tender_agency = tender_agency
    if tender_company is not None:
        project.tender_company = tender_company
    if bidder_name is not None:
        project.bidder_name = bidder_name
    if deadline is not None:
        project.deadline = datetime.fromisoformat(deadline) if deadline else None
    if status is not None:
        project.status = status
    if description is not None:
        project.description = description
    
    db.commit()
    return {"message": "更新成功"}

@app.delete("/api/projects/{project_id}")
async def delete_project(project_id: int, db: Session = Depends(get_db)):
    """删除项目"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    db.delete(project)
    db.commit()
    return {"message": "删除成功"}

@app.post("/api/projects/{project_id}/files")
async def add_files_to_project(
    project_id: int,
    file_ids: List[int],
    section_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """添加文件到项目"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    files = db.query(ManagedFile).filter(ManagedFile.id.in_(file_ids)).all()
    for f in files:
        if f not in project.managed_files:
            project.managed_files.append(f)
    
    db.commit()
    return {"message": f"添加了 {len(files)} 个文件"}

@app.delete("/api/projects/{project_id}/files/{file_id}")
async def remove_file_from_project(
    project_id: int,
    file_id: int,
    db: Session = Depends(get_db)
):
    """从项目移除文件"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    file = db.query(ManagedFile).filter(ManagedFile.id == file_id).first()
    if file in project.managed_files:
        project.managed_files.remove(file)
        db.commit()
    
    return {"message": "移除成功"}

# ==================== Agent 自动分类 API ====================

@app.post("/api/files/{file_id}/classify")
async def classify_file(file_id: int, db: Session = Depends(get_db)):
    """Agent 自动分类文件"""
    file = db.query(ManagedFile).filter(ManagedFile.id == file_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="文件不存在")
    
    # 更新处理状态
    file.processing_status = "analyzing"
    db.commit()
    
    try:
        # 使用 AI 分类服务
        result = agent_classifier.classify_by_rules(file.original_filename)
        
        # 更新文件信息
        file.ai_category = result["category"]
        file.ai_confidence = result["confidence"]
        file.category = result["category"]
        file.ai_analysis = result
        file.is_processed = True
        file.processing_status = "completed"
        
        # 自动添加标签
        for tag_name in result["tags"]:
            tag = db.query(Tag).filter(Tag.name == tag_name).first()
            if not tag:
                tag = Tag(name=tag_name, category="auto", color=result.get("color", "#67C23A"))
                db.add(tag)
            if tag not in file.tags:
                file.tags.append(tag)
        
        db.commit()
        
        return {
            "category": result["category"],
            "confidence": result["confidence"],
            "tags": result["tags"],
            "matched_keywords": result.get("matched_keywords", []),
            "method": result["method"],
            "message": "分类完成"
        }
    except Exception as e:
        file.processing_status = "failed"
        db.commit()
        raise HTTPException(status_code=500, detail=f"分类失败: {str(e)}")

def classify_file_content(file: ManagedFile) -> tuple:
    """基于文件名和类型进行智能分类
    
    Returns:
        (category, confidence, tags)
    """
    filename = file.original_filename.lower()
    
    # 业绩类关键词
    performance_keywords = ['业绩', '合同', '服务协议', '法律顾问', '委托', '聘用']
    # 资质类关键词
    qualification_keywords = ['证书', '执照', '资质', '许可证', '律师证', '营业执照']
    # 奖项类关键词
    award_keywords = ['奖项', '获奖', '荣誉', '排名', 'chambers', 'legal500', 'alb']
    # 财务类关键词
    finance_keywords = ['审计', '财务', '报表', '纳税', '社保']
    
    # 检查关键词匹配
    for kw in performance_keywords:
        if kw in filename:
            return ('业绩', 0.9, ['业绩', '合同'])
    
    for kw in qualification_keywords:
        if kw in filename:
            return ('资质证照', 0.9, ['资质', '证书'])
    
    for kw in award_keywords:
        if kw in filename:
            return ('奖项荣誉', 0.9, ['奖项', '荣誉'])
    
    for kw in finance_keywords:
        if kw in filename:
            return ('财务资料', 0.8, ['财务'])
    
    # 基于文件类型的默认分类
    if file.file_type == 'pdf':
        return ('文档', 0.5, ['PDF'])
    elif file.file_type == 'image':
        return ('图片', 0.5, ['图片'])
    else:
        return ('其他', 0.3, [])

@app.post("/api/files/batch-classify")
async def batch_classify_files(
    file_ids: List[int],
    db: Session = Depends(get_db)
):
    """批量分类文件"""
    files_data = []
    for file_id in file_ids:
        file = db.query(ManagedFile).filter(ManagedFile.id == file_id).first()
        if file:
            files_data.append({"id": file.id, "filename": file.original_filename})
    
    results = agent_classifier.classify_batch(files_data)
    
    for result in results:
        file = db.query(ManagedFile).filter(ManagedFile.id == result["file_id"]).first()
        if file:
            file.ai_category = result["category"]
            file.ai_confidence = result["confidence"]
            file.category = result["category"]
            file.is_processed = True
            
            for tag_name in result["tags"]:
                tag = db.query(Tag).filter(Tag.name == tag_name).first()
                if not tag:
                    tag = Tag(name=tag_name, category="auto", color=result.get("color", "#67C23A"))
                    db.add(tag)
                if tag not in file.tags:
                    file.tags.append(tag)
    
    db.commit()
    return {"results": results, "message": f"分类了 {len(results)} 个文件"}

# ==================== 投标文档生成 API ====================

@app.post("/api/projects/{project_id}/generate")
async def generate_bid_document(
    project_id: int,
    db: Session = Depends(get_db)
):
    """生成投标文档"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 获取项目的章节
    sections = db.query(ProjectSection).filter(
        ProjectSection.project_id == project_id
    ).order_by(ProjectSection.order).all()
    
    # 如果没有章节，创建默认章节
    if not sections:
        default_sections = [
            {"title": "投标函及投标函附录", "section_type": "cover", "order": 1},
            {"title": "投标人资质证明", "section_type": "qualification", "order": 2},
            {"title": "业绩证明材料", "section_type": "performance", "order": 3},
            {"title": "项目团队介绍", "section_type": "team", "order": 4},
            {"title": "服务方案", "section_type": "proposal", "order": 5},
        ]
        for s in default_sections:
            section = ProjectSection(
                project_id=project_id,
                title=s["title"],
                section_type=s["section_type"],
                order=s["order"]
            )
            db.add(section)
        db.commit()
        sections = db.query(ProjectSection).filter(
            ProjectSection.project_id == project_id
        ).order_by(ProjectSection.order).all()
    
    # 获取项目的文件
    files = project.managed_files
    
    # 生成文档
    from bid_document_service import bid_document_service
    result = bid_document_service.generate_bid_document(project, sections, files, db)
    
    if result["success"]:
        return {
            "success": True,
            "filename": result["filename"],
            "file_size": result["file_size"],
            "download_url": f"/api/generated/{result['filename']}",
            "message": "投标文档生成成功"
        }
    else:
        raise HTTPException(status_code=500, detail=result["error"])

@app.get("/api/generated/{filename}")
async def download_generated_file(filename: str):
    """下载生成的文件"""
    file_path = Path("generated_docs") / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

@app.get("/api/projects/{project_id}/sections")
async def list_project_sections(project_id: int, db: Session = Depends(get_db)):
    """获取项目章节列表"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    sections = db.query(ProjectSection).filter(
        ProjectSection.project_id == project_id
    ).order_by(ProjectSection.order).all()
    
    return [
        {
            "id": s.id,
            "title": s.title,
            "section_type": s.section_type,
            "description": s.description,
            "order": s.order,
        }
        for s in sections
    ]

@app.post("/api/projects/{project_id}/sections")
async def create_project_section(
    project_id: int,
    title: str,
    section_type: Optional[str] = None,
    description: Optional[str] = None,
    order: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """创建项目章节"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 如果没有指定排序，放在最后
    if order is None:
        max_order = db.query(ProjectSection).filter(
            ProjectSection.project_id == project_id
        ).count()
        order = max_order + 1
    
    section = ProjectSection(
        project_id=project_id,
        title=title,
        section_type=section_type,
        description=description,
        order=order
    )
    db.add(section)
    db.commit()
    db.refresh(section)
    
    return {"id": section.id, "title": section.title}

# ==================== Agent 分类系统 API ====================

@app.get("/api/classification/categories")
async def get_classification_categories():
    """获取所有文件分类定义"""
    return agent_classifier.get_all_categories()

@app.post("/api/files/{file_id}/classify-ai")
async def classify_file_with_ai(file_id: int, db: Session = Depends(get_db)):
    """使用 Agent (LLM) 深度分类文件"""
    file = db.query(ManagedFile).filter(ManagedFile.id == file_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="文件不存在")
    
    file.processing_status = "analyzing"
    db.commit()
    
    try:
        # 读取文件内容预览
        content_preview = ""
        if file.file_type == "pdf":
            try:
                import fitz
                doc = fitz.open(file.storage_path)
                for page in doc[:3]:  # 只读前3页
                    content_preview += page.get_text()
                doc.close()
            except:
                pass
        
        # 使用 LLM 分类
        result = await agent_classifier.classify_with_llm(
            file.original_filename, 
            content_preview
        )
        
        # 更新文件
        file.ai_category = result["category"]
        file.ai_confidence = result.get("confidence", 0.5)
        file.category = result["category"]
        file.ai_analysis = result
        file.is_processed = True
        file.processing_status = "completed"
        
        # 添加标签
        for tag_name in result.get("tags", []):
            tag = db.query(Tag).filter(Tag.name == tag_name).first()
            if not tag:
                tag = Tag(name=tag_name, category="auto", color=result.get("color", "#67C23A"))
                db.add(tag)
            if tag not in file.tags:
                file.tags.append(tag)
        
        db.commit()
        
        return {
            "category": result["category"],
            "confidence": result.get("confidence", 0.5),
            "tags": result.get("tags", []),
            "summary": result.get("summary", ""),
            "reason": result.get("reason", ""),
            "method": result.get("method", "rules"),
            "message": "分类完成"
        }
    except Exception as e:
        file.processing_status = "failed"
        db.commit()
        raise HTTPException(status_code=500, detail=f"分类失败: {str(e)}")

@app.post("/api/files/batch-classify-ai")
async def batch_classify_files_with_ai(
    file_ids: List[int],
    db: Session = Depends(get_db)
):
    """批量 AI 分类文件"""
    results = []
    
    for file_id in file_ids:
        file = db.query(ManagedFile).filter(ManagedFile.id == file_id).first()
        if not file:
            continue
        
        # 读取内容预览
        content_preview = ""
        if file.file_type == "pdf":
            try:
                import fitz
                doc = fitz.open(file.storage_path)
                for page in doc[:2]:
                    content_preview += page.get_text()
                doc.close()
            except:
                pass
        
        # 分类
        result = await agent_classifier.classify_with_llm(
            file.original_filename,
            content_preview
        )
        
        # 更新文件
        file.ai_category = result["category"]
        file.ai_confidence = result.get("confidence", 0.5)
        file.category = result["category"]
        file.is_processed = True
        
        # 添加标签
        for tag_name in result.get("tags", []):
            tag = db.query(Tag).filter(Tag.name == tag_name).first()
            if not tag:
                tag = Tag(name=tag_name, category="auto", color=result.get("color", "#67C23A"))
                db.add(tag)
            if tag not in file.tags:
                file.tags.append(tag)
        
        results.append({
            "file_id": file_id,
            "filename": file.original_filename,
            "category": result["category"],
            "confidence": result.get("confidence", 0.5),
            "tags": result.get("tags", [])
        })
    
    db.commit()
    return {"results": results, "count": len(results)}

@app.get("/api/files/classification-stats")
async def get_classification_stats(db: Session = Depends(get_db)):
    """获取文件分类统计"""
    from sqlalchemy import func
    
    stats = db.query(
        ManagedFile.ai_category,
        func.count(ManagedFile.id)
    ).filter(
        ManagedFile.ai_category.isnot(None)
    ).group_by(ManagedFile.ai_category).all()
    
    return {
        "stats": {cat: count for cat, count in stats},
        "total_classified": sum(count for _, count in stats),
        "total_files": db.query(ManagedFile).count()
    }

# ==================== 招标文件分析 API ====================

@app.post("/api/tender/analyze")
async def analyze_tender_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """上传招标文件并自动分析，提取项目信息和章节结构"""
    # 保存临时文件
    import tempfile
    suffix = Path(file.filename).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        # 根据文件类型选择分析方法
        if suffix.lower() == '.pdf':
            result = tender_analyzer.analyze_pdf(tmp_path)
        else:
            result = tender_analyzer.analyze_with_docx(tmp_path)
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result.get("error", "分析失败"))
        
        # 同时保存到文件管理
        today = datetime.now()
        rel_path = f"{today.year}/{today.month:02d}/{today.day:02d}"
        save_dir = UPLOAD_DIR / rel_path
        save_dir.mkdir(parents=True, exist_ok=True)
        
        file_hash = hashlib.md5(content).hexdigest()
        new_filename = f"{file_hash[:8]}_{file.filename}"
        file_path = save_dir / new_filename
        
        with open(file_path, "wb") as f:
            f.write(content)
        
        # 创建文件记录
        db_file = ManagedFile(
            original_filename=file.filename,
            display_name=file.filename,
            storage_path=str(file_path),
            file_type="pdf" if suffix.lower() == '.pdf' else "document",
            mime_type=file.content_type,
            file_size=len(content),
            file_hash=file_hash,
            category="招标文件",
            ai_category="招标文件",
            ai_confidence=0.9,
            is_processed=True,
            processing_status="completed"
        )
        db.add(db_file)
        db.commit()
        db.refresh(db_file)
        
        # 添加标签
        for tag_name in ["招标文件", "投标"]:
            tag = db.query(Tag).filter(Tag.name == tag_name).first()
            if not tag:
                tag = Tag(name=tag_name, category="auto", color="#FF9800")
                db.add(tag)
            if tag not in db_file.tags:
                db_file.tags.append(tag)
        db.commit()
        
        return {
            "success": True,
            "file_id": db_file.id,
            "project_info": result["project_info"],
            "sections": result["sections"],
            "text_preview": result["text_preview"],
            "message": "招标文件分析完成"
        }
        
    finally:
        # 清理临时文件
        os.unlink(tmp_path)

@app.post("/api/projects/create-from-tender")
async def create_project_from_tender(
    file_id: int,
    name: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """从招标文件创建项目（使用已上传的文件）"""
    file = db.query(ManagedFile).filter(ManagedFile.id == file_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="文件不存在")
    
    # 分析文件
    if file.storage_path.endswith('.pdf'):
        result = tender_analyzer.analyze_pdf(file.storage_path)
    else:
        result = tender_analyzer.analyze_with_docx(file.storage_path)
    
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error", "分析失败"))
    
    project_info = result["project_info"]
    
    # 创建项目
    project = Project(
        name=name or project_info.get("project_name", file.original_filename),
        tender_company=project_info.get("tender_company"),
        tender_agency=project_info.get("tender_agency"),
        bidder_name=project_info.get("bidder_name"),
        deadline=datetime.fromisoformat(project_info["deadline_parsed"]) if project_info.get("deadline_parsed") else None,
        description=f"从招标文件自动创建: {file.original_filename}"
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    
    # 创建章节
    for section_data in result["sections"]:
        section = ProjectSection(
            project_id=project.id,
            title=section_data["title"],
            section_type=section_data.get("section_type", "other"),
            order=section_data.get("order", 0)
        )
        db.add(section)
    
    # 关联招标文件
    project.managed_files.append(file)
    db.commit()
    
    return {
        "success": True,
        "project_id": project.id,
        "project_name": project.name,
        "project_info": project_info,
        "sections_count": len(result["sections"]),
        "message": "项目创建成功"
    }

# ==================== 用户管理 API ====================

@app.get("/api/users")
async def list_users(db: Session = Depends(get_db)):
    """获取用户列表"""
    users = db.query(User).filter(User.is_active == True).all()
    return [
        {
            "id": u.id,
            "username": u.username,
            "display_name": u.display_name,
            "role": u.role,
            "project_count": len(u.projects),
            "file_count": len(u.uploaded_files)
        }
        for u in users
    ]

@app.post("/api/users")
async def create_user(
    username: str = Query(...),
    display_name: Optional[str] = Query(None),
    email: Optional[str] = Query(None),
    role: str = Query("member"),
    db: Session = Depends(get_db)
):
    """创建用户"""
    existing = db.query(User).filter(User.username == username).first()
    if existing:
        raise HTTPException(status_code=409, detail="用户名已存在")
    
    user = User(
        username=username,
        display_name=display_name or username,
        email=email,
        role=role
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": user.id, "username": user.username}

@app.get("/api/users/{user_id}")
async def get_user(user_id: int, db: Session = Depends(get_db)):
    """获取用户详情"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    return {
        "id": user.id,
        "username": user.username,
        "display_name": user.display_name,
        "email": user.email,
        "role": user.role,
        "projects": [
            {"id": p.id, "name": p.name, "status": p.status}
            for p in user.projects
        ],
        "uploaded_files_count": len(user.uploaded_files)
    }

@app.get("/api/files/shared")
async def list_shared_files(
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取团队共享的参考资料（业绩/证照等）"""
    query = db.query(ManagedFile).filter(
        ManagedFile.is_shared == True,
        ManagedFile.is_reference == True
    )
    
    if category:
        query = query.filter(ManagedFile.ai_category == category)
    
    files = query.order_by(ManagedFile.created_at.desc()).all()
    
    return [
        {
            "id": f.id,
            "filename": f.original_filename,
            "category": f.ai_category or f.category,
            "tags": [{"id": t.id, "name": t.name} for t in f.tags],
            "uploader": f.uploader.display_name if f.uploader else None,
            "created_at": f.created_at.isoformat() if f.created_at else None
        }
        for f in files
    ]

# ==================== Agent 智能代理 API ====================

@app.post("/api/agent/run")
async def run_agent(
    task: str = Query(..., description="任务描述"),
    user_id: Optional[int] = Query(None),
    project_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """运行 Agent 执行任务
    
    Agent 会自主思考、规划、执行多步骤任务。
    """
    context = AgentContext(
        task_id=f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        user_id=user_id,
        project_id=project_id
    )
    
    result = await agent.run(task, context)
    return result

@app.post("/api/agent/classify-batch")
async def agent_classify_batch(
    file_ids: List[int],
    db: Session = Depends(get_db)
):
    """Agent 批量分类文件
    
    使用 Agent 自主分析每个文件并分类。
    """
    results = []
    
    for file_id in file_ids:
        file = db.query(ManagedFile).filter(ManagedFile.id == file_id).first()
        if not file:
            continue
        
        # 让 Agent 分析文件
        task = f"分析文件 '{file.original_filename}' 并判断其类别（业绩/资质证照/奖项荣誉/财务资料/团队资料/公司资料/投标文件/其他）"
        context = AgentContext(task_id=f"classify_{file_id}")
        
        result = await agent.run(task, context)
        
        if result.get("success"):
            # 从结果中提取分类
            category = "其他"
            try:
                # 尝试解析 Agent 返回的分类
                agent_result = result.get("result", {})
                if isinstance(agent_result, dict):
                    category = agent_result.get("category", "其他")
                elif isinstance(agent_result, str):
                    import re
                    json_match = re.search(r'"category"\s*:\s*"([^"]+)"', agent_result)
                    if json_match:
                        category = json_match.group(1)
            except:
                pass
            
            # 更新文件分类
            file.ai_category = category
            file.category = category
            file.is_processed = True
            
            # 添加标签
            for tag_name in [category]:
                tag = db.query(Tag).filter(Tag.name == tag_name).first()
                if not tag:
                    tag = Tag(name=tag_name, category="auto", color="#67C23A")
                    db.add(tag)
                if tag not in file.tags:
                    file.tags.append(tag)
            
            results.append({
                "file_id": file_id,
                "filename": file.original_filename,
                "category": category,
                "agent_steps": result.get("steps", 0)
            })
    
    db.commit()
    return {"results": results, "count": len(results)}

@app.post("/api/agent/analyze-tender")
async def agent_analyze_tender(
    file_id: int,
    db: Session = Depends(get_db)
):
    """Agent 分析招标文件
    
    Agent 会自主读取招标文件，提取项目信息，识别需要提交的材料。
    """
    file = db.query(ManagedFile).filter(ManagedFile.id == file_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="文件不存在")
    
    task = f"""分析招标文件 '{file.original_filename}'，完成以下任务：
1. 读取文件内容
2. 提取项目信息（项目名称、招标人、截止日期等）
3. 识别需要提交的材料类型
4. 识别文档章节结构"""
    
    context = AgentContext(
        task_id=f"tender_{file_id}",
        files=[{"id": file.id, "filename": file.original_filename}]
    )
    
    result = await agent.run(task, context)
    return result

@app.get("/api/agent/tools")
async def list_agent_tools():
    """获取 Agent 可用工具列表"""
    return [
        {"name": t.name, "description": t.description}
        for t in agent.tools.values()
    ]

# ==================== 健康检查 ====================

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "version": "0.1.0"}
    return {"status": "ok", "version": "0.1.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
