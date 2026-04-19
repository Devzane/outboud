"""
sender.py - The Dispatcher
Parses a target CSV list and determines who is eligible to receive a sequence email today.
Updates the sequence state and schedules the next follow up sequence.
"""
import os
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

# Import our custom math engine
# Because campaign_manager.py runs from the root, we use absolute or relative-to-pipeline imports
from .scheduler import calculate_next_send_date

# Define environment path
ENV_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'agency-bot', '.env'))
load_dotenv(ENV_PATH)

def execute_daily_sending(csv_filepath: str):
    """
    Iterates through the campaign list to find eligible targets.
    A target is eligible if:
      - has_replied == False
      - next_scheduled_date is today, in the past, or empty

    Args:
        csv_filepath (str): Path to our campaign list.
    """
    print(f"[DISPATCHER] Starting daily dispatch for {csv_filepath}")
    
    # 1. Load environment variables for SMTP (Prepared for future use)
    email_user = os.getenv("EMAIL_USER")
    email_pass = os.getenv("EMAIL_APP_PASSWORD")

    # 2. Load the DataFrame
    try:
        df = pd.read_csv(csv_filepath)
    except FileNotFoundError:
        print(f"[ERROR] Could not find the CSV file at: {csv_filepath}")
        return

    # 3. Ensure required columns exist
    if 'sequence_step' not in df.columns:
        df['sequence_step'] = 0
    if 'last_contact_date' not in df.columns:
        df['last_contact_date'] = ""
    if 'next_scheduled_date' not in df.columns:
        df['next_scheduled_date'] = ""
    if 'has_replied' not in df.columns:
        df['has_replied'] = False
        
    today = datetime.today()
    today_str = today.strftime('%Y-%m-%d')
    # Midnight normalize today for accurate <= comparisons against schedule strings
    today_date_obj = datetime.strptime(today_str, '%Y-%m-%d')

    send_count = 0
    
    # 4. Iterate over leads
    for index, row in df.iterrows():
        # Crucial Condition #1: They must not have replied
        if row['has_replied'] is True or str(row['has_replied']).lower() == 'true':
            continue # Skip them
            
        seq_step = int(row['sequence_step']) if pd.notna(row['sequence_step']) else 0
        scheduled_date_str = str(row['next_scheduled_date'])
        
        is_eligible = False
        
        # Crucial Condition #2: Is 'next_scheduled_date' valid?
        # If it's empty/NaN, we treat it as ready for Step 1
        if pd.isna(row['next_scheduled_date']) or not scheduled_date_str.strip() or scheduled_date_str == "nan":
            is_eligible = True
        else:
            try:
                # Compare dates
                scheduled_obj = datetime.strptime(scheduled_date_str, '%Y-%m-%d')
                if scheduled_obj <= today_date_obj:
                    is_eligible = True
            except ValueError:
                # Malformed date, treat as eligible to be safe, or log it
                print(f"[WARNING] Invalid date format for lead: {scheduled_date_str}. Treating as eligible.")
                is_eligible = True
                
        # 5. Dispatch Logic
        if is_eligible:
            lead_email = row.get('verified_target_email', f"Lead #{index}")
            print(f"[SMTP SIMULATION] -> Sending Sequence Step {seq_step + 1} to {lead_email}")
            
            # Action: Set up smtplib logic to send actual emails here
            
            # Post-send Updates:
            df.at[index, 'sequence_step'] = seq_step + 1
            df.at[index, 'last_contact_date'] = today_str
            
            # Determine the Next Delay based on the Sequence Architecture (1 > +3 days > 2 > +7 days > 3 > +14 days)
            if seq_step + 1 == 1:
                next_delay = 3
            elif seq_step + 1 == 2:
                next_delay = 7
            elif seq_step + 1 == 3:
                next_delay = 14
            else:
                # End of campaign, sequence 4 doesn't exist. Set next date far in future
                next_delay = 999 
                
            new_date = calculate_next_send_date(today, next_delay)
            df.at[index, 'next_scheduled_date'] = new_date
            
            send_count += 1
            
            # Save incrementally every 10 prospects to protect against crashes
            if send_count % 10 == 0:
                df.to_csv(csv_filepath, index=False)

    # Final save after the loop finishes
    df.to_csv(csv_filepath, index=False)
    print(f"[DISPATCHER] Daily sweep complete. {send_count} emails dispatched. Data saved.")
