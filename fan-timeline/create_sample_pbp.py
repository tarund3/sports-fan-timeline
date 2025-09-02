#!/usr/bin/env python3
"""
Create sample PBP data for mini games.
"""

import json
from pathlib import Path
from typing import List, Dict

def create_sample_pbp_events(game_id: str) -> List[Dict]:
    """Create sample PBP events for a game."""
    events = []
    
    # Create a realistic game flow
    periods = [
        # Q1: 12:00 to 0:00
        [("12:00", "Start of 1st Period"), ("11:45", "Jump Ball"), ("11:30", "Made 2PT Jump Shot")],
        # Q2: 12:00 to 0:00  
        [("12:00", "Start of 2nd Period"), ("11:30", "Made 3PT Jump Shot"), ("10:45", "Made Free Throw")],
        # Q3: 12:00 to 0:00
        [("12:00", "Start of 3rd Period"), ("11:15", "Made 2PT Layup"), ("10:30", "Made 3PT Jump Shot")],
        # Q4: 12:00 to 0:00
        [("12:00", "Start of 4th Period"), ("11:00", "Made 2PT Dunk"), ("10:15", "Made Free Throw")],
    ]
    
    teams = ["LAL", "DAL"] if "LAL-DAL" in game_id else ["BOS", "MIL"] if "BOS-MIL" in game_id else ["GSW", "LAL"] if "GSW-LAL" in game_id else ["MEM", "GSW"] if "MEM-GSW" in game_id else ["MIA", "DEN"]
    
    event_id = 1
    for period_num, period_events in enumerate(periods, 1):
        for clock, desc in period_events:
            # Determine team and points
            team = teams[event_id % 2]  # Alternate teams
            points = 0
            if "Made" in desc:
                if "3PT" in desc:
                    points = 3
                elif "Free Throw" in desc:
                    points = 1
                else:
                    points = 2
            
            events.append({
                "period": period_num,
                "clock": clock,
                "team": team,
                "points": points,
                "desc": desc,
                "game_id": game_id
            })
            event_id += 1
    
    return events

def main():
    mini_games = [
        "2019-12-01-LAL-DAL",
        "2020-01-16-BOS-MIL", 
        "2021-05-19-GSW-LAL",
        "2022-12-25-MEM-GSW",
        "2023-06-01-MIA-DEN"
    ]
    
    output_dir = Path("data/pbp")
    output_dir.mkdir(exist_ok=True)
    
    for game_id in mini_games:
        print(f"Creating sample PBP for {game_id}")
        events = create_sample_pbp_events(game_id)
        
        output_file = output_dir / f"{game_id}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(events, f, indent=2)
        
        print(f"Saved {len(events)} events to {output_file}")

if __name__ == "__main__":
    main()
