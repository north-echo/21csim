#!/usr/bin/env python3
"""QLoRA fine-tuning script for the 21csim narrator model.

Fine-tunes Meta-Llama-3.1-8B-Instruct with QLoRA on narration examples
extracted by extract_training_data.py.

Requirements:
    pip install torch transformers peft trl bitsandbytes datasets accelerate

Hardware:
    - GPU with >= 24 GB VRAM (A100 40 GB recommended)
    - Estimated training time: ~4 hours on A100 for 3 epochs / ~250 examples
    - Also runnable on RTX 4090 (24 GB) with reduced batch size

After training, convert the adapter to GGUF for Ollama:
    1. Merge adapter into base model:
         python -c "
         from peft import PeftModel
         from transformers import AutoModelForCausalLM, AutoTokenizer
         base = AutoModelForCausalLM.from_pretrained('meta-llama/Meta-Llama-3.1-8B-Instruct')
         model = PeftModel.from_pretrained(base, './output/narration-lora')
         merged = model.merge_and_unload()
         merged.save_pretrained('./output/narration-merged')
         AutoTokenizer.from_pretrained('meta-llama/Meta-Llama-3.1-8B-Instruct').save_pretrained('./output/narration-merged')
         "
    2. Convert to GGUF (requires llama.cpp):
         python llama.cpp/convert_hf_to_gguf.py ./output/narration-merged \
             --outfile ./output/narration-lora.gguf --outtype q4_K_M
    3. Copy GGUF and Modelfile, then create Ollama model:
         cp ./output/narration-lora.gguf scripts/
         ollama create 21csim-narrator -f scripts/Modelfile
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Attempt imports -- give a clear message if dependencies are missing
# ---------------------------------------------------------------------------
try:
    import torch
    from datasets import Dataset
    from peft import LoraConfig, TaskType, get_peft_model, prepare_model_for_kbit_training
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        BitsAndBytesConfig,
        TrainingArguments,
    )
    from trl import SFTTrainer
except ImportError as exc:
    print(
        f"Missing dependency: {exc}\n\n"
        "Install with:\n"
        "  pip install torch transformers peft trl bitsandbytes datasets accelerate\n",
        file=sys.stderr,
    )
    sys.exit(1)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
TRAINING_DATA = PROJECT_ROOT / "data" / "training" / "narrations.jsonl"
OUTPUT_DIR = PROJECT_ROOT / "output" / "narration-lora"

BASE_MODEL = "meta-llama/Meta-Llama-3.1-8B-Instruct"

LORA_R = 16
LORA_ALPHA = 32
LORA_DROPOUT = 0.05
LORA_TARGET_MODULES = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]

LEARNING_RATE = 2e-4
BATCH_SIZE = 4
GRADIENT_ACCUMULATION_STEPS = 4
NUM_EPOCHS = 3
MAX_SEQ_LENGTH = 512
WARMUP_RATIO = 0.05
WEIGHT_DECAY = 0.01


def load_training_data() -> Dataset:
    """Load JSONL chat-format training data into a HuggingFace Dataset."""
    records = []
    with open(TRAINING_DATA) as f:
        for line in f:
            records.append(json.loads(line))

    # Convert messages list into the text format expected by SFTTrainer
    texts = []
    for record in records:
        msgs = record["messages"]
        # Build Llama 3.1 chat template manually for clarity
        text = (
            f"<|begin_of_text|>"
            f"<|start_header_id|>system<|end_header_id|>\n\n"
            f"{msgs[0]['content']}<|eot_id|>"
            f"<|start_header_id|>user<|end_header_id|>\n\n"
            f"{msgs[1]['content']}<|eot_id|>"
            f"<|start_header_id|>assistant<|end_header_id|>\n\n"
            f"{msgs[2]['content']}<|eot_id|>"
        )
        texts.append(text)

    return Dataset.from_dict({"text": texts})


def main() -> None:
    if not TRAINING_DATA.exists():
        print(
            f"Training data not found at {TRAINING_DATA}\n"
            "Run extract_training_data.py first.",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"Loading training data from {TRAINING_DATA}")
    dataset = load_training_data()
    print(f"  {len(dataset)} training examples loaded")

    # -----------------------------------------------------------------------
    # Quantization config (4-bit QLoRA)
    # -----------------------------------------------------------------------
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )

    # -----------------------------------------------------------------------
    # Load base model and tokenizer
    # -----------------------------------------------------------------------
    print(f"Loading base model: {BASE_MODEL}")
    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        quantization_config=bnb_config,
        device_map="auto",
        torch_dtype=torch.bfloat16,
        trust_remote_code=True,
    )
    model = prepare_model_for_kbit_training(model)

    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
        model.config.pad_token_id = tokenizer.eos_token_id

    # -----------------------------------------------------------------------
    # LoRA config
    # -----------------------------------------------------------------------
    lora_config = LoraConfig(
        r=LORA_R,
        lora_alpha=LORA_ALPHA,
        lora_dropout=LORA_DROPOUT,
        target_modules=LORA_TARGET_MODULES,
        bias="none",
        task_type=TaskType.CAUSAL_LM,
    )

    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    # -----------------------------------------------------------------------
    # Training arguments
    # -----------------------------------------------------------------------
    training_args = TrainingArguments(
        output_dir=str(OUTPUT_DIR),
        num_train_epochs=NUM_EPOCHS,
        per_device_train_batch_size=BATCH_SIZE,
        gradient_accumulation_steps=GRADIENT_ACCUMULATION_STEPS,
        learning_rate=LEARNING_RATE,
        warmup_ratio=WARMUP_RATIO,
        weight_decay=WEIGHT_DECAY,
        logging_steps=10,
        save_strategy="epoch",
        bf16=True,
        gradient_checkpointing=True,
        optim="paged_adamw_8bit",
        lr_scheduler_type="cosine",
        report_to="none",
        max_grad_norm=0.3,
    )

    # -----------------------------------------------------------------------
    # Trainer
    # -----------------------------------------------------------------------
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        args=training_args,
        max_seq_length=MAX_SEQ_LENGTH,
    )

    print("Starting training...")
    trainer.train()

    # -----------------------------------------------------------------------
    # Save adapter
    # -----------------------------------------------------------------------
    print(f"Saving LoRA adapter to {OUTPUT_DIR}")
    trainer.save_model(str(OUTPUT_DIR))
    tokenizer.save_pretrained(str(OUTPUT_DIR))

    print("\nTraining complete.")
    print(f"Adapter saved to: {OUTPUT_DIR}")
    print("\nNext steps:")
    print("  1. Merge adapter:  see docstring at top of this file")
    print("  2. Convert to GGUF: see docstring at top of this file")
    print("  3. Create Ollama model: ollama create 21csim-narrator -f scripts/Modelfile")


if __name__ == "__main__":
    main()
