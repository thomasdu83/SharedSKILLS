import os
from pathlib import Path
from typing import Optional
from pydantic import Field
try:
    from pydantic_settings import BaseSettings
except ImportError:
    # Fallback if pydantic-settings not installed, though it should be in modern pydantic envs
    # If not, we might need to use standard pydantic with env reading manual or assume pydantic v1
    # Given the environment, I'll assume standard pydantic v2 compatible approach or simple class
    from pydantic import BaseModel as BaseSettings

class TextPipeConfig(BaseSettings):
    """TextPipe 全局配置"""
    
    # OCR Settings
    OCR_ENABLED: bool = True
    OCR_DPI: int = 300
    OCR_LANG: str = "chi_sim+eng"
    OCR_MIN_TOTAL_CHARS: int = 100
    OCR_MIN_CHARS_PER_PAGE: int = 50
    OCR_MIN_VALID_CHAR_RATIO: float = 0.30
    OCR_MAX_REPEATED_SHORT_LINE_RATIO: float = 0.28
    OCR_REPEATED_SHORT_LINE_MAX_LEN: int = 24
    OCR_MAX_NOISE_CHAR_RATIO: float = 0.45

    # Layout Settings
    PDF_HEADER_RATIO: float = 0.10
    PDF_FOOTER_RATIO: float = 0.10
    PDF_SPAN_GAP_SPACE_MULTIPLIER: float = 2.0
    PDF_TABLE_MIN_CELLS: int = 12
    PDF_EXTRACT_TABLES: bool = True
    
    # Tesseract Path (Windows default)
    TESSERACT_CMD: str = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

    # Cleaning Settings
    SENSITIVE_WORDS_PATH: str = str(Path(__file__).parent / "敏感词库.yaml")

    class Config:
        env_prefix = "TEXTPIPE_"
        case_sensitive = True

# Global instance
settings = TextPipeConfig()
