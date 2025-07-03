"""
业绩管理API
"""
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import Optional, List, Dict, Any
import logging
import os
from datetime import datetime

from database import get_db
from models import Performance, PerformanceFile, SystemSettings, AITask
from schemas import PerformanceCreate, PerformanceUpdate, PerformanceResponse
from config_manager import config_manager
from ai_service import create_ai_task, update_ai_task

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/stats")
async def get_performance_stats(db: Session = Depends(get_db)):
    """获取业绩统计数据"""
    try:
        total_performances = db.query(Performance).count()
        verified_performances = db.query(Performance).filter(Performance.is_verified == True).count()
        manual_input_performances = db.query(Performance).filter(Performance.is_manual_input == True).count()
        
        # 按年份统计
        yearly_stats = db.query(
            Performance.year,
            func.count(Performance.id).label('count')
        ).group_by(Performance.year).order_by(desc(Performance.year)).limit(5).all()
        
        # 按业务领域统计
        field_stats = db.query(
            Performance.business_field,
            func.count(Performance.id).label('count')
        ).group_by(Performance.business_field).order_by(desc(func.count(Performance.id))).limit(5).all()
        
        return {
            "success": True,
            "stats": {
                "total_performances": total_performances,
                "verified_performances": verified_performances,
                "manual_input_performances": manual_input_performances,
                "yearly_distribution": [
                    {"year": stat.year, "count": stat.count} 
                    for stat in yearly_stats
                ],
                "field_distribution": [
                    {"field": stat.business_field, "count": stat.count} 
                    for stat in field_stats if stat.business_field
                ]
            }
        }
        
    except Exception as e:
        logger.error(f"获取业绩统计失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取统计数据失败: {str(e)}")

@router.get("/list")
async def list_performances(
    page: int = 1,
    page_size: int = 20,
    search: Optional[str] = None,
    business_field: Optional[str] = None,
    year: Optional[int] = None,
    is_verified: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """获取业绩列表"""
    try:
        query = db.query(Performance)
        
        # 搜索过滤
        if search:
            query = query.filter(
                Performance.project_name.ilike(f'%{search}%') |
                Performance.client_name.ilike(f'%{search}%') |
                Performance.description.ilike(f'%{search}%')
            )
        
        # 业务领域过滤
        if business_field:
            query = query.filter(Performance.business_field == business_field)
        
        # 年份过滤
        if year:
            query = query.filter(Performance.year == year)
        
        # 验证状态过滤
        if is_verified is not None:
            query = query.filter(Performance.is_verified == is_verified)
        
        # 总数
        total = query.count()
        
        # 分页
        offset = (page - 1) * page_size
        performances = query.order_by(desc(Performance.created_at)).offset(offset).limit(page_size).all()
        
        return {
            "success": True,
            "performances": [
                {
                    "id": perf.id,
                    "project_name": perf.project_name,
                    "client_name": perf.client_name,
                    "project_type": perf.project_type,
                    "business_field": perf.business_field,
                    "year": perf.year,
                    "contract_amount": perf.contract_amount,
                    "currency": perf.currency,
                    "start_date": perf.start_date.isoformat() if perf.start_date else None,
                    "end_date": perf.end_date.isoformat() if perf.end_date else None,
                    "description": perf.description,
                    "confidence_score": perf.confidence_score,
                    "ai_analysis_status": getattr(perf, 'ai_analysis_status', 'pending'),  # 兼容旧数据
                    "is_verified": perf.is_verified,
                    "is_manual_input": perf.is_manual_input,
                    "source_document": perf.source_document,
                    "created_at": perf.created_at.isoformat()
                }
                for perf in performances
            ],
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "pages": (total + page_size - 1) // page_size
            }
        }
        
    except Exception as e:
        logger.error(f"获取业绩列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取业绩列表失败: {str(e)}")

@router.post("/create")
async def create_performance(
    performance_data: dict,
    db: Session = Depends(get_db)
):
    """手动创建业绩记录"""
    try:
        # 创建业绩记录
        performance = Performance(
            project_name=performance_data.get("project_name"),
            client_name=performance_data.get("client_name"),
            project_type=performance_data.get("project_type"),
            business_field=performance_data.get("business_field"),
            year=int(performance_data.get("year")),
            contract_amount=performance_data.get("contract_amount"),
            currency=performance_data.get("currency", "CNY"),
            start_date=datetime.fromisoformat(performance_data["start_date"]) if performance_data.get("start_date") else None,
            end_date=datetime.fromisoformat(performance_data["end_date"]) if performance_data.get("end_date") else None,
            description=performance_data.get("description"),
            is_manual_input=True,
            is_verified=True  # 手动创建的默认为已验证
        )
        
        db.add(performance)
        db.commit()
        db.refresh(performance)
        
        logger.info(f"手动创建业绩记录成功: {performance.project_name}")
        
        return {
            "success": True,
            "message": "业绩记录创建成功",
            "performance_id": performance.id
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"创建业绩记录失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建业绩记录失败: {str(e)}")

