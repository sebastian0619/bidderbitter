"""Word 文档解析模块"""
from pathlib import Path
from lxml import etree
import zipfile


NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "wp": "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
}


def extract_docx(docx_path: str, output_dir: str) -> dict:
    """解压 docx 文件，返回结构信息"""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(docx_path, "r") as z:
        z.extractall(output_dir)

    # 解析 relationships
    rels_path = output_dir / "word" / "_rels" / "document.xml.rels"
    rid_map = {}
    if rels_path.exists():
        tree = etree.parse(str(rels_path))
        for rel in tree.findall(".//rel:Relationship", NS):
            rid = rel.get("Id")
            target = rel.get("Target")
            if target and "media/image" in target:
                rid_map[rid] = target.replace("media/", "")

    # 解析 document.xml
    doc_path = output_dir / "word" / "document.xml"
    paragraphs = []
    if doc_path.exists():
        tree = etree.parse(str(doc_path))
        body = tree.find(".//w:body", NS)
        for i, para in enumerate(body.findall(".//w:p", NS)):
            text = _get_para_text(para)
            images = _get_para_images(para)
            paragraphs.append({"idx": i, "text": text, "images": images})

    return {
        "output_dir": str(output_dir),
        "rid_map": rid_map,
        "paragraphs": paragraphs,
    }


def get_para_text(para) -> str:
    """获取段落文本"""
    return _get_para_text(para)


def get_para_images(para) -> list[str]:
    """获取段落中的图片 rId"""
    return _get_para_images(para)


def _get_para_text(para) -> str:
    text = ""
    for run in para.findall(".//w:r", NS):
        for t in run.findall(".//w:t", NS):
            if t.text:
                text += t.text
    return text.strip()


def _get_para_images(para) -> list[str]:
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
