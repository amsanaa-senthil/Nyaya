import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Run inference with base model + LoRA adapter")
    parser.add_argument("--base-model", type=str, default="Qwen/Qwen2.5-3B-Instruct")
    parser.add_argument("--adapter-dir", type=Path, default=Path("finetune/output/qwen2.5-3b-nyaya-lora"))
    parser.add_argument("--question", type=str, required=True)
    parser.add_argument("--max-new-tokens", type=int, default=256)
    args = parser.parse_args()

    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(args.base_model, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    base_model = AutoModelForCausalLM.from_pretrained(
        args.base_model,
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
        device_map="auto",
        trust_remote_code=True,
    )
    model = PeftModel.from_pretrained(base_model, str(args.adapter_dir))

    messages = [
        {
            "role": "system",
            "content": "You are Nyaya, a legal assistant specialized in Sri Lankan law.",
        },
        {"role": "user", "content": args.question},
    ]

    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

    outputs = model.generate(
        **inputs,
        max_new_tokens=args.max_new_tokens,
        do_sample=False,
        temperature=0.2,
    )

    text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    print("\n=== MODEL OUTPUT ===\n")
    print(text)


if __name__ == "__main__":
    main()
