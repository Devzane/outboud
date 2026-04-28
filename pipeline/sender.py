"""
sender.py - The Dispatcher
===========================
Executes prioritized sending logic via Google Sheets:
1. Follow-ups (sequence_step > 0)
2. New Leads (sequence_step == 0) throttled to 15/day
Injects an HTML tracking pixel for open rates.

Data Flow:
    1. Pull leads from Google Sheets via sheets_crm.get_all_leads_as_df()
    2. Phase 1: Process all eligible follow-ups
    3. Phase 2: Process new leads (throttled to 15/day)
    4. Push updated DataFrame back via sheets_crm.update_sheet_from_df()
"""
import os
import resend
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

# Import our custom math engine
from .scheduler import calculate_next_send_date

# Import the shared Google Sheets service — single source of truth for I/O.
from .sheets_crm import get_all_leads_as_df, update_sheet_from_df

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
            "from": "Abdulmuiz <abdulmuiz@vectralautomation.tech>",
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

def generate_email_content(row, step):
    """
    Generates dynamic email content for the HVAC 4-step sequence.
    HTML tracking pixels have been removed for maximum deliverability.
    """
    # Safely extract variables with fallbacks
    first_name = str(row.get('first_name', '')).strip()
    first_name_greeting = f" {first_name}" if first_name and first_name.lower() != 'nan' else " there"
    
    city = str(row.get('city', '')).strip()
    city_text = f" in {city}" if city and city.lower() != 'nan' else " in your area"
    
    company_name = str(row.get('company_name', '')).strip()
    company_text = company_name if company_name and company_name.lower() != 'nan' else "your business"

    if step == 0:
        subject = "I tried to reach your office yesterday"
        body = f"Hi{first_name_greeting},<br><br>I'm an automation engineer researching HVAC dispatch efficiency{city_text}. I actually tried calling your main business line after hours to see how your routing works, and it went straight to a dead voicemail. Industry data shows missing those after-hours emergencies costs shops about $8k per dropped call.<br><br>I built a custom, multi-channel AI overflow valve to fix this. If a customer calls after hours, an AI receptionist answers instantly to handle the emergency. If they text, the system autonomously texts back, qualifies the issue, and secures the lead.<br><br>Mind if I record a quick 60-second video showing a live prototype of exactly how this would work for your specific business?<br><br>Best,<br>Abdulmuiz Sulaiman<br>Lead Automation Engineer, Vectra-Automation"
    elif step == 1:
        subject = "Re: I tried to reach your office yesterday"
        body = f"Hi{first_name_greeting},<br><br>I know you're busy running the team, but I wanted to bump this up.<br><br>I already mapped out the exact math on what that dead voicemail is costing {company_text} this month, and how the Voice & SMS AI prototype fixes it instantly without replacing your human front desk.<br><br>Let me know if you want the link to the video.<br><br>Best,<br>Abdulmuiz"
    elif step == 2:
        subject = "Re: I tried to reach your office yesterday"
        body = f"Hi{first_name_greeting},<br><br>One quick thought on this—research shows that 85% of callers who hit a voicemail will not leave a message and will just hang up to call a competitor instead.<br><br>My multi-channel AI guarantees a sub-5-second response time whether the customer calls or texts, meaning you win the race against other contractors{city_text} every single time.<br><br>Are you open to seeing the 60-second prototype?<br><br>Best,<br>Abdulmuiz"
    else:
        subject = "Re: I tried to reach your office yesterday"
        body = f"Hi{first_name_greeting},<br><br>I haven't heard back, so I'll assume plugging the after-hours call leak isn't a priority for {company_text} right now.<br><br>I will stop reaching out, but if you ever want to see how the Voice and SMS dispatcher works in the future, just reply to this email.<br><br>Best of luck this season!<br><br>Best,<br>Abdulmuiz"

    html_content = body
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

    # 1. Fetch leads from Google Sheets via the shared CRM module.
    #    No more inline gspread boilerplate — sheets_crm handles auth,
    #    worksheet resolution, and DataFrame conversion.
    df = get_all_leads_as_df()
    if df.empty:
        print("[INFO] No leads found in Google Sheets. Nothing to dispatch.")
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
                subject, html_content = generate_email_content(row, seq_step)
                
                success = send_resend_email(lead_email, subject, html_content, simulation_mode)
                
                if success:
                    df.at[index, 'sequence_step'] = seq_step + 1
                    df.at[index, 'last_contact_date'] = today_str
                    
                    if seq_step + 1 == 1:
                        next_delay = 3
                    elif seq_step + 1 == 2:
                        next_delay = 4
                    elif seq_step + 1 == 3:
                        next_delay = 6
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
            subject, html_content = generate_email_content(row, seq_step)
            
            success = send_resend_email(lead_email, subject, html_content, simulation_mode)
            
            if success:
                df.at[index, 'sequence_step'] = seq_step + 1
                df.at[index, 'last_contact_date'] = today_str
                df.at[index, 'next_scheduled_date'] = calculate_next_send_date(today, 3)
                new_leads_sent += 1

    # =========================================================================
    # PHASE 3: STATE PERSISTENCE (Back to Google Sheets via shared CRM)
    # =========================================================================
    if follow_ups_sent > 0 or new_leads_sent > 0:
        print("[DISPATCHER] Updating Google Sheets with latest dispatch data...")
        success = update_sheet_from_df(df)
        if success:
            print("[SUCCESS] Google Sheets successfully updated.")
        else:
            print("[ERROR] Failed to push updates back to Google Sheets.")

    print("[DISPATCHER] Daily sweep complete.")
    print(f"   Follow-ups sent: {follow_ups_sent}")
    print(f"   New leads sent:  {new_leads_sent}")
