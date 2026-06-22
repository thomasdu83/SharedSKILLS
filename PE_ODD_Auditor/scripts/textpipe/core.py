import logging
from pathlib import Path
from typing import Union, Optional, Dict, Type

from .schemas import DocumentResult, ParsingOptions
from .config import settings
from .parsers.base import BaseParser
from .parsers.pdf import PDFParser
from .parsers.general import TextParser, DocxParser, PptxParser
from .cleaner import TextCleaner

logger = logging.getLogger(__name__)

class TextPipe:
    """
    Unified Text Parsing Interface.
    Integrates multiple parsing strategies (PDF, DOCX, PPTX, TXT, MD)
    with consistent error handling and configuration.
    """
    
    def __init__(self):
        self._parsers: Dict[str, BaseParser] = {
            ".pdf": PDFParser(),
            ".txt": TextParser(),
            ".md": TextParser(),
            ".docx": DocxParser(),
            ".pptx": PptxParser()
        }
        self._cleaner = TextCleaner()
        
    def register_parser(self, extension: str, parser: BaseParser):
        """Register a new parser for a specific extension."""
        self._parsers[extension.lower()] = parser

    def parse(self, file_path: Union[str, Path], options: Optional[ParsingOptions] = None) -> DocumentResult:
        """
        Parse a document based on its extension.
        
        Args:
            file_path: Path to the file.
            options: Parsing options (optional).
            
        Returns:
            DocumentResult object containing content and metadata.
        """
        file_path = Path(file_path)
        if not file_path.exists():
            return DocumentResult(
                content="",
                metadata=None, # type: ignore
                status="error",
                error_message=f"File not found: {file_path}"
            )
            
        ext = file_path.suffix.lower()
        parser = self._parsers.get(ext)
        
        if not parser:
            return DocumentResult(
                content="",
                metadata=None, # type: ignore
                status="error",
                error_message=f"Unsupported file type: {ext}"
            )
            
        if options is None:
            options = ParsingOptions(
                ocr_enabled=settings.OCR_ENABLED,
                ocr_lang=settings.OCR_LANG,
                extract_tables=settings.PDF_EXTRACT_TABLES,
                header_ratio=settings.PDF_HEADER_RATIO,
                footer_ratio=settings.PDF_FOOTER_RATIO
            )
            
        try:
            logger.info(f"Parsing {file_path} using {parser.__class__.__name__}")
            result = parser.parse(file_path, options)
            
            if result.status == "success" and options.clean_text:
                logger.info(f"Cleaning text for {file_path.name}")
                cleaned_content = self._cleaner.clean(
                    result.content, 
                    truncate=options.truncate_content
                )
                
                # Check if truncated
                if len(cleaned_content) < len(result.content):
                    logger.info(f"Text cleaned/truncated: {len(result.content)} -> {len(cleaned_content)} chars")
                    if result.metadata:
                        result.metadata.extra["cleaned"] = True
                        result.metadata.extra["original_length"] = len(result.content)
                
                result.content = cleaned_content
                
            return result
            
        except Exception as e:
            logger.error(f"Unexpected error parsing {file_path}: {e}", exc_info=True)
            return DocumentResult(
                content="",
                metadata=None, # type: ignore
                status="error",
                error_message=f"Unexpected error: {str(e)}"
            )

# Convenience function
def parse_file(file_path: Union[str, Path], **kwargs) -> DocumentResult:
    """
    Quick helper to parse a file with default or override options.
    kwargs map to ParsingOptions fields.
    """
    pipe = TextPipe()
    # Build options from settings + kwargs
    defaults = {
        "ocr_enabled": settings.OCR_ENABLED,
        "ocr_lang": settings.OCR_LANG,
        "extract_tables": settings.PDF_EXTRACT_TABLES,
        "header_ratio": settings.PDF_HEADER_RATIO,
        "footer_ratio": settings.PDF_FOOTER_RATIO
    }
    # Update with kwargs
    for k, v in kwargs.items():
        if k in defaults or k in ParsingOptions.model_fields:
            defaults[k] = v
            
    options = ParsingOptions(**defaults)
    return pipe.parse(file_path, options)
