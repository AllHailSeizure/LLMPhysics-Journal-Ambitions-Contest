import time
import json
from datetime import datetime, timezone

EXPECTED_FIELDS = ["hypothesis", "novelty", "scientific_humility", "engagement", "rigor", "citations"]

def score_paper(prepared_document, model, paper_id):
    """
    Scores a paper using the specified model.
    Returns a record dict with scores + metadata, or a flagged error record on total failure.
    """
    # Load prompt
    with open("guidelines_v1_1.txt", "r", encoding="utf-8") as f:
        prompt = f.read()

    # Load citation
    citation = None
    with open("citations.txt", "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith(paper_id):
                citation = line.split("--")[1].strip()
                break

    # Derive group
    group = "baseline" if int(paper_id) <= 50 else "contest"

    # Build messages
    messages = [
        {
            "role": "user",
            "content": [
                prepared_document,
                {"type": "text", "text": prompt}
            ]
        }
    ]

    # Route to correct API
    def attempt_call():
        if "claude" in model.lower():
            return call_anthropic(messages, model)
        elif "gpt" in model.lower():
            return call_openai(messages, model)
        else:
            raise ValueError(f"Unrecognized model: {model}")

    # Retry loop
    last_error = None
    response = None
    for attempt in range(3):
        try:
            response = attempt_call()
            # Strip markdown fences if present
            text = response["text"].strip()
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
                text = text.strip()
            # Parse JSON
            scored = json.loads(text)
            # Validate fields
            for field in EXPECTED_FIELDS:
                assert field in scored
                assert "score" in scored[field]
                assert "justification" in scored[field]
            # Success
            return {
                "paper_id": paper_id,
                "citation": citation,
                "group": group,
                "model": model,
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "input_tokens": response["input_tokens"],
                "output_tokens": response["output_tokens"],
                "error": None,
                "scores": scored
            }
        except Exception as e:
            last_error = str(e)
            if attempt < 2:
                time.sleep(5)

    # Total failure
    return {
        "paper_id": paper_id,
        "citation": citation,
        "group": group,
        "model": model,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "input_tokens": response["input_tokens"] if response else None,
        "output_tokens": response["output_tokens"] if response else None,
        "error": last_error,
        "scores": None
    }