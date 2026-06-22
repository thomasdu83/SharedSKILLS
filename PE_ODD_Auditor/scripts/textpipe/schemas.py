from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from enum import Enum

class ParsingMethod(str, Enum):
    LAYOUT = "layout"
    OCR = "ocr"
    TEXT = "text"  # Plain text reading
    UNSTRUCTURED = "unstructured" # Fallback or general

class DocumentMetadata(BaseModel):
    """文档元数据"""
    page_count: int = 0
    file_size: int = 0
    file_type: str = ""
    parsing_method: ParsingMethod = ParsingMethod.LAYOUT
    parsing_time: float = 0.0
    extra: Dict[str, Any] = Field(default_factory=dict)

class DocumentResult(BaseModel):
    """文档解析结果"""
    content: str
    metadata: Optional[DocumentMetadata] = None
    status: str = "success"  # success, error, warning
    error_message: Optional[str] = None
    
    @property
    def is_success(self) -> bool:
        return self.status == "success"

class ParsingOptions(BaseModel):
    """解析选项"""
    ocr_enabled: bool = True
    ocr_lang: str = "chi_sim+eng"
    extract_tables: bool = True
    table_to_markdown: bool = True
    header_ratio: float = 0.10
    footer_ratio: float = 0.10
    max_workers: int = 1  # For batch processing
    clean_text: bool = True # Enable sensitive word masking and truncation
    truncate_content: bool = True # Enable content truncation based on markers
