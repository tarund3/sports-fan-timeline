#!/usr/bin/env python3
"""
Quick demo script for testing the trained model.
"""

import json
import torch
from pathlib import Path
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

def load_model_and_tokenizer(model_path: str):
    """Load the trained model and tokenizer."""
    print(f"Loading model from {model_path}")
    
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
        print("✅ Model loaded successfully")
        
        return model, tokenizer
        
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        return None, None

def generate_once(game_id: str, model, tokenizer):
    """Generate a single timeline for a game."""
    prompt = f"""You are a sports timeline generator. Given fan comments from a game thread, create a concise event summary with sentiment.

[CONTEXT]
game_id={game_id}
quarter=Q1 window=11:59 score_before=0-0 score_after=0-0

[COMMENTS]
• What a game!
• This is amazing
• Great shot!"""
    
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

def main():
    # Check if model exists
    model_path = "outputs/sft_mini"
    if not Path(model_path).exists():
        print(f"❌ Model not found at {model_path}")
        print("Please run training first: python train_sft_mini.py")
        return
    
    # Load model
    model, tokenizer = load_model_and_tokenizer(model_path)
    if model is None:
        return
    
    # Test generation
    print("\n" + "="*50)
    print("Testing Model Generation")
    print("="*50)
    
    test_games = ["2019-12-01-LAL-DAL", "2020-01-16-BOS-MIL"]
    
    for game_id in test_games:
        print(f"\n🎮 Generating timeline for {game_id}")
        print("-" * 40)
        
        try:
            output = generate_once(game_id, model, tokenizer)
            print(f"Generated: {output}")
            
            # Try to parse as JSON
            try:
                parsed = json.loads(output)
                print("✅ Valid JSON output")
                if "timeline" in parsed:
                    print(f"📊 Sentiment: {parsed['timeline'][0].get('fan_sentiment', 'N/A')}")
            except json.JSONDecodeError:
                print("❌ Invalid JSON output")
                
        except Exception as e:
            print(f"❌ Generation error: {e}")
    
    print(f"\n{'='*50}")
    print("Demo complete!")
    print(f"{'='*50}")

if __name__ == "__main__":
    main()
