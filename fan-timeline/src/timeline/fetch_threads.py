#!/usr/bin/env python3
"""
Fetch Reddit game threads using Pushshift API for mini-dataset.
Usage: python fetch_threads.py --schedule_csv mini_schedule.csv --out_dir data/raw_reddit_mini
"""

import argparse
import csv
import json
import os
import time
from pathlib import Path
from typing import Dict, List, Optional
import requests

def search_game_thread(date: str, away: str, home: str) -> Optional[Dict]:
    """Search for a game thread using Pushshift API."""
    # Try different title patterns
    patterns = [
        f"Game Thread: {away} @ {home}",
        f"Game Thread: {away} vs {home}",
        f"Game Thread: {away} at {home}",
        f"Game Thread: {home} vs {away}",
        f"Game Thread: {home} @ {away}"
    ]
    
    for pattern in patterns:
        try:
            # Search for submission
            url = "https://api.pushshift.io/reddit/search/submission/"
            params = {
                "subreddit": "nba",
                "title": pattern,
                "size": 1,
                "after": f"{date}T00:00:00",
                "before": f"{date}T23:59:59"
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data["data"]:
                submission = data["data"][0]
                print(f"Found thread: {submission['title']}")
                return submission
                
        except Exception as e:
            print(f"Error searching for {pattern}: {e}")
            continue
    
    return None

def fetch_comments(link_id: str, max_comments: int = 5000) -> List[Dict]:
    """Fetch comments for a submission."""
    try:
        url = "https://api.pushshift.io/reddit/comment/search"
        params = {
            "link_id": link_id,
            "size": max_comments,
            "sort": "score",
            "sort_type": "score"
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        return data["data"]
        
    except Exception as e:
        print(f"Error fetching comments: {e}")
        return []

def fetch_game_data(date: str, away: str, home: str, out_dir: Path) -> bool:
    """Fetch complete game data (thread + comments)."""
    print(f"Fetching {date} {away} @ {home}...")
    
    # Search for game thread
    submission = search_game_thread(date, away, home)
    if not submission:
        print(f"No game thread found for {date} {away} @ {home}")
        return False
    
    # Fetch comments
    comments = fetch_comments(submission["id"])
    print(f"Found {len(comments)} comments")
    
    # Save to file
    game_id = f"{date}-{away}-{home}"
    outfile = out_dir / f"{game_id}.json"
    
    game_data = {
        "game_id": game_id,
        "date": date,
        "away": away,
        "home": home,
        "submission": submission,
        "comments": comments
    }
    
    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(game_data, f, indent=2, ensure_ascii=False)
    
    print(f"Saved to {outfile}")
    return True

def main():
    parser = argparse.ArgumentParser(description="Fetch Reddit game threads")
    parser.add_argument("--schedule_csv", required=True, help="CSV with date,away,home columns")
    parser.add_argument("--out_dir", required=True, help="Output directory for JSON files")
    
    args = parser.parse_args()
    
    # Create output directory
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Read schedule
    with open(args.schedule_csv, "r") as f:
        reader = csv.DictReader(f)
        games = list(reader)
    
    print(f"Found {len(games)} games to fetch")
    
    # Fetch each game
    success_count = 0
    for i, game in enumerate(games):
        print(f"\n[{i+1}/{len(games)}] Processing {game['date']} {game['away']} @ {game['home']}")
        
        if fetch_game_data(game["date"], game["away"], game["home"], out_dir):
            success_count += 1
        
        # Rate limiting - be nice to Pushshift
        if i < len(games) - 1:
            print("Waiting 2 seconds...")
            time.sleep(2)
    
    print(f"\nCompleted! Successfully fetched {success_count}/{len(games)} games")
    print(f"Files saved to: {out_dir}")

if __name__ == "__main__":
    main()
