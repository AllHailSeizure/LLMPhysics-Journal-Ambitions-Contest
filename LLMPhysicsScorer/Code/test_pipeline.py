import json
from pipeline_functions import prepare_document, score_paper

# Edit these to match a real paper in your papers folder
TEST_PAPER = "papers/003.pdf"
TEST_PAPER_ID = "003"
TEST_MODEL = "gpt-5.2"


def main():
    print(f"Preparing document: {TEST_PAPER}")
    prepared = prepare_document(TEST_PAPER)
    print(f"Document prepared. Type: {prepared['type']}")

    print(f"\nScoring with {TEST_MODEL}...")
    record = score_paper(prepared, TEST_PAPER, TEST_MODEL, TEST_PAPER_ID)

    print("\n--- RESULT ---")
    print(json.dumps(record, indent=2))

    if record["error"]:
        print("\nWARNING: Record returned with error flag.")
    else:
        print("\nSuccess. Scores:")
        for field, data in record["scores"].items():
            print(f"  {field}: {data['score']}")


if __name__ == "__main__":
    main()
