# ==============================================================================
# Module 1: cleaner.py — The Transformer
# ==============================================================================
# PURPOSE:
#   Discovers all raw Apify CSV files in the Leads/ subdirectory, merges them
#   into a single Pandas DataFrame, deduplicates rows, and fills missing values.
#   Returns the cleaned DataFrame in-memory (no CSV export at this stage).
#
# USAGE:
#   from pipeline import cleaner
#   df = cleaner.clean_raw_leads("Leads")
# ==============================================================================

import pandas as pd
import glob
import os


def clean_raw_leads(input_dir="Leads"):
    """
    Merge, deduplicate, and sanitize all raw CSV files from the input folder.

    Steps:
        1. Resolve the absolute path to the input_dir subdirectory (relative to
           this script's location, not the caller's working directory).
        2. Use glob to discover every .csv file inside Leads/.
        3. Concatenate all discovered files into one master DataFrame.
        4. Drop exact duplicate rows to prevent messaging the same prospect twice.
        5. Fill any NaN / blank values with the string "N/A" for downstream safety.

    Returns:
        pd.DataFrame: The cleaned, merged DataFrame with all columns intact.

    Raises:
        SystemExit: If no CSV files are found in the input directory.
    """

    # -------------------------------------------------------------------------
    # STEP 1: Build the absolute path to the input folder.
    # -------------------------------------------------------------------------
    # os.path.dirname(__file__) gives us the 'pipeline/' directory.
    # If input_dir is absolute, use it directly. Otherwise, go one level up
    # ('..') to reach OutboundScript/, then append the input_dir.
    # -------------------------------------------------------------------------
    pipeline_dir = os.path.dirname(os.path.abspath(__file__))
    if os.path.isabs(input_dir):
        leads_dir = input_dir
    else:
        outbound_root = os.path.join(pipeline_dir, "..")
        leads_dir = os.path.join(outbound_root, input_dir)

    # Build the glob pattern: match every .csv file inside leads_dir
    csv_pattern = os.path.join(leads_dir, "*.csv")
    file_list = glob.glob(csv_pattern)

    # -------------------------------------------------------------------------
    # STEP 2: Safety check — abort if the folder is empty or missing.
    # -------------------------------------------------------------------------
    if not file_list:
        print(f"[CLEANER] CRITICAL: No CSV files found in {input_dir} directory.")
        print(f"[CLEANER] Searched path: {os.path.abspath(leads_dir)}")
        exit(1)

    print(f"[CLEANER] Found {len(file_list)} raw CSV file(s) in {input_dir}.")

    # -------------------------------------------------------------------------
    # STEP 3: Read every CSV and stitch them together along the row axis.
    # -------------------------------------------------------------------------
    # ignore_index=True resets the row index so you get a clean 0..N sequence
    # instead of fragmented indices from each individual file.
    # -------------------------------------------------------------------------
    df = pd.concat(map(pd.read_csv, file_list), ignore_index=True)
    total_raw = len(df)
    print(f"[CLEANER] Total raw leads merged: {total_raw}")

    # -------------------------------------------------------------------------
    # STEP 4: Drop exact duplicate rows.
    # -------------------------------------------------------------------------
    # WHY: Apify scrapes from overlapping search queries, so the same prospect
    # can appear in multiple export files. Deduplication prevents sending the
    # same person two identical cold emails, which destroys sender reputation.
    # -------------------------------------------------------------------------
    df.drop_duplicates(inplace=True)
    deduped_count = len(df)
    removed = total_raw - deduped_count
    print(f"[CLEANER] Duplicates removed: {removed}")
    print(f"[CLEANER] Unique leads after dedup: {deduped_count}")

    # -------------------------------------------------------------------------
    # STEP 5: Fill NaN values with "N/A" in string/object columns ONLY.
    # -------------------------------------------------------------------------
    # WHY: Downstream modules (verifier.py) perform string comparisons on
    # email fields. A raw NaN from Pandas will cause silent failures or
    # TypeErrors if not handled. "N/A" is a safe, explicit sentinel value.
    #
    # IMPORTANT: Pandas 2.x enforces strict dtype checks. Calling
    # df.fillna("N/A") on a float64 column raises a TypeError because you
    # cannot insert a string into a numeric array. The fix is to only fill
    # object-type (string) columns. Numeric NaN values are handled safely
    # downstream by the verifier's pd.isna() guard clause.
    # -------------------------------------------------------------------------
    string_cols = df.select_dtypes(include=["object"]).columns
    df[string_cols] = df[string_cols].fillna("N/A")
    print(f"[CLEANER] NaN values filled with 'N/A' in {len(string_cols)} string columns.")

    print(f"[CLEANER] Cleaning complete. Returning DataFrame with {len(df)} rows.\n")
    return df
