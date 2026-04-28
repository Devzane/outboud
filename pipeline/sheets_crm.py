"""
sheets_crm.py - The Shared Google Sheets Service
=================================================
Centralized module for ALL Google Sheets I/O across the outbound pipeline.
Both imap_sync.py and sender.py import from this single module instead of
managing their own gspread connections. This eliminates duplicated boilerplate
and ensures a single source of truth for:
    - Credential resolution
    - Spreadsheet/worksheet targeting
    - DataFrame <-> Sheet conversion logic

Architecture Note:
    Credentials are resolved relative to this file's location on disk:
    OutboundScript/pipeline/sheets_crm.py -> ../../agency-bot/google_credentials.json
    This avoids hardcoded absolute paths and works across any machine.
"""
import os
import sys

import gspread
import pandas as pd

# =============================================================================
# 1. CREDENTIAL RESOLUTION
# =============================================================================
# Build the path dynamically relative to THIS file's location.
# sheets_crm.py lives at: OutboundScript/pipeline/sheets_crm.py
# google_credentials.json lives at: agency-bot/google_credentials.json
# So we go up two levels (pipeline -> OutboundScript -> Vectra-Automation),
# then down into agency-bot/.
CRED_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '..', 'agency-bot', 'google_credentials.json')
)

# The name of the master Google Sheet that acts as our CRM.
SPREADSHEET_NAME = "Agency Lead Dashboard"

# The specific worksheet (tab) inside the spreadsheet.
WORKSHEET_NAME = "Outbound Pipeline"


# =============================================================================
# 2. LAZY SINGLETON CLIENT
# =============================================================================
# We authenticate once per script invocation, not on every function call.
# The _gc variable holds the authenticated gspread client.
_gc = None


def _get_client():
    """
    Returns an authenticated gspread client, creating it on first call.

    Why lazy? Because importing this module shouldn't crash the entire
    pipeline if the credentials file is missing. We want the error to
    surface only when a function actually tries to USE the client.
    """
    global _gc

    if _gc is not None:
        return _gc

    # --- Pre-flight check: does the credentials file exist? ---
    if not os.path.exists(CRED_PATH):
        print(f"[FATAL] Google Credentials not found at: {CRED_PATH}")
        print("[HINT]  Ensure 'google_credentials.json' exists in the agency-bot/ directory.")
        sys.exit(1)

    try:
        _gc = gspread.service_account(filename=CRED_PATH)
        print(f"[SHEETS CRM] Authenticated with Google Sheets via: {CRED_PATH}")
        return _gc
    except Exception as e:
        print(f"[FATAL] Failed to authenticate with Google Sheets: {e}")
        sys.exit(1)


def _get_worksheet():
    """
    Opens the target spreadsheet and returns the specific worksheet object.

    If the worksheet tab doesn't exist, it creates one automatically.
    This prevents the "WorksheetNotFound" crash on first run.
    """
    gc = _get_client()

    try:
        sh = gc.open(SPREADSHEET_NAME)
    except gspread.exceptions.SpreadsheetNotFound:
        print(f"[FATAL] Spreadsheet '{SPREADSHEET_NAME}' not found.")
        print("[HINT]  Share the Google Sheet with the service account email in your credentials file.")
        sys.exit(1)

    # Attempt to open the worksheet; create it if missing.
    try:
        worksheet = sh.worksheet(WORKSHEET_NAME)
    except gspread.exceptions.WorksheetNotFound:
        print(f"[SHEETS CRM] Worksheet '{WORKSHEET_NAME}' not found. Creating it now...")
        worksheet = sh.add_worksheet(title=WORKSHEET_NAME, rows=1000, cols=20)
        print(f"[SHEETS CRM] Worksheet '{WORKSHEET_NAME}' created successfully.")

    return worksheet


# =============================================================================
# 3. PUBLIC API — These are the only two functions other modules should call.
# =============================================================================

def get_all_leads_as_df() -> pd.DataFrame:
    """
    Fetches every row from the 'Outbound Pipeline' worksheet and returns
    them as a Pandas DataFrame.

    Returns:
        pd.DataFrame: A DataFrame where each row is a lead and each column
                      maps to a Sheet header. Returns an EMPTY DataFrame
                      if the sheet has no data rows (headers only or blank).

    Usage:
        from pipeline.sheets_crm import get_all_leads_as_df
        df = get_all_leads_as_df()
    """
    worksheet = _get_worksheet()

    try:
        records = worksheet.get_all_records()
    except Exception as e:
        print(f"[ERROR] Failed to fetch records from Google Sheets: {e}")
        return pd.DataFrame()

    if not records:
        print(f"[INFO] No data rows found in '{WORKSHEET_NAME}'.")
        return pd.DataFrame()

    df = pd.DataFrame(records)
    print(f"[SHEETS CRM] Loaded {len(df)} leads from '{WORKSHEET_NAME}'.")
    return df


def update_sheet_from_df(df: pd.DataFrame) -> bool:
    """
    Clears the entire 'Outbound Pipeline' worksheet and overwrites it
    with the contents of the provided DataFrame (headers + data).

    Why clear-and-rewrite instead of row-level patches?
        - Our lead volume is in the hundreds, not millions.
        - A full rewrite is atomic: either the whole sheet is updated or it
          isn't. No risk of partial updates leaving the sheet in a bad state.
        - It's dramatically simpler code with zero row-index bookkeeping.

    Args:
        df (pd.DataFrame): The updated DataFrame to write back.

    Returns:
        bool: True if the update succeeded, False otherwise.

    Usage:
        from pipeline.sheets_crm import update_sheet_from_df
        success = update_sheet_from_df(df)
    """
    if df.empty:
        print("[WARNING] DataFrame is empty. Skipping Sheet update to avoid data loss.")
        return False

    worksheet = _get_worksheet()

    try:
        # Step 1: Clear all existing content.
        worksheet.clear()

        # Step 2: Rebuild the sheet — first row is headers, rest is data.
        # .fillna("") prevents numpy NaN from being written as literal "nan" strings.
        clean_df = df.fillna("")
        payload = [clean_df.columns.values.tolist()] + clean_df.values.tolist()
        worksheet.update(payload)

        print(f"[SHEETS CRM] Successfully wrote {len(df)} rows back to '{WORKSHEET_NAME}'.")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to update Google Sheets: {e}")
        return False