@router.post("/upload")
async def upload_performance_files(
    files: List[UploadFile] = File(...),
    project_name: Optional[str] = Form(None),
    client_name: Optional[str] = Form(None),
    business_field: Optional[str] = Form(None),
    enable_ai_analysis: bool = Form(True),
    enable_vision_analysis: bool = Form(True),
    db: Session = Depends(get_db)
):
    """上传业绩文件（支持多文件）并为每个文件创建独立的业绩记录"""
    uploaded_performances = []
    uploaded_files = []
    
    try:
        # 保存文件目录
        upload_dir = os.path.join(os.path.dirname(__file__), "uploads", "performances")
        os.makedirs(upload_dir, exist_ok=True)
        
        # 为每个文件创建独立的业绩记录
        for i, file in enumerate(files):
            # 生成唯一文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            file_path = os.path.join(upload_dir, f"{timestamp}_{i}_{file.filename}")
            
            # 保存文件
            with open(file_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
            
            logger.info(f"✅ 业绩文件保存成功: {file_path}")
            
            # 为每个文件创建独立的业绩记录
            # 使用去除扩展名的文件名作为临时项目名称
            temp_project_name = os.path.splitext(file.filename)[0] if not project_name else f"{project_name}_{i+1}"
            
            performance = Performance(
                project_name=temp_project_name,
                client_name=client_name or "待AI分析",
                project_type="重大个案(非诉)",  # 使用新的项目类型名称
                business_field=business_field or "待AI分析",
                year=datetime.now().year,
                is_manual_input=False,
                is_verified=False,
                confidence_score=0.0,
                description=f"文件 '{file.filename}' 已上传，等待AI分析...",
                source_document=file_path,
                ai_analysis_status="pending"  # 添加分析状态标记
            )
            
            db.add(performance)
            db.commit()  # 立即提交每个记录
            db.refresh(performance)
            
            # 创建文件记录
            performance_file = PerformanceFile(
                performance_id=performance.id,
                file_path=file_path,
                file_type="contract" if "合同" in file.filename or "contract" in file.filename.lower() else "supporting_doc",
                file_name=file.filename,
                file_size=len(content)
            )
            
            db.add(performance_file)
            db.commit()
            
            # 创建AI分析任务
            task_id = None
            if enable_ai_analysis:
                task_id = create_ai_task(db, performance.id, "performance")
                logger.info(f"📋 AI任务已创建: 任务ID={task_id}, 业绩ID={performance.id}")
            
            uploaded_performances.append({
                "id": performance.id,
                "project_name": performance.project_name,
                "file_name": file.filename,
                "ai_analysis_status": "pending",
                "task_id": task_id  # 返回任务ID
            })
            uploaded_files.append(file.filename)
            
            logger.info(f"✅ 业绩记录已创建: ID={performance.id}, 项目名称={performance.project_name}")
        
    except Exception as e:
        logger.error(f"❌ 文件保存失败: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")
    
    # 异步进行AI分析（在后台为每个记录分别处理）
    if enable_ai_analysis:
        # 启动后台任务进行AI分析
        import asyncio
        asyncio.create_task(
            analyze_performances_in_background(
                [perf["id"] for perf in uploaded_performances],
                enable_vision_analysis,
                db
            )
        )
        
        logger.info(f"🤖 已启动后台AI分析任务，共{len(uploaded_performances)}个文件")
    
    # 立即返回结果，不等待AI分析完成
    return {
        "success": True,
        "message": f"成功上传 {len(files)} 个文件，已创建 {len(uploaded_performances)} 条业绩记录",
        "performances": uploaded_performances,
        "uploaded_files": uploaded_files,
        "ai_analysis": {
            "enabled": enable_ai_analysis,
            "status": "background_processing" if enable_ai_analysis else "disabled",
            "total_files": len(files)
        }
    }

async def analyze_performances_in_background(performance_ids: List[int], enable_vision_analysis: bool, db: Session):
    """后台异步分析业绩记录"""
    try:
        from ai_service import ai_service
        
        if not ai_service.enable_ai:
            logger.warning("AI服务未启用，跳过后台分析")
            return
        
        logger.info(f"🤖 开始后台AI分析，共{len(performance_ids)}条记录")
        
        for performance_id in performance_ids:
            task_id = None
            try:
                # 重新获取performance记录
                performance = db.query(Performance).filter(Performance.id == performance_id).first()
                
                if not performance or not performance.source_document:
                    logger.warning(f"⚠️ 业绩记录或文件不存在: {performance_id}")
                    continue
                
                # 查找对应的AI任务
                task = db.query(AITask).filter(
                    AITask.file_id == performance_id,
                    AITask.file_type == "performance"
                ).first()
                
                if task:
                    task_id = task.id
                    # 更新AI任务状态为processing
                    update_ai_task(db, task_id, "processing")
                
                # 更新状态为正在分析
                performance.ai_analysis_status = "analyzing"
                performance.description = f"正在进行AI分析..."
                db.commit()
                
                logger.info(f"🔍 开始分析业绩记录 {performance_id}: {performance.project_name}")
                
                # 进行AI分析
                ai_result = await ai_service.smart_document_analysis(
                    performance.source_document,
                    enable_vision=enable_vision_analysis,
                    enable_ocr=True
                )
                
                if ai_result and ai_result.get("success"):
                    # 提取业绩信息
                    extracted_info = _extract_performance_info(ai_result)
                    
                    # 更新业绩记录（只在AI提取到有效信息时更新）
                    updated_fields = []
                    
                    # 如果AI提取到了有意义的项目名称，则更新
                    if extracted_info.get('project_name') and len(extracted_info['project_name']) > 3:
                        performance.project_name = extracted_info['project_name']
                        updated_fields.append("project_name")
                    
                    if extracted_info.get('client_name') and performance.client_name == "待AI分析":
                        performance.client_name = extracted_info['client_name']
                        updated_fields.append("client_name")
                    
                    if extracted_info.get('business_field') and performance.business_field == "待AI分析":
                        performance.business_field = extracted_info['business_field']
                        updated_fields.append("business_field")
                    
                    if extracted_info.get('contract_amount'):
                        performance.contract_amount = extracted_info['contract_amount']
                        updated_fields.append("contract_amount")
                    
                    if extracted_info.get('year'):
                        performance.year = extracted_info['year']
                        updated_fields.append("year")
                    
                    # 更新分析结果
                    performance.description = extracted_info.get('description', "AI分析完成")
                    performance.confidence_score = ai_result.get("results", {}).get("final_classification", {}).get("confidence", 0.0)
                    performance.ai_analysis_status = "completed"
                    
                    # 保存AI分析结果
                    performance.ai_analysis = {
                        "analysis_result": ai_result,
                        "extracted_info": extracted_info,
                        "updated_fields": updated_fields,
                        "analysis_timestamp": datetime.now().isoformat()
                    }
                    
                    db.commit()
                    
                    # 更新AI任务状态为成功
                    if task_id:
                        update_ai_task(db, task_id, "success", result={
                            "analysis_result": ai_result,
                            "extracted_info": extracted_info,
                            "updated_fields": updated_fields,
                            "confidence_score": performance.confidence_score
                        })
                    
                    logger.info(f"✅ AI分析完成: 记录{performance_id}, 更新字段: {updated_fields}")
                
                else:
                    # AI分析失败
                    performance.ai_analysis_status = "failed"
                    performance.description = "AI分析失败，请手动编辑"
                    db.commit()
                    
                    # 更新AI任务状态为失败
                    if task_id:
                        update_ai_task(db, task_id, "failed", error="AI分析未返回成功结果")
                    
                    logger.warning(f"⚠️ AI分析失败: 记录{performance_id}")
                
            except Exception as single_error:
                logger.error(f"❌ 单个记录分析失败 {performance_id}: {str(single_error)}")
                
                # 标记分析失败
                try:
                    performance = db.query(Performance).filter(Performance.id == performance_id).first()
                    if performance:
                        performance.ai_analysis_status = "failed"
                        performance.description = f"AI分析出错: {str(single_error)}"
                        db.commit()
                    
                    # 更新AI任务状态为失败
                    if task_id:
                        update_ai_task(db, task_id, "failed", error=str(single_error))
                        
                except:
                    pass
        
        logger.info(f"🎉 后台AI分析任务完成，共处理{len(performance_ids)}条记录")
        
    except Exception as e:
        logger.error(f"❌ 后台AI分析任务失败: {str(e)}")

def _extract_performance_info(ai_result):
    """从AI分析结果中提取业绩信息并生成规范化项目名称"""
    extracted_info = {}
    
    if not ai_result:
        return extracted_info
    
    # 从新的AI分析结果结构中提取文本内容
    text_content = ""
    
    # 新结构：ai_result.results.text_extraction_result.text
    if ai_result.get("results", {}).get("text_extraction_result", {}).get("text"):
        text_content = ai_result["results"]["text_extraction_result"]["text"]
    # 兼容旧结构：ai_result.text_extraction_result.text
    elif ai_result.get('text_extraction_result', {}).get('text'):
        text_content = ai_result['text_extraction_result']['text']
    
    # 添加调试日志
    logger.info(f"提取的文本内容长度: {len(text_content)} 字符")
    if text_content:
        logger.info(f"文本内容预览: {text_content[:200]}...")
    else:
        logger.warning("没有找到文本内容")
    
    # 从OCR结果中寻找关键信息（兼容多种结构）
    ocr_text = ""
    if ai_result.get("results", {}).get("ocr_result", {}).get("text"):
        ocr_text = ai_result["results"]["ocr_result"]["text"]
    elif ai_result.get('ocr_result', {}).get('text'):
        ocr_text = ai_result['ocr_result']['text']
    
    # 从AI文本分析结果中提取结构化信息
    ai_text_analysis = ai_result.get("results", {}).get("ai_text_analysis", {})
    if ai_text_analysis and ai_text_analysis.get("key_entities"):
        entities = ai_text_analysis["key_entities"]
        if entities.get("client_name"):
            extracted_info['client_name'] = entities["client_name"]
        if entities.get("amount"):
            try:
                amount_str = str(entities["amount"]).replace(',', '').replace('，', '')
                extracted_info['contract_amount'] = float(amount_str)
            except:
                pass
        if entities.get("date_issued"):
            # 尝试从日期中提取年份
            try:
                import re
                year_match = re.search(r'(\d{4})', str(entities["date_issued"]))
                if year_match:
                    extracted_info['year'] = int(year_match.group(1))
            except:
                pass
    
    # 从最终分类结果中提取信息
    final_classification = ai_result.get("results", {}).get("final_classification", {})
    if final_classification:
        if final_classification.get("business_field"):
            extracted_info['business_field'] = final_classification["business_field"]
        if final_classification.get("description"):
            extracted_info['description'] = final_classification["description"]
    
    # 合并所有文本内容进行关键词匹配
    full_text = f"{text_content}\n{ocr_text}".lower()
    
    if not full_text.strip():
        logger.warning("合并后的文本内容为空，无法进行关键词匹配")
        return extracted_info
    
    logger.info(f"合并后的文本长度: {len(full_text)} 字符")
    
    # 使用关键词匹配提取信息（作为备用方案）
    import re
    
    # 提取客户名称
    client_name = ""
    if not extracted_info.get('client_name'):
        client_patterns = [
            r'甲方[：:]\s*([^\n\r，。；]+)',
            r'委托方[：:]\s*([^\n\r，。；]+)', 
            r'客户[：:]\s*([^\n\r，。；]+)',
            r'委托人[：:]\s*([^\n\r，。；]+)',
            r'当事人[：:]\s*([^\n\r，。；]+)',
            r'申请人[：:]\s*([^\n\r，。；]+)'
        ]
        for pattern in client_patterns:
            match = re.search(pattern, full_text)
            if match:
                client_name = match.group(1).strip()
                # 清理客户名称，移除多余内容
                client_name = re.sub(r'（.*?）|\(.*?\)', '', client_name)  # 移除括号内容
                client_name = re.sub(r'法定代表人.*|统一社会信用代码.*|地址.*', '', client_name)  # 移除无关信息
                client_name = client_name.strip()
                if len(client_name) > 2 and len(client_name) < 50:  # 合理的长度范围
                    extracted_info['client_name'] = client_name
                    logger.info(f"提取到客户名称: {client_name}")
                    break
    
    # 提取金额
    if not extracted_info.get('contract_amount'):
        amount_patterns = [
            r'合同金额[：:]?\s*([0-9,，.]+)\s*万?元',
            r'总金额[：:]?\s*([0-9,，.]+)\s*万?元',
            r'费用[：:]?\s*([0-9,，.]+)\s*万?元',
            r'律师费[：:]?\s*([0-9,，.]+)\s*万?元',
            r'服务费[：:]?\s*([0-9,，.]+)\s*万?元'
        ]
        for pattern in amount_patterns:
            match = re.search(pattern, full_text)
            if match:
                try:
                    amount_str = match.group(1).replace(',', '').replace('，', '')
                    extracted_info['contract_amount'] = float(amount_str)
                    logger.info(f"提取到合同金额: {amount_str}")
                    break
                except:
                    pass
    
    # 提取年份
    current_year = None
    if not extracted_info.get('year'):
        year_patterns = [
            r'(\d{4})\s*年',
            r'签订时间[：:]\s*(\d{4})',
            r'合同日期[：:]\s*(\d{4})',
            r'(\d{4})[年/-]\d{1,2}[月/-]\d{1,2}'
        ]
        for pattern in year_patterns:
            match = re.search(pattern, full_text)
            if match:
                try:
                    year = int(match.group(1))
                    if 2000 <= year <= 2030:  # 合理的年份范围
                        extracted_info['year'] = year
                        current_year = year
                        logger.info(f"提取到年份: {year}")
                        break
                except:
                    pass
    else:
        current_year = extracted_info['year']
    
    # 提取业务领域和项目类型
    business_field = extracted_info.get('business_field', '')
    project_type = ""
    case_cause = ""  # 案由，用于诉讼案件
    project_description = ""  # 项目描述，用于非诉项目
    
    # 判断项目类型并提取相关信息
    if '诉讼' in full_text or '仲裁' in full_text or '纠纷' in full_text or '争议' in full_text:
        project_type = "诉讼仲裁"
        # 提取案由
        case_patterns = [
            r'案由[：:]\s*([^\n\r，。；]+)',
            r'纠纷类型[：:]\s*([^\n\r，。；]+)',
            r'争议事项[：:]\s*([^\n\r，。；]+)',
            r'([^\n\r]*?纠纷)',
            r'([^\n\r]*?争议)',
            r'([^\n\r]*?侵权)',
            r'([^\n\r]*?违约)'
        ]
        for pattern in case_patterns:
            match = re.search(pattern, full_text)
            if match:
                case_cause = match.group(1).strip()
                if len(case_cause) > 2 and len(case_cause) < 30:
                    logger.info(f"提取到案由: {case_cause}")
                    break
        
        if not case_cause:
            # 根据业务领域推断案由
            if business_field == "知识产权":
                case_cause = "知识产权纠纷"
            elif business_field == "合同纠纷":
                case_cause = "合同纠纷"
            else:
                case_cause = "商事纠纷"
        
        if not business_field:
            business_field = "争议解决"
            extracted_info['business_field'] = business_field
            
    elif '常年' in full_text or '顾问' in full_text:
        project_type = "常年法律顾问"
        if not business_field:
            business_field = "合规监管"
            extracted_info['business_field'] = business_field
    else:
        project_type = "重大个案(非诉)"
        # 提取项目描述
        project_patterns = [
            r'项目名称[：:]\s*([^\n\r，。；]+)',
            r'服务内容[：:]\s*([^\n\r，。；]+)',
            r'委托事项[：:]\s*([^\n\r，。；]+)',
            r'业务范围[：:]\s*([^\n\r，。；]+)'
        ]
        for pattern in project_patterns:
            match = re.search(pattern, full_text)
            if match:
                project_description = match.group(1).strip()
                # 清理项目描述，移除多余的"项目"字样
                if project_description.endswith('项目'):
                    project_description = project_description[:-2]
                if len(project_description) > 3 and len(project_description) < 50:
                    logger.info(f"提取到项目描述: {project_description}")
                    break
        
        if not project_description:
            # 根据业务领域生成默认项目描述
            if business_field == "并购重组":
                project_description = "并购重组"
            elif business_field == "资本市场":
                project_description = "资本市场"
            elif business_field == "银行金融":
                project_description = "银团贷款"
            elif business_field == "房地产":
                project_description = "房地产项目"
            elif business_field == "知识产权":
                project_description = "知识产权"
            else:
                project_description = "法律服务"
        
        # 如果没有提取到业务领域，尝试从文本推断
        if not business_field:
            if '并购' in full_text or '收购' in full_text or 'M&A' in full_text.upper():
                business_field = '并购重组'
            elif 'IPO' in full_text.upper() or '上市' in full_text or '发行' in full_text:
                business_field = '资本市场'
            elif '破产' in full_text or '重整' in full_text:
                business_field = '破产重整'
            elif '金融' in full_text or '银行' in full_text or '贷款' in full_text:
                business_field = '银行金融'
            elif '房地产' in full_text or '土地' in full_text:
                business_field = '房地产'
            elif '知识产权' in full_text or '专利' in full_text or '商标' in full_text:
                business_field = '知识产权'
            else:
                business_field = '合规监管'
            
            extracted_info['business_field'] = business_field
    
    # 生成规范化项目名称
    client_name = extracted_info.get('client_name', '').strip()
    
    if client_name and project_type:
        if project_type == "诉讼仲裁":
            # 格式：代表xxxx的xxxx(案由)纠纷
            standardized_name = f"代表{client_name}的{case_cause}"
            if not case_cause.endswith('纠纷'):
                standardized_name += "纠纷"
        elif project_type == "常年法律顾问":
            # 格式：xxxx常年法律顾问(xxxx年度)
            year_suffix = f"({current_year}年度)" if current_year else ""
            standardized_name = f"{client_name}常年法律顾问{year_suffix}"
        else:  # 重大个案(非诉)
            # 格式：代表xxxx的xxxxxx项目
            standardized_name = f"代表{client_name}的{project_description}项目"
        
        extracted_info['project_name'] = standardized_name
        extracted_info['project_type'] = project_type
        logger.info(f"生成规范化项目名称: {standardized_name}")
        logger.info(f"确定项目类型: {project_type}")
    
    # 生成项目描述
    if not extracted_info.get('description'):
        if project_type == "诉讼仲裁":
            description = f"代表{client_name}处理{case_cause}案件，提供专业的诉讼代理服务"
        elif project_type == "常年法律顾问":
            description = f"为{client_name}提供{current_year or ''}年度常年法律顾问服务，涵盖日常法律事务咨询和风险防控"
        else:
            description = f"代表{client_name}的{project_description}项目，在{business_field}领域提供专业法律服务"
        
        extracted_info['description'] = description
        logger.info(f"生成项目描述: {description}")
    
    logger.info(f"最终提取的业绩信息: {extracted_info}")
    return extracted_info

@router.patch("/{performance_id}")
async def update_performance(
    performance_id: int,
    performance_data: dict,
    db: Session = Depends(get_db)
):
    """更新业绩记录"""
    try:
        performance = db.query(Performance).filter(Performance.id == performance_id).first()
        if not performance:
            raise HTTPException(status_code=404, detail="业绩记录不存在")
        
        # 更新字段
        updateable_fields = [
            'project_name', 'client_name', 'project_type', 'business_field',
            'year', 'contract_amount', 'currency', 'start_date', 'end_date',
            'description', 'is_manual_input'
        ]
        
        for field in updateable_fields:
            if field in performance_data:
                if field in ['start_date', 'end_date'] and performance_data[field]:
                    # 处理日期字段
                    setattr(performance, field, datetime.fromisoformat(performance_data[field]))
                elif field == 'year' and performance_data[field]:
                    # 处理年份字段
                    setattr(performance, field, int(performance_data[field]))
                else:
                    setattr(performance, field, performance_data[field])
        
        performance.updated_at = datetime.now()
        db.commit()
        
        logger.info(f"业绩记录更新成功: ID={performance_id}")
        
        return {
            "success": True,
            "message": "业绩记录更新成功"
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"更新业绩记录失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新业绩记录失败: {str(e)}")

@router.patch("/{performance_id}/verify")
async def verify_performance(
    performance_id: int,
    verification_notes: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """用户主动验证业绩记录"""
    try:
        performance = db.query(Performance).filter(Performance.id == performance_id).first()
        if not performance:
            raise HTTPException(status_code=404, detail="业绩记录不存在")
        
        # 记录验证历史
        if not performance.verification_history:
            performance.verification_history = []
        
        verification_record = {
            "timestamp": datetime.now().isoformat(),
            "verified_by": "user",  # 可以扩展为具体用户ID
            "verification_notes": verification_notes,
            "previous_status": performance.is_verified,
            "ai_confidence_score": performance.confidence_score,
            "ai_analysis_status": performance.ai_analysis_status
        }
        
        performance.verification_history.append(verification_record)
        performance.is_verified = True
        performance.verified_at = datetime.now()
        performance.verification_notes = verification_notes
        
        db.commit()
        
        logger.info(f"业绩记录验证成功: ID={performance_id}, 验证备注={verification_notes}")
        
        return {
            "success": True,
            "message": "业绩记录验证成功",
            "verification_record": verification_record
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"验证业绩记录失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"验证失败: {str(e)}")

@router.patch("/{performance_id}/unverify")
async def unverify_performance(
    performance_id: int,
    unverification_reason: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """取消验证业绩记录（重新验证）"""
    try:
        performance = db.query(Performance).filter(Performance.id == performance_id).first()
        if not performance:
            raise HTTPException(status_code=404, detail="业绩记录不存在")
        
        # 记录取消验证历史
        if not performance.verification_history:
            performance.verification_history = []
        
        unverification_record = {
            "timestamp": datetime.now().isoformat(),
            "action": "unverify",
            "unverified_by": "user",
            "unverification_reason": unverification_reason,
            "previous_status": performance.is_verified,
            "ai_confidence_score": performance.confidence_score,
            "ai_analysis_status": performance.ai_analysis_status
        }
        
        performance.verification_history.append(unverification_record)
        performance.is_verified = False
        performance.verified_at = None
        performance.verification_notes = None
        
        db.commit()
        
        logger.info(f"业绩记录取消验证成功: ID={performance_id}, 原因={unverification_reason}")
        
        return {
            "success": True,
            "message": "业绩记录已取消验证，可以重新验证",
            "unverification_record": unverification_record
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"取消验证业绩记录失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"取消验证失败: {str(e)}")

@router.get("/{performance_id}/verification-history")
async def get_verification_history(
    performance_id: int,
    db: Session = Depends(get_db)
):
    """获取业绩记录的验证历史"""
    try:
        performance = db.query(Performance).filter(Performance.id == performance_id).first()
        if not performance:
            raise HTTPException(status_code=404, detail="业绩记录不存在")
        
        return {
            "success": True,
            "verification_history": performance.verification_history or [],
            "current_status": {
                "is_verified": performance.is_verified,
                "verified_at": performance.verified_at.isoformat() if performance.verified_at else None,
                "verification_notes": performance.verification_notes,
                "ai_confidence_score": performance.confidence_score,
                "ai_analysis_status": performance.ai_analysis_status
            }
        }
        
    except Exception as e:
        logger.error(f"获取验证历史失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取验证历史失败: {str(e)}")

@router.post("/{performance_id}/reanalyze")
async def reanalyze_performance(
    performance_id: int,
    enable_vision_analysis: bool = Form(True),
    enable_ocr: bool = Form(True),
    update_fields: bool = Form(False),  # 是否使用AI结果更新字段
    db: Session = Depends(get_db)
):
    """重新分析业绩文件"""
    try:
        from ai_service import ai_service
        
        performance = db.query(Performance).filter(Performance.id == performance_id).first()
        if not performance:
            raise HTTPException(status_code=404, detail="业绩记录不存在")
        
        if not performance.source_document or not os.path.exists(performance.source_document):
            raise HTTPException(status_code=400, detail="源文档不存在，无法重新分析")
        
        # 检查OCR设置
        ocr_enabled = False
        try:
            from database import get_db
            from models import SystemSettings
            
            db_check = next(get_db())
            ocr_setting = db_check.query(SystemSettings).filter(
                SystemSettings.setting_key == "docling_enable_ocr"
            ).first()
            
            if ocr_setting:
                ocr_enabled = ocr_setting.setting_value.lower() == "true"
            db_check.close()
        except Exception as e:
            logger.warning(f"检查OCR设置失败: {e}")
        
        # 如果用户请求OCR但OCR已关闭，给出提示
        if enable_ocr and not ocr_enabled:
            logger.info("⚠️ 用户请求OCR分析，但OCR功能已关闭")
            # 继续执行，但OCR会被AI服务自动禁用
        
        # 更新状态为正在分析
        performance.ai_analysis_status = "analyzing"
        db.commit()
        
        # 调用AI服务重新分析文档
        logger.info(f"开始重新分析业绩文件: {performance.source_document}")
        
        if not ai_service.enable_ai:
            raise HTTPException(status_code=503, detail="AI服务未启用，无法进行分析")
        
        try:
            ai_result = await ai_service.smart_document_analysis(
                performance.source_document,
                enable_vision=enable_vision_analysis,
                enable_ocr=enable_ocr
            )
            
            if not ai_result:
                raise Exception("AI分析未返回结果")
            
            logger.info(f"AI重新分析完成: {performance.source_document}")
            
            # 从AI结果中提取业绩信息
            extracted_info = _extract_performance_info(ai_result)
            logger.info(f"重新提取的业绩信息: {extracted_info}")

            # 更新AI分析结果
            performance.ai_analysis = {
                "reanalysis_result": ai_result,
                "reanalysis_timestamp": datetime.now().isoformat(),
                "extracted_info": extracted_info
            }
            
            # 设置置信度
            if ai_result.get("final_classification"):
                classification = ai_result["final_classification"]
                performance.confidence_score = classification.get("confidence", 0.0)
            
            # 提取文本内容
            if ai_result.get('text_extraction_result', {}).get('text'):
                performance.extracted_text = ai_result['text_extraction_result']['text']
            
            # 如果启用了字段更新，则使用AI结果更新业绩字段
            if update_fields:
                if extracted_info.get('project_name'):
                    performance.project_name = extracted_info['project_name']
                if extracted_info.get('client_name'):
                    performance.client_name = extracted_info['client_name']
                if extracted_info.get('business_field'):
                    performance.business_field = extracted_info['business_field']
                if extracted_info.get('contract_amount'):
                    performance.contract_amount = extracted_info['contract_amount']
                if extracted_info.get('year'):
                    performance.year = extracted_info['year']
                if extracted_info.get('description'):
                    performance.description = extracted_info['description']
                
                logger.info(f"已使用AI结果更新业绩字段")
            
            # 更新AI分析状态为完成
            performance.ai_analysis_status = "completed"
            db.commit()
            
            # 构建响应消息
            response_message = "AI重新分析完成"
            if enable_ocr and not ocr_enabled:
                response_message += "（注意：OCR功能已关闭，分析不包含OCR文本识别）"
        
            return {
                "success": True,
                "message": response_message,
                "ai_analysis": {
                    "confidence_score": performance.confidence_score,
                    "extracted_info": extracted_info,
                    "fields_updated": update_fields,
                    "ocr_status": ai_result.get("ocr_status", "unknown")
                }
            }
                    
        except Exception as e:
            logger.error(f"AI重新分析失败: {str(e)}")
            # 更新AI分析状态为失败
            performance.ai_analysis_status = "failed"
            db.commit()
            raise HTTPException(status_code=500, detail=f"AI重新分析失败: {str(e)}")
        
    except Exception as e:
        db.rollback()
        logger.error(f"重新分析业绩失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"重新分析失败: {str(e)}")

@router.delete("/{performance_id}")
async def delete_performance(
    performance_id: int,
    db: Session = Depends(get_db)
):
    """删除业绩记录"""
    try:
        performance = db.query(Performance).filter(Performance.id == performance_id).first()
        if not performance:
            raise HTTPException(status_code=404, detail="业绩记录不存在")
        
        # 删除关联文件
        performance_files = db.query(PerformanceFile).filter(PerformanceFile.performance_id == performance_id).all()
        for perf_file in performance_files:
            if perf_file.file_path and os.path.exists(perf_file.file_path):
                try:
                    os.remove(perf_file.file_path)
                    logger.info(f"已删除文件: {perf_file.file_path}")
                except Exception as file_error:
                    logger.warning(f"删除文件失败: {perf_file.file_path}, 错误: {file_error}")
        
        # 删除源文档
        if performance.source_document and os.path.exists(performance.source_document):
            try:
                os.remove(performance.source_document)
                logger.info(f"已删除源文档: {performance.source_document}")
            except Exception as source_error:
                logger.warning(f"删除源文档失败: {performance.source_document}, 错误: {source_error}")
        
        # 删除数据库记录
        db.delete(performance)
        db.commit()
        
        logger.info(f"✅ 业绩记录删除成功: ID={performance_id}")
        
        return {
            "success": True,
            "message": "业绩记录已删除"
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"删除业绩记录失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")

@router.post("/{performance_id}/delete")
async def deletePerformance(
    performance_id: int,
    db: Session = Depends(get_db)
):
    """删除业绩记录（POST方法，供前端调用）"""
    return await delete_performance(performance_id, db)

# ==================== 配置管理API ====================

@router.get("/config/business-fields")
async def get_business_fields():
    """获取业务领域列表"""
    try:
        fields = config_manager.get_business_fields()
        return {
            "success": True,
            "business_fields": fields
        }
    except Exception as e:
        logger.error(f"获取业务领域失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取业务领域失败: {str(e)}")

@router.get("/config/performance-types")
async def get_performance_types():
    """获取业绩类型列表"""
    try:
        types = config_manager.get_performance_types()
        return {
            "success": True,
            "performance_types": types
        }
    except Exception as e:
        logger.error(f"获取业绩类型失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取业绩类型失败: {str(e)}")

@router.post("/config/reload")
async def reload_configs():
    """重新加载配置文件"""
    try:
        config_manager.reload_all_configs()
        return {
            "success": True,
            "message": "配置文件重新加载成功"
        }
    except Exception as e:
        logger.error(f"重新加载配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"重新加载配置失败: {str(e)}")

@router.put("/config/business-fields")
async def update_business_fields(business_fields: List[Dict[str, Any]]):
    """更新业务领域配置"""
    try:
        config_manager.update_business_fields(business_fields)
        return {
            "success": True,
            "message": "业务领域配置更新成功"
        }
    except Exception as e:
        logger.error(f"更新业务领域配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新业务领域配置失败: {str(e)}")

@router.put("/config/performance-types")
async def update_performance_types(performance_types: List[Dict[str, Any]]):
    """更新业绩类型配置"""
    try:
        config_manager.update_performance_types(performance_types)
        return {
            "success": True,
            "message": "业绩类型配置更新成功"
        }
    except Exception as e:
        logger.error(f"更新业绩类型配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新业绩类型配置失败: {str(e)}")

# ==================== AI学习API ====================

@router.post("/{performance_id}/verify-with-learning")
async def verify_performance_with_learning(
    performance_id: int,
    original_values: Dict[str, Any],
    corrected_values: Dict[str, Any],
    learning_notes: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """验证业绩记录并记录AI学习数据"""
    try:
        performance = db.query(Performance).filter(Performance.id == performance_id).first()
        if not performance:
            raise HTTPException(status_code=404, detail="业绩记录不存在")
        
        # 记录用户反馈
        feedback_data = {
            "type": "performance_correction",
            "performance_id": performance_id,
            "original_values": original_values,
            "corrected_values": corrected_values,
            "learning_notes": learning_notes,
            "source_document": performance.source_document,
            "ai_analysis_status": performance.ai_analysis_status,
            "confidence_score": performance.confidence_score
        }
        
        config_manager.add_user_feedback(feedback_data)
        
        # 记录修正模式
        for field, original_value in original_values.items():
            corrected_value = corrected_values.get(field)
            if original_value != corrected_value:
                pattern_data = {
                    "field": field,
                    "original_value": original_value,
                    "corrected_value": corrected_value,
                    "performance_id": performance_id,
                    "context": {
                        "project_name": performance.project_name,
                        "client_name": performance.client_name,
                        "business_field": performance.business_field,
                        "project_type": performance.project_type
                    }
                }
                config_manager.add_correction_pattern(pattern_data)
        
        # 更新业绩记录
        for field, value in corrected_values.items():
            if hasattr(performance, field):
                setattr(performance, field, value)
        
        performance.is_verified = True
        performance.updated_at = datetime.now()
        
        db.commit()
        
        logger.info(f"业绩记录验证完成并记录学习数据: ID={performance_id}")
        
        return {
            "success": True,
            "message": "业绩记录验证成功，AI学习数据已记录",
            "learning_recorded": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"验证业绩记录失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"验证业绩记录失败: {str(e)}")

@router.get("/ai-learning/stats")
async def get_ai_learning_stats():
    """获取AI学习统计信息"""
    try:
        learning_data = config_manager.get_ai_learning_data()
        
        feedback_count = len(learning_data.get("user_feedback", []))
        pattern_count = len(learning_data.get("correction_patterns", []))
        
        # 统计修正模式
        field_corrections = {}
        for pattern in learning_data.get("correction_patterns", []):
            field = pattern.get("field", "unknown")
            field_corrections[field] = field_corrections.get(field, 0) + 1
        
        return {
            "success": True,
            "stats": {
                "total_feedback": feedback_count,
                "total_corrections": pattern_count,
                "field_corrections": field_corrections,
                "last_updated": learning_data.get("last_updated")
            }
        }
    except Exception as e:
        logger.error(f"获取AI学习统计失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取AI学习统计失败: {str(e)}")

@router.get("/ai-learning/patterns")
async def get_correction_patterns():
    """获取修正模式"""
    patterns = config_manager.get_correction_patterns()
    return {
        "success": True,
        "patterns": patterns
    }

# AI任务管理API
@router.get("/tasks/{task_id}")
async def get_ai_task_status(
    task_id: int,
    db: Session = Depends(get_db)
):
    """获取AI任务状态"""
    from ai_service import get_ai_task_status
    
    task_status = get_ai_task_status(db, task_id)
    
    if "error" in task_status:
        raise HTTPException(status_code=404, detail=task_status["error"])
    
    return {
        "success": True,
        "task": task_status
    }

@router.get("/tasks")
async def list_ai_tasks(
    page: int = 1,
    page_size: int = 20,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取AI任务列表"""
    try:
        query = db.query(AITask).filter(AITask.file_type == "performance")
        
        if status:
            query = query.filter(AITask.status == status)
        
        total = query.count()
        offset = (page - 1) * page_size
        tasks = query.order_by(AITask.created_at.desc()).offset(offset).limit(page_size).all()
        
        return {
            "success": True,
            "tasks": [
                {
                    "id": task.id,
                    "file_id": task.file_id,
                    "file_type": task.file_type,
                    "status": task.status,
                    "result_snapshot": task.result_snapshot,
                    "error_message": task.error_message,
                    "created_at": task.created_at.isoformat() if task.created_at else None,
                    "updated_at": task.updated_at.isoformat() if task.updated_at else None
                }
                for task in tasks
            ],
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "pages": (total + page_size - 1) // page_size
            }
        }
        
    except Exception as e:
        logger.error(f"获取AI任务列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取AI任务列表失败: {str(e)}") 