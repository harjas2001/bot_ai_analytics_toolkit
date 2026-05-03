"""
tools/check_for_agent_schema_parse.py
─────────────────────────────────────────────────────────────────────────────
Scans all intents in an exported NLU agent and flags training phrases
written entirely in CAPITAL LETTERS.

All-caps training phrases are a widespread data quality issue across
conversational AI platforms — they cause the NLU model to overfit to
casing patterns rather than semantic content, and typically originate
from phrases copy-pasted from CRM exports, ticketing systems, or
internal documentation.

Works with any platform that stores training phrases in JSON files
under a standard per-intent directory structure.

Configuration (via .env):
  AGENT_BASE_PATH — base path of your exported agent
                    (expects <base>/df_cx_agent/intents or similar inside)
─────────────────────────────────────────────────────────────────────────────
"""

import json
import os
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv()

AGENT_BASE_PATH = os.getenv("AGENT_BASE_PATH", ".")


def extract_phrases_from_json(json_file_path: str) -> list:
    """
    Extract training phrases from a single JSON training phrases file.
    Joins all 'text' parts from each phrase's 'parts' array.
    Compatible with Dialogflow CX export schema.
    """
    phrases = []

    try:
        with open(json_file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for phrase_group in data.get("trainingPhrases", []):
            complete = "".join(
                part["text"]
                for part in phrase_group.get("parts", [])
                if "text" in part and part["text"]
            )
            if complete.strip():
                phrases.append(complete.strip())

    except (json.JSONDecodeError, FileNotFoundError, KeyError) as e:
        print(f"  Error reading {json_file_path}: {e}")

    return phrases


def is_all_caps(text: str) -> bool:
    """
    Return True if all alphabetic characters in text are uppercase.
    Ignores digits, punctuation, and whitespace.
    """
    alpha = [c for c in text if c.isalpha()]
    return len(alpha) > 0 and all(c.isupper() for c in alpha)


def scan_agent_intents(base_path: str) -> dict:
    """
    Walk the agent's intents directory and return all training phrases
    grouped by intent name.

    Expects the structure:
      <base_path>/df_cx_agent/intents/<intent>/trainingPhrases/en.json
    """
    intents_folder = os.path.join(base_path, "df_cx_agent", "intents")
    all_phrases = {}

    if not os.path.exists(intents_folder):
        print(f"Intents folder not found: {intents_folder}")
        return all_phrases

    for intent_folder in os.listdir(intents_folder):
        intent_path = os.path.join(intents_folder, intent_folder)

        if not os.path.isdir(intent_path):
            continue

        tp_folder = os.path.join(intent_path, "trainingPhrases")
        en_json   = os.path.join(tp_folder, "en.json")

        if os.path.exists(en_json):
            phrases = extract_phrases_from_json(en_json)
            if phrases:
                all_phrases[intent_folder] = phrases
                print(f"  {intent_folder}: {len(phrases)} phrases")
        elif os.path.exists(tp_folder):
            print(f"  en.json not found in: {tp_folder}")

    return all_phrases


def find_all_caps_phrases(all_phrases: dict) -> dict:
    """Return phrases grouped by intent where the phrase is entirely all-caps."""
    flagged = defaultdict(list)
    for intent, phrases in all_phrases.items():
        for phrase in phrases:
            if is_all_caps(phrase):
                flagged[intent].append(phrase)
    return flagged


def main():
    print(f"Scanning agent: {AGENT_BASE_PATH}\n")
    all_phrases = scan_agent_intents(AGENT_BASE_PATH)

    if not all_phrases:
        print("No training phrases found. Check your agent export folder structure.")
        return

    print(f"\nScanned {len(all_phrases)} intents.")
    flagged = find_all_caps_phrases(all_phrases)

    if flagged:
        print("\n" + "=" * 60)
        print("  TRAINING PHRASES — ALL CAPITALS DETECTED")
        print("=" * 60)

        for intent_name, phrases in flagged.items():
            print(f"\n  Intent: {intent_name}")
            print("  " + "-" * 38)
            for phrase in phrases:
                print(f"    • {phrase}")

        total = sum(len(p) for p in flagged.values())
        print(f"\n{'=' * 60}")
        print(f"  {total} all-caps phrase(s) across {len(flagged)} intent(s).")
        print(f"  Recommendation: lowercase and review before retraining.")
        print("=" * 60)
    else:
        print("\n✅  No all-caps training phrases found.")


if __name__ == "__main__":
    main()
