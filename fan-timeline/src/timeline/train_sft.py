from __future__ import annotations
import os, json, argparse, yaml
from typing import List, Dict
from pathlib import Path

def load_config(config_path: str) -> Dict:
    """Load training configuration from YAML."""
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

def create_training_script(config: Dict, output_dir: str):
    """Create a training script that can be run independently."""
    script_content = f'''#!/usr/bin/env python3
"""
QLoRA SFT Training Script for Sports Timeline Generation
Generated from config: {config.get('train', {}).get('base_model', 'unknown')}
"""

import os
import torch
from datasets import Dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling
)
from peft import LoraConfig, get_peft_model, TaskType
import json

def load_sft_data(data_path: str):
    """Load SFT training data."""
    data = []
    with open(data_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    return data

def format_training_example(example):
    """Format example for training."""
    # Combine instruction + input + output
    text = example["instruction"]
    if example.get("input"):
        text += "\\n" + example["input"]
    text += "\\n" + example["output"]
    return {{"text": text}}

def main():
    # Load data
    print("Loading SFT data...")
    raw_data = load_sft_data("{config.get('paths', {}).get('sft_out', 'data/sft/sft_data.jsonl')}")
    
    # Format for training
    formatted_data = [format_training_example(ex) for ex in raw_data]
    dataset = Dataset.from_list(formatted_data)
    
    print(f"Loaded {{len(dataset)}} training examples")
    
    # Load model and tokenizer
    print("Loading base model...")
    model_name = "{config.get('train', {}).get('base_model', 'meta-llama/Meta-Llama-3.1-8B-Instruct')}"
    
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float16,
        device_map="auto" if torch.cuda.is_available() else None,
        trust_remote_code=True
    )
    
    # Configure LoRA
    print("Configuring LoRA...")
    lora_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r={config.get('train', {}).get('lora_rank', 16)},
        lora_alpha={config.get('train', {}).get('lora_alpha', 32)},
        lora_dropout={config.get('train', {}).get('dropout', 0.05)},
        target_modules=["q_proj", "v_proj", "k_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
    )
    
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()
    
    # Training arguments
    training_args = TrainingArguments(
        output_dir="{output_dir}",
        num_train_epochs={config.get('train', {}).get('epochs', 3)},
        learning_rate={config.get('train', {}).get('lr', 2e-4)},
        per_device_train_batch_size={config.get('train', {}).get('micro_batch_size', 1)},
        gradient_accumulation_steps={config.get('train', {}).get('gradient_accumulation', 8)},
        max_seq_length={config.get('train', {}).get('max_seq_len', 3072)},
        warmup_steps=100,
        logging_steps=10,
        save_steps=500,
        evaluation_strategy="no",
        save_strategy="epoch",
        load_best_model_at_end=False,
        ddp_find_unused_parameters=False,
        remove_unused_columns=False,
        dataloader_pin_memory=False,
    )
    
    # Data collator
    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=False,
    )
    
    # Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=dataset,
        data_collator=data_collator,
        tokenizer=tokenizer,
    )
    
    # Train
    print("Starting training...")
    trainer.train()
    
    # Save
    print("Saving model...")
    trainer.save_model()
    tokenizer.save_pretrained("{output_dir}")
    
    print("Training complete!")

if __name__ == "__main__":
    main()
'''
    
    script_path = os.path.join(output_dir, "train_sft.py")
    with open(script_path, "w") as f:
        f.write(script_content)
    
    # Make executable
    os.chmod(script_path, 0o755)
    return script_path

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True, help="Path to config YAML")
    ap.add_argument("--output_dir", help="Override output directory from config")
    args = ap.parse_args()
    
    # Load config
    config = load_config(args.config)
    
    # Determine output directory
    if args.output_dir:
        output_dir = args.output_dir
    else:
        output_dir = config.get("train", {}).get("output_dir", "outputs/sft-default")
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Create training script
    script_path = create_training_script(config, output_dir)
    
    print(f"Created training script: {script_path}")
    print(f"Output directory: {output_dir}")
    print("\\nTo train:")
    print(f"cd {output_dir}")
    print("python train_sft.py")
    print("\\nNote: This requires a GPU with sufficient VRAM for the base model.")

if __name__ == "__main__":
    main()
