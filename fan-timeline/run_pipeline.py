#!/usr/bin/env python3
"""
Run the full pipeline for one game.
"""

import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from timeline.align_time import load_game_schedule, add_elapsed_times, add_elapsed_times_pbp
from timeline.windowing import build_windows, save_windows_to_jsonl

def run_pipeline_for_game(game_id: str):
    """Run the full pipeline for a single game."""
    print(f"Running pipeline for {game_id}")
    
    # Load game schedule
    schedule = load_game_schedule("game_schedule.csv")
    game_start_utc = schedule.get(game_id)
    if not game_start_utc:
        print(f"Error: No start time found for game {game_id}")
        return
    
    print(f"Game start time: {game_start_utc}")
    
    # Load comments
    comments_file = Path(f"data/reddit/{game_id}.jsonl")
    if not comments_file.exists():
        print(f"Error: Comments file not found: {comments_file}")
        return
    
    comments = []
    with open(comments_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                comments.append(json.loads(line))
    
    print(f"Loaded {len(comments)} comments")
    
    # Load PBP events
    pbp_file = Path(f"data/pbp/{game_id}.jsonl")
    if not pbp_file.exists():
        print(f"Error: PBP file not found: {pbp_file}")
        return
    
    pbp_events = []
    with open(pbp_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                pbp_events.append(json.loads(line))
    
    print(f"Loaded {len(pbp_events)} PBP events")
    
    # Add elapsed times
    comments = add_elapsed_times(comments, game_start_utc)
    pbp_events = add_elapsed_times_pbp(pbp_events, game_start_utc)
    
    print(f"Added elapsed times to {len(comments)} comments and {len(pbp_events)} PBP events")
    
    # Build windows
    windows = build_windows(comments, pbp_events)
    print(f"Built {len(windows)} windows")
    
    # Save windows
    windows_dir = Path("data/windows")
    windows_dir.mkdir(exist_ok=True)
    windows_file = windows_dir / f"{game_id}.jsonl"
    save_windows_to_jsonl(windows, windows_file)
    
    print(f"Saved windows to {windows_file}")
    
    # Print some stats
    total_comments = sum(len(w["comments"]) for w in windows.values())
    total_pbp = sum(len(w["pbp"]) for w in windows.values())
    print(f"Total comments in windows: {total_comments}")
    print(f"Total PBP events in windows: {total_pbp}")

def main():
    if len(sys.argv) != 2:
        print("Usage: python run_pipeline.py <game_id>")
        print("Example: python run_pipeline.py 2019-12-01-LAL-DAL")
        return
    
    game_id = sys.argv[1]
    run_pipeline_for_game(game_id)

if __name__ == "__main__":
    main()
