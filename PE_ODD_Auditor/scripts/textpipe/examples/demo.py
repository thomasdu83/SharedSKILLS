import sys
import logging
from pathlib import Path
import os

# Add project root to sys.path to enable absolute imports
project_root = Path(__file__).resolve().parents[3]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.textpipe import TextPipe, parse_file, ParsingOptions

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    # Example 1: Basic Usage using helper function
    print("--- Example 1: Basic Usage ---")
    # Replace with an actual file path
    sample_pdf = project_root / "utils/textpipe/examples/sample1.pdf"
    
    if not sample_pdf.exists():
        print(f"Note: {sample_pdf} does not exist. Skipping actual parsing.")
    else:
        result = parse_file(sample_pdf)
        if result.status == "success":
            print(f"Successfully parsed {sample_pdf}")
            print(f"Content length: {len(result.content)}")
            print(f"Metadata: {result.metadata}")
        else:
            print(f"Failed: {result.error_message}")

    # Example 2: Advanced Usage with TextPipe class and custom options
    print("\n--- Example 2: Advanced Usage ---")
    pipe = TextPipe()
    
    options = ParsingOptions(
        ocr_enabled=True,
        ocr_lang="eng", # Use English for this example
        extract_tables=True,
        header_ratio=0.15, # Custom header cutoff
        clean_text=True,
        truncate_content=True
    )
    
    # Try parsing a non-existent file to see error handling
    sample_pdf = project_root / "utils/textpipe/examples/sample2.pdf"
    result = pipe.parse(sample_pdf, options)
    print(f"Parsing non-existent file result: {result.status}")
    print(f"Error message: {result.error_message}")

    # Example 3: Parsing text directly with Cleaning
    print("\n--- Example 3: Text Parsing with Cleaning ---")
    # Create a dummy file with sensitive words and disclaimer
    sample_pdf = project_root / "utils/textpipe/examples/sample2.pdf"
    # Enable cleaning and truncation
    clean_options = ParsingOptions(clean_text=True, truncate_content=True)
    result = pipe.parse(sample_pdf, clean_options)
    print(result.content)
    print(f"Metadata: {result.metadata}")
    
if __name__ == "__main__":
    main()
