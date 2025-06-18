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
import json
from pydantic import BaseModel

from database import get_db
from models import Project, Template, TemplateField, TemplateMapping
from document_processor import document_processor

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(prefix="/api/templates", tags=["templates"])

# 上传目录
UPLOAD_DIR = os.environ.get("UPLOAD_PATH", "/app/uploads")
TEMPLATE_DIR = os.path.join(UPLOAD_DIR, "templates")
os.makedirs(TEMPLATE_DIR, exist_ok=True)

# ============ 数据模型 ============

class TemplateBase(BaseModel):
    name: str
    type: str
    description: Optional[str] = None
    is_default: Optional[bool] = False

class TemplateCreate(TemplateBase):
    pass

class TemplateUpdate(TemplateBase):
    pass

class TemplateResponse(TemplateBase):
    id: int
    file_path: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True

class FieldBase(BaseModel):
    field_name: str
    field_key: str
    field_type: str
    placeholder: str
    is_required: Optional[bool] = False
    description: Optional[str] = None

class FieldCreate(FieldBase):
    position: Optional[Dict[str, Any]] = None

class FieldResponse(FieldBase):
    id: int
    template_id: int
    position: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True

class MappingCreate(BaseModel):
    template_id: int
    field_id: int
    value: str

class MappingUpdate(BaseModel):
    value: str

class MappingResponse(BaseModel):
    id: int
    project_id: int
    template_id: int
    field_id: int
    value: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True

# ============ API端点 ============

@router.post("", response_model=TemplateResponse)
async def create_template(
    name: str = Form(...),
    template_type: str = Form(...),
    description: Optional[str] = Form(None),
    is_default: bool = Form(False),
    file: UploadFile = File(...),
    analyze: bool = Form(False),
    db: Session = Depends(get_db)
):
    """上传新模板"""
    try:
        # 生成唯一文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        ext = os.path.splitext(file.filename)[1]
        new_filename = f"template_{template_type}_{timestamp}_{unique_id}{ext}"
        
        # 保存文件
        file_path = os.path.join(TEMPLATE_DIR, new_filename)
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # 创建模板记录
        template = Template(
            name=name,
            type=template_type,
            description=description,
            file_path=file_path,
            is_default=is_default
        )
        
        db.add(template)
        db.commit()
        db.refresh(template)
        
        # 如果需要分析字段
        if analyze:
            try:
                # 分析模板中的字段
                fields = await document_processor.analyze_template_fields(file_path)
                
                # 保存字段信息
                for field_info in fields:
                    field = TemplateField(
                        template_id=template.id,
                        field_name=field_info.get("field_name"),
                        field_key=field_info.get("field_key"),
                        field_type=field_info.get("field_type", "text"),
                        placeholder=field_info.get("placeholder"),
                        is_required=False  # 默认非必填
                    )
                    db.add(field)
                
                db.commit()
            except Exception as analyze_err:
                logger.error(f"分析模板字段失败: {str(analyze_err)}")
        
        return template
        
    except Exception as e:
        logger.error(f"上传模板失败: {str(e)}")
        db.rollback()
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"上传模板失败: {str(e)}")

