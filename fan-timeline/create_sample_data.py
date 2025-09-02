#!/usr/bin/env python3
"""
Create sample Reddit data for testing the mini-pipeline.
Since Pushshift API is returning 403, we'll create realistic sample data.
"""

import json
import random
from pathlib import Path
from datetime import datetime, timedelta

def create_sample_game_data(date_str, away, home):
    """Create realistic sample game data."""
    # Parse date and create game start time
    game_date = datetime.strptime(date_str, "%Y-%m-%d")
    game_start = game_date.replace(hour=20, minute=0, second=0)  # 8 PM tip-off
    
    # Create sample comments over 3 hours (game + pre/post)
    comments = []
    comment_id = 1
    
    # Pre-game comments (1 hour before)
    for i in range(10):
        comment_time = game_start - timedelta(hours=1, minutes=i*6)
        comments.append({
            "id": f"comment_{comment_id}",
            "body": random.choice([
                f"Let's go {home}!",
                f"{away} gonna get smoked tonight",
                "Game thread is live!",
                "Who's watching this one?",
                "Should be a good game",
                "I'm hyped for this matchup",
                "Anyone got the lineups?",
                "Let's get this W!",
                "Game time baby!",
                "This is gonna be fun"
            ]),
            "created_utc": int(comment_time.timestamp()),
            "score": random.randint(1, 25),
            "author": f"user_{random.randint(1, 100)}",
            "subreddit": "nba"
        })
        comment_id += 1
    
    # Game comments (every 30 seconds for 2.5 hours)
    for i in range(180):  # 2.5 hours * 2 per minute
        comment_time = game_start + timedelta(minutes=i//2, seconds=30*(i%2))
        comments.append({
            "id": f"comment_{comment_id}",
            "body": random.choice([
                "Great shot!",
                "What a play!",
                "Refs are terrible tonight",
                "This is amazing basketball",
                "Can't believe that call",
                "What a dunk!",
                "Three pointer!",
                "Great defense",
                "This game is wild",
                "Incredible pass",
                "Foul? Really?",
                "That was clean",
                "MVP performance",
                "Bench is stepping up",
                "Clutch shot!",
                "Game over",
                "What a comeback",
                "This is why I love basketball",
                "Historic game",
                "Unbelievable"
            ]),
            "created_utc": int(comment_time.timestamp()),
            "score": random.randint(1, 50),
            "author": f"user_{random.randint(1, 200)}",
            "subreddit": "nba"
        })
        comment_id += 1
    
    # Post-game comments (30 minutes after)
    for i in range(15):
        comment_time = game_start + timedelta(hours=2, minutes=30) + timedelta(minutes=i*2)
        comments.append({
            "id": f"comment_{comment_id}",
            "body": random.choice([
                "What a game!",
                "That was incredible",
                "Best game I've seen this season",
                "Can't believe the ending",
                "Historic performance",
                "That's why they're champions",
                "What a finish!",
                "Incredible comeback",
                "Game of the year candidate",
                "That was wild",
                "What a show",
                "Amazing basketball",
                "That's the NBA for you",
                "What a night",
                "Unforgettable game"
            ]),
            "created_utc": int(comment_time.timestamp()),
            "score": random.randint(1, 35),
            "author": f"user_{random.randint(1, 150)}",
            "subreddit": "nba"
        })
        comment_id += 1
    
    # Create submission
    submission = {
        "id": f"submission_{date_str}_{away}_{home}",
        "title": f"Game Thread: {away} @ {home} ({date_str})",
        "created_utc": int((game_start - timedelta(hours=1)).timestamp()),
        "score": random.randint(100, 500),
        "author": "AutoModerator",
        "subreddit": "nba",
        "num_comments": len(comments)
    }
    
    return {
        "game_id": f"{date_str}-{away}-{home}",
        "date": date_str,
        "away": away,
        "home": home,
        "submission": submission,
        "comments": comments
    }

def main():
    """Create sample data for the mini schedule."""
    # Read the mini schedule
    with open("mini_schedule.csv", "r") as f:
        lines = f.readlines()[1:]  # Skip header
    
    # Create output directory
    out_dir = Path("data/raw_reddit_mini")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    print("Creating sample Reddit data for testing...")
    
    for line in lines:
        date, away, home = line.strip().split(",")
        print(f"Creating sample data for {date} {away} @ {home}")
        
        game_data = create_sample_game_data(date, away, home)
        
        # Save to file
        outfile = out_dir / f"{date}-{away}-{home}.json"
        with open(outfile, "w", encoding="utf-8") as f:
            json.dump(game_data, f, indent=2, ensure_ascii=False)
        
        print(f"  Created {len(game_data['comments'])} comments")
    
    print(f"\nSample data created in {out_dir}")
    print("Now you can test the ingest pipeline!")

if __name__ == "__main__":
    main()
