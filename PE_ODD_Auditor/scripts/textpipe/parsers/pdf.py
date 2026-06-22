try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

try:
    import pytesseract
except ImportError:
    pytesseract = None

from PIL import Image
import io
import re
import logging
from typing import List, Tuple, Dict, Any, Optional, Union
from pathlib import Path
import time

from ..schemas import DocumentResult, DocumentMetadata, ParsingOptions, ParsingMethod
from ..config import settings
from .base import BaseParser

logger = logging.getLogger(__name__)

class PDFParser(BaseParser):
    """
    Robust PDF Parser with Layout Analysis and OCR fallback.
    Based on QuantSystem engineering standards.
    """

    def parse(self, file_path: Path, options: ParsingOptions) -> DocumentResult:
        start_time = time.time()
        file_path = Path(file_path)
        
        if fitz is None:
            return DocumentResult(
                content="",
                metadata=DocumentMetadata(file_type=".pdf", parsing_time=0),
                status="error",
                error_message="PyMuPDF (fitz) is not installed. Please install it via 'pip install pymupdf'."
            )

        try:
            doc = fitz.open(file_path)
            page_count = doc.page_count
            
            # 1. First try Layout extraction
            text_layout = self._extract_pdf_text_layout(doc, options)
            
            # 2. Check text quality
            is_valid, reason = self._is_text_valid(text_layout, page_count)
            
            parsing_method = ParsingMethod.LAYOUT
            final_text = text_layout
            
            # 3. OCR Fallback
            if not is_valid and options.ocr_enabled:
                if pytesseract is None:
                    logger.warning("OCR enabled but pytesseract is not installed. Skipping OCR fallback.")
                else:
                    logger.info(f"Layout extraction failed quality check: {reason}. Falling back to OCR.")
                    try:
                        ocr_text = self._extract_with_ocr(file_path, options)
                        # Simple check if OCR produced something
                        if len(ocr_text.strip()) > len(text_layout.strip()):
                            final_text = ocr_text
                            parsing_method = ParsingMethod.OCR
                        else:
                            logger.warning("OCR produced less text than layout analysis. Reverting to layout text.")
                    except Exception as e:
                        logger.error(f"OCR failed: {e}")
                        # Keep layout text if OCR fails
            
            doc.close()
            
            metadata = DocumentMetadata(
                page_count=page_count,
                file_size=file_path.stat().st_size,
                file_type=".pdf",
                parsing_method=parsing_method,
                parsing_time=time.time() - start_time,
                extra={"quality_check": reason}
            )
            
            return DocumentResult(
                content=final_text,
                metadata=metadata,
                status="success"
            )
            
        except Exception as e:
            logger.error(f"Failed to parse PDF {file_path}: {e}", exc_info=True)
            return DocumentResult(
                content="",
                metadata=DocumentMetadata(file_type=".pdf", parsing_time=time.time() - start_time),
                status="error",
                error_message=str(e)
            )

    def _is_text_valid(self, text: str, page_count: int) -> Tuple[bool, str]:
        """Check if extracted text is valid/readable."""
        if not text:
            return False, "Empty text"
            
        total_chars = len(text)
        if total_chars < settings.OCR_MIN_TOTAL_CHARS:
            return False, f"Total chars too low ({total_chars} < {settings.OCR_MIN_TOTAL_CHARS})"
            
        chars_per_page = total_chars / max(page_count, 1)
        if chars_per_page < settings.OCR_MIN_CHARS_PER_PAGE:
            return False, f"Chars per page too low ({chars_per_page:.1f} < {settings.OCR_MIN_CHARS_PER_PAGE})"
            
        # Check for garbled text (mojibake)
        # Use a simple heuristic: ratio of valid characters (CJK + Alnum + Punct)
        valid_chars = 0
        lines = text.splitlines()
        for char in text:
            if '\u4e00' <= char <= '\u9fff' or char.isalnum() or char in ",.;:!?()[]{}<>-+*/=_\"'":
                valid_chars += 1
        
        valid_ratio = valid_chars / total_chars
        if valid_ratio < settings.OCR_MIN_VALID_CHAR_RATIO:
            return False, f"Valid char ratio too low ({valid_ratio:.1%} < {settings.OCR_MIN_VALID_CHAR_RATIO:.0%})"

        # Check for repeated short lines (common in failed parsing)
        def _norm(s): return re.sub(r"\s+", "", s)
        counts = {}
        for ln in lines:
            n = _norm(ln)
            if 2 <= len(n) <= settings.OCR_REPEATED_SHORT_LINE_MAX_LEN:
                counts[n] = counts.get(n, 0) + 1
        
        repeated = sum(1 for n in counts if counts[n] >= 3) # Count unique repeated lines? Or occurrences?
        # Re-reading original logic:
        # for n in norms: if ... counts[n] >=3: repeated += 1
        # It counts *lines* that belong to a repeated group.
        
        norms = [_norm(ln) for ln in lines]
        repeated_lines_count = 0
        for n in norms:
            if 2 <= len(n) <= settings.OCR_REPEATED_SHORT_LINE_MAX_LEN and counts.get(n, 0) >= 3:
                repeated_lines_count += 1
                
        repeated_ratio = repeated_lines_count / max(len(lines), 1)
        if repeated_ratio >= settings.OCR_MAX_REPEATED_SHORT_LINE_RATIO and chars_per_page < (settings.OCR_MIN_CHARS_PER_PAGE * 2):
             return False, f"Repeated short lines too high ({repeated_ratio:.1%})"
             
        return True, "Valid"

    def _extract_with_ocr(self, file_path: Path, options: ParsingOptions) -> str:
        """Fallback to OCR."""
        doc = fitz.open(file_path)
        full_text = []
        
        logger.info(f"OCR Start: {file_path.name}")
        
        for page_num in range(doc.page_count):
            page = doc.load_page(page_num)
            pix = page.get_pixmap(dpi=settings.OCR_DPI)
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            
            text = pytesseract.image_to_string(img, lang=options.ocr_lang)
            full_text.append(text)
            
        doc.close()
        return "\n".join(full_text)

    def _extract_pdf_text_layout(self, doc: Any, options: ParsingOptions) -> str:
        all_lines: List[str] = []
        
        for page in doc:
            rect = page.rect
            header_cutoff = rect.height * options.header_ratio
            footer_cutoff = rect.height * (1 - options.footer_ratio)
            
            page_lines: List[Tuple[float, float, str]] = []
            
            # Extract tables
            table_items: List[Tuple[float, float, str, Tuple[float, float, float, float]]] = []
            table_bboxes: List[Tuple[float, float, float, float]] = []
            
            if options.extract_tables:
                table_items, table_bboxes = self._extract_tables_as_markdown(
                    page, header_cutoff, footer_cutoff
                )
            
            try:
                data = page.get_text("dict")
            except Exception:
                fallback = page.get_text()
                if fallback:
                    all_lines.extend(fallback.splitlines())
                continue
                
            for block in data.get("blocks", []):
                if block.get("type") != 0: continue # Text block only
                
                bbox = block.get("bbox")
                if not bbox: continue
                x0, y0, x1, y1 = bbox
                
                if y1 <= header_cutoff or y0 >= footer_cutoff: continue
                
                for line in block.get("lines", []):
                    line_bbox = line.get("bbox")
                    if line_bbox:
                        lx0, ly0, lx1, ly1 = line_bbox
                        if ly1 <= header_cutoff or ly0 >= footer_cutoff: continue
                        if table_bboxes and self._intersects_any_bbox((lx0, ly0, lx1, ly1), table_bboxes):
                            continue
                    else:
                        lx0, ly0 = x0, y0
                        
                    spans = line.get("spans", [])
                    if not spans: continue
                    
                    # Sort spans by x
                    spans_sorted = sorted(spans, key=lambda s: s.get("bbox", [0])[0])
                    parts = []
                    prev_x1 = None
                    
                    for sp in spans_sorted:
                        text = (sp.get("text") or "").replace("\n", " ").strip()
                        if not text: continue
                        
                        sp_bbox = sp.get("bbox")
                        sp_x0 = sp_bbox[0] if sp_bbox else None
                        sp_x1 = sp_bbox[2] if sp_bbox else None
                        sp_size = float(sp.get("size") or 0.0)
                        
                        if prev_x1 is not None and sp_x0 is not None and sp_size > 0:
                            gap = sp_x0 - prev_x1
                            if gap >= sp_size * settings.PDF_SPAN_GAP_SPACE_MULTIPLIER:
                                parts.append(" ")
                                
                        parts.append(text)
                        prev_x1 = sp_x1 if sp_x1 is not None else prev_x1
                        
                    line_text = "".join(parts).strip()
                    if not line_text: continue
                    
                    # Filter pure numbers (likely page numbers)
                    if re.match(r"^\s*\d+\s*$", line_text): continue
                    
                    # Fix percentage
                    line_text = re.sub(r"%(?=\d)", "% ", line_text)
                    
                    page_lines.append((float(ly0), float(lx0), line_text))
                    
            # Add table items
            for ty0, tx0, tmd, _ in table_items:
                page_lines.append((ty0, tx0, tmd))
                
            # Sort
            sorted_lines = self._sort_page_lines_for_reading(page_lines, rect.width)
            all_lines.extend([t[2] for t in sorted_lines])
            all_lines.append("") # Page separator
            
        return "\n".join(all_lines).strip()

    def _sort_page_lines_for_reading(self, page_lines: List[Tuple[float, float, str]], page_width: float) -> List[Tuple[float, float, str]]:
        if not page_lines: return []
        
        # Filter markdown tables for column detection
        x0s = []
        for _, x0, txt in page_lines:
            if not txt.strip() or (txt.strip().startswith("|") and txt.count("|") >= 2):
                continue
            x0s.append(x0)
            
        if len(x0s) < 30 or page_width <= 0:
            return sorted(page_lines, key=lambda t: (t[0], t[1]))
            
        mid = page_width * 0.5
        left = [x for x in x0s if x < mid]
        right = [x for x in x0s if x >= mid]
        
        if len(left) < 12 or len(right) < 12:
            return sorted(page_lines, key=lambda t: (t[0], t[1]))
            
        left_med = sorted(left)[len(left) // 2]
        right_med = sorted(right)[len(right) // 2]
        
        if right_med - left_med < page_width * 0.18:
            return sorted(page_lines, key=lambda t: (t[0], t[1]))
            
        split = (left_med + right_med) * 0.5
        
        def _key(t):
            y0, x0, _ = t
            col = 0 if x0 < split else 1
            return (col, y0, x0)
            
        return sorted(page_lines, key=_key)

    def _intersects_any_bbox(self, bbox: Tuple[float, float, float, float], others: List[Tuple[float, float, float, float]]) -> bool:
        x0, y0, x1, y1 = bbox
        for ox0, oy0, ox1, oy1 in others:
            if x0 < ox1 and x1 > ox0 and y0 < oy1 and y1 > oy0:
                return True
        return False

    def _extract_tables_as_markdown(self, page, header_cutoff, footer_cutoff) -> Tuple[List, List]:
        items = []
        bboxes = []
        
        finder = getattr(page, "find_tables", None)
        if not callable(finder): return items, bboxes
        
        try:
            tf = finder()
            tables = getattr(tf, "tables", [])
            
            for t in tables:
                bbox = getattr(t, "bbox", None)
                if not bbox: continue
                x0, y0, x1, y1 = bbox
                
                if y1 <= header_cutoff or y0 >= footer_cutoff: continue
                
                rows = t.extract()
                if not rows: continue
                
                cell_count = sum(len(r or []) for r in rows)
                if cell_count < settings.PDF_TABLE_MIN_CELLS: continue
                
                md = self._table_rows_to_markdown(rows)
                if not md.strip(): continue
                
                injected = "\n\n" + md.strip() + "\n\n"
                items.append((float(y0), float(x0), injected, (float(x0), float(y0), float(x1), float(y1))))
                bboxes.append((float(x0), float(y0), float(x1), float(y1)))
                
        except Exception:
            pass
            
        return items, bboxes

    def _table_rows_to_markdown(self, rows: List[List[Any]]) -> str:
        if not rows: return ""
        
        normalized = []
        max_cols = 0
        for r in rows:
            r = r or []
            str_row = []
            for c in r:
                s = "" if c is None else str(c)
                s = re.sub(r"\s+", " ", s).strip()
                s = s.replace("|", r"\|")
                str_row.append(s)
            max_cols = max(max_cols, len(str_row))
            normalized.append(str_row)
            
        if max_cols == 0: return ""
        
        normalized = [r + [""] * (max_cols - len(r)) for r in normalized]
        
        header = normalized[0]
        body = normalized[1:] if len(normalized) > 1 else []
        sep = ["---"] * max_cols
        
        lines = [
            "| " + " | ".join(header) + " |",
            "| " + " | ".join(sep) + " |",
        ]
        for r in body:
            lines.append("| " + " | ".join(r) + " |")
        return "\n".join(lines)
