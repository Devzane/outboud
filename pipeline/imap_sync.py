"""
imap_sync.py - The Kill Switch (IMAP Reply Sync)
Monitors the connected IMAP inbox to detect when a prospect has replied.
If a reply is found, it flags the prospect as 'has_replied' in our CSV.
This prevents further automated follow-up sequences.
"""
import imaplib
import email
import os
import pandas as pd
from dotenv import load_dotenv

# Define the absolute path to the agency-bot .env file
# Based on project structure: Vectra-Automation/OutboundScript/pipeline/imap_sync.py -> ../agency-bot/.env
ENV_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'agency-bot', '.env'))
load_dotenv(ENV_PATH)

def sync_replies(csv_filepath: str):
    """
    Connects to Gmail IMAP, reads recent emails, and checks the sender 
    addresses against our CSV 'verified_target_email' column.

    Args:
        csv_filepath (str): The path to the CSV file holding our campaign leads.
    """
    print(f"[IMAP SYNC] Starting synchronization on {csv_filepath}")
    
    # 1. Load Environment Variables
    email_user = os.getenv("EMAIL_USER")
    email_pass = os.getenv("EMAIL_APP_PASSWORD")
    
    if not email_user or not email_pass:
        print(f"[ERROR] Credentials not found in environment at {ENV_PATH}")
        return

    # 2. Load the Leads DataFrame
    try:
        df = pd.read_csv(csv_filepath)
    except FileNotFoundError:
        print(f"[ERROR] Could not find the CSV file at: {csv_filepath}")
        return

    # 3. Ensure 'has_replied' column exists to prevent key errors
    if 'has_replied' not in df.columns:
        print("[IMAP SYNC] 'has_replied' column is missing. Initializing it as False.")
        df['has_replied'] = False
        
    # We also need a fast way to check emails. Let's make sure verified_target_email exists
    if 'verified_target_email' not in df.columns:
        print("[ERROR] Column 'verified_target_email' not found in CSV. Aborting sync.")
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
    # Using 'ALL' rather than 'UNSEEN' guarantees we don't miss read replies.
    status, messages = mail.search(None, 'ALL')
    
    if status != 'OK':
        print("[ERROR] Failed to perform IMAP search.")
        return
        
    # Get the last 100 emails to prevent extremely long processing times
    message_ids = messages[0].split()[-100:] 
    
    repliers = set()

    for msg_id in message_ids:
        # Fetch individual email packet (RFC822 gets full message, BODY[HEADER.FIELDS (FROM)] is faster)
        # Using BODY[HEADER.FIELDS (FROM)] to limit data transfer weight
        res, data = mail.fetch(msg_id, '(BODY[HEADER.FIELDS (FROM)])')
        if res != 'OK': continue
            
        for response_part in data:
            if isinstance(response_part, tuple):
                # Parse the raw email bytes
                msg = email.message_from_bytes(response_part[1])
                
                # The 'From' header might look like "Name <email@domain.com>"
                from_header = msg.get('From', '')
                if not from_header:
                    continue
                    
                # Extract just the email if standard format `<email>` is found
                clean_email = from_header
                if '<' in from_header and '>' in from_header:
                    start = from_header.find('<') + 1
                    end = from_header.find('>')
                    clean_email = from_header[start:end]
                    
                repliers.add(clean_email.lower().strip())

    # Close the mailbox
    mail.close()
    mail.logout()

    print(f"[IMAP SYNC] Found {len(repliers)} unique senders in recent inbox history.")

    # 6. Cross-reference with our DataFrame
    match_count = 0
    # Clean the CSV email column for safe matching
    df['verified_target_email'] = df['verified_target_email'].astype(str).str.lower().str.strip()
    
    for sender_email in repliers:
        # Check if this sender email matches a target
        mask = df['verified_target_email'] == sender_email
        if mask.any():
            # If so, they replied! Change the flag for all matching rows
            df.loc[mask, 'has_replied'] = True
            match_count += 1
            print(f"[KILL SWITCH ACTIVATED] Lead replied: {sender_email}")

    # 7. Save Results
    if match_count > 0:
        df.to_csv(csv_filepath, index=False)
        print(f"[IMAP SYNC] Update successful! {match_count} new leads marked as replied.")
    else:
        print("[IMAP SYNC] No new matching replies found.")
