import argparse
import json
from pathlib import Path

SYSTEM_PROMPT = (
    "You are Nyaya, a Sri Lankan legal assistant. "
    "Provide concise, accurate legal answers grounded in the provided legal corpus context. "
    "If context is insufficient, say so clearly."
)


def build_example(item: dict) -> dict:
    question = item.get("question", "").strip()
    answer = item.get("ground_truth_answer", "").strip()
    citations = item.get("ground_truth_citations", [])

    citation_text = ""
    if citations:
        citation_text = "\nCitations: " + ", ".join(str(c) for c in citations)

    user_text = f"Question: {question}\n\nAnswer in Sri Lankan legal context."
    assistant_text = f"{answer}{citation_text}".strip()

    return {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_text},
            {"role": "assistant", "content": assistant_text},
        ]
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare SFT dataset from evaluation_dataset.json")
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("evaluation_dataset.json"),
        help="Path to source evaluation dataset JSON",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("finetune/data/train_sft.jsonl"),
        help="Output JSONL path",
    )
    args = parser.parse_args()

    with args.input.open("r", encoding="utf-8") as file:
        raw = json.load(file)

    entries = raw.get("evaluation_dataset", [])
    examples = [build_example(item) for item in entries if item.get("question") and item.get("ground_truth_answer")]

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as file:
        for record in examples:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"[OK] Wrote {len(examples)} SFT examples to {args.output}")


if __name__ == "__main__":
    main()
