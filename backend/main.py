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

from models import get_db, init_db, ManagedFile, Tag, file_tags

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
    db: Session = Depends(get_db)
):
    """上传文件
    
    Args:
        save_to_manager: 是否存入文件管理，默认为 True
    """
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
        )
        db.add(db_file)
        db.commit()
        db.refresh(db_file)
        return {"id": db_file.id, "filename": db_file.original_filename, "size": db_file.file_size}
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

# ==================== 健康检查 ====================

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "version": "0.1.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
