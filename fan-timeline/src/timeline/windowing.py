from __future__ import annotations
from typing import List, Dict, Tuple
import random
import json
from pathlib import Path
try:
    from .utils import truncate_tokens
except ImportError:
    from utils import truncate_tokens

def build_windows(comments: List[Dict], pbp_events: List[Dict], win_len: int = 60) -> Dict[int, Dict]:
    """Collapse comments + PBP into fixed 60-second bins.
    
    Args:
        comments: List of comment dictionaries with 'elapsed' field
        pbp_events: List of PBP event dictionaries with 'elapsed' field
        win_len: Window length in seconds (default 60)
        
    Returns:
        Dictionary mapping window_id to window data
    """
    windows = {}
    
    # Add comments to windows
    for c in comments:
        if 'elapsed' not in c:
            continue
        win = int(c["elapsed"] // win_len)
        if win not in windows:
            windows[win] = {"comments": [], "pbp": []}
        windows[win]["comments"].append(c)
    
    # Add PBP events to windows
    for e in pbp_events:
        if 'elapsed' not in e:
            continue
        win = int(e["elapsed"] // win_len)
        if win not in windows:
            windows[win] = {"comments": [], "pbp": []}
        windows[win]["pbp"].append(e)
    
    return windows

def create_window_summary(win_id: int, window_data: Dict, win_len: int = 60) -> Dict:
    """Create a summary for a single window."""
    comments = window_data.get("comments", [])
    pbp = window_data.get("pbp", [])
    
    # Calculate window timing
    start_sec = win_id * win_len
    end_sec = start_sec + win_len - 1
    
    # Convert to period and clock
    period = (start_sec // 720) + 1
    secs_into_period = start_sec % 720
    clock_start = f"{11 - secs_into_period // 60:02d}:{59 - secs_into_period % 60:02d}"
    
    # Calculate scores (simplified - would need more sophisticated logic in practice)
    score_before = "0-0"  # Placeholder
    score_after = "0-0"   # Placeholder
    
    return {
        "win_id": win_id,
        "period": period,
        "clock_start": clock_start,
        "score_before": score_before,
        "score_after": score_after,
        "comments": comments,
        "pbp": pbp
    }

def save_windows_to_jsonl(windows: Dict[int, Dict], output_path: Path, win_len: int = 60):
    """Save windows to JSONL file."""
    with open(output_path, 'w', encoding='utf-8') as f:
        for win_id in sorted(windows.keys()):
            window_summary = create_window_summary(win_id, windows[win_id], win_len)
            f.write(json.dumps(window_summary, ensure_ascii=False) + "\n")

def build_windows_legacy(comments: List[Dict], start_utc: int, seconds: int = 60,
                  max_chars: int = 3500, top_k_upvoted: int = 8, sample_extra: int = 12) -> List[Dict]:
    """Group comments into minute windows; select top-K by score plus a sample of others."""
    # Bucket by minute from start
    buckets: Dict[int, List[Dict]] = {}
    for c in comments:
        t = max(0, int(c["created_utc"]) - start_utc)
        minute = t // seconds
        buckets.setdefault(minute, []).append(c)
    
    windows = []
    for minute, group in sorted(buckets.items()):
        group = sorted(group, key=lambda x: x.get("score", 0), reverse=True)
        topk = group[:top_k_upvoted]
        rest = group[top_k_upvoted:]
        sample = random.sample(rest, k=min(len(rest), sample_extra)) if rest else []
        chosen = topk + sample
        text = "\n".join(f"• {c['body']}" for c in chosen)
        text = truncate_tokens(text, max_chars)
        win = {
            "minute": int(minute),
            "window_label": f"{minute:02d}:00–{minute:02d}:59",
            "comments": chosen,
            "comments_text": text,
        }
        windows.append(win)
    return windows
