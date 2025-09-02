#!/usr/bin/env python3
"""
FastAPI server for timeline generation.
"""

import json
import torch
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pathlib import Path
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Sports Timeline Generator", version="1.0.0")

# Global variables for model and tokenizer
model = None
tokenizer = None

class TimelineRequest(BaseModel):
    game_id: str
    comments: list[str] = []
    quarter: str = "Q1"
    window: str = "11:59"
    score_before: str = "0-0"
    score_after: str = "0-0"

class TimelineResponse(BaseModel):
    timeline: list[dict]
    success: bool
    error: str = None

def load_model_and_tokenizer(model_path: str):
    """Load the trained model and tokenizer."""
    global model, tokenizer
    
    logger.info(f"Loading model from {model_path}")
    
    try:
        # Load tokenizer
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        
        # Load base model
        base_model_path = Path(model_path) / "base_model"
        if base_model_path.exists():
            base_model = AutoModelForCausalLM.from_pretrained(
                str(base_model_path),
                torch_dtype=torch.float16,
                device_map="auto" if torch.cuda.is_available() else None,
                trust_remote_code=True
            )
        else:
            # Try to load from the main directory
            base_model = AutoModelForCausalLM.from_pretrained(
                model_path,
                torch_dtype=torch.float16,
                device_map="auto" if torch.cuda.is_available() else None,
                trust_remote_code=True
            )
        
        # Load LoRA weights
        model = PeftModel.from_pretrained(base_model, model_path)
        logger.info("✅ Model loaded successfully")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error loading model: {e}")
        return False

def generate_timeline(request: TimelineRequest) -> str:
    """Generate timeline from request."""
    global model, tokenizer
    
    if model is None or tokenizer is None:
        raise HTTPException(status_code=500, detail="Model not loaded")
    
    # Build prompt
    comments_text = "\n• ".join(request.comments) if request.comments else "• What a game!\n• This is amazing"
    
    prompt = f"""You are a sports timeline generator. Given fan comments from a game thread, create a concise event summary with sentiment.

[CONTEXT]
game_id={request.game_id}
quarter={request.quarter} window={request.window} score_before={request.score_before} score_after={request.score_after}

[COMMENTS]
{comments_text}"""
    
    inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512)
    
    if torch.cuda.is_available():
        inputs = {k: v.cuda() for k, v in inputs.items()}
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=256,
            temperature=0.7,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id,
            eos_token_id=tokenizer.eos_token_id
        )
    
    generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    # Extract only the new generated part
    prompt_length = len(tokenizer.decode(inputs["input_ids"][0], skip_special_tokens=True))
    generated_part = generated_text[prompt_length:].strip()
    
    return generated_part

@app.on_event("startup")
async def startup_event():
    """Load model on startup."""
    model_path = "outputs/sft_mini"
    if not Path(model_path).exists():
        logger.warning(f"Model not found at {model_path}. Please train first.")
        return
    
    success = load_model_and_tokenizer(model_path)
    if not success:
        logger.error("Failed to load model")

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Sports Timeline Generator API", "status": "running"}

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "cuda_available": torch.cuda.is_available()
    }

@app.post("/v1/timeline/generate", response_model=TimelineResponse)
async def generate_timeline_endpoint(request: TimelineRequest):
    """Generate timeline from fan comments."""
    try:
        generated_text = generate_timeline(request)
        
        # Try to parse as JSON
        try:
            parsed = json.loads(generated_text)
            if "timeline" in parsed:
                return TimelineResponse(
                    timeline=parsed["timeline"],
                    success=True
                )
            else:
                return TimelineResponse(
                    timeline=[],
                    success=False,
                    error="Generated text missing timeline field"
                )
        except json.JSONDecodeError:
            return TimelineResponse(
                timeline=[],
                success=False,
                error=f"Generated text is not valid JSON: {generated_text[:200]}"
            )
            
    except Exception as e:
        logger.error(f"Generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
