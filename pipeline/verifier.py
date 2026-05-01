# ==============================================================================
# Module 2: verifier.py — The Cascading Validator
# ==============================================================================
# PURPOSE:
#   Performs cascading email verification using the Reoon Email Verifier API.
#   For each lead, it checks the work email first. If that fails, it cascades
#   to the personal email. If both fail, the lead is discarded entirely.
#
#   Surviving leads get three new columns appended:
#     - verified_target_email : the email address that passed verification
#     - verification_status   : the Reoon API status (safe, role, catch-all)
#     - email_source_type     : "work_email" or "personal_email"
#
# AUTO-SAVE PROTOCOL:
#   After every surviving lead, the running results are overwritten to
#   FINAL_CASCADING_LEADS.csv. This protects against terminal crashes,
#   API timeouts, or accidental Ctrl+C — you never lose verified progress.
#
# USAGE:
#   from pipeline import verifier
#   verifier.execute_cascading_verification(df)
# ==============================================================================

import pandas as pd
import requests
import time
import os
from dotenv import load_dotenv


# =============================================================================
# CONFIGURATION — Load the Reoon API key securely from the .env file.
# =============================================================================
# The .env file lives in the agency-bot/ folder, which is a sibling directory
# of OutboundScript/. We resolve the path relative to THIS script's location
# (pipeline/verifier.py), going up two levels to Vectra-Automation/, then
# into agency-bot/.
#
# File system layout:
#   Vectra-Automation/
#   ├── agency-bot/.env          <-- contains REOON_API_KEY
#   └── OutboundScript/
#       └── pipeline/verifier.py <-- this file
# =============================================================================
_script_dir = os.path.dirname(os.path.abspath(__file__))
_env_path = os.path.join(_script_dir, "..", "..", "agency-bot", ".env")
load_dotenv(dotenv_path=_env_path)

API_KEY = os.getenv("REOON_API_KEY")

# Hard stop if the key is missing — no point running 1000+ API calls that
# will all return 401 Unauthorized.
if not API_KEY:
    print("[VERIFIER] CRITICAL ERROR: REOON_API_KEY not found.")
    print(f"[VERIFIER] Searched .env path: {os.path.abspath(_env_path)}")
    exit(1)

print("[VERIFIER] REOON_API_KEY loaded successfully.\n")

# Reoon API endpoint and the statuses we consider "deliverable enough" to keep.
REOON_ENDPOINT = "https://emailverifier.reoon.com/api/v1/verify"
ACCEPTABLE_STATUSES = ["safe", "role", "catch-all", "catch_all"]


# =============================================================================
# HELPER FUNCTION: verify_email()
# =============================================================================
def verify_email(email, mode="power"):
    """
    Send a single email address to the Reoon Email Verifier API.

    Args:
        email (str): The email address to verify.
        mode  (str): Reoon verification depth — "quick" (domain/syntax only)
                     or "power" (deep SMTP check). Defaults to "power".

    Returns:
        str: One of the following:
            - "missing"  : The input was blank, NaN, or a sentinel string.
            - "safe"     : Reoon confirms the mailbox exists and is safe.
            - "role"     : The email is a role-based address (e.g., info@).
            - "catch-all": The domain accepts all addresses (risky but usable).
            - "invalid"  : The mailbox does not exist.
            - "unknown"  : The API call failed (timeout, network error, etc.).

    Notes:
        - timeout=15 prevents infinite terminal hangs on slow API responses.
        - mode is passed directly to the Reoon API params.
    """

    # -------------------------------------------------------------------------
    # Guard clause: Check for missing/blank/sentinel values BEFORE hitting
    # the API. This saves an API credit and avoids a wasted 15-second timeout.
    # -------------------------------------------------------------------------
    if pd.isna(email) or str(email).strip() in ["nan", "N/A", "None", ""]:
        return "missing"

    params = {
        "email": email,
        "key": API_KEY,
        "mode": mode,
    }

    try:
        response = requests.get(REOON_ENDPOINT, params=params, timeout=15)
        data = response.json()
        return data.get("status", "unknown")
    except requests.exceptions.Timeout:
        print(f"  [TIMEOUT] Reoon did not respond within 15s for: {email}")
        return "unknown"
    except requests.exceptions.ConnectionError:
        print(f"  [CONN ERROR] Network issue verifying: {email}")
        return "unknown"
    except Exception as e:
        print(f"  [ERROR] Unexpected failure verifying {email}: {e}")
        return "unknown"


