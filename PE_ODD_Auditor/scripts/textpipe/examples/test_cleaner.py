import sys
import logging
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parents[3]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.textpipe import TextPipe, parse_file, ParsingOptions

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    print("--- Testing Text Cleaner ---")
    
    # Create a dummy file with sensitive content and disclaimer
    dummy_txt = Path("test_clean.txt")
    content = """
    这是一个包含敏感信息的测试文档。
    这里提到了天安门和爆炸事件。
    所有的内容都应该被处理。
    
    免责声明：
    本报告仅供参考，不构成投资建议。
    版权所有，翻录必究。
    """
    
    with open(dummy_txt, "w", encoding="utf-8") as f:
        f.write(content)
        
    # 1. Test Default Cleaning (Enabled)
    print("\n[Test 1] Default Cleaning (Mask + Truncate)")
    pipe = TextPipe()
    result = pipe.parse(dummy_txt)
    
    print(f"Original Length: {len(content)}")
    print(f"Cleaned Length: {len(result.content)}")
    print("-" * 20)
    print(result.content)
    print("-" * 20)
    
    # 2. Test Disable Truncation
    print("\n[Test 2] Mask Only (No Truncate)")
    options = ParsingOptions(clean_text=True, truncate_content=False)
    result = pipe.parse(dummy_txt, options)
    print("-" * 20)
    print(result.content)
    print("-" * 20)

    # Cleanup
    if dummy_txt.exists():
        dummy_txt.unlink()

if __name__ == "__main__":
    main()
