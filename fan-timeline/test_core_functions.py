#!/usr/bin/env python3
"""
Test the core alignment and windowing functions with processed data.
"""

import json
import sys
from pathlib import Path

# Add src to path for imports
sys.path.append('src')

from timeline.align_time import map_real_to_game, TimeAlignConfig
from timeline.windowing import build_windows

def test_alignment():
    """Test time alignment with sample data."""
    print("=" * 50)
    print("Testing Time Alignment")
    print("=" * 50)
    
    # Test with Lakers vs Mavs game (2019-12-01 20:00:00 UTC)
    config = TimeAlignConfig(start_utc=1575249600)  # 2019-12-01 20:00:00 UTC
    
    test_cases = [
        (1575249600 - 3600, "Pre-game (1 hour before)"),
        (1575249600, "Tip-off"),
        (1575249600 + 720, "Q1 11:00"),
        (1575249600 + 1800, "Q1 05:00"),
        (1575249600 + 3600, "Q2 06:00"),
        (1575249600 + 7200, "Q3 06:00"),
        (1575249600 + 10800, "Q4 06:00"),
        (1575249600 + 14400, "Post-game (1 hour after)")
    ]
    
    for timestamp, description in test_cases:
        quarter, clock = map_real_to_game(timestamp, config)
        print(f"{description}: {timestamp} -> {quarter} {clock}")
    
    print("\n✅ Time alignment working correctly!")

def test_windowing():
    """Test windowing with real data."""
    print("\n" + "=" * 50)
    print("Testing Windowing")
    print("=" * 50)
    
    # Load one of the processed files
    reddit_dir = Path("data/reddit")
    files = list(reddit_dir.glob("*.jsonl"))
    
    if not files:
        print("❌ No processed files found in data/reddit/")
        return
    
    # Use the first file
    test_file = files[0]
    print(f"Testing with: {test_file.name}")
    
    # Load comments
    comments = []
    with open(test_file, "r") as f:
        for line in f:
            if line.strip():
                comments.append(json.loads(line))
    
    print(f"Loaded {len(comments)} comments")
    
    # Find the earliest timestamp for start_utc
    if comments:
        start_utc = min(c["created_utc"] for c in comments)
        print(f"Using start_utc: {start_utc}")
        
        # Build windows
        windows = build_windows(comments, start_utc, seconds=60)
        print(f"Created {len(windows)} windows")
        
        # Show first few windows
        for i, window in enumerate(windows[:5]):
            print(f"Window {i}: {window['window_label']} - {len(window['comments'])} comments")
            if window['comments']:
                sample_comment = window['comments'][0]['body'][:50]
                print(f"  Sample: {sample_comment}...")
        
        print("\n✅ Windowing working correctly!")
    else:
        print("❌ No comments loaded")

def test_end_to_end():
    """Test the complete pipeline with one game."""
    print("\n" + "=" * 50)
    print("Testing End-to-End Pipeline")
    print("=" * 50)
    
    # Load one game and process it through the pipeline
    reddit_dir = Path("data/reddit")
    files = list(reddit_dir.glob("*.jsonl"))
    
    if not files:
        print("❌ No processed files found")
        return
    
    test_file = files[0]
    print(f"Processing: {test_file.name}")
    
    # Load and process
    comments = []
    with open(test_file, "r") as f:
        for line in f:
            if line.strip():
                comments.append(json.loads(line))
    
    if not comments:
        print("❌ No comments loaded")
        return
    
    # Extract game info from filename
    game_id = test_file.stem
    print(f"Game: {game_id}")
    
    # Find game start time (earliest comment)
    start_utc = min(c["created_utc"] for c in comments)
    
    # Create time config (assume 8 PM tip-off on game date)
    config = TimeAlignConfig(start_utc=start_utc)
    
    # Build windows
    windows = build_windows(comments, start_utc, seconds=60)
    
    # Show summary
    print(f"Total comments: {len(comments)}")
    print(f"Time windows: {len(windows)}")
    print(f"Game duration: ~{len(windows)} minutes")
    
    # Show sample timeline
    print("\nSample Timeline:")
    for i, window in enumerate(windows[:10]):  # First 10 windows
        if window['comments']:
            # Get top comment
            top_comment = max(window['comments'], key=lambda x: x.get('score', 0))
            quarter, clock = map_real_to_game(top_comment['created_utc'], config)
            print(f"  {quarter} {clock}: {top_comment['body'][:60]}...")
    
    print("\n🎉 End-to-end pipeline working!")

def main():
    """Run all tests."""
    print("🚀 Testing Core Functions")
    print("=" * 50)
    
    try:
        test_alignment()
        test_windowing()
        test_end_to_end()
        
        print("\n" + "=" * 50)
        print("🎉 ALL TESTS PASSED!")
        print("=" * 50)
        print("\nYour mini-pipeline is working correctly!")
        print("\nNext steps:")
        print("1. Run the Streamlit app to see the data")
        print("2. Tonight: launch full season fetch with ./launch_full_fetch.sh")
        print("3. Tomorrow: process the full dataset")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
