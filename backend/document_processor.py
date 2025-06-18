import os
import logging
import time
from datetime import datetime
import uuid
import fitz  # PyMuPDF
import magic
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.section import WD_SECTION_START
from PIL import Image
import io
import asyncio
from typing import List, Dict, Any, Optional, Tuple
import shutil

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 输出目录配置
UPLOAD_DIR = os.environ.get("UPLOAD_PATH", "/app/uploads")
CONVERTED_DIR = os.path.join(UPLOAD_DIR, "converted")
GENERATED_DIR = os.environ.get("GENERATED_DOCS_PATH", "/app/generated_docs")

# 确保目录存在
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(CONVERTED_DIR, exist_ok=True)
os.makedirs(GENERATED_DIR, exist_ok=True)

class DocumentProcessor:
    """文档处理服务"""
    
    @staticmethod
    async def detect_file_type(file_path: str) -> str:
        """检测文件类型"""
        mime = magic.Magic(mime=True)
        mime_type = mime.from_file(file_path)
        return mime_type
    
    @staticmethod
    async def convert_to_word(file_path: str, filename: str = None) -> Tuple[str, int]:
        """
        将文件转换为Word格式
        
        参数:
        - file_path: 源文件路径
        - filename: 输出文件名(可选)
        
        返回:
        - 转换后的Word文档路径
        - 文档页数
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        # 检测文件类型
        mime_type = await DocumentProcessor.detect_file_type(file_path)
        logger.info(f"文件类型: {mime_type}")
        
        # 生成输出文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if not filename:
            filename = os.path.basename(file_path)
            basename, _ = os.path.splitext(filename)
        else:
            basename = filename
        
        output_filename = f"{basename}_{timestamp}.docx"
        output_path = os.path.join(CONVERTED_DIR, output_filename)
        
        # 根据文件类型调用相应的转换方法
        if "pdf" in mime_type.lower():
            return await DocumentProcessor.convert_pdf_to_word(file_path, output_path)
        elif "image" in mime_type.lower():
            return await DocumentProcessor.convert_image_to_word(file_path, output_path)
        elif "word" in mime_type.lower() or mime_type.endswith('document'):
            # 如果已经是Word文档，复制一份到转换目录
            shutil.copy2(file_path, output_path)
            
            # 尝试获取页数
            try:
                doc = Document(file_path)
                # Word文档页数计算不精确，这里估算一个值
                page_count = len(doc.paragraphs) // 40 + 1  # 假设每页40段落
            except:
                page_count = 1
            
            return output_path, page_count
        else:
            raise ValueError(f"不支持的文件类型: {mime_type}")

    @staticmethod
    async def convert_pdf_to_word(pdf_path: str, output_path: str) -> Tuple[str, int]:
        """
        将PDF转换为Word文档
        
        参数:
        - pdf_path: PDF文件路径
        - output_path: 输出Word文档路径
        
        返回:
        - 转换后的Word文档路径
        - PDF页数
        """
        # 创建Word文档
        doc = Document()
        
        try:
            # 打开PDF
            pdf_document = fitz.open(pdf_path)
            page_count = len(pdf_document)
            
            for page_num in range(len(pdf_document)):
                page = pdf_document.load_page(page_num)
                
                # 添加页面标题
                if page_num > 0:  # 第一页不添加页面分隔标题
                    doc.add_heading(f"第 {page_num + 1} 页", level=2)
                
                # 获取文本（以防万一，可能有些可提取文本）
                text = page.get_text()
                if text.strip():
                    doc.add_paragraph(text)
                
                # 将页面渲染为图片
                pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))
                img_data = pix.tobytes("png")
                
                # 创建临时图片文件
                img_stream = io.BytesIO(img_data)
                
                # 添加图片到Word
                doc.add_picture(img_stream, width=Inches(6))
                
                # 添加分页符（除最后一页）
                if page_num < len(pdf_document) - 1:
                    doc.add_page_break()
            
            # 保存Word文档
            doc.save(output_path)
            pdf_document.close()
            
            return output_path, page_count
            
        except Exception as e:
            logger.error(f"PDF转Word失败: {str(e)}")
            raise
    
    @staticmethod
    async def convert_image_to_word(image_path: str, output_path: str) -> Tuple[str, int]:
        """
        将图片转换为Word文档
        
        参数:
        - image_path: 图片文件路径
        - output_path: 输出Word文档路径
        
        返回:
        - 转换后的Word文档路径
        - 页数(图片为1页)
        """
        # 创建Word文档
        doc = Document()
        
        try:
            # 获取图片信息
            with Image.open(image_path) as img:
                width, height = img.size
                
                # 添加简要说明
                p = doc.add_paragraph()
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                run = p.add_run(f"图片尺寸: {width} x {height} 像素")
                run.italic = True
                run.font.size = Pt(9)
                run.font.color.rgb = RGBColor(128, 128, 128)
            
            # 添加图片
            doc.add_picture(image_path, width=Inches(6))
            
            # 保存Word文档
            doc.save(output_path)
            
            return output_path, 1  # 图片算作1页
            
        except Exception as e:
            logger.error(f"图片转Word失败: {str(e)}")
            raise
    
    @staticmethod
    async def merge_documents(document_paths: List[str], output_filename: str = None) -> Tuple[str, int, float]:
        """
        合并多个Word文档为一个
        
        参数:
        - document_paths: 待合并Word文档路径列表
        - output_filename: 输出文件名(可选)
        
        返回:
        - 合并后的文档路径
        - 总页数
        - 处理时间(秒)
        """
        if not document_paths:
            raise ValueError("没有要合并的文档")
        
        start_time = time.time()
        
        # 生成输出文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if not output_filename:
            output_filename = f"merged_{timestamp}.docx"
        
        output_path = os.path.join(GENERATED_DIR, output_filename)
        
        # 创建新文档作为主文档
        master_doc = Document()
        total_pages = 0
        
        try:
            # 遍历每个文档并合并
            for i, doc_path in enumerate(document_paths):
                # 打开子文档
                if not os.path.exists(doc_path):
                    logger.warning(f"文档不存在，已跳过: {doc_path}")
                    continue
                    
                try:
                    sub_doc = Document(doc_path)
                except Exception as e:
                    logger.error(f"无法打开文档 {doc_path}: {str(e)}")
                    continue
                
                # 添加分节符(除了第一个文档)
                if i > 0:
                    master_doc.add_section(WD_SECTION_START.NEW_PAGE)
                
                # 复制所有段落
                for para in sub_doc.paragraphs:
                    p = master_doc.add_paragraph()
                    p.paragraph_format.alignment = para.paragraph_format.alignment
                    p.paragraph_format.left_indent = para.paragraph_format.left_indent
                    p.paragraph_format.right_indent = para.paragraph_format.right_indent
                    p.paragraph_format.space_before = para.paragraph_format.space_before
                    p.paragraph_format.space_after = para.paragraph_format.space_after
                    p.paragraph_format.line_spacing = para.paragraph_format.line_spacing
                    
                    for run in para.runs:
                        r = p.add_run(run.text)
                        r.bold = run.bold
                        r.italic = run.italic
                        r.underline = run.underline
                        if run.font.size:
                            r.font.size = run.font.size
                        if run.font.color.rgb:
                            r.font.color.rgb = run.font.color.rgb
                
                # 复制所有表格
                for table in sub_doc.tables:
                    tbl = master_doc.add_table(rows=0, cols=len(table.columns))
                    tbl.style = table.style
                    
                    for row in table.rows:
                        new_row = tbl.add_row()
                        for idx, cell in enumerate(row.cells):
                            if idx < len(new_row.cells):  # 防止列索引越界
                                new_cell = new_row.cells[idx]
                                new_cell.text = cell.text
                                for paragraph in cell.paragraphs:
                                    for run in paragraph.runs:
                                        for i, char in enumerate(run.text):
                                            if i < len(new_cell.paragraphs[0].runs):
                                                new_run = new_cell.paragraphs[0].runs[i]
                                                new_run.bold = run.bold
                                                new_run.italic = run.italic
                                                if run.font.size:
                                                    new_run.font.size = run.font.size
                
                # 复制图片和其他形状
                for shape in sub_doc.inline_shapes:
                    try:
                        if shape.type == 3:  # 图片
                            # 提取图片，保存为临时文件，然后添加到主文档
                            img_stream = io.BytesIO()
                            if hasattr(shape, '_inline') and hasattr(shape._inline, 'graphic') and \
                               hasattr(shape._inline.graphic, 'graphicData') and \
                               hasattr(shape._inline.graphic.graphicData, 'pic'):
                                
                                blob = shape._inline.graphic.graphicData.pic.blipFill.blip.embed
                                if hasattr(sub_doc.part, 'related_parts') and blob in sub_doc.part.related_parts:
                                    image_part = sub_doc.part.related_parts[blob]
                                    if hasattr(image_part, 'blob'):
                                        img_stream.write(image_part.blob)
                                        img_stream.seek(0)
                                        master_doc.add_picture(img_stream, width=shape.width, height=shape.height)
                    except Exception as img_err:
                        logger.error(f"复制图片失败: {str(img_err)}")
                
                # 估算页数(粗略估计)
                doc_pages = len(sub_doc.paragraphs) // 40 + 1
                total_pages += doc_pages
            
            # 保存合并后的文档
            master_doc.save(output_path)
            
            # 计算处理时间
            processing_time = time.time() - start_time
            
            return output_path, total_pages, processing_time
            
        except Exception as e:
            logger.error(f"合并文档失败: {str(e)}")
            raise
    
    @staticmethod
    async def fill_template(template_path: str, field_values: Dict[str, Any], output_filename: str = None) -> str:
        """
        填充Word模板
        
        参数:
        - template_path: 模板文件路径
        - field_values: 字段值字典 {field_key: value}
        - output_filename: 输出文件名(可选)
        
        返回:
        - 填充后的文档路径
        """
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"模板文件不存在: {template_path}")
        
        # 生成输出文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if not output_filename:
            basename = os.path.basename(template_path)
            name, _ = os.path.splitext(basename)
            output_filename = f"{name}_filled_{timestamp}.docx"
        
        output_path = os.path.join(GENERATED_DIR, output_filename)
        
        try:
            # 打开文档
            doc = Document(template_path)
            
            # 替换所有段落中的占位符
            for paragraph in doc.paragraphs:
                for key, value in field_values.items():
                    # 支持多种占位符格式
                    placeholders = [
                        f"{{${key}$}}",  # {$field_key$}
                        f"{{{key}}}",    # {field_key}
                        f"${key}$",      # $field_key$
                        f"[[{key}]]"     # [[field_key]]
                    ]
                    
                    for placeholder in placeholders:
                        if placeholder in paragraph.text:
                            str_value = str(value) if value is not None else ""
                            paragraph.text = paragraph.text.replace(placeholder, str_value)
            
            # 替换表格中的占位符
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        for paragraph in cell.paragraphs:
                            for key, value in field_values.items():
                                placeholders = [
                                    f"{{${key}$}}",
                                    f"{{{key}}}",
                                    f"${key}$",
                                    f"[[{key}]]"
                                ]
                                
                                for placeholder in placeholders:
                                    if placeholder in paragraph.text:
                                        str_value = str(value) if value is not None else ""
                                        paragraph.text = paragraph.text.replace(placeholder, str_value)
            
            # 保存文档
            doc.save(output_path)
            
            return output_path
            
        except Exception as e:
            logger.error(f"填充模板失败: {str(e)}")
            raise
    
    @staticmethod
    async def analyze_template_fields(template_path: str) -> List[Dict[str, Any]]:
        """
        分析模板中的字段
        
        参数:
        - template_path: 模板文件路径
        
        返回:
        - 字段列表
        """
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"模板文件不存在: {template_path}")
        
        try:
            doc = Document(template_path)
            fields = []
            
            # 定义可能的占位符正则模式
            # 这里使用简单字符串匹配而非正则，以便于演示
            placeholders_patterns = [
                ("{$", "$}"),   # {$field_key$}
                ("{", "}"),     # {field_key}
                ("$", "$"),     # $field_key$
                ("[[", "]]")    # [[field_key]]
            ]
            
            # 提取段落中的字段
            for paragraph in doc.paragraphs:
                text = paragraph.text
                
                for start_pat, end_pat in placeholders_patterns:
                    start_idx = 0
                    while True:
                        start_pos = text.find(start_pat, start_idx)
                        if start_pos == -1:
                            break
                            
                        end_pos = text.find(end_pat, start_pos + len(start_pat))
                        if end_pos == -1:
                            break
                            
                        # 提取字段名
                        field_key = text[start_pos + len(start_pat):end_pos]
                        
                        # 判断字段类型
                        field_type = "text"  # 默认为文本
                        if "date" in field_key.lower() or "日期" in field_key:
                            field_type = "date"
                        elif "number" in field_key.lower() or "金额" in field_key or "数量" in field_key:
                            field_type = "number"
                            
                        # 添加到结果
                        field = {
                            "field_key": field_key,
                            "field_name": field_key.replace("_", " ").title(),
                            "field_type": field_type,
                            "placeholder": text[start_pos:end_pos + len(end_pat)]
                        }
                        
                        # 检查是否已存在
                        if not any(f["field_key"] == field_key for f in fields):
                            fields.append(field)
                            
                        start_idx = end_pos + len(end_pat)
            
            # 提取表格中的字段
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        for paragraph in cell.paragraphs:
                            text = paragraph.text
                            
                            for start_pat, end_pat in placeholders_patterns:
                                start_idx = 0
                                while True:
                                    start_pos = text.find(start_pat, start_idx)
                                    if start_pos == -1:
                                        break
                                        
                                    end_pos = text.find(end_pat, start_pos + len(start_pat))
                                    if end_pos == -1:
                                        break
                                        
                                    field_key = text[start_pos + len(start_pat):end_pos]
                                    
                                    # 判断字段类型
                                    field_type = "text"
                                    if "date" in field_key.lower() or "日期" in field_key:
                                        field_type = "date"
                                    elif "number" in field_key.lower() or "金额" in field_key or "数量" in field_key:
                                        field_type = "number"
                                        
                                    field = {
                                        "field_key": field_key,
                                        "field_name": field_key.replace("_", " ").title(),
                                        "field_type": field_type,
                                        "placeholder": text[start_pos:end_pos + len(end_pat)]
                                    }
                                    
                                    if not any(f["field_key"] == field_key for f in fields):
                                        fields.append(field)
                                        
                                    start_idx = end_pos + len(end_pat)
            
            return fields
            
        except Exception as e:
            logger.error(f"分析模板字段失败: {str(e)}")
            raise

# 单例实例
document_processor = DocumentProcessor() 