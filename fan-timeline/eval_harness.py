#!/usr/bin/env python3
"""
Evaluation harness for the trained SFT model.
"""

import json
import argparse
import torch
from pathlib import Path
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_model_and_tokenizer(model_path: str):
    """Load the trained model and tokenizer."""
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
        logger.info("Model loaded successfully")
        
        return model, tokenizer
        
    except Exception as e:
        logger.error(f"Error loading model: {e}")
        return None, None

def generate_timeline(model, tokenizer, prompt: str, max_length: int = 512):
    """Generate timeline from prompt."""
    inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=max_length)
    
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

def validate_json_output(text: str) -> dict:
    """Validate if the generated text is valid JSON."""
    try:
        # Try to find JSON in the text
        start_idx = text.find('{')
        end_idx = text.rfind('}') + 1
        
        if start_idx == -1 or end_idx == 0:
            return {"valid": False, "error": "No JSON brackets found"}
        
        json_text = text[start_idx:end_idx]
        parsed = json.loads(json_text)
        
        # Check schema
        if "timeline" not in parsed:
            return {"valid": False, "error": "Missing 'timeline' field"}
        
        timeline = parsed["timeline"]
        if not isinstance(timeline, list) or len(timeline) == 0:
            return {"valid": False, "error": "Timeline must be non-empty list"}
        
        # Check first timeline entry
        entry = timeline[0]
        required_fields = ["ts", "event", "fan_sentiment"]
        missing_fields = [field for field in required_fields if field not in entry]
        
        if missing_fields:
            return {"valid": False, "error": f"Missing fields: {missing_fields}"}
        
        # Check sentiment values
        valid_sentiments = {"pos", "neg", "mixed"}
        if entry["fan_sentiment"] not in valid_sentiments:
            return {"valid": False, "error": f"Invalid sentiment: {entry['fan_sentiment']}"}
        
        return {"valid": True, "parsed": parsed}
        
    except json.JSONDecodeError as e:
        return {"valid": False, "error": f"JSON decode error: {e}"}
    except Exception as e:
        return {"valid": False, "error": f"Validation error: {e}"}

def evaluate_model(model_path: str, test_prompts: list):
    """Evaluate the model on test prompts."""
    model, tokenizer = load_model_and_tokenizer(model_path)
    if model is None:
        return
    
    results = []
    
    for i, prompt in enumerate(test_prompts):
        logger.info(f"Testing prompt {i+1}/{len(test_prompts)}")
        
        # Generate response
        generated = generate_timeline(model, tokenizer, prompt)
        
        # Validate output
        validation = validate_json_output(generated)
        
        result = {
            "prompt": prompt,
            "generated": generated,
            "validation": validation
        }
        
        results.append(result)
        
        # Log results
        if validation["valid"]:
            logger.info(f"✅ Valid output generated")
        else:
            logger.warning(f"❌ Invalid output: {validation['error']}")
    
    # Calculate statistics
    valid_count = sum(1 for r in results if r["validation"]["valid"])
    total_count = len(results)
    success_rate = (valid_count / total_count) * 100 if total_count > 0 else 0
    
    logger.info(f"\n{'='*50}")
    logger.info(f"Evaluation Results")
    logger.info(f"{'='*50}")
    logger.info(f"Total prompts: {total_count}")
    logger.info(f"Valid outputs: {valid_count}")
    logger.info(f"Success rate: {success_rate:.1f}%")
    
    # Show sample outputs
    logger.info(f"\nSample outputs:")
    for i, result in enumerate(results[:3]):  # Show first 3
        logger.info(f"\nPrompt {i+1}:")
        logger.info(f"Generated: {result['generated'][:200]}...")
        if result["validation"]["valid"]:
            logger.info(f"✅ Valid JSON")
        else:
            logger.info(f"❌ {result['validation']['error']}")
    
    return results

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model_path", required=True, help="Path to trained model")
    ap.add_argument("--test_prompts", nargs="+", help="Test prompts to evaluate")
    args = ap.parse_args()
    
    # Default test prompts if none provided
    if not args.test_prompts:
        args.test_prompts = [
            "You are a sports timeline generator. Given fan comments from a game thread, create a concise event summary with sentiment.\n\n[CONTEXT]\ngame_id=2019-12-01-LAL-DAL\nquarter=Q1 window=11:59 score_before=0-0 score_after=0-0\n\n[COMMENTS]\n• What a game!\n• This is amazing\n• Great shot!",
            "You are a sports timeline generator. Given fan comments from a game thread, create a concise event summary with sentiment.\n\n[CONTEXT]\ngame_id=2020-01-16-BOS-MIL\nquarter=Q2 window=10:30 score_before=45-42 score_after=50-45\n\n[COMMENTS]\n• Terrible call\n• Refs are awful\n• Can't believe this"
        ]
    
    results = evaluate_model(args.model_path, args.test_prompts)
    
    # Save results
    output_file = Path(args.model_path) / "evaluation_results.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Results saved to: {output_file}")

if __name__ == "__main__":
    main()
