# Conversational AI — NLU Toolkit

A platform-agnostic toolkit for auditing, analysing, and improving NLU (Natural Language Understanding) training data in conversational AI agents. Built from production work on enterprise-scale voicebot deployments.

Works out of the box with **Dialogflow CX** agent exports. Adaptable to any platform that stores training phrases as JSON under per-intent directories (CCAI, Lex, Rasa, and others).

---

## Background

Built to address a recurring gap in NLU quality assurance across production conversational AI agents handling enterprise call volumes. As agent intent libraries grow, training data accumulates systematic issues — overlapping vocabularies, underpopulated intents, all-caps copy-paste phrases, and flow pages that become unreachable — all of which degrade NLU confidence without any obvious signal in aggregate metrics.

These tools were built to surface those issues programmatically, producing prioritised, actionable output rather than raw data dumps. The analysis pipeline was run across agents spanning multiple brands and deployment environments, with results fed into GCP (Cloud Storage + BigQuery) for downstream BI reporting and trend tracking.

---

## Toolkit Overview

```
tools/
├── phrase_extraction.py          — extract training phrases → CSV
├── analyse_training_phrases.py   — deep NLU overlap + quality analysis → Excel
├── check_for_upper_lower_case.py — flag all-caps training phrases
└── lastPage_list.py              — audit all pages across all flows

gcp/
├── storage_utils.py              — upload / download files via Cloud Storage
└── bigquery_utils.py             — push results to BigQuery for BI / trending
```

---

## Tools

### `phrase_extraction.py`
Extracts training phrases from a whitelisted set of intents and writes them to a CSV. The output feeds `analyse_training_phrases.py`.

```bash
python tools/phrase_extraction.py
```

Intent whitelist is loaded from `config/include_intents.txt` (gitignored). Only listed intents are extracted — useful for scoping analysis to a specific domain or product area.

---

### `analyse_training_phrases.py`
Deep NLU analysis of training phrase quality and intent overlap. Takes the extraction CSV and produces a fully formatted 6-sheet Excel report.

```bash
python tools/analyse_training_phrases.py
```

| Sheet | Content |
|---|---|
| Summary | Per-intent phrase count, word length stats, quality flags |
| Token Overlap Matrix | Pairwise Jaccard similarity heatmap across all intents |
| High Overlap Pairs | Ranked intent pairs above the overlap threshold |
| Shared Tokens Detail | Tokens shared across multiple intents |
| Intent Word Stats | Word-count distribution per intent |
| Action Items | Prioritised remediation tasks: CRITICAL / HIGH / MEDIUM / LOW |

---

### `check_for_upper_lower_case.py`
Scans all intents in an agent export and flags training phrases written entirely in CAPITAL LETTERS. All-caps phrases cause NLU models to overfit to casing patterns — they typically originate from CRM exports or internal documentation.

```bash
python tools/check_for_upper_lower_case.py
```

---

### `lastPage_list.py`
Maps all pages across all flows in an exported agent. Useful for auditing flow structure and identifying orphaned or unreachable pages before a deployment.

```bash
python tools/lastPage_list.py
```

---

## GCP Integration

The `gcp/` module connects the toolkit to Google Cloud for data ingestion, output storage, and BigQuery-backed BI reporting.

### Cloud Storage (`gcp/storage_utils.py`)

```python
from gcp.storage_utils import download_input, upload_output

# Pull this month's fallback export from a shared GCS bucket
download_input("fallback_nov.csv", local_path="data/fallback.csv")

# Push the generated Excel report back to GCS
upload_output("output/training_phrase_analysis.xlsx")
```

### BigQuery (`gcp/bigquery_utils.py`)

```python
from gcp.bigquery_utils import push_phrase_analysis, query_to_dataframe

# Push analysis results to BigQuery for PowerBI / Looker trending
push_phrase_analysis(results_df)

# Query historical results
df = query_to_dataframe("""
    SELECT intent, AVG(jaccard_score) as avg_overlap, COUNT(*) as runs
    FROM `project.conversational_ai.training_phrase_analysis`
    GROUP BY intent
    ORDER BY avg_overlap DESC
""")
```

---

## Setup

```bash
git clone https://github.com/your-username/conversational-ai-nlu-toolkit.git
cd conversational-ai-nlu-toolkit

python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# Edit .env — set agent paths, GCP project, bucket, BQ dataset

cp config/include_intents.example.txt config/include_intents.txt
# Add your intent names, one per line
```

For GCP: place your service account key at the path set in `GOOGLE_APPLICATION_CREDENTIALS` (gitignored). Or use [Application Default Credentials](https://cloud.google.com/docs/authentication/application-default-credentials) if running on GCP infrastructure.

---

## Expected Agent Export Structure

```
agent_export/
├── flows/
│   └── <flow-name>/
│       └── pages/
│           └── <page-name>.json
└── intents/
    └── <intent-name>/
        └── trainingPhrases/
            └── en.json
```

See `sample_data/training_phrases_schema.json` for the expected JSON schema of a training phrases file.

---

## Platform Compatibility

| Platform | phrase_extraction | analyse | casing check | page audit |
|---|---|---|---|---|
| Dialogflow CX | ✅ native | ✅ | ✅ | ✅ native |
| Dialogflow ES | ⚙ adapt JSON schema | ✅ | ✅ | — |
| Amazon Lex | ⚙ adapt JSON schema | ✅ | ✅ | — |
| Rasa | ⚙ adapt YAML → CSV | ✅ | ✅ | — |

The analysis and quality tools work on any `(utterance, intent)` CSV regardless of platform.

---

## Stack

Python · pandas · openpyxl · python-dotenv · google-cloud-storage · google-cloud-bigquery
