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
import shutil


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


# ==============================================================================
# Function 2: merge_and_clean_new_leads() — The Ingestor
# ==============================================================================
# PURPOSE:
#   Scans Leads/ for raw Apify CSV exports, merges and deduplicates them,
#   filters to essential outreach columns, appends to the master
#   RECOVERED_LEADS.csv, and archives the processed files so they are
#   never ingested twice.
#
# USAGE:
#   from pipeline.cleaner import merge_and_clean_new_leads
#   result = merge_and_clean_new_leads()
# ==============================================================================


def merge_and_clean_new_leads():
    """
    One-shot ingestion pipeline for raw Apify CSV exports.

    Steps:
        1. Resolve the Leads/ directory relative to the project root.
        2. Create Leads/Archive/ if it doesn't exist.
        3. Glob Leads/*.csv, excluding Archive/ contents and MASTER_CLEANED_LEADS.csv.
        4. Merge all CSVs, drop duplicate rows.
        5. Filter to essential outreach columns.
        6. Fill NaN with "N/A" in string columns.
        7. Append cleaned leads to RECOVERED_LEADS.csv (the master database).
        8. Move processed raw CSVs into Leads/Archive/.
        9. Return a result dict with status, message, and new_leads count.

    Returns:
        dict: {"status": str, "message": str, "new_leads": int}
    """

    # -------------------------------------------------------------------------
    # STEP 1: Resolve paths relative to the project root (OutboundScript/).
    # -------------------------------------------------------------------------
    pipeline_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.join(pipeline_dir, "..")
    leads_dir = os.path.join(project_root, "Leads")
    archive_dir = os.path.join(leads_dir, "Archive")
    master_csv = os.path.join(project_root, "RECOVERED_LEADS.csv")

    # -------------------------------------------------------------------------
    # STEP 2: Create the Archive/ subfolder if it doesn't exist.
    # -------------------------------------------------------------------------
    # WHY: We need a safe destination to move processed files into so they
    # are never scanned again on a future run. os.makedirs with exist_ok
    # is idempotent — safe to call every time.
    # -------------------------------------------------------------------------
    os.makedirs(archive_dir, exist_ok=True)
    print(f"[INGESTOR] Archive directory confirmed: {os.path.abspath(archive_dir)}")

    # -------------------------------------------------------------------------
    # STEP 3: Discover raw CSV files, excluding Archive/ and master files.
    # -------------------------------------------------------------------------
    # WHY: glob.glob("Leads/*.csv") does NOT recurse into subdirectories,
    # so Archive/ contents are naturally excluded. We also explicitly skip
    # MASTER_CLEANED_LEADS.csv which is a pre-existing aggregate file.
    # -------------------------------------------------------------------------
    csv_pattern = os.path.join(leads_dir, "*.csv")
    all_csvs = glob.glob(csv_pattern)

    # Filter out any master/aggregate files that live in Leads/
    excluded_files = {"MASTER_CLEANED_LEADS.csv"}
    file_list = [
        f for f in all_csvs
        if os.path.basename(f) not in excluded_files
    ]

    if not file_list:
        msg = "No new lead files found in Leads/ directory."
        print(f"[INGESTOR] {msg}")
        return {"status": "info", "message": msg, "new_leads": 0}

    print(f"[INGESTOR] Found {len(file_list)} raw CSV file(s) to ingest.")

    # -------------------------------------------------------------------------
    # STEP 4: Merge all CSVs and deduplicate.
    # -------------------------------------------------------------------------
    # WHY: Apify exports from overlapping searches produce duplicate rows.
    # pd.concat stitches them vertically; drop_duplicates removes exact
    # copies so a prospect is never emailed twice.
    # -------------------------------------------------------------------------
    try:
        frames = [pd.read_csv(f) for f in file_list]
        df = pd.concat(frames, ignore_index=True)
    except Exception as e:
        msg = f"Failed to read CSV files: {str(e)}"
        print(f"[INGESTOR] ERROR: {msg}")
        return {"status": "error", "message": msg, "new_leads": 0}

    total_raw = len(df)
    df.drop_duplicates(inplace=True)
    deduped_count = len(df)
    print(f"[INGESTOR] Raw rows: {total_raw} | After dedup: {deduped_count} "
          f"| Duplicates removed: {total_raw - deduped_count}")

    # -------------------------------------------------------------------------
    # STEP 5: Filter to essential outreach columns.
    # -------------------------------------------------------------------------
    # WHY: Apify exports contain dozens of columns (social links, company
    # descriptions, etc.) that are irrelevant for cold outreach. We keep
    # only the columns that match the RECOVERED_LEADS.csv schema.
    # -------------------------------------------------------------------------
    essential_columns = [
        "first_name", "last_name", "job_title", "email", "personal_email",
        "company_name", "company_phone", "company_website", "city",
        "linkedin", "verification_status", "verified_target_email",
        "email_source_type"
    ]

    # Only keep columns that actually exist in the merged DataFrame
    available_columns = [col for col in essential_columns if col in df.columns]
    df = df[available_columns]
    print(f"[INGESTOR] Filtered to {len(available_columns)} essential columns.")

    # -------------------------------------------------------------------------
    # STEP 6: Fill NaN in string columns with "N/A".
    # -------------------------------------------------------------------------
    # WHY: Downstream modules (sender.py, verifier.py) perform string
    # comparisons. Raw NaN values cause TypeErrors. "N/A" is an explicit
    # sentinel value that all modules can safely check against.
    # -------------------------------------------------------------------------
    string_cols = df.select_dtypes(include=["object"]).columns
    df[string_cols] = df[string_cols].fillna("N/A")
    print(f"[INGESTOR] NaN values filled in {len(string_cols)} string columns.")

    # -------------------------------------------------------------------------
    # STEP 7: Append to the master CSV (RECOVERED_LEADS.csv).
    # -------------------------------------------------------------------------
    # WHY: This is the single source of truth for the outbound pipeline.
    # If it exists, we append without writing headers again (prevents
    # duplicate header rows in the middle of the file). If it doesn't
    # exist, we create it fresh with headers.
    # -------------------------------------------------------------------------
    if os.path.exists(master_csv):
        df.to_csv(master_csv, mode="a", header=False, index=False)
        print(f"[INGESTOR] Appended {len(df)} leads to existing {os.path.basename(master_csv)}.")
    else:
        df.to_csv(master_csv, mode="w", header=True, index=False)
        print(f"[INGESTOR] Created new {os.path.basename(master_csv)} with {len(df)} leads.")

    # -------------------------------------------------------------------------
    # STEP 8: Archive processed raw CSV files.
    # -------------------------------------------------------------------------
    # WHY: This is the critical idempotency guard. By moving raw files into
    # Archive/, subsequent runs of this function will not re-process them.
    # shutil.move() is atomic on most filesystems, preventing partial moves.
    # -------------------------------------------------------------------------
    for filepath in file_list:
        filename = os.path.basename(filepath)
        dest = os.path.join(archive_dir, filename)
        shutil.move(filepath, dest)
        print(f"[INGESTOR] Archived: {filename}")

    # -------------------------------------------------------------------------
    # STEP 9: Return summary result.
    # -------------------------------------------------------------------------
    new_leads = len(df)
    msg = f"Successfully ingested {new_leads} new leads from {len(file_list)} file(s)."
    print(f"[INGESTOR] {msg}\n")
    return {"status": "success", "message": msg, "new_leads": new_leads}

