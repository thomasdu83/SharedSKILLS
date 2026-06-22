from abc import ABC, abstractmethod
from pathlib import Path
from ..schemas import DocumentResult, ParsingOptions

class BaseParser(ABC):
    """Abstract base class for document parsers."""
    
    @abstractmethod
    def parse(self, file_path: Path, options: ParsingOptions) -> DocumentResult:
        """
        Parse a document and return the result.
        
        Args:
            file_path: Path to the file.
            options: Parsing options.
            
        Returns:
            DocumentResult object.
        """
        pass
