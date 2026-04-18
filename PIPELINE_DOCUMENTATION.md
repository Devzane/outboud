# Vectra Automation — Outbound Data Pipeline

This document explains the architecture and operational flow of the modular data pipeline built for Vectra Automation. 

The pipeline is designed to sanitize raw lead data scraped via Apify, merge it, and rigorously verify the target emails using a "cascading" architecture with the Reoon API. This ensures maximum email deliverability and protects the agency's sender reputation.

---

## 📂 Architecture Overview

The codebase has been refactored from isolated, monolithic scripts into a clean, modular Python package located in the `OutboundScript` directory.

```text
OutboundScript/
├── pipeline/
│   ├── __init__.py          # Marks the folder as a Python package
│   ├── cleaner.py           # Module 1: Merge, Deduplicate, Sanitize
│   └── verifier.py          # Module 2: Cascading Email Verification
├── run_pipeline.py          # The command-line orchestrator
└── Leads/                   # Default folder for raw Apify CSV files
```

---

## 🧩 Moduler Components

### 1. The Transformer (`pipeline/cleaner.py`)
This module handles the extraction and formatting of raw data before hitting the API.
- **Dynamic Globbing**: Scans a provided input directory (defaults to `Leads/`) for all `.csv` files.
- **Concatenation**: Merges multiple raw dataset files together seamlessly.
- **Deduplication**: Eliminates duplicate rows. This is critical because overlapping scraped queries often collect the same prospect multiple times. Messaging them twice destroys sender reputation.
- **Strict Typing (`fillna`)**: Intelligently fills missing (`NaN`) values in string columns with `"N/A"`, preventing downstream TypeErrors on newer versions of Pandas without corrupting numeric columns.

### 2. The Cascading Validator (`pipeline/verifier.py`)
This is the core business logic engine, interfacing with the Reoon Email Verifier API.

Instead of just checking one inbox entirely, the script executes a **Cascading Verification**:
1. Checks the **Work Email** (`email` column). If the API returns `safe`, `role`, or `catch-all`, it keeps the lead and moves to the next row.
2. If the work email fails or is missing, it **cascades to the Personal Email** (`personal_email` column) and repeats the checks.
3. If both emails fail, the lead is dropped to ensure domain health.

Surviving leads are tagged with three new columns:
- `verified_target_email`
- `verification_status`
- `email_source_type` (indicating if the `work_email` or `personal_email` won the cascade).

#### The Resume/Skip Fix
To avoid spending unnecessary API credits, the verifier automatically bypasses rows that already possess a valid `verification_status`. This allows interrupted data (`RECOVERED_LEADS.csv`) to be passed directly back into the pipeline — safely picking up exactly where it left off.

#### Auto-save Protocol
To combat network timeouts and terminal freezing, the verifier actively writes successful verifications to the disk (to the defined output CSV) *after every single valid lead*. No progress is lost on a crash.

---

## 🚀 How to Run the Orchestrator

The pipeline is powered by `run_pipeline.py`, which is controlled via a command-line interface (`argparse`). This decouples the logic from hardcoded folder names, allowing continuous use for different campaigns.

**Prerequisites:**
You need a `.env` file in the `../agency-bot/` folder containing your `REOON_API_KEY`.

**Basic Execution:**
Runs the default flow (looks in `Leads/`, outputs to `VERIFIED_LEADS.csv`, overwrites existing data).
```powershell
python run_pipeline.py
```

**Custom Campaign Execution:**
Specify a custom input folder and output filename.
```powershell
python run_pipeline.py -i Campaign_May2026 -o MAY_OUTPUT.csv
```

**Append to Existing File (Resume Protocol):**
Use the `--append` flag when feeding fresh leads into an existing verified master list. The script intelligently shifts its auto-save logic to an `a` append mode to prevent duplicating past lines in the CSV.
```powershell
python run_pipeline.py -i Leads -o RECOVERED_LEADS.csv --append
```

---

## 🛠 Command-Line Arguments Reference

| Argument | Short | Type | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `--input` | `-i` | String | `Leads` | The child folder holding raw Apify CSV datasets. |
| `--output` | `-o` | String | `VERIFIED_LEADS.csv` | The target file for verified leads. |
| `--append` | `-a` | Flag | `False` | Triggers file append mode instead of overwrite. |

---
*Created by Abdulmuiz - Lead Automation Engineer.*
