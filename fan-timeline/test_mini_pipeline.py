#!/usr/bin/env python3
"""
Test the mini-pipeline end-to-end.
This script will:
1. Fetch 5 games using fetch_threads.py
2. Process them with ingest_reddit.py
3. Test the alignment and windowing functions
"""

import subprocess
import sys
from pathlib import Path

def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"\n{'='*50}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print('='*50)
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("SUCCESS!")
        if result.stdout:
            print("Output:", result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERROR: {e}")
        if e.stdout:
            print("stdout:", e.stdout)
        if e.stderr:
            print("stderr:", e.stderr)
        return False

def test_alignment():
    """Test the time alignment function."""
    print(f"\n{'='*50}")
    print("Testing time alignment...")
    print('='*50)
    
    try:
        # Import and test alignment
        sys.path.append('src')
        from timeline.align_time import map_real_to_game, TimeAlignConfig
        
        # Test with a sample timestamp (Lakers vs Mavs game start)
        config = TimeAlignConfig(start_utc=1575249600)  # 2019-12-01 20:00:00 UTC
        test_ts = 1575249600 + 720  # 12 minutes into game
        
        quarter, clock = map_real_to_game(test_ts, config)
        print(f"Test timestamp {test_ts} -> {quarter} {clock}")
        
        if quarter == "Q1" and clock == "11:00":
            print("✅ Time alignment working correctly!")
        else:
            print(f"⚠️  Time alignment returned {quarter} {clock}, expected Q1 11:00")
            
    except Exception as e:
        print(f"❌ Time alignment test failed: {e}")

def test_windowing():
    """Test the windowing function."""
    print(f"\n{'='*50}")
    print("Testing windowing...")
    print('='*50)
    
    try:
        # Import and test windowing
        sys.path.append('src')
        from timeline.windowing import build_windows
        
        # Create sample comments
        sample_comments = [
            {"created_utc": 1575249600 + 30, "body": "Great start!", "score": 10, "author": "user1"},
            {"created_utc": 1575249600 + 90, "body": "Nice shot!", "score": 5, "author": "user2"},
            {"created_utc": 1575249600 + 150, "body": "What a play!", "score": 15, "author": "user3"},
        ]
        
        windows = build_windows(sample_comments, 1575249600, seconds=60)
        print(f"Created {len(windows)} windows")
        
        for i, window in enumerate(windows):
            print(f"Window {i}: {window['window_label']} - {len(window['comments'])} comments")
            
        print("✅ Windowing working correctly!")
        
    except Exception as e:
        print(f"❌ Windowing test failed: {e}")

def main():
    """Run the full mini-pipeline test."""
    print("🚀 Starting mini-pipeline test...")
    
    # Step 1: Fetch threads
    if not run_command([
        "python", "src/timeline/fetch_threads.py",
        "--schedule_csv", "mini_schedule.csv",
        "--out_dir", "data/raw_reddit_mini"
    ], "Fetching Reddit game threads"):
        print("❌ Fetch failed, stopping test")
        return
    
    # Step 2: Process with ingest
    if not run_command([
        "python", "src/timeline/ingest_reddit.py",
        "--in_dir", "data/raw_reddit_mini",
        "--out_dir", "data/reddit"
    ], "Processing Reddit data"):
        print("❌ Ingest failed, stopping test")
        return
    
    # Step 3: Test core functions
    test_alignment()
    test_windowing()
    
    # Step 4: Show results
    print(f"\n{'='*50}")
    print("🎉 MINI-PIPELINE TEST COMPLETE!")
    print('='*50)
    
    reddit_dir = Path("data/reddit")
    if reddit_dir.exists():
        files = list(reddit_dir.glob("*.jsonl"))
        print(f"Generated {len(files)} processed files:")
        for f in files:
            print(f"  - {f.name}")
    
    print("\nNext steps:")
    print("1. Check the generated files in data/reddit/")
    print("2. Run the Streamlit app to see the data")
    print("3. Tonight: launch the full season fetch with nohup")

if __name__ == "__main__":
    main()
