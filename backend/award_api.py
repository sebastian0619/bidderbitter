"""
奖项管理API
"""
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import Optional, List
import logging
import os
from datetime import datetime

from database import get_db
from models import Award

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/stats")
async def get_award_stats(db: Session = Depends(get_db)):
    """获取奖项统计数据"""
    try:
        total_awards = db.query(Award).count()
        verified_awards = db.query(Award).filter(Award.is_verified == True).count()
        
        # 按年份统计
        yearly_stats = db.query(
            Award.year,
            func.count(Award.id).label('count')
        ).group_by(Award.year).order_by(desc(Award.year)).limit(5).all()
        
        # 按品牌统计
        brand_stats = db.query(
            Award.brand,
            func.count(Award.id).label('count')
        ).group_by(Award.brand).order_by(desc(func.count(Award.id))).limit(5).all()
        
        return {
            "success": True,
            "stats": {
                "total_awards": total_awards,
                "verified_awards": verified_awards,
                "yearly_distribution": [
                    {"year": stat.year, "count": stat.count} 
                    for stat in yearly_stats
                ],
                "brand_distribution": [
                    {"brand": stat.brand, "count": stat.count} 
                    for stat in brand_stats if stat.brand
                ]
            }
        }
        
    except Exception as e:
        logger.error(f"获取奖项统计失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取统计数据失败: {str(e)}")

@router.get("/list")
async def list_awards(
    page: int = 1,
    page_size: int = 20,
    search: Optional[str] = None,
    brand: Optional[str] = None,
    year: Optional[int] = None,
    business_type: Optional[str] = None,
    is_verified: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """获取奖项列表"""
    try:
        query = db.query(Award)
        
        # 搜索过滤
        if search:
            query = query.filter(
                Award.title.ilike(f'%{search}%') |
                Award.description.ilike(f'%{search}%')
            )
        
        # 品牌过滤
        if brand:
            query = query.filter(Award.brand == brand)
        
        # 年份过滤
        if year:
            query = query.filter(Award.year == year)
        
        # 业务类型过滤
        if business_type:
            query = query.filter(Award.business_type == business_type)
        
        # 验证状态过滤
        if is_verified is not None:
            query = query.filter(Award.is_verified == is_verified)
        
        # 总数
        total = query.count()
        
        # 分页
        offset = (page - 1) * page_size
        awards = query.order_by(desc(Award.created_at)).offset(offset).limit(page_size).all()
        
        return {
            "success": True,
            "awards": [
                {
                    "id": award.id,
                    "title": award.title,
                    "brand": award.brand,
                    "year": award.year,
                    "business_type": award.business_type,
                    "description": award.description,
                    "is_verified": award.is_verified,
                    "source_type": getattr(award, 'source_type', 'upload'),
                    "confidence_score": getattr(award, 'confidence_score', None),
                    "screenshot_path": getattr(award, 'screenshot_path', None),
                    "created_at": award.created_at.isoformat()
                }
                for award in awards
            ],
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "pages": (total + page_size - 1) // page_size
            }
        }
        
    except Exception as e:
        logger.error(f"获取奖项列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取奖项列表失败: {str(e)}")

@router.post("/upload")
async def upload_award_file(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    brand: Optional[str] = Form(None),
    business_type: Optional[str] = Form(None),
    year: Optional[int] = Form(None),
    enable_ai_analysis: bool = Form(True),
    db: Session = Depends(get_db)
):
    """上传奖项文件并进行AI分析"""
    try:
        # 保存文件
        upload_dir = os.path.join(os.path.dirname(__file__), "uploads", "awards")
        os.makedirs(upload_dir, exist_ok=True)
        
        file_path = os.path.join(upload_dir, f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}")
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # TODO: 集成AI分析
        # 这里应该调用AI服务进行文档分析
        
        # 创建奖项记录
        award = Award(
            title=title or "待AI分析",
            brand=brand or "待AI分析",
            year=year or datetime.now().year,
            business_type=business_type or "待AI分析",
            description="通过文件上传创建",
            is_verified=False
        )
        
        db.add(award)
        db.commit()
        db.refresh(award)
        
        logger.info(f"奖项文件上传成功: {file.filename}")
        
        return {
            "success": True,
            "message": "奖项文件上传成功",
            "award_id": award.id
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"上传奖项文件失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")

