#!/usr/bin/env python3
"""
Run the pipeline for all mini games.
"""

import subprocess
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from run_pipeline import run_pipeline_for_game

def main():
    mini_games = [
        "2019-12-01-LAL-DAL",
        "2020-01-16-BOS-MIL", 
        "2021-05-19-GSW-LAL",
        "2022-12-25-MEM-GSW",
        "2023-06-01-MIA-DEN"
    ]
    
    for game_id in mini_games:
        print(f"\n{'='*50}")
        print(f"Processing {game_id}")
        print(f"{'='*50}")
        
        try:
            run_pipeline_for_game(game_id)
            print(f"✅ Successfully processed {game_id}")
        except Exception as e:
            print(f"❌ Error processing {game_id}: {e}")
    
    print(f"\n{'='*50}")
    print("Pipeline complete!")
    print(f"{'='*50}")
    
    # Print summary
    windows_dir = Path("data/windows")
    if windows_dir.exists():
        window_files = list(windows_dir.glob("*.jsonl"))
        print(f"Created {len(window_files)} window files:")
        for f in window_files:
            print(f"  - {f.name}")

if __name__ == "__main__":
    main()
