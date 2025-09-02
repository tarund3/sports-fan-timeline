from __future__ import annotations
import json, argparse, os, random
from typing import List, Dict
from datetime import datetime, timedelta

# Sample Reddit comments for synthetic data
SAMPLE_COMMENTS = [
    "LeBron is absolutely cooking tonight! 🔥",
    "This defense is suffocating them",
    "AD with the block! What a play!",
    "Refs are missing obvious calls",
    "Bench unit is stepping up big time",
    "Cold from three tonight, need to get hot",
    "Turnover after turnover, killing our momentum",
    "Clutch shot! This team has heart",
    "Foul trouble is going to be a problem",
    "Great ball movement, beautiful basketball",
    "Can't buy a bucket right now",
    "Defensive intensity is through the roof",
    "Rebounding is keeping us in this",
    "Fast break points are the difference",
    "Need to close out quarters better",
    "This run is exactly what we needed",
    "Bench mob is making plays",
    "Star players showing up when it matters",
    "Role players stepping up in big moments",
    "This is championship basketball right here"
]

# Sample PBP events
SAMPLE_PBP = [
    {"period": 1, "clock": "11:45", "team": "LAL", "points": 2, "desc": "LeBron James makes 2-pt layup"},
    {"period": 1, "clock": "10:32", "team": "DAL", "points": 3, "desc": "Luka Doncic makes 3-pt jump shot"},
    {"period": 1, "clock": "09:15", "team": "LAL", "points": 2, "desc": "Anthony Davis makes 2-pt dunk"},
    {"period": 1, "clock": "08:42", "team": "DAL", "points": 2, "desc": "Kyrie Irving makes 2-pt layup"},
    {"period": 1, "clock": "07:30", "team": "LAL", "points": 0, "desc": "LeBron James misses 3-pt jump shot"},
    {"period": 1, "clock": "06:45", "team": "DAL", "points": 2, "desc": "Luka Doncic makes 2-pt layup"},
    {"period": 1, "clock": "05:20", "team": "LAL", "points": 2, "desc": "Austin Reaves makes 2-pt layup"},
    {"period": 1, "clock": "04:15", "team": "DAL", "points": 0, "desc": "Kyrie Irving misses 3-pt jump shot"},
    {"period": 1, "clock": "03:30", "team": "LAL", "points": 2, "desc": "Anthony Davis makes 2-pt hook shot"},
    {"period": 1, "clock": "02:45", "team": "DAL", "points": 2, "desc": "Luka Doncic makes 2-pt layup"},
    {"period": 1, "clock": "01:20", "team": "LAL", "points": 3, "desc": "LeBron James makes 3-pt jump shot"},
    {"period": 2, "clock": "11:30", "team": "DAL", "points": 2, "desc": "Kyrie Irving makes 2-pt layup"},
    {"period": 2, "clock": "10:15", "team": "LAL", "points": 2, "desc": "Anthony Davis makes 2-pt dunk"},
    {"period": 2, "clock": "09:00", "team": "DAL", "points": 3, "desc": "Luka Doncic makes 3-pt jump shot"},
    {"period": 2, "clock": "08:30", "team": "LAL", "points": 2, "desc": "LeBron James makes 2-pt layup"},
    {"period": 2, "clock": "07:15", "team": "DAL", "points": 0, "desc": "Kyrie Irving misses 2-pt layup"},
    {"period": 2, "clock": "06:45", "team": "LAL", "points": 2, "desc": "Austin Reaves makes 2-pt layup"},
    {"period": 2, "clock": "05:30", "team": "DAL", "points": 2, "desc": "Luka Doncic makes 2-pt layup"},
    {"period": 2, "clock": "04:15", "team": "LAL", "points": 3, "desc": "LeBron James makes 3-pt jump shot"},
    {"period": 2, "clock": "03:00", "team": "DAL", "points": 2, "desc": "Kyrie Irving makes 2-pt layup"},
    {"period": 2, "clock": "02:30", "team": "LAL", "points": 2, "desc": "Anthony Davis makes 2-pt hook shot"},
    {"period": 2, "clock": "01:45", "team": "DAL", "points": 3, "desc": "Luka Doncic makes 3-pt jump shot"},
    {"period": 2, "clock": "01:00", "team": "LAL", "points": 2, "desc": "LeBron James makes 2-pt layup"}
]

def generate_synthetic_reddit(game_id: str, num_comments: int = 100) -> List[Dict]:
    """Generate synthetic Reddit comments for a game."""
    comments = []
    base_time = datetime.now() - timedelta(hours=2)  # 2 hours ago
    
    for i in range(num_comments):
        # Random time within the game window
        comment_time = base_time + timedelta(minutes=random.randint(0, 120))
        
        comment = {
            "body": random.choice(SAMPLE_COMMENTS),
            "created_utc": int(comment_time.timestamp()),
            "score": random.randint(-5, 50),  # Some downvoted, some highly upvoted
            "author": f"user_{random.randint(1000, 9999)}"
        }
        comments.append(comment)
    
    # Sort by time
    comments.sort(key=lambda x: x["created_utc"])
    return comments

def generate_synthetic_pbp() -> List[Dict]:
    """Generate synthetic play-by-play data."""
    return SAMPLE_PBP.copy()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, help="Output directory for synthetic data")
    ap.add_argument("--game_id", default="2019-12-01-LAL-DAL", help="Game identifier")
    ap.add_argument("--num_comments", type=int, default=100, help="Number of Reddit comments to generate")
    args = ap.parse_args()
    
    # Create output directories
    reddit_dir = os.path.join(args.out, "reddit")
    pbp_dir = os.path.join(args.out, "pbp")
    os.makedirs(reddit_dir, exist_ok=True)
    os.makedirs(pbp_dir, exist_ok=True)
    
    # Generate synthetic data
    print("Generating synthetic Reddit comments...")
    reddit_data = generate_synthetic_reddit(args.game_id, args.num_comments)
    
    print("Generating synthetic play-by-play...")
    pbp_data = generate_synthetic_pbp()
    
    # Save Reddit data
    reddit_file = os.path.join(reddit_dir, f"{args.game_id}.jsonl")
    with open(reddit_file, "w", encoding="utf-8") as f:
        for comment in reddit_data:
            f.write(json.dumps(comment, ensure_ascii=False) + "\n")
    
    # Save PBP data
    pbp_file = os.path.join(pbp_dir, f"{args.game_id}.json")
    with open(pbp_file, "w", encoding="utf-8") as f:
        json.dump(pbp_data, f, indent=2, ensure_ascii=False)
    
    print(f"Generated synthetic data:")
    print(f"  Reddit: {reddit_file} ({len(reddit_data)} comments)")
    print(f"  PBP: {pbp_file} ({len(pbp_data)} events)")
    print(f"\\nYou can now run:")
    print(f"  python src/timeline/teacher.py --reddit {reddit_file} --pbp {pbp_file} --out {args.out}/teacher")

if __name__ == "__main__":
    main()
