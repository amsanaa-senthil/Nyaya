import argparse
import os
from pathlib import Path


def ensure_dependencies() -> None:
    missing = []
    try:
        import datasets  # noqa: F401
    except ImportError:
        missing.append("datasets")
    try:
        import peft  # noqa: F401
    except ImportError:
        missing.append("peft")
    try:
        import trl  # noqa: F401
    except ImportError:
        missing.append("trl")
    try:
        import transformers  # noqa: F401
    except ImportError:
        missing.append("transformers")

    if missing:
        joined = ", ".join(missing)
        raise RuntimeError(
            f"Missing dependencies: {joined}. "
            "Install with: pip install -r finetune/requirements_finetune.txt"
        )


def format_chat_messages(example: dict, tokenizer):
    messages = example["messages"]
    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
    return {"text": text}


def main() -> None:
    parser = argparse.ArgumentParser(description="LoRA fine-tuning for Nyaya local legal assistant")
    parser.add_argument("--train-file", type=Path, default=Path("finetune/data/train_sft.jsonl"))
    parser.add_argument("--base-model", type=str, default="Qwen/Qwen2.5-3B-Instruct")
    parser.add_argument("--output-dir", type=Path, default=Path("finetune/output/qwen2.5-3b-nyaya-lora"))
    parser.add_argument("--epochs", type=int, default=2)
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--learning-rate", type=float, default=2e-4)
    parser.add_argument("--max-length", type=int, default=1024)
    args = parser.parse_args()

    ensure_dependencies()

    import torch
    from datasets import load_dataset
    from peft import LoraConfig
    from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments
    from trl import SFTTrainer

    if not args.train_file.exists():
        raise FileNotFoundError(
            f"Training file not found: {args.train_file}. Run finetune/prepare_sft_dataset.py first."
        )

    tokenizer = AutoTokenizer.from_pretrained(args.base_model, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        args.base_model,
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
        device_map="auto",
        trust_remote_code=True,
    )

    dataset = load_dataset("json", data_files=str(args.train_file), split="train")
    dataset = dataset.map(lambda row: format_chat_messages(row, tokenizer), remove_columns=dataset.column_names)

    peft_config = LoraConfig(
        r=16,
        lora_alpha=32,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    )

    training_args = TrainingArguments(
        output_dir=str(args.output_dir),
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=8,
        learning_rate=args.learning_rate,
        logging_steps=10,
        save_strategy="epoch",
        bf16=torch.cuda.is_available() and torch.cuda.get_device_capability(0)[0] >= 8,
        fp16=torch.cuda.is_available(),
        report_to="none",
        remove_unused_columns=False,
        lr_scheduler_type="cosine",
        warmup_ratio=0.05,
    )

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        peft_config=peft_config,
        args=training_args,
        max_seq_length=args.max_length,
        dataset_text_field="text",
    )

    trainer.train()
    trainer.model.save_pretrained(str(args.output_dir))
    tokenizer.save_pretrained(str(args.output_dir))

    print(f"[OK] LoRA adapter saved to: {args.output_dir}")


if __name__ == "__main__":
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    main()
