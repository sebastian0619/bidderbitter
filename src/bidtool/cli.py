"""CLI 入口"""
import click
from pathlib import Path


@click.group()
@click.version_option(version="0.1.0")
def main():
    """BidTool - 投标文件工具"""
    pass


# ==================== PDF 命令 ====================

@main.group()
def pdf():
    """PDF 相关操作"""
    pass


@pdf.command("merge")
@click.argument("files", nargs=-1, required=True)
@click.option("-o", "--output", default="merged.pdf", help="输出文件路径")
def pdf_merge(files, output):
    """合并多个 PDF 文件"""
    from bidtool.core.pdf import merge_pdfs

    # 如果传入的是目录，获取目录下所有 PDF
    input_paths = []
    for f in files:
        p = Path(f)
        if p.is_dir():
            input_paths.extend(sorted(p.glob("*.pdf")))
        elif p.is_file():
            input_paths.append(p)
        else:
            click.echo(f"跳过: {f}")
            continue

    if not input_paths:
        click.echo("没有找到 PDF 文件")
        return

    click.echo(f"合并 {len(input_paths)} 个 PDF 文件...")
    result = merge_pdfs([str(p) for p in input_paths], output)
    click.echo(f"完成: {result}")


@pdf.command("extract-images")
@click.argument("file")
@click.option("-o", "--output", default="./images", help="输出目录")
@click.option("--min-size", default="100x100", help="最小图片尺寸 (如: 200x200)")
def pdf_extract_images(file, output, min_size):
    """从 PDF 中提取所有图片"""
    from bidtool.core.pdf import extract_images_from_pdf

    w, h = map(int, min_size.split("x"))
    images = extract_images_from_pdf(file, output, min_size=(w, h))
    click.echo(f"提取了 {len(images)} 张图片到 {output}")


@pdf.command("info")
@click.argument("file")
def pdf_info(file):
    """显示 PDF 文件信息"""
    from bidtool.core.pdf import get_pdf_info

    info = get_pdf_info(file)
    click.echo(f"文件: {info['path']}")
    click.echo(f"页数: {info['page_count']}")
    if info.get("metadata"):
        for k, v in info["metadata"].items():
            if v:
                click.echo(f"{k}: {v}")


# ==================== Image 命令 ====================

@main.group()
def image():
    """图片相关操作"""
    pass


@image.command("to-pdf")
@click.argument("files", nargs=-1, required=True)
@click.option("-o", "--output", default="output.pdf", help="输出文件路径")
def image_to_pdf(files, output):
    """将多张图片合并为一个 PDF"""
    from bidtool.core.image import images_to_pdf

    # 如果传入的是目录，获取目录下所有图片
    image_paths = []
    img_exts = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff"}
    for f in files:
        p = Path(f)
        if p.is_dir():
            image_paths.extend(
                sorted(img for img in p.iterdir() if img.suffix.lower() in img_exts)
            )
        elif p.is_file() and p.suffix.lower() in img_exts:
            image_paths.append(p)
        else:
            click.echo(f"跳过: {f}")

    if not image_paths:
        click.echo("没有找到图片文件")
        return

    click.echo(f"将 {len(image_paths)} 张图片合并为 PDF...")
    result = images_to_pdf([str(p) for p in image_paths], output)
    click.echo(f"完成: {result}")


# ==================== Extract 命令 ====================

@main.group()
def extract():
    """智能提取操作"""
    pass


@extract.command("performance")
@click.argument("file")
@click.option("-o", "--output", default="./output", help="输出目录")
@click.option("--start-para", default=658, help="业绩开始段落索引")
@click.option("--end-para", default=762, help="业绩结束段落索引")
def extract_performance(file, output, start_para, end_para):
    """从 Word 文档中提取业绩图片并按名称生成 PDF"""
    from bidtool.extractors.performance import extract_performance_from_docx

    click.echo(f"从 {file} 中提取业绩...")
    results = extract_performance_from_docx(
        file,
        output,
        start_para=start_para,
        end_para=end_para,
    )

    click.echo(f"\n提取完成，共 {len(results)} 个业绩项目：")
    for r in results:
        click.echo(f"  [{r['section']}] {r['name']} ({r['image_count']} 张图片)")


# ==================== Batch 命令 ====================

@main.group()
def batch():
    """批量操作"""
    pass


@batch.command("extract")
@click.argument("input_dir")
@click.option("-o", "--output", default="./output", help="输出目录")
def batch_extract(input_dir, output):
    """批量提取业绩"""
    from bidtool.extractors.performance import extract_performance_from_docx

    input_path = Path(input_dir)
    docx_files = list(input_path.glob("**/*.docx"))

    if not docx_files:
        click.echo("没有找到 .docx 文件")
        return

    click.echo(f"找到 {len(docx_files)} 个 Word 文件")
    for docx_file in docx_files:
        click.echo(f"\n处理: {docx_file.name}")
        try:
            results = extract_performance_from_docx(
                str(docx_file),
                str(Path(output) / docx_file.stem),
            )
            click.echo(f"  提取了 {len(results)} 个业绩项目")
        except Exception as e:
            click.echo(f"  错误: {e}")


if __name__ == "__main__":
    main()
