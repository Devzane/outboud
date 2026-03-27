"""
=============================================================================
  Vectra Automation – Modular Apify Google Maps Scraper
=============================================================================
Orchestrator script that ties together Configuration, Scraping, Extraction, 
and Exporting into a single cohesive pipeline.
"""
import sys

# Import our custom isolated modules
from config import load_config, SEARCH_QUERIES, OUTPUT_CSV
from apify_service import build_actor_input, run_scraper
from extractor import extract_leads
from exporter import save_to_csv

def main():
    """
    Orchestrates the four-phase pipeline.
    All Apify and network operations are wrapped in a try/except for robust error handling.
    """
    # ── Phase 1: Config ─────────────────────────────────────────────────
    api_token = load_config()
    actor_input = build_actor_input(SEARCH_QUERIES)

    try:
        # ── Phase 2: Scrape ─────────────────────────────────────────────
        client, run = run_scraper(api_token, actor_input)

        # ── Phase 3: Extract ────────────────────────────────────────────
        leads = extract_leads(client, run)

        if not leads:
            print("⚠️  The scraper returned 0 results.")
            print("   Try broadening your search queries or checking the Apify console.")
            sys.exit(0)

        # ── Phase 4: Export ─────────────────────────────────────────────
        save_to_csv(leads, OUTPUT_CSV)

    except ConnectionError as exc:
        print(f"🌐  Network error: {exc}")
        sys.exit(1)
    except TimeoutError as exc:
        print(f"⏱️  Timeout error: {exc}")
        sys.exit(1)
    except Exception as exc:
        print(f"💥  Unexpected error: {exc}")
        sys.exit(1)

    print("🎯  Done! Your leads are ready for outreach.")

if __name__ == "__main__":
    main()
