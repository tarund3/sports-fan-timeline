from __future__ import annotations
import json, argparse, csv
from dataclasses import dataclass
from typing import List, Dict
from pathlib import Path
try:
    from .utils import mmss_to_secs
except ImportError:
    from utils import mmss_to_secs

@dataclass
class PbpEvent:
    period: int            # 1..4 (OT as 5+)
    clock: str             # MM:SS (game clock)
    team: str              # e.g., LAL/DAL
    points: int            # points on this event
    desc: str              # description
    game_id: str           # game identifier

def parse_clock(clock_str: str) -> str:
    """Convert NBA clock format (PT12M00.00S) to MM:SS."""
    if not clock_str or clock_str == "PT12M00.00S":
        return "12:00"
    
    # Handle format like "PT11M40.00S"
    if clock_str.startswith("PT"):
        # Extract minutes and seconds
        parts = clock_str.replace("PT", "").replace("S", "").split("M")
        if len(parts) == 2:
            minutes = int(float(parts[0]))
            seconds = int(float(parts[1]))
            return f"{minutes:02d}:{seconds:02d}"
    
    return "12:00"

def extract_points(desc: str, team: str) -> int:
    """Extract points from description."""
    if not desc:
        return 0
    
    # Look for common scoring patterns
    if "3PT" in desc and "Made" in desc:
        return 3
    elif "2PT" in desc and "Made" in desc:
        return 2
    elif "Free Throw" in desc and "Made" in desc:
        return 1
    elif "Made" in desc and "PT" not in desc:
        # Default to 2 points if not specified
        return 2
    
    return 0

def load_pbp_csv(path: str, game_id: str) -> List[PbpEvent]:
    """Load PBP data from CSV format."""
    events: List[PbpEvent] = []
    
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Skip non-game events
            if row.get("type") in ["period", "timeout"]:
                continue
            
            period = int(row.get("period", 1))
            clock = parse_clock(row.get("clock", "PT12M00.00S"))
            team = row.get("team", "")
            desc = row.get("desc", "")
            points = extract_points(desc, team)
            
            # Only include events with meaningful descriptions
            if desc and desc.strip():
                events.append(PbpEvent(
                    period=period,
                    clock=clock,
                    team=team,
                    points=points,
                    desc=desc,
                    game_id=game_id
                ))
    
    return events

def load_pbp_json(path: str) -> List[PbpEvent]:
    """Legacy function for JSON format."""
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    events: List[PbpEvent] = []
    for e in raw:
        period = int(e.get("period", 1))
        clock = str(e.get("clock", "12:00"))
        team = str(e.get("team", ""))
        points = int(e.get("points", 0))
        desc = str(e.get("desc", ""))
        events.append(PbpEvent(period, clock, team, points, desc, ""))
    return events

def detect_big_runs(events: List[PbpEvent], window_secs: int = 120) -> List[Dict]:
    # Simple heuristic: any 8-0 (or more) within rolling 2-min
    # Returns list of dicts: {period, clock, run_str}
    out = []
    # Build timeline in seconds remaining within period
    pts_by_time = []
    for e in events:
        t = mmss_to_secs(e.clock)
        delta = e.points if e.team else 0
        pts_by_time.append((e.period, t, e.team, delta))
    
    # naive scan
    for i in range(len(pts_by_time)):
        p0, t0, team0, _ = pts_by_time[i]
        sum_team = {team0: 0}
        for j in range(i, len(pts_by_time)):
            p, t, team, delta = pts_by_time[j]
            if p != p0 or t < t0 - window_secs:
                break
            if team:
                sum_team[team] = sum_team.get(team, 0) + delta
        
        for tm, pts in sum_team.items():
            if pts >= 8:
                out.append({"period": p0, "clock": f"{t0//60:02d}:{t0%60:02d}", "run": f"{tm} {pts}-0"})
    return out

def process_file(infile: Path, outfile: Path, game_id: str):
    """Process a single PBP file to JSONL output."""
    print(f"Processing {infile} -> {outfile}")
    
    if infile.suffix == ".csv":
        events = load_pbp_csv(str(infile), game_id)
    elif infile.suffix == ".json":
        events = load_pbp_json(str(infile))
    else:
        print(f"Unknown file format: {infile}")
        return
    
    print(f"Loaded {len(events)} PBP events")
    
    # Save as JSONL
    with open(outfile, "w", encoding="utf-8") as f:
        for e in events:
            f.write(json.dumps(e.__dict__, ensure_ascii=False) + "\n")
    
    print(f"Saved {len(events)} events to {outfile}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in_dir", help="Input directory with CSV/JSON files")
    ap.add_argument("--out_dir", help="Output directory for JSONL files")
    ap.add_argument("--infile", help="Single input file (legacy)")
    ap.add_argument("--outfile", help="Single output file (legacy)")
    ap.add_argument("--print_runs", action="store_true")
    args = ap.parse_args()
    
    if args.in_dir and args.out_dir:
        # Directory mode
        in_dir = Path(args.in_dir)
        out_dir = Path(args.out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        
        # Process all CSV/JSON files
        input_files = list(in_dir.glob("*.csv")) + list(in_dir.glob("*.json"))
        print(f"Found {len(input_files)} input files")
        
        for infile in input_files:
            # Extract game ID from filename or use stem
            game_id = infile.stem
            outfile = out_dir / f"{game_id}.jsonl"
            process_file(infile, outfile, game_id)
            
    elif args.infile and args.outfile:
        # Single file mode (legacy)
        process_file(Path(args.infile), Path(args.outfile), "")
    else:
        print("Use --in_dir and --out_dir for directory processing, or --infile and --outfile for single file")
        return 1

if __name__ == "__main__":
    main()