# =============================================================================
# MAIN FUNCTION: execute_cascading_verification()
# =============================================================================
def execute_cascading_verification(df, mode="power", output_file="VERIFIED_LEADS.csv", append_mode=False):
    """
    Apply cascading email verification logic to every row in the DataFrame.

    Cascade Logic:
        1. Check the WORK email (column: 'email') first.
           - If Reoon returns safe, role, or catch-all → KEEP this email.
        2. If the work email fails or is missing, CHECK the PERSONAL email
           (column: 'personal_email').
           - If Reoon returns safe, role, or catch-all → KEEP this email.
        3. If BOTH emails fail → DISCARD the lead entirely.

    For surviving leads, three new columns are added:
        - verified_target_email : the winning email address
        - verification_status   : the Reoon status string
        - email_source_type     : "work_email" or "personal_email"

    Auto-Save Protocol:
        If append_mode is True:
            Appends the single latest row to the output file on each iteration.
            Creates the file with a header if it doesn't already exist.
        If append_mode is False:
            Overwrites the entire output file with the cumulative list of
            verified leads on each iteration.

    Args:
        df (pd.DataFrame): The DataFrame of leads to verify.
        mode (str): Reoon verification depth — "quick" or "power".
        output_file (str): The filename or path for the saved results.
        append_mode (bool): Whether to append to output_file instead of overwriting.

    Returns:
        dict: Summary with keys "status", "verified", "discarded", "output_file".
    """

    # -------------------------------------------------------------------------
    # Resolve the output path.
    # -------------------------------------------------------------------------
    outbound_root = os.path.join(_script_dir, "..")
    if os.path.isabs(output_file):
        output_filepath = output_file
    else:
        output_filepath = os.path.join(outbound_root, output_file)

    valid_rows = []    # Accumulator for surviving leads
    total_leads = len(df)
    discarded = 0      # Counter for leads where both emails failed

    print("=" * 65)
    print(f"  CASCADING EMAIL VERIFICATION — {total_leads} leads to process")
    print("=" * 65)

    # -------------------------------------------------------------------------
    # MAIN LOOP: Iterate through every row in the DataFrame.
    # -------------------------------------------------------------------------
    for index, row in df.iterrows():
        lead_num = index + 1   # Human-readable 1-based counter

        # -----------------------------------------------------------------
        # THE RESUME FIX: Skip leads that were already verified in a prior
        # run. This prevents burning Reoon API credits re-checking emails
        # that already have a known status from a recovered/merged CSV.
        # -----------------------------------------------------------------
        existing_status = str(row.get("verification_status", "")).strip()
        if existing_status not in ["nan", "N/A", "None", ""]:
            print(
                f"  [{lead_num}/{total_leads}] Skipping already verified "
                f"lead: {row.get('verified_target_email')}"
            )
            if existing_status in ACCEPTABLE_STATUSES:
                valid_rows.append(row)
                # Auto-save the already-verified lead to maintain the file.
                if append_mode:
                    pd.DataFrame([row]).to_csv(
                        output_filepath, mode="a", index=False, na_rep="N/A",
                        header=not os.path.exists(output_filepath)
                    )
                else:
                    pd.DataFrame(valid_rows).to_csv(
                        output_filepath, index=False, na_rep="N/A"
                    )
            continue
        # -----------------------------------------------------------------

        # Extract both email candidates from the current row.
        work_email = str(row.get("email", "")).strip()
        personal_email = str(row.get("personal_email", "")).strip()

        # These will hold the "winner" of the cascade.
        final_email = None
        final_status = None
        email_type = None

        # ----- STEP 1: Verify the WORK email first -----
        work_status = verify_email(work_email, mode=mode)

        if work_status in ACCEPTABLE_STATUSES:
            # Work email passed! No need to check personal.
            final_email = work_email
            final_status = work_status
            email_type = "work_email"
            print(
                f"  [{lead_num}/{total_leads}] WORK email PASSED: "
                f"{work_email} -> {work_status.upper()}"
            )

        else:
            # ----- STEP 2: Cascade to PERSONAL email -----
            print(
                f"  [{lead_num}/{total_leads}] Work email failed "
                f"({work_status}). Cascading to personal..."
            )
            personal_status = verify_email(personal_email, mode=mode)

            if personal_status in ACCEPTABLE_STATUSES:
                # Personal email saved this lead.
                final_email = personal_email
                final_status = personal_status
                email_type = "personal_email"
                print(
                    f"  [{lead_num}/{total_leads}] PERSONAL email PASSED: "
                    f"{personal_email} -> {personal_status.upper()}"
                )
            else:
                # ----- STEP 3: Both failed — discard the lead -----
                discarded += 1
                print(
                    f"  [{lead_num}/{total_leads}] BOTH emails FAILED. "
                    f"Lead DISCARDED."
                )

        # -----------------------------------------------------------------
        # AUTO-SAVE PROTOCOL: If the lead survived, append it and overwrite
        # the CSV file immediately. This means that even if the terminal
        # crashes on lead #500, leads #1 through #499 are already on disk.
        # -----------------------------------------------------------------
        if final_email:
            row_copy = row.copy()
            row_copy["verified_target_email"] = final_email
            row_copy["verification_status"] = final_status
            row_copy["email_source_type"] = email_type
            valid_rows.append(row_copy)

            # Auto-save protocol
            if append_mode:
                pd.DataFrame([row_copy]).to_csv(
                    output_filepath, mode="a", index=False, na_rep="N/A",
                    header=not os.path.exists(output_filepath)
                )
            else:
                pd.DataFrame(valid_rows).to_csv(
                    output_filepath, index=False, na_rep="N/A"
                )

        # -----------------------------------------------------------------
        # RATE LIMIT: 0.5 second delay between API calls to respect Reoon's
        # rate limits and avoid getting temporarily IP-banned.
        # -----------------------------------------------------------------
        time.sleep(0.5)

    # -------------------------------------------------------------------------
    # FINAL SUMMARY
    # -------------------------------------------------------------------------
    verified_count = len(valid_rows)
    print("\n" + "=" * 65)
    print("  CASCADING VERIFICATION COMPLETE")
    print("=" * 65)
    print(f"  Total leads processed : {total_leads}")
    print(f"  Verified & saved      : {verified_count}")
    print(f"  Discarded             : {discarded}")
    print(f"  Output file           : {os.path.abspath(output_filepath)}")
    print("=" * 65)

    # -------------------------------------------------------------------------
    # Return a summary dict so the API endpoint can relay results to the UI.
    # -------------------------------------------------------------------------
    return {
        "status": "success",
        "message": f"Verification complete. {verified_count} verified, {discarded} discarded.",
        "verified": verified_count,
        "discarded": discarded,
        "total_processed": total_leads,
        "output_file": os.path.abspath(output_filepath),
    }
