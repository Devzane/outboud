# ==============================================================================
# run_pipeline.py — The Orchestrator
# ==============================================================================
# PURPOSE:
#   Single entry point that executes the full outbound data pipeline in order:
#     Stage 1: Merge and clean all raw Apify CSVs    (pipeline/cleaner.py)
#     Stage 2: Cascading Reoon email verification     (pipeline/verifier.py)
#
# HOW TO RUN:
#   Open a terminal in the OutboundScript/ directory and execute:
#     python run_pipeline.py
#
# PREREQUISITES:
#   - Raw Apify CSV files must exist in the Leads/ subfolder.
#   - REOON_API_KEY must be set in ../agency-bot/.env
#   - Required packages: pandas, requests, python-dotenv
#     Install via: pip install -r requirements.txt
# ==============================================================================

from pipeline import cleaner, verifier


def main():
    """
    Execute the two-stage outbound data pipeline.

    Stage 1 — The Transformer (cleaner.py):
        Discovers, merges, deduplicates, and sanitizes all raw CSV files
        from the Leads/ directory. Returns a clean in-memory DataFrame.

    Stage 2 — The Cascading Validator (verifier.py):
        Iterates through the cleaned DataFrame, verifies each lead's work
        email (then personal email as fallback) via the Reoon API, and
        saves surviving leads to FINAL_CASCADING_LEADS.csv.
    """

    # =========================================================================
    # STAGE 1: MERGE & CLEAN
    # =========================================================================
    print("=" * 65)
    print("  STAGE 1: DATA MERGE & CLEANING")
    print("=" * 65)

    df = cleaner.clean_raw_leads()

    # =========================================================================
    # STAGE 2: CASCADING EMAIL VERIFICATION
    # =========================================================================
    print("=" * 65)
    print("  STAGE 2: CASCADING EMAIL VERIFICATION")
    print("=" * 65)

    verifier.execute_cascading_verification(df)

    # =========================================================================
    # PIPELINE COMPLETE
    # =========================================================================
    print("\n[PIPELINE] All stages complete. Check FINAL_CASCADING_LEADS.csv.\n")


if __name__ == "__main__":
    main()
