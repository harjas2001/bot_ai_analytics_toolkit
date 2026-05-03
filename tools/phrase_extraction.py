"""
tools/phrase_extraction.py
─────────────────────────────────────────────────────────────────────────────
Extracts training phrases from a filtered set of NLU intents and writes
them to a CSV (columns: utterance, intent).

Designed for the Dialogflow CX agent export folder structure out of the box,
but adaptable to any platform that stores training phrases as JSON files
under per-intent directories.

The output CSV feeds directly into tools/analyse_training_phrases.py.

Configuration (via .env):
  AGENT_INTENTS_PATH  — path to the intents folder in your agent export
  OUTPUT_CSV          — output CSV filename

Intent filter:
  Only intents listed in config/include_intents.txt are extracted.
  Copy config/include_intents.example.txt to get started.

GCP integration (optional):
  After extraction, optionally upload the output CSV to Cloud Storage:

    from gcp.storage_utils import upload_output
    upload_output(OUTPUT_CSV)
─────────────────────────────────────────────────────────────────────────────
"""

import os
import json
import csv
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Config ────────────────────────────────────────────────────────────────────
AGENT_INTENTS_PATH = os.getenv("AGENT_INTENTS_PATH", "agent_export/intents")
OUTPUT_CSV         = os.getenv("OUTPUT_CSV", "output/training_phrases.csv")

# ── Intent whitelist ──────────────────────────────────────────────────────────
_INTENTS_FILE = Path("config/include_intents.txt")

if not _INTENTS_FILE.exists():
    raise FileNotFoundError(
        f"\n[phrase_extraction] Intent filter file not found: {_INTENTS_FILE}\n"
        f"  Copy config/include_intents.example.txt → config/include_intents.txt\n"
        f"  and add the intent names you want to extract, one per line."
    )

INCLUDE_INTENTS = {
    line.strip()
    for line in _INTENTS_FILE.read_text(encoding="utf-8").splitlines()
    if line.strip() and not line.strip().startswith("#")
}

# ── Extraction ────────────────────────────────────────────────────────────────
def extract_phrases(intents_path: str, include_intents: set) -> dict:
    """
    Walk the intents directory and extract training phrases for whitelisted intents.

    Expected structure (Dialogflow CX):
      <intents_path>/
        <intent-name>/
          trainingPhrases/
            en.json   ← or any .json language file

    Returns:
      {intent_name: [phrase, phrase, ...]}
    """
    data = {}

    for intent_folder in os.listdir(intents_path):
        intent_dir = os.path.join(intents_path, intent_folder)

        if not os.path.isdir(intent_dir):
            continue
        if intent_folder not in include_intents:
            continue

        training_phrases_dir = os.path.join(intent_dir, "trainingPhrases")

        if not os.path.isdir(training_phrases_dir):
            continue

        for filename in os.listdir(training_phrases_dir):
            if not filename.endswith(".json"):
                continue

            file_path = os.path.join(training_phrases_dir, filename)

            with open(file_path, "r", encoding="utf-8") as f:
                json_data = json.load(f)

            # Schema: { "trainingPhrases": [ { "parts": [ { "text": "..." } ] } ] }
            for phrase_obj in json_data.get("trainingPhrases", []):
                phrase = "".join(
                    part.get("text", "")
                    for part in phrase_obj.get("parts", [])
                )
                if phrase:
                    data.setdefault(intent_folder, []).append(phrase)

    return data


def write_csv(data: dict, output_path: str) -> None:
    """Write extracted phrases to CSV with columns: utterance, intent."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["utterance", "intent"])
        for intent, phrases in data.items():
            for phrase in phrases:
                writer.writerow([phrase, intent])

    print(f"Training phrases extracted → {output_path}")


def report_low_coverage(data: dict, min_phrases: int = 4) -> None:
    """Flag intents with fewer than min_phrases training phrases."""
    low = {intent: len(phrases) for intent, phrases in data.items() if len(phrases) < min_phrases}
    for intent, count in low.items():
        print(f"  ⚠  '{intent}' has fewer than {min_phrases} phrases: {count}")
    print(f"Total intents with < {min_phrases} phrases: {len(low)}")


if __name__ == "__main__":
    data = extract_phrases(AGENT_INTENTS_PATH, INCLUDE_INTENTS)
    write_csv(data, OUTPUT_CSV)
    report_low_coverage(data)

    # ── Optional: push to GCS ─────────────────────────────────────────────────
    # from gcp.storage_utils import upload_output
    # upload_output(OUTPUT_CSV)
