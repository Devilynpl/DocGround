"""Convert DocGround's golden_set.json to JudgeKit's standard golden_set.jsonl format."""

import json
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
JSON_PATH = CURRENT_DIR / "golden_set.json"
JSONL_PATH = CURRENT_DIR / "golden_set.jsonl"


def convert():
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    with open(JSONL_PATH, "w", encoding="utf-8") as out:
        for item in data:
            rec = {
                "id": item["id"],
                "category": item["category"],
                "query": item["question"],
                "expected_behavior": "Odpowiedz zgodnie z dokumentacją z cytowaniem" if item.get("is_answerable") else "Odmów odpowiedzi ('Nie wiem')",
                "reference_answer": ", ".join(item.get("expected_answer_keywords", [])) if item.get("is_answerable") else None,
                "reference_contexts": [f"{item.get('expected_doc')}, s. {item.get('expected_page')}"] if item.get("expected_doc") else [],
            }
            out.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print(f"Generated {len(data)} JudgeKit test cases in {JSONL_PATH}")


if __name__ == "__main__":
    convert()