@router.post("/upload/batch")
async def upload_award_files_batch(
    files: List[UploadFile] = File(...),
    titles: Optional[str] = Form(None),  # JSON数组，每个文件的标题
    brand: Optional[str] = Form(None),
    business_type: Optional[str] = Form(None),
    year: Optional[int] = Form(None),
    enable_ai_analysis: bool = Form(True),
    db: Session = Depends(get_db)
):
    """批量上传奖项文件并进行AI分析"""
    try:
        import json
        
        uploaded_files = []
        failed_files = []
        created_awards = []
        
        # 解析标题
        titles_list = []
        if titles:
            try:
                titles_list = json.loads(titles)
            except:
                titles_list = []
        
        # 保存文件目录
        upload_dir = os.path.join(os.path.dirname(__file__), "uploads", "awards")
        os.makedirs(upload_dir, exist_ok=True)
        
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
                
                if file_size > 100 * 1024 * 1024:  # 100MB限制
                    failed_files.append({
                        "filename": file.filename,
                        "error": "文件大小超过限制(100MB)"
                    })
                    continue
                
                # 生成文件路径
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                file_path = os.path.join(upload_dir, f"{timestamp}_{i}_{file.filename}")
                
                # 保存文件
                with open(file_path, "wb") as buffer:
                    buffer.write(content)
                
                # 确定标题
                title = titles_list[i] if i < len(titles_list) else os.path.splitext(file.filename)[0]
                
                # 创建奖项记录
                award = Award(
                    title=title,
                    brand=brand or "待AI分析",
                    year=year or datetime.now().year,
                    business_type=business_type or "待AI分析",
                    description=f"通过批量文件上传创建 - {file.filename}",
                    is_verified=False,
                    source_document=file_path
                )
                
                db.add(award)
                db.flush()  # 获取ID
                
                # AI分析结果
                ai_analysis_result = None
                if enable_ai_analysis:
                    try:
                        # TODO: 集成AI分析服务
                        # 这里应该调用AI服务进行文档分析
                        # analysis_result = await ai_service.analyze_award_document(file_path)
                        pass
                    except Exception as ai_err:
                        logger.warning(f"AI分析失败: {ai_err}")
                
                created_awards.append({
                    "id": award.id,
                    "title": award.title,
                    "filename": file.filename
                })
                
                uploaded_files.append({
                    "filename": file.filename,
                    "file_size": file_size,
                    "file_path": file_path,
                    "award_id": award.id,
                    "title": title,
                    "ai_analysis": ai_analysis_result
                })
                
                logger.info(f"批量奖项文件上传成功: {file.filename}")
                
            except Exception as file_err:
                failed_files.append({
                    "filename": file.filename,
                    "error": str(file_err)
                })
                logger.error(f"上传奖项文件失败 {file.filename}: {file_err}")
        
        db.commit()
        
        return {
            "success": True,
            "message": f"批量上传完成: {len(uploaded_files)} 成功, {len(failed_files)} 失败",
            "uploaded_files": uploaded_files,
            "failed_files": failed_files,
            "created_awards": created_awards,
            "ai_analysis": {
                "enabled": enable_ai_analysis
            },
            "summary": {
                "total": len(files),
                "success": len(uploaded_files),
                "failed": len(failed_files),
                "awards_created": len(created_awards)
            }
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"批量上传奖项文件失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"批量上传失败: {str(e)}")

@router.patch("/{award_id}/verify")
async def verify_award(
    award_id: int,
    db: Session = Depends(get_db)
):
    """验证奖项记录"""
    try:
        award = db.query(Award).filter(Award.id == award_id).first()
        if not award:
            raise HTTPException(status_code=404, detail="奖项记录不存在")
        
        award.is_verified = True
        db.commit()
        
        return {
            "success": True,
            "message": "奖项记录已验证"
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"验证奖项记录失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"验证失败: {str(e)}")

@router.delete("/{award_id}")
async def delete_award(
    award_id: int,
    db: Session = Depends(get_db)
):
    """删除奖项记录"""
    try:
        award = db.query(Award).filter(Award.id == award_id).first()
        if not award:
            raise HTTPException(status_code=404, detail="奖项记录不存在")
        
        db.delete(award)
        db.commit()
        
        return {
            "success": True,
            "message": "奖项记录已删除"
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"删除奖项记录失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")

# 实时浏览器相关API
@router.post("/browser/screenshot")
async def take_browser_screenshot(
    url: str,
    db: Session = Depends(get_db)
):
    """浏览器截图功能"""
    try:
        # TODO: 实现浏览器截图功能
        # 这里应该使用Selenium或类似工具进行网页截图
        
        logger.info(f"浏览器截图请求: {url}")
        
        return {
            "success": True,
            "message": "截图功能开发中",
            "screenshot_path": None
        }
        
    except Exception as e:
        logger.error(f"浏览器截图失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"截图失败: {str(e)}")

@router.post("/browser/save-content")
async def save_browser_content(
    content_data: dict,
    db: Session = Depends(get_db)
):
    """保存浏览器选中的内容到系统"""
    try:
        # TODO: 实现内容保存功能
        
        logger.info(f"保存浏览器内容: {content_data.get('title', 'Unknown')}")
        
        return {
            "success": True,
            "message": "内容保存功能开发中"
        }
        
    except Exception as e:
        logger.error(f"保存浏览器内容失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"保存失败: {str(e)}")

# AI自动检索相关API
@router.post("/auto-search")
async def start_auto_search(
    search_params: dict,
    db: Session = Depends(get_db)
):
    """启动AI自动检索奖项"""
    try:
        # TODO: 实现AI自动检索功能
        
        logger.info(f"AI自动检索请求: {search_params}")
        
        return {
            "success": True,
            "message": "AI自动检索功能开发中",
            "task_id": "mock_task_id"
        }
        
    except Exception as e:
        logger.error(f"AI自动检索失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"检索失败: {str(e)}") 