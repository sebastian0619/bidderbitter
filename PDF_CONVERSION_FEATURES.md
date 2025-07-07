# PDF转换功能增强说明

## 概述

系统现在支持智能PDF类型检测和处理，能够自动识别扫描件和非扫描件PDF，并采用不同的处理策略。

## 功能特性

### 1. 智能PDF类型检测

系统会自动检测PDF文件的类型：

- **扫描件PDF**: 通过OCR技术提取文本内容
- **非扫描件PDF**: 保持原始格式，转换为高质量图片
- **混合类型PDF**: 优先按非扫描件处理

### 2. 扫描件PDF处理

**适用场景**: 纸质文档扫描后的PDF文件

**处理方式**:
- 使用Docling OCR技术提取文本内容
- 在Word文档中显示提取的文本
- 同时保留原始页面图像作为参考
- 添加文档信息说明处理方式

**输出内容**:
- OCR识别的文本内容
- 原始页面图像
- 文档元数据信息

### 3. 非扫描件PDF处理

**适用场景**: 从Word、PowerPoint等软件直接生成的PDF文件

**处理方式**:
- 直接转换为高分辨率图片
- 保持原始格式和布局
- 使用3倍分辨率确保文本清晰
- 添加处理说明

**输出内容**:
- 高质量页面图像
- 处理说明信息
- 保持原始文档的视觉效果

### 4. 技术实现

#### PDF类型检测算法

```python
# 检查前3页的文本和图片比例
text_percentage = 有文本的页面数 / 检查的页面数
image_percentage = 有图片的页面数 / 检查的页面数

if text_percentage > 0.7:
    return "native"  # 非扫描件
elif image_percentage > 0.7 and text_percentage < 0.3:
    return "scanned"  # 扫描件
else:
    return "mixed"  # 混合类型
```

#### 分辨率优化

- **扫描件**: 使用2.0倍分辨率，平衡质量和文件大小
- **非扫描件**: 使用3.0倍分辨率，确保文本清晰度

#### 图片尺寸优化

- **第一页**: 使用较小尺寸，为标题留空间
- **其他页面**: 使用较大尺寸，充分利用页面空间

## 使用方法

### 1. 通过Web界面

1. 访问文件转换页面
2. 上传PDF文件（支持拖拽）
3. 系统自动检测PDF类型
4. 点击"开始转换为Word文档"
5. 下载转换结果

### 2. 通过API

```python
# 使用DoclingDocumentProcessor
processor = DoclingDocumentProcessor()
result = await processor.process_pdf_with_docling(
    pdf_path, doc, filename, 
    show_file_titles=True, 
    file_title_level=2, 
    is_last_file=True
)

# 使用DocumentProcessor
result_path, page_count = await DocumentProcessor.convert_pdf_to_word(
    pdf_path, output_path
)
```

### 3. 测试工具

运行测试脚本验证功能：

```bash
python test_pdf_conversion.py
```

## 配置选项

### 文档标题设置

- `show_file_titles`: 是否显示文件标题
- `file_title_level`: 文件标题的大纲级别
- `main_title_level`: 主标题的大纲级别

### 水印设置

- `enable_watermark`: 是否启用水印
- `watermark_text`: 水印文本内容
- `watermark_font_size`: 水印字体大小
- `watermark_opacity`: 水印透明度

### 分页设置

- `add_page_break`: 是否在文件间添加分页符
- `show_page_numbers`: 是否显示页码

## 性能优化

### 1. 内存管理

- 使用临时文件处理大PDF
- 及时清理临时文件
- 分批处理多页文档

### 2. 处理速度

- 扫描件PDF限制处理前10页图像
- 非扫描件PDF处理全部页面
- 使用异步处理提高响应速度

### 3. 文件大小

- 根据PDF类型优化分辨率
- 智能压缩图片质量
- 支持文件大小限制

## 错误处理

### 1. 常见错误

- **文件不存在**: 检查文件路径
- **文件格式不支持**: 确保是PDF格式
- **文件过大**: 检查文件大小限制
- **处理超时**: 检查网络连接

### 2. 降级处理

- Docling服务不可用时自动降级到PyMuPDF
- 类型检测失败时默认按非扫描件处理
- 单个页面处理失败时继续处理其他页面

## 更新日志

### V2.1 - PDF智能处理版本

- ✅ 新增PDF类型自动检测
- ✅ 扫描件PDF OCR文本提取
- ✅ 非扫描件PDF高质量图片转换
- ✅ 智能分辨率优化
- ✅ 处理说明和元数据
- ✅ 测试工具和文档

### 技术改进

- 优化PDF类型检测算法
- 提高非扫描件PDF的图片质量
- 改进错误处理和降级机制
- 增强用户界面提示信息

## 注意事项

1. **OCR准确性**: 扫描件OCR识别效果取决于原文档质量
2. **文件大小**: 高分辨率转换会增加输出文件大小
3. **处理时间**: 大文件或复杂文档需要更长处理时间
4. **格式保持**: 非扫描件PDF会保持原始视觉效果

## 技术支持

如有问题或建议，请：

1. 查看系统日志获取详细错误信息
2. 使用测试工具验证功能
3. 检查文件格式和大小是否符合要求
4. 联系技术支持团队 