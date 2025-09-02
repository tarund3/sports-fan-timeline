from __future__ import annotations
import json, os
from typing import List, Dict, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import jsonschema
from .teacher import windows_from_sources, aggregate_sentiment, label_sentiment, write_event
from .utils import clean_text

app = FastAPI(title="Sports Timeline API", version="1.0.0")

# Load schema for validation
SCHEMA_PATH = "schema/timeline.schema.json"
try:
    with open(SCHEMA_PATH, "r") as f:
        TIMELINE_SCHEMA = json.load(f)
except FileNotFoundError:
    print(f"Warning: Schema file {SCHEMA_PATH} not found. Validation disabled.")
    TIMELINE_SCHEMA = None

class TimelineRequest(BaseModel):
    game_id: str
    reddit_thread_json: Optional[str] = None
    pbp_json: Optional[str] = None
    mode: str = "post_hoc"  # "post_hoc" or "live_sim"

class TimelineResponse(BaseModel):
    game_id: str
    timeline: List[Dict]
    top_themes: Optional[List[str]] = None
    notes: Optional[str] = None

def validate_timeline(data: Dict) -> bool:
    """Validate timeline data against schema."""
    if TIMELINE_SCHEMA is None:
        return True  # Skip validation if schema not available
    
    try:
        jsonschema.validate(data, TIMELINE_SCHEMA)
        return True
    except jsonschema.ValidationError as e:
        print(f"Schema validation error: {e}")
        return False

def extract_themes(windows: List[Dict]) -> List[str]:
    """Extract top themes from windows."""
    from collections import Counter
    all_text = " ".join(w.get("comments_text", "") for w in windows)
    words = [w.lower() for w in all_text.split() if len(w) > 3]
    themes = [word for word, count in Counter(words).most_common(20) if count >= 3]
    return themes[:5]

@app.post("/v1/timeline/generate", response_model=TimelineResponse)
async def generate_timeline(request: TimelineRequest):
    """Generate a timeline from Reddit thread and PBP data."""
    try:
        # Parse input data
        if request.reddit_thread_json:
            reddit_data = json.loads(request.reddit_thread_json)
        else:
            raise HTTPException(status_code=400, detail="reddit_thread_json is required")
        
        if request.pbp_json:
            pbp_data = json.loads(request.pbp_json)
        else:
            raise HTTPException(status_code=400, detail="pbp_json is required")
        
        # Create temporary files for processing
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as reddit_file:
            for comment in reddit_data:
                reddit_file.write(json.dumps(comment) + '\n')
            reddit_path = reddit_file.name
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as pbp_file:
            json.dump(pbp_data, pbp_file)
            pbp_path = pbp_file.name
        
        try:
            # Process with teacher pipeline
            windows, pbp = windows_from_sources(reddit_path, pbp_path)
            
            # Build timeline
            timeline = []
            for w in windows:
                sent_val = aggregate_sentiment(w.get("comments", []))
                sent_lbl = label_sentiment(sent_val, 0.15, -0.15)
                event = write_event(w, max_len=120)
                
                timeline.append({
                    "ts": w["window_label"],
                    "event": event,
                    "fan_sentiment": sent_lbl
                })
            
            # Extract themes
            themes = extract_themes(windows)
            
            # Build response
            response_data = {
                "game_id": request.game_id,
                "timeline": timeline,
                "top_themes": themes,
                "notes": "Generated using teacher pipeline (no fine-tuned model)"
            }
            
            # Validate response
            if not validate_timeline(response_data):
                raise HTTPException(status_code=500, detail="Generated timeline failed schema validation")
            
            return TimelineResponse(**response_data)
            
        finally:
            # Clean up temp files
            os.unlink(reddit_path)
            os.unlink(pbp_path)
            
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON in request")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "sports-timeline-api"}

@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "service": "Sports Timeline API",
        "version": "1.0.0",
        "endpoints": {
            "POST /v1/timeline/generate": "Generate timeline from Reddit + PBP data",
            "GET /health": "Health check",
            "GET /docs": "API documentation (Swagger UI)"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
