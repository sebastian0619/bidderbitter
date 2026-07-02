"""图片处理模块"""
from pathlib import Path
from PIL import Image


def images_to_pdf(
    image_paths: list[str],
    output_path: str,
    page_size: str = "A4",
) -> str:
    """将多张图片合并为一个 PDF"""
    img_list = []
    for path in image_paths:
        img = Image.open(path)
        if img.mode != "RGB":
            img = img.convert("RGB")
        img_list.append(img)

    if not img_list:
        raise ValueError("没有有效的图片")

    first = img_list[0]
    if len(img_list) > 1:
        first.save(output_path, save_all=True, append_images=img_list[1:])
    else:
        first.save(output_path)
    return output_path


def resize_image(
    input_path: str,
    output_path: str,
    size: tuple[int, int] = (800, 600),
) -> str:
    """调整图片大小"""
    img = Image.open(input_path)
    img = img.resize(size, Image.Resampling.LANCZOS)
    img.save(output_path)
    return output_path


def get_image_info(image_path: str) -> dict:
    """获取图片信息"""
    img = Image.open(image_path)
    return {
        "path": image_path,
        "width": img.width,
        "height": img.height,
        "format": img.format,
        "mode": img.mode,
    }
