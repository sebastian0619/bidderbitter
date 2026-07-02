"""招标文件分析服务

使用 lexitool / python-docx 读取招标文件，提取：
1. 项目基本信息（项目名称、招标人、截止日期等）
2. 文档结构（章节标题）
3. 评分标准、资质要求等关键信息
"""
import re
import logging
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class TenderAnalyzer:
    """招标文件分析器"""
    
    # 常见招标信息关键词
    FIELD_PATTERNS = {
        "project_name": [
            r"项目名称[：:]\s*(.+)",
            r"采购项目[：:]\s*(.+)",
            r"工程名称[：:]\s*(.+)",
            r"招标项目[：:]\s*(.+)",
        ],
        "tender_company": [
            r"招标人[：:]\s*(.+)",
            r"采购人[：:]\s*(.+)",
            r"业主[：:]\s*(.+)",
            r"甲方[：:]\s*(.+)",
        ],
        "tender_agency": [
            r"招标代理[机构]*[：:]\s*(.+)",
            r"代理机构[：:]\s*(.+)",
        ],
        "bidder_name": [
            r"投标人[：:]\s*(.+)",
            r"供应商[：:]\s*(.+)",
            r"乙方[：:]\s*(.+)",
        ],
        "deadline": [
            r"投标截止[时间日期]*[：:]\s*(\d{4}[-年]\d{1,2}[-月]\d{1,2}[日]?)",
            r"截止时间[：:]\s*(\d{4}[-年]\d{1,2}[-月]\d{1,2}[日]?)",
            r"开标时间[：:]\s*(\d{4}[-年]\d{1,2}[-月]\d{1,2}[日]?)",
        ],
        "budget": [
            r"预算[金额]*[：:]\s*([\d,.]+)\s*[万]?元",
            r"项目预算[：:]\s*([\d,.]+)\s*[万]?元",
            r"控制价[：:]\s*([\d,.]+)\s*[万]?元",
        ],
        "project_number": [
            r"项目编号[：:]\s*(.+)",
            r"招标编号[：:]\s*(.+)",
            r"采购编号[：:]\s*(.+)",
        ]
    }
    
    # 常见章节类型映射
    SECTION_TYPE_MAP = {
        "投标函": "cover",
        "投标函附录": "cover",
        "报价": "pricing",
        "报价表": "pricing",
        "商务标": "pricing",
        "资质": "qualification",
        "资质证明": "qualification",
        "资格": "qualification",
        "业绩": "performance",
        "案例": "performance",
        "项目经验": "performance",
        "团队": "team",
        "人员": "team",
        "项目团队": "team",
        "服务方案": "proposal",
        "技术方案": "proposal",
        "实施方案": "proposal",
        "服务承诺": "proposal",
        "售后": "proposal",
    }
    
    def analyze_with_docx(self, file_path: str) -> Dict:
        """使用 python-docx 分析招标文件
        
        Args:
            file_path: 文件路径
        
        Returns:
            分析结果
        """
        try:
            from docx import Document
            
            doc = Document(file_path)
            
            # 提取所有文本
            full_text = []
            for para in doc.paragraphs:
                if para.text.strip():
                    full_text.append(para.text.strip())
            
            # 提取表格文本
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        if cell.text.strip():
                            full_text.append(cell.text.strip())
            
            text = "\n".join(full_text)
            
            # 提取项目信息
            project_info = self._extract_project_info(text)
            
            # 提取章节结构
            sections = self._extract_sections(doc)
            
            return {
                "success": True,
                "project_info": project_info,
                "sections": sections,
                "text_preview": text[:2000],
                "paragraph_count": len(doc.paragraphs),
                "table_count": len(doc.tables)
            }
            
        except Exception as e:
            logger.error(f"分析招标文件失败: {e}")
            return {"success": False, "error": str(e)}
    
    def analyze_with_lexitool(self, file_path: str) -> Dict:
        """使用 lexitool 分析招标文件
        
        Args:
            file_path: 文件路径
        
        Returns:
            分析结果
        """
        try:
            import sys
            sys.path.insert(0, '/opt/lexitool')
            from lexitool.api import stats, doc_stats
            
            # 获取文档统计信息
            doc_info = stats(file_path)
            
            # 使用 python-docx 提取内容
            return self.analyze_with_docx(file_path)
            
        except Exception as e:
            logger.warning(f"lexitool 分析失败，回退到 python-docx: {e}")
            return self.analyze_with_docx(file_path)
    
    def _extract_project_info(self, text: str) -> Dict:
        """从文本中提取项目信息"""
        info = {}
        
        for field, patterns in self.FIELD_PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, text)
                if match:
                    value = match.group(1).strip()
                    # 清理值
                    value = value.rstrip("。．.")
                    if value:
                        info[field] = value
                        break
        
        # 解析日期
        if "deadline" in info:
            try:
                deadline_str = info["deadline"]
                # 尝试多种日期格式
                for fmt in ["%Y年%m月%d日", "%Y-%m-%d", "%Y/%m/%d"]:
                    try:
                        info["deadline_parsed"] = datetime.strptime(deadline_str, fmt).isoformat()
                        break
                    except:
                        continue
            except:
                pass
        
        return info
    
    def _extract_sections(self, doc) -> List[Dict]:
        """从文档中提取章节结构"""
        sections = []
        seen_titles = set()
        
        for para in doc.paragraphs:
            text = para.text.strip()
            if not text:
                continue
            
            # 检查是否是标题（通过样式或格式判断）
            is_heading = False
            heading_level = 0
            
            # 通过样式判断
            if para.style and para.style.name:
                style_name = para.style.name.lower()
                if 'heading' in style_name or '标题' in style_name:
                    is_heading = True
                    # 提取级别
                    level_match = re.search(r'(\d+)', style_name)
                    if level_match:
                        heading_level = int(level_match.group(1))
            
            # 通过格式判断（加粗、字号大等）
            if not is_heading:
                for run in para.runs:
                    if run.bold and len(text) < 50:
                        is_heading = True
                        break
            
            # 通过编号模式判断
            if not is_heading:
                # 匹配 "一、" "1." "第一章" 等模式
                if re.match(r'^[一二三四五六七八九十]+[、．.]', text) or \
                   re.match(r'^第[一二三四五六七八九十百]+[章节部分]', text) or \
                   re.match(r'^\d+[.、．]', text):
                    is_heading = True
            
            if is_heading and len(text) < 80 and text not in seen_titles:
                seen_titles.add(text)
                
                # 判断章节类型
                section_type = self._guess_section_type(text)
                
                sections.append({
                    "title": text,
                    "level": heading_level,
                    "section_type": section_type,
                    "order": len(sections) + 1
                })
        
        return sections
    
    def _guess_section_type(self, title: str) -> str:
        """根据标题猜测章节类型"""
        title_lower = title.lower()
        
        for keyword, section_type in self.SECTION_TYPE_MAP.items():
            if keyword in title_lower:
                return section_type
        
        return "other"
    
    def analyze_pdf(self, file_path: str) -> Dict:
        """分析 PDF 格式的招标文件"""
        try:
            import fitz
            
            doc = fitz.open(file_path)
            full_text = []
            
            for page in doc:
                full_text.append(page.get_text())
            
            text = "\n".join(full_text)
            doc.close()
            
            # 提取项目信息
            project_info = self._extract_project_info(text)
            
            # PDF 无法直接提取章节结构，尝试从文本中识别
            sections = self._extract_sections_from_text(text)
            
            return {
                "success": True,
                "project_info": project_info,
                "sections": sections,
                "text_preview": text[:2000],
                "page_count": len(doc) if doc else 0
            }
            
        except Exception as e:
            logger.error(f"分析 PDF 招标文件失败: {e}")
            return {"success": False, "error": str(e)}
    
    def _extract_sections_from_text(self, text: str) -> List[Dict]:
        """从纯文本中提取章节结构"""
        sections = []
        seen_titles = set()
        
        lines = text.split("\n")
        for line in lines:
            line = line.strip()
            if not line or len(line) > 80:
                continue
            
            # 匹配章节标题模式
            is_section = False
            section_type = "other"
            
            # 一、二、三、... 格式
            if re.match(r'^[一二三四五六七八九十]+[、．.]', line):
                is_section = True
            # 第一章/节/部分 格式
            elif re.match(r'^第[一二三四五六七八九十百]+[章节部分]', line):
                is_section = True
            # 1. 2. 3. 格式（且内容较短）
            elif re.match(r'^\d+[.、．]\s*\S', line) and len(line) < 30:
                is_section = True
            
            if is_section and line not in seen_titles:
                seen_titles.add(line)
                section_type = self._guess_section_type(line)
                sections.append({
                    "title": line,
                    "level": 0,
                    "section_type": section_type,
                    "order": len(sections) + 1
                })
        
        return sections


# 全局实例
tender_analyzer = TenderAnalyzer()
