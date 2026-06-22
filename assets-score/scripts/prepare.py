import sys
import json
import os
import argparse

# Add path to find skill_interface
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
# Add QuantSystem root (4 levels up from scripts: scripts -> assets-score -> skills -> .trae -> QuantSystem)
sys.path.append(os.path.abspath(os.path.join(current_dir, "../../../..")))

from skill_interface import prepare_macro_context

def main():
    parser = argparse.ArgumentParser(description="Prepare macro research context")
    parser.add_argument("--date", help="Date string YYYY-MM-DD", default=None)
    parser.add_argument("--output", help="Output JSON file path", default="macro_context.json")
    args = parser.parse_args()

    print(f"Running prepare_macro_context with date={args.date}...")
    result = prepare_macro_context(date_str=args.date)
    
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"Context prepared and saved to {args.output}")

if __name__ == "__main__":
    main()
