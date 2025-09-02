#!/usr/bin/env python3
"""
Validate SFT data quality and schema.
"""

import json
import argparse
from pathlib import Path
from typing import Dict, List

def validate_sft_file(file_path: str) -> Dict:
    """Validate SFT file and return statistics."""
    stats = {
        "total_lines": 0,
        "valid_json": 0,
        "valid_schema": 0,
        "errors": []
    }
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            stats["total_lines"] += 1
            
            try:
                # Parse JSON
                data = json.loads(line.strip())
                stats["valid_json"] += 1
                
                # Validate schema
                if validate_sft_pair(data):
                    stats["valid_schema"] += 1
                else:
                    stats["errors"].append(f"Line {line_num}: Invalid schema")
                    
            except json.JSONDecodeError as e:
                stats["errors"].append(f"Line {line_num}: JSON decode error - {e}")
            except Exception as e:
                stats["errors"].append(f"Line {line_num}: Unexpected error - {e}")
    
    return stats

def validate_sft_pair(data: Dict) -> bool:
    """Validate a single SFT pair."""
    required_fields = ["instruction", "input", "output", "history"]
    
    # Check required fields
    for field in required_fields:
        if field not in data:
            return False
    
    # Check output format
    try:
        output = json.loads(data["output"])
        if "timeline" not in output:
            return False
        
        timeline = output["timeline"]
        if not isinstance(timeline, list) or len(timeline) == 0:
            return False
        
        # Check timeline entry
        entry = timeline[0]
        required_timeline_fields = ["ts", "event", "fan_sentiment"]
        for field in required_timeline_fields:
            if field not in entry:
                return False
        
        # Check sentiment values
        valid_sentiments = {"pos", "neg", "mixed"}
        if entry["fan_sentiment"] not in valid_sentiments:
            return False
            
    except (json.JSONDecodeError, KeyError, TypeError):
        return False
    
    return True

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sft_file", help="Path to SFT data file")
    args = ap.parse_args()
    
    if not Path(args.sft_file).exists():
        print(f"Error: File {args.sft_file} not found")
        return 1
    
    print(f"Validating {args.sft_file}...")
    stats = validate_sft_file(args.sft_file)
    
    print(f"\n{'='*50}")
    print("Validation Results")
    print(f"{'='*50}")
    print(f"Total lines: {stats['total_lines']}")
    print(f"Valid JSON: {stats['valid_json']}")
    print(f"Valid schema: {stats['valid_schema']}")
    print(f"Success rate: {(stats['valid_schema'] / stats['total_lines']) * 100:.1f}%")
    
    if stats["errors"]:
        print(f"\nErrors found:")
        for error in stats["errors"][:10]:  # Show first 10 errors
            print(f"  {error}")
        if len(stats["errors"]) > 10:
            print(f"  ... and {len(stats['errors']) - 10} more errors")
    
    return 0

if __name__ == "__main__":
    main()
