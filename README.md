# OutboundScript — Automated Outbound Lead Generation Pipeline

A modular, three-stage Python automation pipeline that sources high-ticket SMB leads from Google Maps, enriches them with owner names and emails scraped directly from company websites, and warms up a new email domain to ensure inbox deliverability before outreach begins. Designed for HVAC, Commercial Real Estate, and other high-ticket trade verticals.

---

## Tech Stack

| Layer              | Technology        | Role                                                          |
| ------------------ | ----------------- | ------------------------------------------------------------- |
| **Lead Sourcing**  | Apify Client      | Google Maps Scraper actor for bulk SMB lead extraction         |
| **Web Scraping**   | Requests + BeautifulSoup4 | Concurrent HTML fetching and parsing of company websites |
| **Email Delivery** | Resend            | Transactional email API for domain warm-up sends              |
| **Data Processing**| Pandas            | CSV I/O, DataFrame manipulation, and enrichment merging       |
| **Config**         | python-dotenv     | Secure API key management via `.env` files                    |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                   STAGE 1: LEAD SOURCING                    │
│                   Apify_Lead_Scraper/                        │
│                                                             │
│  Config → Apify Google Maps Actor → Extract → Export CSV    │
└──────────────────────┬──────────────────────────────────────┘
                       │  smb_leads.csv
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                  STAGE 2: LEAD ENRICHMENT                   │
│                  Lead_Enrichment_Pipeline/                   │
│                                                             │
│  Load CSV → Scrape Websites (8 threads) → Parse Emails,     │
│  Owner Names, Company Summaries → Export Enriched CSV        │
└──────────────────────┬──────────────────────────────────────┘
                       │  master_enriched_leads.csv
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                  STAGE 3: DOMAIN WARM-UP                    │
│                  Email_Warmup_Engine/                        │
│                                                             │
│  Load Seed CSVs → Graduated Send Schedule → Randomised      │
│  Content & Pacing → State Persistence → Resend API          │
└─────────────────────────────────────────────────────────────┘
```

---

## Module Breakdown

### 1. Apify Lead Scraper (`Apify_Lead_Scraper/`)

A four-phase pipeline that sources raw SMB lead data from Google Maps via the Apify platform.

| Phase       | File              | Description                                                    |
| ----------- | ----------------- | -------------------------------------------------------------- |
| **Config**  | `config.py`       | Loads the `APIFY_API_TOKEN` from `.env`, defines search queries and output path |
| **Scrape**  | `apify_service.py`| Builds the actor payload and invokes the Compass Google Maps Scraper synchronously |
| **Extract** | `extractor.py`    | Iterates the actor's dataset, safely extracting Company Name, Website, Phone, and City |
| **Export**  | `exporter.py`     | Writes the extracted lead dicts to a CSV file with auto-directory creation |

**Orchestrator**: `script.py` ties all four phases together with comprehensive `try/except` error handling for network, timeout, and unexpected failures.

**Output**: `Leads/hvac_smb_leads.csv`

---

### 2. Lead Enrichment Pipeline (`Lead_Enrichment_Pipeline/`)

A concurrent web scraper that takes the raw lead CSV, visits each company's website, and extracts three critical data points for cold outreach personalization.

| Component      | File             | Description                                                    |
| -------------- | ---------------- | -------------------------------------------------------------- |
| **Orchestrator** | `main.py`      | Loads the CSV, spawns an 8-thread `ThreadPoolExecutor`, and merges results back into the DataFrame |
| **Scraper**    | `scraper.py`     | Fetches HTML via `requests`, discovers About/Contact subpages via keyword-matched `<a>` tags, and extracts clean text with BeautifulSoup |
| **Parser**     | `parser.py`      | Uses regex to extract emails (filtering out image extensions), owner/founder names (via role-keyword heuristics), and company summaries (via mission-keyword matching) |
| **File Handler** | `file_handler.py` | Pandas-based CSV loader and saver with error handling         |

**Key Engineering Decisions**:
- **Concurrency**: `ThreadPoolExecutor(max_workers=8)` processes multiple websites in parallel, dramatically reducing total runtime.
- **Subpage Crawling**: Automatically discovers and scrapes up to 3 internal subpages (`/about`, `/team`, `/contact`) per lead to maximize data yield.
- **Graceful Degradation**: Missing websites or failed requests return `None` rather than crashing the pipeline.

**Output**: `master_enriched_leads.csv` — original lead data enriched with `Owner_Name`, `Email`, and `Company_Summary` columns.

---

### 3. Email Warmup Engine (`Email_Warmup_Engine/`)

A production-grade domain warm-up system powered by the Resend API. Builds sender reputation gradually over a configurable multi-day schedule to ensure cold emails land in the inbox rather than spam.

| Component        | File                 | Description                                                |
| ---------------- | -------------------- | ---------------------------------------------------------- |
| **Engine**       | `warmup_engine.py`   | Core `EmailWarmupEngine` class: state management, content generation, send dispatch, and pacing |
| **Config**       | `warmup_config.py`   | Graduated schedule (Day 1: 5, Day 2: 10, ... Day 7: 50), pacing delays (3-7 min), file paths, and sender identity |
| **Templates**    | `content_templates.py` | 10 realistic (subject, body) tuples that simulate natural human-to-human email traffic |

**Core Engineering Features**:

- **Crash-Safe State Persistence**: Progress is saved to `warmup_state.json` after *every single send*, so the engine can resume exactly where it left off after any interruption.
- **Graduated Volume Ramp**: Day-by-day send schedule (5 → 10 → 20 → 30 → 50) that mirrors best-practice domain warm-up protocols. Falls back to a configurable `DEFAULT_MAX_VOLUME` (100) for days beyond the explicit schedule.
- **Randomised Pacing**: Each send is followed by a random delay (3-7 minutes) to mimic natural human sending cadence and avoid ESP rate-limit flags.
- **Idempotent Day Tracking**: Automatically detects new calendar days and advances the warm-up counter — safe to run multiple times per day without double-sending.
- **Dual Logging**: File + console logging with structured timestamps for full audit trails.

**Warmup Schedule**:

| Day | Emails |
| --- | ------ |
| 1   | 5      |
| 2   | 10     |
| 3   | 10     |
| 4   | 20     |
| 5   | 20     |
| 6   | 30     |
| 7   | 50     |
| 8+  | 100    |

---

## Project Structure

```
OutboundScript/
├── Apify_Lead_Scraper/
│   ├── config.py            # Env loader + search query definitions
│   ├── apify_service.py     # Apify actor payload builder + runner
│   ├── extractor.py         # Lead data field extraction
│   ├── exporter.py          # CSV writer with safe directory creation
│   ├── script.py            # Main orchestrator
│   └── Leads/               # Output directory for scraped CSVs
├── Lead_Enrichment_Pipeline/
│   ├── main.py              # Concurrent enrichment orchestrator
│   ├── scraper.py           # HTML fetcher + subpage discovery
│   ├── parser.py            # Regex-based email/name/summary extractor
│   └── file_handler.py      # Pandas CSV I/O
├── Email_Warmup_Engine/
│   ├── warmup_engine.py     # Core warm-up engine class
│   ├── warmup_config.py     # Schedule, pacing, and sender config
│   └── content_templates.py # Realistic email content pool
├── requirements.txt         # Python dependencies
├── .env                     # API keys (gitignored)
└── .gitignore               # Secrets, CSVs, cache, venv
```

---

## Local Setup

### Prerequisites
- Python 3.10+
- An Apify API token (free tier available)
- A Resend API key with a verified sending domain

### 1. Create and Activate the Virtual Environment

```bash
cd OutboundScript
python -m venv venv

# Windows (PowerShell)
.\venv\Scripts\Activate.ps1

# Windows (Git Bash)
source venv/Scripts/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the `OutboundScript/` root:

```env
APIFY_API_TOKEN=your_apify_token_here
RESEND_API_KEY=your_resend_api_key_here
```

---

## Running the Pipeline

Execute each stage sequentially:

```bash
# Stage 1: Source leads from Google Maps
python Apify_Lead_Scraper/script.py

# Stage 2: Enrich leads with emails, names, and summaries
cd Lead_Enrichment_Pipeline
python main.py
cd ..

# Stage 3: Warm up your email domain (run daily)
python Email_Warmup_Engine/warmup_engine.py
```

> **Note**: The Email Warmup Engine is designed to be run **once per day**. It automatically tracks progress and will skip if the daily target has already been met.

---

## License

Proprietary — Vectra Automation. All rights reserved.
