#!/usr/bin/env python3
import json
import sys
from pathlib import Path

def clean_file(input_path: Path, output_path: Path):
    # 1. Load the raw file
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    cleaned = []
    for entry in data:
        raw_resp = entry.get("response", "")
        try:
            # 2. Parse the embedded JSON string
            parsed = json.loads(raw_resp)
        except json.JSONDecodeError:
            # If there are stray line breaks or escapes, try a simple sanitize
            sanitized = raw_resp.replace('\n', '').replace('\\', '')
            parsed = json.loads(sanitized)

        # 3. Replace the string with the actual dict
        entry["response"] = parsed
        cleaned.append(entry)

    # 4. Write out the cleaned JSON
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(cleaned, f, ensure_ascii=False, indent=2)

    print(f"Cleaned JSON written to {output_path}")

if __name__ == "__main__":
    # You can pass input/output filenames as command-line args
    in_file  = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("all_results.json")
    out_file = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("cleaned_results.json")
    clean_file(in_file, out_file)
