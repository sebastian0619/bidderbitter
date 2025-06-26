from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import List, Optional, Dict, Any
import json
import asyncio
from datetime import datetime
import time

from database import get_db
from models import (
    DataSource, SearchTask, SearchResult, Award, Brand
)

router = APIRouter(prefix="/api/search", tags=["AI自动检索"])

# 数据源管理
@router.get("/sources")
async def get_data_sources(db: Session = Depends(get_db)):
    """获取所有数据源"""
    sources = db.query(DataSource).filter(DataSource.is_active == True).all()
    return sources

@router.post("/sources")
async def create_data_source(source_data: dict, db: Session = Depends(get_db)):
    """创建数据源"""
    db_source = DataSource(**source_data)
    db.add(db_source)
    db.commit()
    db.refresh(db_source)
    return db_source

# 搜索任务管理
@router.get("/tasks")
async def get_search_tasks(
    status: Optional[str] = Query(None, description="任务状态"),
    db: Session = Depends(get_db)
):
    """获取搜索任务列表"""
    query = db.query(SearchTask)
    if status:
        query = query.filter(SearchTask.status == status)
    tasks = query.order_by(SearchTask.created_at.desc()).all()
    return tasks

@router.post("/tasks")
async def create_search_task(
    task_data: dict,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """创建搜索任务"""
    # 验证数据源
    data_source = db.query(DataSource).filter(
        DataSource.id == task_data["data_source_id"]
    ).first()
    if not data_source:
        raise HTTPException(status_code=404, detail="数据源不存在")
    
    # 创建搜索任务
    db_task = SearchTask(**task_data)
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    
    # 在后台执行搜索任务
    background_tasks.add_task(execute_search_task, db_task.id)
    
    return db_task

@router.get("/tasks/{task_id}")
async def get_search_task(task_id: int, db: Session = Depends(get_db)):
    """获取搜索任务详情"""
    task = db.query(SearchTask).filter(SearchTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="搜索任务不存在")
    
    # 获取搜索结果
    results = db.query(SearchResult).filter(
        SearchResult.search_task_id == task_id
    ).order_by(SearchResult.created_at.desc()).all()
    
    return {
        "task": task,
        "results": results
    }

@router.delete("/tasks/{task_id}")
async def delete_search_task(task_id: int, db: Session = Depends(get_db)):
    """删除搜索任务"""
    task = db.query(SearchTask).filter(SearchTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="搜索任务不存在")
    
    # 删除相关搜索结果
    db.query(SearchResult).filter(SearchResult.search_task_id == task_id).delete()
    
    # 删除任务
    db.delete(task)
    db.commit()
    
    return {"message": "搜索任务已删除"}

# 搜索结果管理
@router.get("/results")
async def get_search_results(
    task_id: Optional[int] = Query(None, description="任务ID"),
    status: Optional[str] = Query(None, description="结果状态"),
    db: Session = Depends(get_db)
):
    """获取搜索结果"""
    query = db.query(SearchResult)
    if task_id:
        query = query.filter(SearchResult.search_task_id == task_id)
    if status:
        query = query.filter(SearchResult.status == status)
    
    results = query.order_by(SearchResult.created_at.desc()).all()
    return results

@router.post("/results/{result_id}/import")
async def import_search_result(
    result_id: int,
    db: Session = Depends(get_db)
):
    """导入搜索结果到奖项库"""
    result = db.query(SearchResult).filter(SearchResult.id == result_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="搜索结果不存在")
    
    if result.status == "imported":
        raise HTTPException(status_code=400, detail="该结果已导入")
    
    # 创建奖项记录
    award_data = {
        "title": result.award_name,
        "brand": result.search_task.data_source.name,
        "year": result.award_year,
        "business_type": result.business_field,
        "description": f"来自{result.search_task.data_source.name}的搜索结果",
        "source_url": result.source_url,
        "is_verified": False,
        "is_manual_input": False
    }
    
    db_award = Award(**award_data)
    db.add(db_award)
    db.commit()
    db.refresh(db_award)
    
    # 更新搜索结果状态
    result.status = "imported"
    result.award_id = db_award.id
    db.commit()
    
    return {"message": "搜索结果已导入", "award_id": db_award.id}

# 智能搜索功能
@router.post("/smart-search")
async def smart_search_awards(
    search_params: dict,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """智能搜索奖项"""
    law_firm_name = search_params.get("law_firm_name")
    search_year = search_params.get("search_year")
    business_field = search_params.get("business_field")
    
    if not law_firm_name or not search_year:
        raise HTTPException(status_code=400, detail="律师事务所名称和搜索年份为必填项")
    
    # 创建搜索任务
    task_data = {
        "task_name": f"搜索{law_firm_name}在{search_year}年的奖项",
        "data_source_id": 1,  # 默认使用钱伯斯数据源
        "law_firm_name": law_firm_name,
        "search_year": search_year,
        "business_field": business_field,
        "search_keywords": [law_firm_name, str(search_year), business_field] if business_field else [law_firm_name, str(search_year)]
    }
    
    db_task = SearchTask(**task_data)
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    
    # 在后台执行搜索
    background_tasks.add_task(execute_search_task, db_task.id)
    
    return db_task

# 后台任务执行函数
async def execute_search_task(task_id: int):
    """执行搜索任务"""
    from database import SessionLocal
    
    db = SessionLocal()
    try:
        task = db.query(SearchTask).filter(SearchTask.id == task_id).first()
        if not task:
            return
        
        # 更新任务状态
        task.status = "running"
        task.started_at = datetime.now()
        db.commit()
        
        # 根据数据源类型执行不同的搜索策略
        if task.data_source.type == "chambers":
            await search_chambers(task, db)
        elif task.data_source.type == "legal500":
            await search_legal500(task, db)
        else:
            # 通用搜索
            await search_generic(task, db)
        
        # 更新任务状态
        task.status = "completed"
        task.completed_at = datetime.now()
        db.commit()
        
    except Exception as e:
        # 更新任务状态为失败
        task.status = "failed"
        task.error_message = str(e)
        task.completed_at = datetime.now()
        db.commit()
    finally:
        db.close()

async def search_chambers(task: SearchTask, db: Session):
    """搜索钱伯斯网站"""
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    
    # 配置Chrome选项
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # 访问钱伯斯搜索页面
        search_url = f"https://chambers.com/legal-guide/search?q={task.law_firm_name}"
        driver.get(search_url)
        
        # 等待页面加载
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "search-results"))
        )
        
        # 查找律师事务所
        firm_elements = driver.find_elements(By.CSS_SELECTOR, ".firm-item")
        
        for firm_element in firm_elements:
            firm_name = firm_element.find_element(By.CSS_SELECTOR, ".firm-name").text
            
            if task.law_firm_name.lower() in firm_name.lower():
                # 点击进入律师事务所详情页
                firm_element.click()
                
                # 等待详情页加载
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "firm-details"))
                )
                
                # 查找奖项信息
                award_elements = driver.find_elements(By.CSS_SELECTOR, ".award-item")
                
                for award_element in award_elements:
                    try:
                        award_name = award_element.find_element(By.CSS_SELECTOR, ".award-name").text
                        award_year = award_element.find_element(By.CSS_SELECTOR, ".award-year").text
                        business_field = award_element.find_element(By.CSS_SELECTOR, ".business-field").text
                        ranking = award_element.find_element(By.CSS_SELECTOR, ".ranking").text
                        
                        # 检查年份匹配
                        if str(task.search_year) in award_year:
                            # 创建搜索结果
                            result_data = {
                                "search_task_id": task.id,
                                "raw_data": {
                                    "award_name": award_name,
                                    "award_year": award_year,
                                    "business_field": business_field,
                                    "ranking": ranking
                                },
                                "source_url": driver.current_url,
                                "law_firm_name": task.law_firm_name,
                                "award_name": award_name,
                                "award_year": int(award_year),
                                "business_field": business_field,
                                "ranking": ranking,
                                "status": "pending"
                            }
                            
                            db_result = SearchResult(**result_data)
                            db.add(db_result)
                            task.total_found += 1
                            
                    except Exception as e:
                        task.error_count += 1
                        continue
                
                break
        
        db.commit()
        
    finally:
        driver.quit()

async def search_legal500(task: SearchTask, db: Session):
    """搜索Legal 500网站"""
    # 实现Legal 500的搜索逻辑
    pass

async def search_generic(task: SearchTask, db: Session):
    """通用搜索逻辑"""
    # 实现通用搜索逻辑
    pass 