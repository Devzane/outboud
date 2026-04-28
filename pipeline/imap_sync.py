"""
imap_sync.py - The Kill Switch & Telegram Notifier
===================================================
Monitors the connected IMAP inbox to detect when a prospect has replied.
If a reply is found, it flags the prospect as 'has_replied' in Google Sheets
and sends an instant push notification via Telegram.

Data Flow:
    1. Pull leads from Google Sheets via sheets_crm.get_all_leads_as_df()
    2. Connect to Gmail IMAP and scan recent inbox senders
    3. Cross-reference senders against our 'verified_target_email' column
    4. On match: set has_replied=True, fire Telegram alert
    5. Push updated DataFrame back via sheets_crm.update_sheet_from_df()
"""
import imaplib
import email
import os
import pandas as pd
import requests
from dotenv import load_dotenv

# Import the shared Google Sheets service — single source of truth for I/O.
from .sheets_crm import get_all_leads_as_df, update_sheet_from_df

# Define the absolute path to the agency-bot .env file
ENV_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'agency-bot', '.env'))
load_dotenv(ENV_PATH)

def send_telegram_alert(sender_email):
    """Sends a push notification to your phone via Telegram."""
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not bot_token or not chat_id:
        print("[WARNING] TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID missing in .env. Skipping push notification.")
        return
        
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    message = f"🚨 LEAD REPLIED: {sender_email}.\n\nOpen Loom and record the 60-second video NOW!"
    
    try:
        response = requests.post(url, json={"chat_id": chat_id, "text": message})
        if response.status_code == 200:
            print("[TELEGRAM] Alert sent successfully to your phone.")
        else:
            print(f"[ERROR] Failed to send Telegram alert: {response.text}")
    except Exception as e:
        print(f"[ERROR] Exception sending Telegram alert: {e}")

def sync_replies():
    """
    Connects to Gmail IMAP, reads recent emails, and checks the sender 
    addresses against our Google Sheet 'verified_target_email' column.
    """
    print("[IMAP SYNC] Starting synchronization with Google Sheets")
    
    # 1. Load Environment Variables
    email_user = os.getenv("EMAIL_USER")
    email_pass = os.getenv("EMAIL_APP_PASSWORD")
    
    if not email_user or not email_pass:
        print(f"[ERROR] Credentials not found in environment at {ENV_PATH}")
        return

    # 2. Fetch leads from Google Sheets via the shared CRM module.
    #    No more inline gspread boilerplate — sheets_crm handles auth,
    #    worksheet resolution, and DataFrame conversion.
    df = get_all_leads_as_df()
    if df.empty:
        print("[INFO] No leads found in Google Sheets. Nothing to sync.")
        return

    # 3. Ensure columns exist
    if 'has_replied' not in df.columns:
        print("[IMAP SYNC] 'has_replied' column is missing. Initializing it as False.")
        df['has_replied'] = False
        
    if 'verified_target_email' not in df.columns:
        print("[ERROR] Column 'verified_target_email' not found in Sheet. Aborting sync.")
        return

    # 4. Connect to IMAP
    try:
        mail = imaplib.IMAP4_SSL('imap.gmail.com')
        mail.login(email_user, email_pass)
        mail.select('INBOX')
    except Exception as e:
        print(f"[ERROR] Failed to connect to IMAP server: {e}")
        return

    print("[IMAP SYNC] Connected to INBOX successfully. Searching for recent messages...")

    # 5. Fetch Senders from Recent emails
    status, messages = mail.search(None, 'ALL')
    
    if status != 'OK':
        print("[ERROR] Failed to perform IMAP search.")
        return
        
    # Get the last 100 emails to prevent extremely long processing times
    message_ids = messages[0].split()[-100:] 
    repliers = set()

    for msg_id in message_ids:
        res, data = mail.fetch(msg_id, '(BODY[HEADER.FIELDS (FROM)])')
        if res != 'OK': continue
            
        for response_part in data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])
                from_header = msg.get('From', '')
                if not from_header:
                    continue
                    
                clean_email = from_header
                if '<' in from_header and '>' in from_header:
                    start = from_header.find('<') + 1
                    end = from_header.find('>')
                    clean_email = from_header[start:end]
                    
                repliers.add(clean_email.lower().strip())

    mail.close()
    mail.logout()

    print(f"[IMAP SYNC] Found {len(repliers)} unique senders in recent inbox history.")

    # 6. Cross-reference with our DataFrame
    match_count = 0
    df['verified_target_email'] = df['verified_target_email'].astype(str).str.lower().str.strip()
    
    for sender_email in repliers:
        mask = df['verified_target_email'] == sender_email
        if mask.any():
            # Check if we already marked them as replied (to avoid duplicate telegram alerts)
            already_replied_mask = (mask) & (df['has_replied'] == True)
            if already_replied_mask.any():
                continue # We already sent an alert for this previously
                
            df.loc[mask, 'has_replied'] = True
            match_count += 1
            
            # TRIGGER MASSIVE TERMINAL ALERT AND TELEGRAM NOTIFICATION
            print("=========================================================")
            print(f"[🚨 ACTION REQUIRED 🚨] LEAD REPLIED: {sender_email}")
            print("=========================================================")
            send_telegram_alert(sender_email)

    # 7. Save Results back to Google Sheets via the shared CRM module.
    if match_count > 0:
        success = update_sheet_from_df(df)
        if success:
            print(f"[IMAP SYNC] Update successful! {match_count} new leads marked as replied.")
        else:
            print("[ERROR] Failed to push updates back to Google Sheets.")
    else:
        print("[IMAP SYNC] No new matching replies found.")

if __name__ == "__main__":
    sync_replies()
