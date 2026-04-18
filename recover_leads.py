import pandas as pd
import os

def recover_terminal_data():
    print("Parsing terminal_logs.txt...")
    recovered_emails = {}

    # 1. Read the copied terminal text (Make sure the file is named exactly terminal_logs.txt)
    try:
        with open("terminal_log.txt", "r", encoding="utf-8") as f:
            lines = f.readlines()
    except FileNotFoundError:
        print("Error: Please make sure terminal_log.txt exists in this folder.")
        return

    # 2. Extract the email and status based on the NEW cascading log format
    for line in lines:
        # CRITICAL: The log uses UPPERCASE ("PASSED:") but we were searching
        # for lowercase ("passed:"). Python's `in` is case-sensitive, so
        # "passed:" in "WORK email PASSED: ..." returns False — zero matches.
        # Fix: lowercase the entire line before matching.
        line_lower = line.lower()
        if "passed:" in line_lower and "->" in line_lower:
            try:
                # Extracts data from strings like:
                #   "  [123/719] WORK email PASSED: javier@air.com -> SAFE"
                part1 = line_lower.split("passed: ")[1]
                email = part1.split(" -> ")[0].strip()
                status = part1.split(" -> ")[1].strip()
                recovered_emails[email] = status
            except Exception as e:
                continue

    print(f"Successfully salvaged {len(recovered_emails)} emails from the terminal log!")

    # 3. Load the CURRENT master file (Since we deleted the old outbound file)
    try:
        df = pd.read_csv("RECOVERED_LEADS.csv")
    except FileNotFoundError:
        print("Error: RECOVERED_LEADS.csv not found!")
        return

    # 4. Map the salvaged data back to the spreadsheet
    for index, row in df.iterrows():
        primary = str(row.get('email', '')).strip()
        personal = str(row.get('personal_email', '')).strip()

        # Update the row if we recovered the primary email
        if primary in recovered_emails:
            df.at[index, 'verification_status'] = recovered_emails[primary]
            df.at[index, 'verified_target_email'] = primary
            df.at[index, 'email_source_type'] = "work_email"
            
        # Update the row if we recovered the personal email
        elif personal in recovered_emails:
            df.at[index, 'verification_status'] = recovered_emails[personal]
            df.at[index, 'verified_target_email'] = personal
            df.at[index, 'email_source_type'] = "personal_email"

    # 5. Overwrite the file with the newly combined data
    df.to_csv("RECOVERED_LEADS.csv", index=False)
    print("Saved updates directly to RECOVERED_LEADS.csv. Your credits are safe!")

if __name__ == "__main__":
    recover_terminal_data()