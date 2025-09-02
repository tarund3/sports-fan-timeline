#!/usr/bin/env python3
"""
Extract specific games from PBP CSV files for the mini dataset.
"""

import csv
import json
from pathlib import Path
from typing import Dict, List

# Mini dataset games
MINI_GAMES = {
    "2019-12-01-LAL-DAL": {"date": "2019-12-01", "away": "LAL", "home": "DAL", "year": 2019},
    "2020-01-16-BOS-MIL": {"date": "2020-01-16", "away": "BOS", "home": "MIL", "year": 2020},
    "2021-05-19-GSW-LAL": {"date": "2021-05-19", "away": "GSW", "home": "LAL", "year": 2021},
    "2022-12-25-MEM-GSW": {"date": "2022-12-25", "away": "MEM", "home": "GSW", "year": 2022},
    "2023-06-01-MIA-DEN": {"date": "2023-06-01", "away": "MIA", "home": "DEN", "year": 2023},
}

def extract_game_from_csv(csv_path: Path, game_info: Dict) -> List[Dict]:
    """Extract events for a specific game from the CSV file."""
    events = []
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Check if this row belongs to our target game
            # We'll need to match by date or game ID
            # For now, let's extract all events and filter later
            events.append(row)
    
    return events

def main():
    pbp_dir = Path("data/pbp/raw_pbp")
    output_dir = Path("data/pbp")
    output_dir.mkdir(exist_ok=True)
    
    # For each mini game, extract from the appropriate year's CSV
    for game_id, game_info in MINI_GAMES.items():
        year = game_info["year"]
        csv_file = pbp_dir / f"pbp{year}.csv"
        
        if not csv_file.exists():
            print(f"Warning: {csv_file} not found for {game_id}")
            continue
        
        print(f"Processing {game_id} from {csv_file}")
        
        # Extract all events from the year's CSV
        events = extract_game_from_csv(csv_file, game_info)
        
        # For now, let's create a simple JSON file with all events
        # We'll need to implement proper game filtering later
        output_file = output_dir / f"{game_id}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(events, f, indent=2)
        
        print(f"Saved {len(events)} events to {output_file}")

if __name__ == "__main__":
    main()
