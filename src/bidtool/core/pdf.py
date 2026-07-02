"""PDF 处理模块"""
from pathlib import Path
import pymupdf


def merge_pdfs(input_paths: list[str], output_path: str) -> str:
    """合并多个 PDF 文件"""
    doc = pymupdf.open()
    for path in input_paths:
        src = pymupdf.open(path)
        doc.insert_pdf(src)
        src.close()
    doc.save(output_path)
    doc.close()
    return output_path


def extract_images_from_pdf(
    pdf_path: str,
    output_dir: str,
    min_size: tuple[int, int] = (100, 100),
) -> list[str]:
    """从 PDF 中提取所有图片"""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open(pdf_path)
    extracted = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        images = page.get_images(full=True)
        for img_idx, img_info in enumerate(images):
            xref = img_info[0]
            try:
                pix = pymupdf.Pixmap(doc, xref)
                if pix.width < min_size[0] or pix.height < min_size[1]:
                    continue
                if pix.n > 4:
                    pix = pymupdf.Pixmap(pymupdf.csRGB, pix)
                ext = "png" if pix.alpha else "jpg"
                out_path = f"{output_dir}/page{page_num+1}_img{img_idx+1}.{ext}"
                pix.save(out_path)
                extracted.append(out_path)
            except Exception:
                continue
    doc.close()
    return extracted


def get_pdf_info(pdf_path: str) -> dict:
    """获取 PDF 文件信息"""
    doc = pymupdf.open(pdf_path)
    info = {
        "path": pdf_path,
        "page_count": doc.page_count,
        "metadata": doc.metadata,
    }
    doc.close()
    return info