@router.get("", response_model=List[TemplateResponse])
async def get_templates(
    template_type: Optional[str] = None,
    is_default: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """获取模板列表"""
    try:
        query = db.query(Template)
        
        if template_type:
            query = query.filter(Template.type == template_type)
        
        if is_default is not None:
            query = query.filter(Template.is_default == is_default)
        
        return query.all()
        
    except Exception as e:
        logger.error(f"获取模板列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取模板列表失败: {str(e)}")

@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(template_id: int, db: Session = Depends(get_db)):
    """获取模板详情"""
    try:
        template = db.query(Template).filter(Template.id == template_id).first()
        if not template:
            raise HTTPException(status_code=404, detail="模板不存在")
        
        return template
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取模板详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取模板详情失败: {str(e)}")

@router.put("/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: int,
    template_data: TemplateUpdate,
    db: Session = Depends(get_db)
):
    """更新模板信息"""
    try:
        template = db.query(Template).filter(Template.id == template_id).first()
        if not template:
            raise HTTPException(status_code=404, detail="模板不存在")
        
        # 更新字段
        for key, value in template_data.dict(exclude_unset=True).items():
            setattr(template, key, value)
        
        template.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(template)
        
        return template
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新模板失败: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新模板失败: {str(e)}")

@router.delete("/{template_id}")
async def delete_template(template_id: int, db: Session = Depends(get_db)):
    """删除模板"""
    try:
        template = db.query(Template).filter(Template.id == template_id).first()
        if not template:
            raise HTTPException(status_code=404, detail="模板不存在")
        
        # 删除文件
        if template.file_path and os.path.exists(template.file_path):
            os.remove(template.file_path)
        
        # 删除数据库记录(关联的字段会通过cascade自动删除)
        db.delete(template)
        db.commit()
        
        return {"message": "模板删除成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除模板失败: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除模板失败: {str(e)}")

@router.post("/{template_id}/analyze", response_model=List[FieldResponse])
async def analyze_template(template_id: int, db: Session = Depends(get_db)):
    """分析模板中的字段"""
    try:
        template = db.query(Template).filter(Template.id == template_id).first()
        if not template:
            raise HTTPException(status_code=404, detail="模板不存在")
        
        if not template.file_path or not os.path.exists(template.file_path):
            raise HTTPException(status_code=404, detail="模板文件不存在")
        
        # 分析模板字段
        field_infos = await document_processor.analyze_template_fields(template.file_path)
        
        # 删除现有字段
        db.query(TemplateField).filter(TemplateField.template_id == template_id).delete()
        db.commit()
        
        # 创建新字段
        created_fields = []
        for field_info in field_infos:
            field = TemplateField(
                template_id=template.id,
                field_name=field_info.get("field_name"),
                field_key=field_info.get("field_key"),
                field_type=field_info.get("field_type", "text"),
                placeholder=field_info.get("placeholder"),
                is_required=False  # 默认非必填
            )
            db.add(field)
            db.flush()  # 获取ID
            db.refresh(field)
            created_fields.append(field)
        
        db.commit()
        
        return created_fields
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"分析模板字段失败: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"分析模板字段失败: {str(e)}")

@router.get("/{template_id}/fields", response_model=List[FieldResponse])
async def get_template_fields(template_id: int, db: Session = Depends(get_db)):
    """获取模板字段列表"""
    try:
        template = db.query(Template).filter(Template.id == template_id).first()
        if not template:
            raise HTTPException(status_code=404, detail="模板不存在")
        
        fields = db.query(TemplateField).filter(
            TemplateField.template_id == template_id
        ).all()
        
        return fields
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取模板字段失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取模板字段失败: {str(e)}")

@router.post("/{template_id}/fields", response_model=FieldResponse)
async def create_template_field(
    template_id: int,
    field_data: FieldCreate,
    db: Session = Depends(get_db)
):
    """创建模板字段"""
    try:
        template = db.query(Template).filter(Template.id == template_id).first()
        if not template:
            raise HTTPException(status_code=404, detail="模板不存在")
        
        field = TemplateField(
            template_id=template_id,
            **field_data.dict()
        )
        
        db.add(field)
        db.commit()
        db.refresh(field)
        
        return field
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建模板字段失败: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建模板字段失败: {str(e)}")

@router.put("/fields/{field_id}", response_model=FieldResponse)
async def update_field(
    field_id: int,
    field_data: FieldBase,
    db: Session = Depends(get_db)
):
    """更新模板字段"""
    try:
        field = db.query(TemplateField).filter(TemplateField.id == field_id).first()
        if not field:
            raise HTTPException(status_code=404, detail="字段不存在")
        
        # 更新字段
        for key, value in field_data.dict(exclude_unset=True).items():
            setattr(field, key, value)
        
        field.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(field)
        
        return field
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新字段失败: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新字段失败: {str(e)}")

@router.delete("/fields/{field_id}")
async def delete_field(field_id: int, db: Session = Depends(get_db)):
    """删除模板字段"""
    try:
        field = db.query(TemplateField).filter(TemplateField.id == field_id).first()
        if not field:
            raise HTTPException(status_code=404, detail="字段不存在")
        
        db.delete(field)
        db.commit()
        
        return {"message": "字段删除成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除字段失败: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除字段失败: {str(e)}")

@router.post("/apply", response_model=Dict[str, Any])
async def apply_template(
    template_id: int,
    project_id: int,
    field_values: Dict[str, str],
    output_filename: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """应用模板，填充字段值"""
    try:
        # 检查项目和模板是否存在
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        template = db.query(Template).filter(Template.id == template_id).first()
        if not template:
            raise HTTPException(status_code=404, detail="模板不存在")
        
        if not template.file_path or not os.path.exists(template.file_path):
            raise HTTPException(status_code=404, detail="模板文件不存在")
        
        # 获取模板的所有字段
        fields = db.query(TemplateField).filter(
            TemplateField.template_id == template_id
        ).all()
        
        field_dict = {field.field_key: field for field in fields}
        
        # 创建或更新字段映射
        for field_key, value in field_values.items():
            if field_key in field_dict:
                field = field_dict[field_key]
                
                # 检查映射是否存在
                mapping = db.query(TemplateMapping).filter(
                    TemplateMapping.project_id == project_id,
                    TemplateMapping.template_id == template_id,
                    TemplateMapping.field_id == field.id
                ).first()
                
                if mapping:
                    # 更新现有映射
                    mapping.value = value
                    mapping.updated_at = datetime.utcnow()
                else:
                    # 创建新映射
                    mapping = TemplateMapping(
                        project_id=project_id,
                        template_id=template_id,
                        field_id=field.id,
                        value=value
                    )
                    db.add(mapping)
        
        db.commit()
        
        # 生成输出文件名
        if not output_filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = os.path.basename(template.file_path)
            name, ext = os.path.splitext(base_name)
            output_filename = f"{name}_filled_{timestamp}{ext}"
        
        # 应用模板
        filled_path = await document_processor.fill_template(
            template.file_path,
            field_values,
            output_filename
        )
        
        # 构建下载URL
        download_url = f"/api/templates/download/{os.path.basename(filled_path)}"
        
        return {
            "success": True,
            "message": "模板应用成功",
            "filled_path": filled_path,
            "download_url": download_url
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"应用模板失败: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"应用模板失败: {str(e)}")

@router.get("/download/{filename}")
async def download_filled_template(filename: str):
    """下载填充后的模板"""
    try:
        # 构建文件路径
        file_path = os.path.join(os.environ.get("GENERATED_DOCS_PATH", "/app/generated_docs"), filename)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="文件不存在")
        
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"下载填充模板失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"下载填充模板失败: {str(e)}")

@router.get("/projects/{project_id}/mappings", response_model=List[Dict[str, Any]])
async def get_project_mappings(project_id: int, db: Session = Depends(get_db)):
    """获取项目的字段映射"""
    try:
        # 检查项目是否存在
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        # 查询映射记录
        mappings = db.query(TemplateMapping).filter(
            TemplateMapping.project_id == project_id
        ).all()
        
        # 获取字段和模板信息
        result = []
        for mapping in mappings:
            field = db.query(TemplateField).filter(
                TemplateField.id == mapping.field_id
            ).first()
            
            template = db.query(Template).filter(
                Template.id == mapping.template_id
            ).first()
            
            if field and template:
                result.append({
                    "id": mapping.id,
                    "project_id": project_id,
                    "template_id": template.id,
                    "template_name": template.name,
                    "template_type": template.type,
                    "field_id": field.id,
                    "field_name": field.field_name,
                    "field_key": field.field_key,
                    "field_type": field.field_type,
                    "value": mapping.value,
                    "created_at": mapping.created_at,
                    "updated_at": mapping.updated_at
                })
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取项目字段映射失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取项目字段映射失败: {str(e)}")

# 导出API路由器供main.py使用
def setup_router(app):
    app.include_router(router) 