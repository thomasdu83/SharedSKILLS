import yaml
import logging
from pathlib import Path
from typing import List, Dict, Set, Optional

from .config import settings

logger = logging.getLogger(__name__)

class TextCleaner:
    """
    Handles text cleaning, sensitive word masking, and content truncation.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.sensitive_words: Set[str] = set()
        self.truncation_markers: List[str] = []
        self._loaded = False
        
        path = config_path or settings.SENSITIVE_WORDS_PATH
        self._load_config(path)

    def _load_config(self, path: str):
        """Load configuration from YAML file."""
        try:
            config_file = Path(path)
            if not config_file.exists():
                logger.warning(f"Sensitive words file not found: {path}")
                return

            with open(config_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                
            if not data:
                return

            # Load sensitive words from all categories except truncation_markers
            for category, words in data.items():
                if category == "truncation_markers":
                    self.truncation_markers = [str(w) for w in words if w]
                elif isinstance(words, list):
                    for w in words:
                        if w:
                            self.sensitive_words.add(str(w))
                            
            self._loaded = True
            logger.info(f"TextCleaner loaded: {len(self.sensitive_words)} sensitive words, {len(self.truncation_markers)} truncation markers.")
            
        except Exception as e:
            logger.error(f"Failed to load text cleaner config: {e}")

    def clean(self, text: str, mask_char: str = "*", truncate: bool = True) -> str:
        """
        Clean the text by masking sensitive words and truncating at markers.
        """
        if not text or not self._loaded:
            return text

        cleaned_text = text

        # 1. Truncation (Fail Fast: Truncate before masking to save work)
        if truncate and self.truncation_markers:
            min_index = len(cleaned_text)
            found = False
            
            for marker in self.truncation_markers:
                idx = cleaned_text.find(marker)
                if idx != -1 and idx < min_index:
                    min_index = idx
                    found = True
            
            if found:
                logger.debug(f"Truncating text at index {min_index}")
                cleaned_text = cleaned_text[:min_index]

        # 2. Sensitive Word Masking
        # Simple replacement approach. For very large dictionaries, Aho-Corasick is preferred.
        if self.sensitive_words:
            for word in self.sensitive_words:
                if word in cleaned_text:
                    mask = mask_char * 3 # Fixed length mask or len(word)? Let's use ***
                    cleaned_text = cleaned_text.replace(word, mask)

        return cleaned_text
