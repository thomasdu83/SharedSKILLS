# TextPipe: Unified Document Parsing Service

TextPipe 是一个用于 QuantSystem 的统一文档解析服务，旨在提供一致、健壮的文本提取能力。它整合了 PDF（支持 OCR 与 Layout 分析）、Word、PowerPoint、Markdown 和纯文本的解析逻辑。

## 功能特性

- **多格式支持**: PDF, DOCX, PPTX, TXT, MD
- **智能 PDF 解析**:
  - **Layout 分析**: 保持阅读顺序，处理双栏排版。
  - **OCR 回退**: 自动检测文本质量（乱码、重复行、字符密度），必要时回退到 OCR。
  - **表格提取**: 自动识别 PDF 表格并转换为 Markdown 格式插入文本流。
  - **清洗优化**: 自动处理页眉页脚、去除水印干扰。
- **统一接口**: 所有格式返回统一的 `DocumentResult` 对象。
- **配置驱动**: 通过 Pydantic 模型和环境变量管理配置。

## 快速开始

### 安装

确保已安装依赖：

```bash
pip install pymupdf pytesseract pillow python-docx python-pptx pydantic pydantic-settings
```

并且已安装 Tesseract OCR 引擎（如需 OCR 功能）。

### 使用示例

确保 `QuantSystem` 项目根目录在 `PYTHONPATH` 中，或者作为包的一部分运行。

```python
# 注意：TextPipe 位于 utils 包下
from utils.textpipe import parse_file, TextPipe, ParsingOptions

# 1. 简单用法
result = parse_file("report.pdf")
if result.status == "success":
    print(result.content)
    print(result.metadata)

# 2. 高级用法（自定义配置）
pipe = TextPipe()
options = ParsingOptions(
    ocr_enabled=True,
    ocr_lang="chi_sim+eng",
    extract_tables=True,
    header_ratio=0.12
)

result = pipe.parse("strategy.pptx", options)
```

## 数据结构

### DocumentResult

- `content` (str): 解析后的全文内容。
- `metadata` (DocumentMetadata): 元数据（页数、耗时、文件大小等）。
- `status` (str): "success" 或 "error"。
- `error_message` (str): 错误信息（如果有）。

### ParsingOptions

- `ocr_enabled` (bool): 是否启用 OCR 回退。
- `ocr_lang` (str): OCR 语言（默认 "chi_sim+eng"）。
- `extract_tables` (bool): 是否提取 PDF 表格为 Markdown。
- `header_ratio` (float): 页眉切除比例。
- `footer_ratio` (float): 页脚切除比例。

## 工程规范

本项目遵循 QuantSystem 工程标准：
- **Fail Fast**: 参数校验优先。
- **Type Hints**: 全面类型注解。
- **Logging**: 使用 `logging` 模块而非 `print`。
- **Modular**: 职责分离，核心逻辑在 `parsers/` 目录下。
