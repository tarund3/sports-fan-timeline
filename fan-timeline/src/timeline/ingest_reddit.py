from __future__ import annotations
import json
import argparse
from dataclasses import dataclass
from typing import List, Dict
from pathlib import Path
try:
    from .utils import clean_text
except ImportError:
    from utils import clean_text

@dataclass
class Comment:
    body: str
    created_utc: int
    score: int
    author: str

def load_reddit_jsonl(path: str) -> List[Comment]:
    """Load from old JSONL format (legacy)."""
    out: List[Comment] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            obj = json.loads(line)
            body = clean_text(obj.get("body", ""))
            if not body:
                continue
            out.append(Comment(
                body=body,
                created_utc=int(obj.get("created_utc", 0)),
                score=int(obj.get("score", 0)),
                author=str(obj.get("author", "")),
            ))
    return out

def load_reddit_json(path: str) -> List[Comment]:
    """Load from new JSON format (from fetch_threads.py)."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    comments = []
    for comment_data in data.get("comments", []):
        body = clean_text(comment_data.get("body", ""))
        if not body:
            continue
        
        comments.append(Comment(
            body=body,
            created_utc=int(comment_data.get("created_utc", 0)),
            score=int(comment_data.get("score", 0)),
            author=str(comment_data.get("author", "")),
        ))
    
    return comments

def process_file(infile: Path, outfile: Path):
    """Process a single input file to output file."""
    print(f"Processing {infile} -> {outfile}")
    
    # Determine format and load
    if infile.suffix == ".jsonl":
        comments = load_reddit_jsonl(str(infile))
    elif infile.suffix == ".json":
        comments = load_reddit_json(str(infile))
    else:
        print(f"Unknown file format: {infile}")
        return
    
    print(f"Loaded {len(comments)} comments")
    
    # Save as JSONL
    with open(outfile, "w", encoding="utf-8") as f:
        for c in comments:
            f.write(json.dumps(c.__dict__, ensure_ascii=False) + "\n")
    
    print(f"Saved {len(comments)} comments to {outfile}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in_dir", help="Input directory with JSON/JSONL files")
    ap.add_argument("--out_dir", help="Output directory for JSONL files")
    ap.add_argument("--infile", help="Single input file (legacy)")
    ap.add_argument("--outfile", help="Single output file (legacy)")
    args = ap.parse_args()
    
    if args.in_dir and args.out_dir:
        # Directory mode
        in_dir = Path(args.in_dir)
        out_dir = Path(args.out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        
        # Process all JSON/JSONL files
        input_files = list(in_dir.glob("*.json")) + list(in_dir.glob("*.jsonl"))
        print(f"Found {len(input_files)} input files")
        
        for infile in input_files:
            outfile = out_dir / f"{infile.stem}.jsonl"
            process_file(infile, outfile)
            
    elif args.infile and args.outfile:
        # Single file mode (legacy)
        process_file(Path(args.infile), Path(args.outfile))
    else:
        print("Use --in_dir and --out_dir for directory processing, or --infile and --outfile for single file")
        return 1

if __name__ == "__main__":
    main()
