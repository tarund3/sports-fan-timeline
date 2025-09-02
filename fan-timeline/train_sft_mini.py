#!/usr/bin/env python3
"""
QLoRA SFT Training Script for Sports Timeline Generation
Mini dataset version for Day 3 debugging
"""

import os
import json
import yaml
import torch
from pathlib import Path
from datasets import Dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling
)
from peft import LoraConfig, get_peft_model, TaskType
from trl import SFTTrainer
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_config(config_path: str) -> dict:
    """Load training configuration from YAML."""
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

def load_sft_data(data_path: str):
    """Load SFT training data."""
    data = []
    with open(data_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    return data

def format_training_example(example, tokenizer, max_length=512):
    """Format example for training."""
    # Combine instruction + input + output
    text = example["instruction"]
    if example.get("input"):
        text += "\n" + example["input"]
    text += "\n" + example["output"]
    
    # Tokenize the text
    encoding = tokenizer(
        text,
        truncation=True,
        max_length=max_length,
        padding="max_length",
        return_tensors="pt"
    )
    
    return {
        "input_ids": encoding["input_ids"].squeeze(),
        "attention_mask": encoding["attention_mask"].squeeze(),
        "labels": encoding["input_ids"].squeeze()
    }

def main():
    # Load configuration
    config_path = "configs/sft_mini.yaml"
    if not os.path.exists(config_path):
        logger.error(f"Config file not found: {config_path}")
        return
    
    config = load_config(config_path)
    logger.info("Configuration loaded successfully")
    
    # Load data
    logger.info("Loading SFT data...")
    data_path = config["paths"]["sft_data"]
    if not os.path.exists(data_path):
        logger.error(f"SFT data file not found: {data_path}")
        return
    
    raw_data = load_sft_data(data_path)
    logger.info(f"Loaded {len(raw_data)} training examples")
    
    # Load model and tokenizer
    logger.info("Loading base model...")
    model_name = config["train"]["base_model"]
    
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        
        # Load model with appropriate settings
        model_kwargs = {
            "torch_dtype": getattr(torch, config["hardware"]["torch_dtype"]),
            "trust_remote_code": True
        }
        
        if config["hardware"]["use_8bit"]:
            model_kwargs["load_in_8bit"] = True
        elif config["hardware"]["use_4bit"]:
            model_kwargs["load_in_4bit"] = True
        
        if torch.cuda.is_available():
            model_kwargs["device_map"] = config["hardware"]["device_map"]
        
        model = AutoModelForCausalLM.from_pretrained(model_name, **model_kwargs)
        
    except Exception as e:
        logger.error(f"Error loading model: {e}")
        # Fallback to CPU if GPU loading fails
        logger.info("Falling back to CPU loading...")
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float32,
            device_map=None,
            trust_remote_code=True
        )
    
    # Configure LoRA
    logger.info("Configuring LoRA...")
    
    # Get model architecture to determine target modules
    model_arch = type(model).__name__
    logger.info(f"Model architecture: {model_arch}")
    
    if "GPT" in model_arch or "DialoGPT" in model_arch:
        # GPT-style models
        target_modules = ["c_attn", "c_proj", "c_fc", "c_proj"]
    elif "Llama" in model_arch or "Mistral" in model_arch:
        # Llama/Mistral models
        target_modules = ["q_proj", "v_proj", "k_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
    else:
        # Generic transformer
        target_modules = ["query", "key", "value", "dense", "attention"]
    
    logger.info(f"Target modules: {target_modules}")
    
    lora_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=config["train"]["lora_rank"],
        lora_alpha=config["train"]["lora_alpha"],
        lora_dropout=config["train"]["dropout"],
        target_modules=target_modules
    )
    
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()
    
    # Format data for training
    logger.info("Formatting training data...")
    formatted_data = [format_training_example(ex, tokenizer, config["train"]["max_seq_len"]) for ex in raw_data]
    dataset = Dataset.from_list(formatted_data)
    logger.info(f"Formatted {len(dataset)} training examples")
    
    # Create output directory
    output_dir = config["paths"]["output_dir"]
    os.makedirs(output_dir, exist_ok=True)
    
    # Training arguments
    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=config["train"]["epochs"],
        learning_rate=float(config["train"]["lr"]),
        per_device_train_batch_size=config["train"]["micro_batch_size"],
        gradient_accumulation_steps=config["train"]["gradient_accumulation"],
        max_steps=100,  # Set a specific number of steps for mini training
        warmup_steps=config["train"]["warmup_steps"],
        logging_steps=config["train"]["logging_steps"],
        save_steps=config["train"]["save_steps"],
        eval_strategy="no",  # No evaluation for mini training
        save_strategy="epoch",
        load_best_model_at_end=False,
        ddp_find_unused_parameters=False,
        remove_unused_columns=False,
        dataloader_pin_memory=False,
        report_to=None,  # Disable wandb/tensorboard for mini training
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
    logger.info("Starting training...")
    trainer.train()
    
    # Save
    logger.info("Saving model...")
    trainer.save_model()
    tokenizer.save_pretrained(output_dir)
    
    # Save training config for reference
    with open(os.path.join(output_dir, "training_config.yaml"), "w") as f:
        yaml.dump(config, f, default_flow_style=False)
    
    logger.info("Training complete!")
    logger.info(f"Model saved to: {output_dir}")

if __name__ == "__main__":
    main()
