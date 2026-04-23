"""
sender.py - The Dispatcher
Executes prioritized sending logic via Google Sheets:
1. Follow-ups (sequence_step > 0)
2. New Leads (sequence_step == 0) throttled to 15/day
Injects an HTML tracking pixel for open rates.
"""
import os
import resend
import gspread
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

# Import our custom math engine
from .scheduler import calculate_next_send_date

# Define environment path
ENV_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'agency-bot', '.env'))
load_dotenv(ENV_PATH)

# Load Resend API Key
# Usually stored in OutboundScript/.env or agency-bot/.env
OUTBOUND_ENV_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.env'))
load_dotenv(OUTBOUND_ENV_PATH)

RESEND_API_KEY = os.getenv("RESEND_API_KEY")
resend.api_key = RESEND_API_KEY

def send_resend_email(to_email, subject, html_content, simulation_mode=False):
    """Executes the actual email dispatch using the Resend API with Reply-To Inbound Routing."""
    if simulation_mode:
        print(f"[RESEND SIMULATION] -> Sending to {to_email} with Reply-To Routing.")
        return True
    
    if not RESEND_API_KEY:
        print("[ERROR] RESEND_API_KEY missing. Cannot send.")
        return False
        
    try:
        # The reply-to header routes replies to Resend instead of Zoho
        params: resend.Emails.SendParams = {
            "from": "abdulmuiz@vectralautomation.tech",
            "reply_to": "hello@inbound.vectralautomation.tech",
            "to": [to_email],
            "subject": subject,
            "html": html_content,
        }
        response = resend.Emails.send(params)
        print(f"[SUCCESS] Dispatched to {to_email}. ID: {response.get('id', 'N/A') if isinstance(response, dict) else response}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to send email to {to_email} via Resend: {e}")
        return False

def generate_email_content(to_email, step):
    """
    Generates dynamic email content and automatically injects an HTML tracking pixel.
    """
    # Base Content Generation
    if step == 0:
        subject = "Quick question about your operations"
        body = f"Hi,<br><br>I noticed your company and wanted to see if you handle X...<br><br>Best,<br>Vectra Automation"
    elif step == 1:
        subject = "Following up on my previous email"
        body = f"Hi,<br><br>Just bubbling this up. Did you see my last note?<br><br>Best,<br>Vectra Automation"
    elif step == 2:
        subject = "Any thoughts?"
        body = f"Hi,<br><br>Checking in one last time...<br><br>Best,<br>Vectra Automation"
    else:
        subject = "Final Check-in"
        body = f"Hi,<br><br>Assuming this isn't a priority right now.<br><br>Best,<br>Vectra Automation"

    # HTML Tracking Pixel Injection
    tracking_url = f"https://vectralautomation.tech/api/track?email={to_email}&step={step}"
    tracking_pixel = f'<img src="{tracking_url}" width="1" height="1" style="display:none;" />'
    
    html_content = body + tracking_pixel
    return subject, html_content

