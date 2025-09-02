#!/usr/bin/env python3
"""
Generate SFT training data from teacher-labeled windows.
"""

import json
import argparse
import os
from pathlib import Path
from typing import List, Dict
import random

try:
    from .teacher import label_window, extract_top_themes
except ImportError:
    from teacher import label_window, extract_top_themes

def create_sft_pairs(windows: List[Dict], game_id: str = "sample-game") -> List[Dict]:
    """Create SFT training pairs from teacher-labeled windows."""
    pairs = []
    
    for window in windows:
        # Sample up to 10 comments per window (top-3 by score + random rest)
        comments = window.get("comments", [])
        if not comments:
            continue
        
        # Sort by score and get top 3
        scored_comments = [(c.get("score", 0), c.get("body", "")) for c in comments]
        scored_comments.sort(key=lambda x: x[0], reverse=True)
        top_comments = [body for _, body in scored_comments[:3]]
        
        # Add random rest (up to 7 more)
        remaining = [body for _, body in scored_comments[3:]]
        if remaining:
            random.shuffle(remaining)
            top_comments.extend(remaining[:7])
        
        # Create comment text
        comment_text = "\n• ".join(top_comments)
        
        # Get scores
        score_before = window.get("score_before", "0-0")
        score_after = window.get("score_after", "0-0")
        
        # Create input prompt
        prompt = f"""[CONTEXT]
game_id={game_id}
quarter=Q{window['period']} window={window['clock_start']} score_before={score_before} score_after={score_after}

[COMMENTS]
• {comment_text}"""
        
        # Get teacher output
        try:
            teacher_output = label_window(window)
            output = json.dumps(teacher_output, ensure_ascii=False)
        except Exception as e:
            print(f"Error processing window: {e}")
            continue
        
        pairs.append({
            "instruction": "You are a sports timeline generator. Given fan comments from a game thread, create a concise event summary with sentiment.",
            "input": prompt,
            "output": output,
            "history": []
        })
    
    return pairs

def process_game_file(game_file: Path, game_id: str) -> List[Dict]:
    """Process a single game file and return SFT pairs."""
    print(f"Processing {game_file}")
    
    # Load windows
    windows = []
    with open(game_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                windows.append(json.loads(line))
    
    print(f"Loaded {len(windows)} windows")
    
    # Create SFT pairs
    pairs = create_sft_pairs(windows, game_id)
    print(f"Generated {len(pairs)} SFT pairs")
    
    return pairs

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, help="Output path for SFT data")
    ap.add_argument("--windows_dir", default="data/windows", help="Directory containing window files")
    ap.add_argument("--game_id", help="Process single game (optional)")
    args = ap.parse_args()
    
    windows_dir = Path(args.windows_dir)
    if not windows_dir.exists():
        print(f"Error: Windows directory {windows_dir} not found")
        return 1
    
    all_pairs = []
    
    if args.game_id:
        # Process single game
        game_file = windows_dir / f"{args.game_id}.jsonl"
        if not game_file.exists():
            print(f"Error: Game file {game_file} not found")
            return 1
        
        pairs = process_game_file(game_file, args.game_id)
        all_pairs.extend(pairs)
    else:
        # Process all games
        game_files = list(windows_dir.glob("*.jsonl"))
        print(f"Found {len(game_files)} game files")
        
        for game_file in game_files:
            game_id = game_file.stem
            pairs = process_game_file(game_file, game_id)
            all_pairs.extend(pairs)
    
    # Save all pairs
    output_dir = os.path.dirname(args.out)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        for pair in all_pairs:
            f.write(json.dumps(pair, ensure_ascii=False) + "\n")
    
    print(f"\n{'='*50}")
    print(f"Created {len(all_pairs)} total SFT training pairs")
    print(f"Saved to: {args.out}")
    print(f"{'='*50}")
    
    # Print sentiment distribution
    sentiment_counts = {"pos": 0, "neg": 0, "mixed": 0}
    for pair in all_pairs:
        try:
            output = json.loads(pair["output"])
            sentiment = output["timeline"][0]["fan_sentiment"]
            sentiment_counts[sentiment] += 1
        except:
            pass
    
    print(f"Sentiment distribution:")
    for sentiment, count in sentiment_counts.items():
        percentage = (count / len(all_pairs)) * 100
        print(f"  {sentiment}: {count} ({percentage:.1f}%)")

if __name__ == "__main__":
    main()
