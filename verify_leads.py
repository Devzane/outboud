import pandas as pd
import requests
import time
import os
from dotenv import load_dotenv

# 1. Securely load the API key from your agency-bot folder
current_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(current_dir, '..', 'agency-bot', '.env')
load_dotenv(dotenv_path=env_path)

API_KEY = os.getenv("REOON_API_KEY")

if not API_KEY:
    print("CRITICAL ERROR: REOON_API_KEY not found.")
    exit()

def verify_email(email):
    """Sends the email to Reoon's API with a strict timeout."""
    # Catch any pandas NaN values or blank strings based on our previous terminal debugging
    if pd.isna(email) or str(email).strip() in ["nan", "N/A", "None", ""]:
        return "missing"
        
    url = "https://emailverifier.reoon.com/api/v1/verify"
    params = {"email": email, "key": API_KEY, "mode": "power"}
    
    try:
        response = requests.get(url, params=params, timeout=15)
        data = response.json()
        return data.get("status", "unknown")
    except Exception as e:
        print(f" Timeout or Error verifying {email}: {e}")
        return "unknown"

def process_cascading_verification():
    print("Loading OUTBOUND_READY_LEADS.csv...")
    df = pd.read_csv("OUTBOUND_READY_LEADS.csv")
    
    valid_rows = []
    output_filename = "FINAL_CASCADING_LEADS.csv"
    acceptable_statuses = ['safe', 'role', 'catch-all']
    
    print(f"Starting Cascading Verification for {len(df)} leads...")
    
    for index, row in df.iterrows():
        work_email = str(row.get('email')).strip()
        personal_email = str(row.get('personal_email')).strip()
        
        final_email = None
        final_status = None
        email_type = None
        
        # STEP 1: Verify the Work Email first
        work_status = verify_email(work_email)
        
        if work_status in acceptable_statuses:
            final_email = work_email
            final_status = work_status
            email_type = "work_email"
            print(f"[{index + 1}/{len(df)}] WORK email passed: {work_email} -> {work_status.upper()}")
            
        else:
            # STEP 2: Work email failed or was missing. Cascade to Personal Email.
            print(f"[{index + 1}/{len(df)}] Work email failed ({work_status}). Checking personal...")
            personal_status = verify_email(personal_email)
            
            if personal_status in acceptable_statuses:
                final_email = personal_email
                final_status = personal_status
                email_type = "personal_email"
                print(f"[{index + 1}/{len(df)}] PERSONAL email passed: {personal_email} -> {personal_status.upper()}")
            else:
                print(f"[{index + 1}/{len(df)}] BOTH emails failed. Lead discarded.")

        # STEP 3: If either email survived, save the row
        if final_email:
            row_copy = row.copy()
            row_copy['verified_target_email'] = final_email
            row_copy['verification_status'] = final_status
            row_copy['email_source_type'] = email_type  # This is your new indicator column
            valid_rows.append(row_copy)
            
            # Auto-save feature to protect against terminal freezing
            pd.DataFrame(valid_rows).to_csv(output_filename, index=False, na_rep="N/A")
            
        # Respect the Reoon API rate limit
        time.sleep(0.5)

    print(f"\nSuccess! Cascading verification complete.")
    print(f"Saved {len(valid_rows)} highly-deliverable leads to {output_filename}.")

if __name__ == "__main__":
    process_cascading_verification()