def execute_daily_sending():
    """
    Prioritized Dispatch Engine using Google Sheets:
    Phase 1: Processes all eligible Follow-Ups.
    Phase 2: Processes New Leads (Strictly throttled to 15/day).
    """
    print(f"[DISPATCHER] Starting Cloud-Native prioritized daily dispatch...")
    
    simulation_mode = False
    if not RESEND_API_KEY:
        print("[WARNING] RESEND_API_KEY missing. Defaulting to SIMULATION MODE.")
        simulation_mode = True

    # 1. Connect to Google Sheets
    CRED_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'agency-bot', 'google_credentials.json'))
    if not os.path.exists(CRED_PATH):
        print(f"[ERROR] Google Credentials not found at {CRED_PATH}. Please provide it.")
        return

    try:
        gc = gspread.service_account(filename=CRED_PATH)
        # Open the specific worksheet
        sh = gc.open("Agency Lead Dashboard")
        
        # Try to open "Outbound Pipeline", if not exist, fail gracefully
        try:
            worksheet = sh.worksheet("Outbound Pipeline")
        except gspread.exceptions.WorksheetNotFound:
            print("[ERROR] Worksheet 'Outbound Pipeline' not found. Please create it and add your leads.")
            return

        # Fetch all records into a DataFrame
        records = worksheet.get_all_records()
        if not records:
            print("[INFO] No leads found in 'Outbound Pipeline'.")
            return
        df = pd.DataFrame(records)
    except Exception as e:
        print(f"[ERROR] Failed to connect to Google Sheets: {e}")
        return

    # Ensure required columns exist
    if 'sequence_step' not in df.columns:
        df['sequence_step'] = 0
    if 'last_contact_date' not in df.columns:
        df['last_contact_date'] = ""
    if 'next_scheduled_date' not in df.columns:
        df['next_scheduled_date'] = ""
    if 'has_replied' not in df.columns:
        df['has_replied'] = False
    if 'verification_status' not in df.columns:
        df['verification_status'] = 'valid'

    today = datetime.today()
    today_str = today.strftime('%Y-%m-%d')
    today_date_obj = datetime.strptime(today_str, '%Y-%m-%d')

    follow_ups_sent = 0
    new_leads_sent = 0

    # =========================================================================
    # PHASE 1: FOLLOW-UPS (sequence_step > 0)
    # =========================================================================
    print("--- Phase 1: Processing Follow-Ups ---")
    for index, row in df.iterrows():
        replied = str(row.get('has_replied', 'False')).lower() == 'true'
        bounced = str(row.get('verification_status', '')).lower() == 'bounced'
        
        if replied or bounced:
            continue

        seq_step = int(row['sequence_step']) if pd.notna(row['sequence_step']) and str(row['sequence_step']).strip() != '' else 0
        scheduled_date_str = str(row['next_scheduled_date'])

        if seq_step > 0:
            is_eligible = False
            
            if pd.isna(row['next_scheduled_date']) or not scheduled_date_str.strip() or scheduled_date_str == "nan":
                is_eligible = True
            else:
                try:
                    scheduled_obj = datetime.strptime(scheduled_date_str, '%Y-%m-%d')
                    if scheduled_obj <= today_date_obj:
                        is_eligible = True
                except ValueError:
                    is_eligible = True
            
            if is_eligible:
                lead_email = row.get('verified_target_email', f"Lead #{index}")
                subject, html_content = generate_email_content(lead_email, seq_step)
                
                success = send_resend_email(lead_email, subject, html_content, simulation_mode)
                
                if success:
                    df.at[index, 'sequence_step'] = seq_step + 1
                    df.at[index, 'last_contact_date'] = today_str
                    
                    if seq_step + 1 == 2:
                        next_delay = 7
                    elif seq_step + 1 == 3:
                        next_delay = 14
                    else:
                        next_delay = 999 
                        
                    df.at[index, 'next_scheduled_date'] = calculate_next_send_date(today, next_delay)
                    follow_ups_sent += 1

    # =========================================================================
    # PHASE 2: NEW LEADS (sequence_step == 0) - THROTTLED to 15
    # =========================================================================
    print("--- Phase 2: Processing New Leads (Throttle: 15) ---")
    for index, row in df.iterrows():
        if new_leads_sent >= 15:
            print("[DISPATCHER] Daily limit of 15 new leads reached. Breaking loop.")
            break

        replied = str(row.get('has_replied', 'False')).lower() == 'true'
        bounced = str(row.get('verification_status', '')).lower() == 'bounced'
        
        if replied or bounced:
            continue

        seq_step = int(row['sequence_step']) if pd.notna(row['sequence_step']) and str(row['sequence_step']).strip() != '' else 0
        
        if seq_step == 0:
            lead_email = row.get('verified_target_email', f"Lead #{index}")
            subject, html_content = generate_email_content(lead_email, seq_step)
            
            success = send_resend_email(lead_email, subject, html_content, simulation_mode)
            
            if success:
                df.at[index, 'sequence_step'] = seq_step + 1
                df.at[index, 'last_contact_date'] = today_str
                df.at[index, 'next_scheduled_date'] = calculate_next_send_date(today, 3)
                new_leads_sent += 1

    # =========================================================================
    # PHASE 3: STATE PERSISTENCE (Back to Google Sheets)
    # =========================================================================
    if follow_ups_sent > 0 or new_leads_sent > 0:
        print("[DISPATCHER] Updating Google Sheets with latest dispatch data...")
        try:
            # We clear the worksheet and upload the entire dataframe
            # A more robust solution for huge datasets is updating only specific rows, 
            # but for cold outreach limits, rewriting the sheet is clean and fast enough.
            worksheet.clear()
            worksheet.update([df.columns.values.tolist()] + df.values.tolist())
            print("[SUCCESS] Google Sheets successfully updated.")
        except Exception as e:
            print(f"[ERROR] Failed to push updates back to Google Sheets: {e}")

    print("[DISPATCHER] Daily sweep complete.")
    print(f"   Follow-ups sent: {follow_ups_sent}")
    print(f"   New leads sent:  {new_leads_sent}")
