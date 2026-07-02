"""业绩提取器 - 从 Word 文档中提取业绩图片并按名称生成 PDF"""
from pathlib import Path
from lxml import etree
from PIL import Image
import re
import zipfile
import tempfile
import shutil


NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "wp": "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
}

# 默认的业绩段落范围（基于光大投标文件的经验值）
DEFAULT_PERFORMANCE_START = 658
DEFAULT_PERFORMANCE_END = 762


def extract_performance_from_docx(
    docx_path: str,
    output_dir: str,
    start_para: int = DEFAULT_PERFORMANCE_START,
    end_para: int = DEFAULT_PERFORMANCE_END,
) -> list[dict]:
    """
    从 Word 文档中提取业绩图片并按名称生成 PDF

    Args:
        docx_path: Word 文件路径
        output_dir: 输出目录
        start_para: 业绩开始段落索引
        end_para: 业绩结束段落索引

    Returns:
        业绩条目列表 [{"name": str, "section": str, "pdf_path": str, "image_count": int}]
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 临时目录解压 docx
    with tempfile.TemporaryDirectory() as tmp_dir:
        # 解压
        extract_docx_to_dir(docx_path, tmp_dir)

        # 解析 relationships 获取 rId -> image 映射
        rid_map = parse_relationships(tmp_dir)

        # 解析 document.xml 获取段落
        paragraphs = parse_document(tmp_dir)

        # 提取业绩
        results = []
        current_section = None
        current_project = None
        current_images = []

        for i in range(start_para, min(end_para, len(paragraphs))):
            para = paragraphs[i]
            text = para["text"]
            images = para["images"]

            # 检测分类标题
            if "金融业常年法律服务项目的业绩经验" in text:
                _save_current(results, current_section, current_project, current_images, output_dir, tmp_dir)
                current_section = "金融业常年法律服务项目"
                current_project = None
                current_images = []
                continue
            elif "上市公司、国有企业、政府机关常年法律服务项目业绩经验" in text:
                _save_current(results, current_section, current_project, current_images, output_dir, tmp_dir)
                current_section = "上市公司国有企业政府机关常年法律服务项目"
                current_project = None
                current_images = []
                continue

            # 情况1: 只有文字没有图片 - 新项目名称
            if text and not images and current_section:
                _save_current(results, current_section, current_project, current_images, output_dir, tmp_dir)
                current_images = []
                current_project = text

            # 情况2: 有文字也有图片 - 项目名称和部分图片在同一段落
            elif text and images and current_section:
                _save_current(results, current_section, current_project, current_images, output_dir, tmp_dir)
                current_project = text
                current_images = images

            # 情况3: 只有图片没有文字 - 追加到当前项目
            elif images and not text and current_project:
                current_images.extend(images)

        # 保存最后一个
        _save_current(results, current_section, current_project, current_images, output_dir, tmp_dir)

        return results


def extract_docx_to_dir(docx_path: str, output_dir: str):
    """解压 docx 到指定目录"""
    with zipfile.ZipFile(docx_path, "r") as z:
        z.extractall(output_dir)


def parse_relationships(tmp_dir: str) -> dict:
    """解析 relationships 文件，返回 rId -> image 文件名映射"""
    rels_path = Path(tmp_dir) / "word" / "_rels" / "document.xml.rels"
    rid_map = {}
    if rels_path.exists():
        tree = etree.parse(str(rels_path))
        for rel in tree.findall(".//rel:Relationship", NS):
            rid = rel.get("Id")
            target = rel.get("Target")
            if target and "media/image" in target:
                rid_map[rid] = target.replace("media/", "")
    return rid_map


def parse_document(tmp_dir: str) -> list[dict]:
    """解析 document.xml，返回段落列表"""
    doc_path = Path(tmp_dir) / "word" / "document.xml"
    paragraphs = []
    if doc_path.exists():
        tree = etree.parse(str(doc_path))
        body = tree.find(".//w:body", NS)
        for para in body.findall(".//w:p", NS):
            text = _get_para_text(para)
            images = _get_para_images(para)
            paragraphs.append({"text": text, "images": images})
    return paragraphs


def _get_para_text(para) -> str:
    """获取段落文本"""
    text = ""
    for run in para.findall(".//w:r", NS):
        for t in run.findall(".//w:t", NS):
            if t.text:
                text += t.text
    return text.strip()


def _get_para_images(para) -> list[str]:
    """获取段落中的图片 rId"""
    images = []
    for drawing in para.findall(".//w:drawing", NS):
        for inline in drawing.findall(".//wp:inline", NS):
            blip = inline.find(".//a:blip", NS)
            if blip is not None:
                rid = blip.get(
                    "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed"
                )
                if rid:
                    images.append(rid)
        for anchor in drawing.findall(".//wp:anchor", NS):
            blip = anchor.find(".//a:blip", NS)
            if blip is not None:
                rid = blip.get(
                    "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed"
                )
                if rid:
                    images.append(rid)
    return images


def _sanitize_filename(name: str, max_len: int = 50) -> str:
    """清理文件名"""
    name = re.sub(r'[<>:"/\\|?*]', "", name)
    name = name.replace("(", "（").replace(")", "）")
    if len(name) > max_len:
        name = name[:max_len]
    return name.strip()


def _save_current(
    results: list,
    section: str | None,
    project: str | None,
    images: list[str],
    output_dir: Path,
    tmp_dir: str = None,
):
    """保存当前业绩并生成 PDF"""
    if not project or not images or not section:
        return

    # 获取当前临时目录
    if tmp_dir is None:
        # 从 results 推断 tmp_dir（应该从调用方传入）
        return

    rid_map = parse_relationships(tmp_dir)
    media_dir = Path(tmp_dir) / "word" / "media"

    # 映射 rId 到实际图片路径
    image_paths = []
    for rid in images:
        if rid in rid_map:
            img_file = media_dir / rid_map[rid]
            if img_file.exists():
                image_paths.append(str(img_file))

    if not image_paths:
        return

    # 创建分类目录
    section_dir = output_dir / _sanitize_filename(section)
    section_dir.mkdir(parents=True, exist_ok=True)

    # 生成 PDF
    safe_name = _sanitize_filename(project)
    idx = len([r for r in results if r["section"] == section]) + 1
    pdf_name = f"{idx:02d}_{safe_name}.pdf"
    pdf_path = section_dir / pdf_name

    _images_to_pdf(image_paths, str(pdf_path))

    results.append({
        "name": project,
        "section": section,
        "pdf_path": str(pdf_path),
        "image_count": len(image_paths),
    })


def _images_to_pdf(image_paths: list[str], output_path: str):
    """将多张图片合并为 PDF"""
    img_list = []
    for path in image_paths:
        try:
            img = Image.open(path)
            if img.mode != "RGB":
                img = img.convert("RGB")
            img_list.append(img)
        except Exception:
            continue

    if not img_list:
        return

    first = img_list[0]
    if len(img_list) > 1:
        first.save(output_path, save_all=True, append_images=img_list[1:])
    else:
        first.save(output_path)
