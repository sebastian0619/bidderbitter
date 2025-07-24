import os
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import asyncio
from docx import Document
from docx.shared import Inches, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.shared import OxmlElement, qn
from PIL import Image
import fitz  # PyMuPDF
from io import BytesIO
import re
import uuid

from ai_service import AIService
from models import Project, ProjectSection, SectionDocument, Template, TemplateField, TemplateMapping, GeneratedDocument
from models import Award, Performance, LawyerCertificate, ManagedFile
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BidDocumentService:
    """投标文档生成服务"""
    
    def __init__(self):
        self.ai_service = AIService()
        self.output_dir = "/app/generated_docs"
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 招标信息提取字段配置
        self.tender_info_fields = {
            "tender_company": ["招标人", "采购人", "业主", "甲方"],
            "tender_agency": ["招标代理", "代理机构", "招标代理机构"],
            "bidder_name": ["投标人", "供应商", "乙方"],
            "legal_representative": ["法定代表人", "法人代表", "代表"],
            "authorized_representative": ["授权代表", "委托代理人"],
            "deadline": ["投标截止", "截止时间", "投标截止时间", "开标时间"],
            "project_name": ["项目名称", "工程名称", "采购项目"],
            "project_budget": ["预算", "预算金额", "项目预算"],
            "business_scope": ["业务范围", "服务范围", "工作内容"]
        }
    
    async def extract_tender_info(self, file_path: str) -> Dict[str, Any]:
        """从招标文件中提取关键信息"""
        try:
            logger.info(f"开始提取招标文件信息: {file_path}")
            
            # 使用AI服务进行文档分析
            analysis_result = await self.ai_service.smart_document_analysis(file_path)
            
            if not analysis_result.get("success"):
                return {"success": False, "error": "文档分析失败"}
            
            text_content = analysis_result.get("text_extraction_result", {}).get("text", "")
            
            if not text_content:
                return {"success": False, "error": "无法提取文本内容"}
            
            # 使用AI提取招标信息
            extracted_info = await self._extract_tender_info_with_ai(text_content)
            
            # 补充正则表达式提取
            regex_info = self._extract_tender_info_with_regex(text_content)
            
            # 合并结果
            final_info = {**regex_info, **extracted_info}
            
            logger.info(f"招标信息提取完成: {final_info}")
            return {
                "success": True,
                "extracted_info": final_info,
                "text_content": text_content[:1000] + "..." if len(text_content) > 1000 else text_content
            }
            
        except Exception as e:
            logger.error(f"提取招标信息失败: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _extract_tender_info_with_ai(self, text_content: str) -> Dict[str, str]:
        """使用AI提取招标信息"""
        try:
            prompt = f"""
请从以下招标文件文本中提取关键信息，以JSON格式返回：

{text_content[:3000]}

请提取以下字段：
- tender_company: 招标人/采购人名称
- tender_agency: 招标代理机构名称
- bidder_name: 投标人名称（如果有）
- legal_representative: 法定代表人
- authorized_representative: 授权代表
- deadline: 投标截止时间
- project_name: 项目名称
- project_budget: 项目预算金额
- business_scope: 业务范围

只返回JSON格式，不要其他内容。
"""
            
            result = await self.ai_service.analyze_text(prompt)
            if result.get("success"):
                try:
                    # 尝试解析AI返回的JSON
                    ai_result = json.loads(result.get("content", "{}"))
                    return {k: v for k, v in ai_result.items() if v}
                except json.JSONDecodeError:
                    logger.warning("AI返回结果不是有效的JSON格式")
                    return {}
            return {}
            
        except Exception as e:
            logger.error(f"AI提取招标信息失败: {str(e)}")
            return {}
    
    def _extract_tender_info_with_regex(self, text_content: str) -> Dict[str, str]:
        """使用正则表达式提取招标信息"""
        extracted_info = {}
        
        # 提取招标人
        for pattern in self.tender_info_fields["tender_company"]:
            match = re.search(f"{pattern}[：:]*([^\\n\\r]+)", text_content)
            if match:
                extracted_info["tender_company"] = match.group(1).strip()
                break
        
        # 提取招标代理
        for pattern in self.tender_info_fields["tender_agency"]:
            match = re.search(f"{pattern}[：:]*([^\\n\\r]+)", text_content)
            if match:
                extracted_info["tender_agency"] = match.group(1).strip()
                break
        
        # 提取投标截止时间
        for pattern in self.tender_info_fields["deadline"]:
            match = re.search(f"{pattern}[：:]*([^\\n\\r]+)", text_content)
            if match:
                extracted_info["deadline"] = match.group(1).strip()
                break
        
        # 提取项目名称
        for pattern in self.tender_info_fields["project_name"]:
            match = re.search(f"{pattern}[：:]*([^\\n\\r]+)", text_content)
            if match:
                extracted_info["project_name"] = match.group(1).strip()
                break
        
        return extracted_info
    
    async def generate_bid_document(self, project_id: int, db: Session, 
                                  template_id: Optional[int] = None,
                                  include_awards: bool = True,
                                  include_performances: bool = True,
                                  include_lawyers: bool = True) -> Dict[str, Any]:
        """生成投标文档"""
        try:
            logger.info(f"开始生成投标文档，项目ID: {project_id}")
            
            # 获取项目信息
            project = db.query(Project).filter(Project.id == project_id).first()
            if not project:
                return {"success": False, "error": "项目不存在"}
            
            # 获取项目章节
            sections = db.query(ProjectSection).filter(
                ProjectSection.project_id == project_id
            ).order_by(ProjectSection.order).all()
            
            # 创建文档
            doc = Document()
            
            # 设置页面边距
            sections_doc = doc.sections
            for section in sections_doc:
                section.top_margin = Cm(2.54)
                section.bottom_margin = Cm(2.54)
                section.left_margin = Cm(3.18)
                section.right_margin = Cm(3.18)
            
            # 添加封面
            self._add_cover_page(doc, project)
            
            # 添加目录（可选）
            # self._add_table_of_contents(doc, sections)
            
            # 处理每个章节
            for section in sections:
                await self._process_section(doc, section, db, include_awards, include_performances, include_lawyers)
            
            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"bid_document_{project.name}_{timestamp}.docx"
            filepath = os.path.join(self.output_dir, filename)
            
            # 保存文档
            doc.save(filepath)
            
            # 记录生成的文档
            generated_doc = GeneratedDocument(
                project_id=project_id,
                filename=filename,
                file_path=filepath,
                file_size=os.path.getsize(filepath),
                page_count=len(doc.paragraphs),  # 简单估算
                generation_time=0.0  # 可以添加计时
            )
            db.add(generated_doc)
            db.commit()
            
            logger.info(f"投标文档生成成功: {filepath}")
            return {
                "success": True,
                "filepath": filepath,
                "filename": filename,
                "document_id": generated_doc.id
            }
            
        except Exception as e:
            logger.error(f"生成投标文档失败: {str(e)}")
            db.rollback()
            return {"success": False, "error": str(e)}
    
    def _add_cover_page(self, doc: Document, project: Project):
        """添加封面页"""
        # 标题
        title = doc.add_heading('投标文件', 0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # 项目信息表格
        table = doc.add_table(rows=6, cols=2)
        table.style = 'Table Grid'
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        
        # 设置表格内容
        table_data = [
            ["项目名称", project.name or ""],
            ["招标人", project.tender_company or ""],
            ["招标代理机构", project.tender_agency or ""],
            ["投标人", project.bidder_name or ""],
            ["投标截止日期", project.deadline.strftime("%Y年%m月%d日") if project.deadline else ""],
            ["编制日期", datetime.now().strftime("%Y年%m月%d日")]
        ]
        
        for i, (label, value) in enumerate(table_data):
            table.cell(i, 0).text = label
            table.cell(i, 1).text = value
        
        # 添加分页符
        doc.add_page_break()
    
    async def _process_section(self, doc: Document, section: ProjectSection, db: Session,
                             include_awards: bool, include_performances: bool, include_lawyers: bool):
        """处理单个章节"""
        try:
            # 添加章节标题
            heading = doc.add_heading(section.title, level=1)
            
            # 获取章节文档
            documents = db.query(SectionDocument).filter(
                SectionDocument.section_id == section.id
            ).order_by(SectionDocument.order).all()
            
            # 处理章节文档
            for doc_item in documents:
                await self._process_section_document(doc, doc_item, db)
            
            # 根据章节类型自动填充相关内容
            await self._auto_fill_section_content(doc, section, db, include_awards, include_performances, include_lawyers)
            
        except Exception as e:
            logger.error(f"处理章节失败 {section.title}: {str(e)}")
    
    async def _process_section_document(self, doc: Document, doc_item: SectionDocument, db: Session):
        """处理章节中的文档"""
        try:
            if not doc_item.converted_path or not os.path.exists(doc_item.converted_path):
                logger.warning(f"文档转换路径不存在: {doc_item.converted_path}")
                return
            
            # 这里可以添加文档内容到Word文档的逻辑
            # 由于文档已经转换为Word格式，可以直接复制内容
            logger.info(f"处理文档: {doc_item.original_filename}")
            
        except Exception as e:
            logger.error(f"处理文档失败 {doc_item.original_filename}: {str(e)}")
    
    async def _auto_fill_section_content(self, doc: Document, section: ProjectSection, db: Session,
                                       include_awards: bool, include_performances: bool, include_lawyers: bool):
        """自动填充章节内容"""
        try:
            section_title_lower = section.title.lower()
            
            # 根据章节标题判断类型并填充相应内容
            if any(keyword in section_title_lower for keyword in ["获奖", "荣誉", "奖项"]):
                if include_awards:
                    await self._fill_awards_content(doc, db)
            
            elif any(keyword in section_title_lower for keyword in ["业绩", "案例", "项目"]):
                if include_performances:
                    await self._fill_performances_content(doc, db)
            
            elif any(keyword in section_title_lower for keyword in ["团队", "律师", "人员"]):
                if include_lawyers:
                    await self._fill_lawyers_content(doc, db)
            
        except Exception as e:
            logger.error(f"自动填充章节内容失败: {str(e)}")
    
    async def _fill_awards_content(self, doc: Document, db: Session):
        """填充获奖信息"""
        try:
            # 获取获奖信息
            awards = db.query(Award).filter(Award.is_verified == True).order_by(Award.year.desc()).all()
            
            if not awards:
                doc.add_paragraph("暂无获奖信息")
                return
            
            # 按年份分组
            awards_by_year = {}
            for award in awards:
                year = award.year
                if year not in awards_by_year:
                    awards_by_year[year] = []
                awards_by_year[year].append(award)
            
            # 添加获奖信息
            for year in sorted(awards_by_year.keys(), reverse=True):
                year_heading = doc.add_heading(f"{year}年获奖情况", level=2)
                
                for award in awards_by_year[year]:
                    # 创建获奖信息表格
                    table = doc.add_table(rows=4, cols=2)
                    table.style = 'Table Grid'
                    
                    table.cell(0, 0).text = "奖项名称"
                    table.cell(0, 1).text = award.title
                    table.cell(1, 0).text = "颁发机构"
                    table.cell(1, 1).text = award.brand
                    table.cell(2, 0).text = "业务领域"
                    table.cell(2, 1).text = award.business_type
                    table.cell(3, 0).text = "奖项描述"
                    table.cell(3, 1).text = award.description or ""
                    
                    doc.add_paragraph()  # 添加空行
            
        except Exception as e:
            logger.error(f"填充获奖信息失败: {str(e)}")
    
    async def _fill_performances_content(self, doc: Document, db: Session):
        """填充业绩信息"""
        try:
            # 获取业绩信息
            performances = db.query(Performance).filter(Performance.is_verified == True).order_by(Performance.year.desc()).all()
            
            if not performances:
                doc.add_paragraph("暂无业绩信息")
                return
            
            # 按年份分组
            performances_by_year = {}
            for performance in performances:
                year = performance.year
                if year not in performances_by_year:
                    performances_by_year[year] = []
                performances_by_year[year].append(performance)
            
            # 添加业绩信息
            for year in sorted(performances_by_year.keys(), reverse=True):
                year_heading = doc.add_heading(f"{year}年业绩情况", level=2)
                
                for performance in performances_by_year[year]:
                    # 创建业绩信息表格
                    table = doc.add_table(rows=6, cols=2)
                    table.style = 'Table Grid'
                    
                    table.cell(0, 0).text = "项目名称"
                    table.cell(0, 1).text = performance.project_name
                    table.cell(1, 0).text = "客户名称"
                    table.cell(1, 1).text = performance.client_name
                    table.cell(2, 0).text = "项目类型"
                    table.cell(2, 1).text = performance.project_type
                    table.cell(3, 0).text = "业务领域"
                    table.cell(3, 1).text = performance.business_field
                    table.cell(4, 0).text = "合同金额"
                    table.cell(4, 1).text = f"{performance.contract_amount} {performance.currency}" if performance.contract_amount else ""
                    table.cell(5, 0).text = "项目描述"
                    table.cell(5, 1).text = performance.description or ""
                    
                    doc.add_paragraph()  # 添加空行
            
        except Exception as e:
            logger.error(f"填充业绩信息失败: {str(e)}")
    
    async def _fill_lawyers_content(self, doc: Document, db: Session):
        """填充律师团队信息"""
        try:
            # 获取律师信息
            lawyers = db.query(LawyerCertificate).filter(LawyerCertificate.is_verified == True).all()
            
            if not lawyers:
                doc.add_paragraph("暂无律师团队信息")
                return
            
            # 创建律师团队表格
            table = doc.add_table(rows=len(lawyers) + 1, cols=5)
            table.style = 'Table Grid'
            
            # 表头
            headers = ["姓名", "执业证号", "执业机构", "职位", "业务领域"]
            for i, header in enumerate(headers):
                table.cell(0, i).text = header
            
            # 律师信息
            for i, lawyer in enumerate(lawyers, 1):
                table.cell(i, 0).text = lawyer.lawyer_name
                table.cell(i, 1).text = lawyer.certificate_number
                table.cell(i, 2).text = lawyer.law_firm
                table.cell(i, 3).text = lawyer.position or ""
                table.cell(i, 4).text = ", ".join(lawyer.business_field_tags) if lawyer.business_field_tags else ""
            
        except Exception as e:
            logger.error(f"填充律师团队信息失败: {str(e)}")
    
    async def apply_template_to_project(self, project_id: int, template_id: int, 
                                      field_values: Dict[str, str], db: Session) -> Dict[str, Any]:
        """将模板应用到项目"""
        try:
            # 获取模板
            template = db.query(Template).filter(Template.id == template_id).first()
            if not template:
                return {"success": False, "error": "模板不存在"}
            
            # 获取项目
            project = db.query(Project).filter(Project.id == project_id).first()
            if not project:
                return {"success": False, "error": "项目不存在"}
            
            # 获取模板字段
            fields = db.query(TemplateField).filter(TemplateField.template_id == template_id).all()
            
            # 创建或更新字段映射
            for field in fields:
                value = field_values.get(field.field_key, "")
                
                # 查找现有映射
                mapping = db.query(TemplateMapping).filter(
                    and_(
                        TemplateMapping.project_id == project_id,
                        TemplateMapping.template_id == template_id,
                        TemplateMapping.field_id == field.id
                    )
                ).first()
                
                if mapping:
                    mapping.value = value
                else:
                    mapping = TemplateMapping(
                        project_id=project_id,
                        template_id=template_id,
                        field_id=field.id,
                        value=value
                    )
                    db.add(mapping)
            
            db.commit()
            
            return {"success": True, "message": "模板应用成功"}
            
        except Exception as e:
            logger.error(f"应用模板失败: {str(e)}")
            db.rollback()
            return {"success": False, "error": str(e)}
    
    def get_available_data_for_project(self, project_id: int, db: Session) -> Dict[str, Any]:
        """获取项目可用的数据"""
        try:
            # 获取获奖信息
            awards = db.query(Award).filter(Award.is_verified == True).all()
            
            # 获取业绩信息
            performances = db.query(Performance).filter(Performance.is_verified == True).all()
            
            # 获取律师信息
            lawyers = db.query(LawyerCertificate).filter(LawyerCertificate.is_verified == True).all()
            
            # 获取项目文件
            project_files = db.query(ManagedFile).filter(
                ManagedFile.file_category == "permanent"
            ).all()
            
            return {
                "success": True,
                "data": {
                    "awards": [{"id": a.id, "title": a.title, "year": a.year} for a in awards],
                    "performances": [{"id": p.id, "project_name": p.project_name, "client_name": p.client_name} for p in performances],
                    "lawyers": [{"id": l.id, "lawyer_name": l.lawyer_name, "position": l.position} for l in lawyers],
                    "files": [{"id": f.id, "display_name": f.display_name, "category": f.category} for f in project_files]
                }
            }
            
        except Exception as e:
            logger.error(f"获取项目可用数据失败: {str(e)}")
            return {"success": False, "error": str(e)}

# 创建全局实例
bid_document_service = BidDocumentService() 