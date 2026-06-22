import sys
import json
import os
import argparse

# Add path to find skill_interface
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
# Add QuantSystem root
sys.path.append(os.path.abspath(os.path.join(current_dir, "../../../..")))

from skill_interface import archive_macro_results

def main():
    parser = argparse.ArgumentParser(description="Archive macro research results")
    parser.add_argument("scores_file", help="Path to JSON file containing scores")
    parser.add_argument("--date", help="Date string YYYY-MM-DD", default=None)
    args = parser.parse_args()
    
    if not os.path.exists(args.scores_file):
        print(f"Error: File {args.scores_file} not found.")
        sys.exit(1)
        
    print(f"Reading scores from {args.scores_file}...")
    with open(args.scores_file, "r", encoding="utf-8") as f:
        scores = json.load(f)
        
    print("Archiving results...")
    result = archive_macro_results(scores, date_str=args.date)
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
