from __future__ import annotations
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import math
import csv
from pathlib import Path
try:
    from .utils import mmss_to_secs
except ImportError:
    from utils import mmss_to_secs

@dataclass
class TimeAlignConfig:
    start_utc: int    # scheduled tip-off in UTC seconds
    q_seconds: int = 12 * 60

def utc_to_game_clock(comment_ts: int, game_start_ts: int) -> Optional[str]:
    """Convert UTC timestamp to game clock format.
    
    Args:
        comment_ts: UTC timestamp of the comment
        game_start_ts: UTC timestamp of game tip-off
        
    Returns:
        Game clock string like "Q1 03:58" or None if pre-game
    """
    delta = comment_ts - game_start_ts
    if delta < 0:
        return None                 # pre-game
    
    period = delta // 720 + 1       # 12-min quarters
    secs_into_q = delta % 720
    
    if period > 4:
        # Overtime periods
        ot_period = period - 4
        label = f"OT{ot_period}"
    else:
        label = f"Q{period}"
    
    mm = 11 - secs_into_q // 60
    ss = 59 - secs_into_q % 60
    
    return f"{label} {mm:02d}:{ss:02d}"

def load_game_schedule(schedule_path: str) -> Dict[str, int]:
    """Load game schedule with tip-off times."""
    schedule = {}
    with open(schedule_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            game_id = row['game_id']
            start_utc = int(row['start_utc'])
            schedule[game_id] = start_utc
    return schedule

def map_real_to_game(utc_ts: int, cfg: TimeAlignConfig) -> Tuple[str, str]:
    """Map absolute unix time to (quarter label, MM:SS clock).
    If mapping is uncertain/negative, return real-time bin label instead: "00:00–00:59" style.
    """
    delta = utc_ts - cfg.start_utc
    if delta < 0:
        # pregame chatter → use real-time bins
        mm = max(0, delta // 60)
        return ("REAL", f"{mm:02d}:00–{mm:02d}:59")
    
    q = delta // cfg.q_seconds
    if q > 5:
        # postgame
        mm = delta // 60
        return ("REAL", f"{mm:02d}:00–{mm:02d}:59")
    
    within = delta % cfg.q_seconds
    # Convert to game clock (counting down)
    remain = cfg.q_seconds - within
    m = remain // 60
    s = remain % 60
    return (f"Q{min(q+1, 4) if q < 4 else 'OT'}", f"{m:02d}:{s:02d}")

def add_elapsed_times(comments: List[Dict], game_start_utc: int) -> List[Dict]:
    """Add elapsed time to comments based on game start time."""
    for comment in comments:
        comment_ts = comment.get('created_utc', 0)
        elapsed = comment_ts - game_start_utc
        comment['elapsed'] = max(0, elapsed)  # Don't allow negative elapsed times
    return comments

def add_elapsed_times_pbp(pbp_events: List[Dict], game_start_utc: int) -> List[Dict]:
    """Add elapsed time to PBP events based on game start time."""
    for event in pbp_events:
        # For PBP events, we need to convert game clock to elapsed time
        # This is a simplified approach - in practice you'd need more sophisticated mapping
        period = event.get('period', 1)
        clock = event.get('clock', '12:00')
        
        # Convert game clock to seconds into the period
        clock_secs = mmss_to_secs(clock)
        period_secs = (period - 1) * 720  # 12 minutes per period
        elapsed = period_secs + (720 - clock_secs)  # Convert from countdown to elapsed
        
        event['elapsed'] = elapsed
    
    return pbp_events
