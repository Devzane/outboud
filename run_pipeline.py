# ==============================================================================
# run_pipeline.py — The Orchestrator
# ==============================================================================
# PURPOSE:
#   Single entry point that executes the full outbound data pipeline in order:
#     Stage 1: Merge and clean all raw Apify CSVs    (pipeline/cleaner.py)
#     Stage 2: Cascading Reoon email verification     (pipeline/verifier.py)
#
# HOW TO RUN:
#   Open a terminal in the OutboundScript/ directory.
#
# USAGE EXAMPLES:
#   python run_pipeline.py                                      (defaults)
#   python run_pipeline.py -i Campaign_Feb -o feb_verified.csv  (custom)
#   python run_pipeline.py -o leads.csv --append                (append mode)
#
# PREREQUISITES:
#   - Raw Apify CSV files must exist in the specified input subfolder.
#   - REOON_API_KEY must be set in ../agency-bot/.env
#   - Required packages: pandas, requests, python-dotenv
#     Install via: pip install -r requirements.txt
# ==============================================================================

import argparse
from pipeline import cleaner, verifier


def main():
    """
    Execute the two-stage outbound data pipeline.

    Stage 1 — The Transformer (cleaner.py):
        Discovers, merges, deduplicates, and sanitizes all raw CSV files
        from the specified input directory. Returns a clean in-memory DataFrame.

    Stage 2 — The Cascading Validator (verifier.py):
        Iterates through the cleaned DataFrame, verifies each lead's work
        email (then personal email as fallback) via the Reoon API, and
        saves surviving leads to the specified output file (overwrite or append).
    """

    parser = argparse.ArgumentParser(description="Vectra Automation - Outbound Data Pipeline")
    parser.add_argument(
        "-i", "--input",
        type=str,
        default="Leads",
        help="Folder containing the raw CSVs (default: Leads)"
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default="VERIFIED_LEADS.csv",
        help="Name of the final verified CSV file (default: VERIFIED_LEADS.csv)"
    )
    parser.add_argument(
        "-a", "--append",
        action="store_true",
        help="Append new leads to the existing output file instead of overwriting"
    )

    args = parser.parse_args()

    # =========================================================================
    # STAGE 1: MERGE & CLEAN
    # =========================================================================
    print("=" * 65)
    print(f"  STAGE 1: DATA MERGE & CLEANING (Input: {args.input})")
    print("=" * 65)

    df = cleaner.clean_raw_leads(input_dir=args.input)

    # =========================================================================
    # STAGE 2: CASCADING EMAIL VERIFICATION
    # =========================================================================
    print("=" * 65)
    mode_str = "APPEND" if args.append else "OVERWRITE"
    print(f"  STAGE 2: CASCADING EMAIL VERIFICATION (Output: {args.output} | Mode: {mode_str})")
    print("=" * 65)

    verifier.execute_cascading_verification(df, output_file=args.output, append_mode=args.append)

    # =========================================================================
    # PIPELINE COMPLETE
    # =========================================================================
    print(f"\n[PIPELINE] All stages complete. Check {args.output}.\n")


if __name__ == "__main__":
    main()
