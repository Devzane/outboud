import pandas as pd

def refine_leads():
    print("Loading master list...")
    df = pd.read_csv("MASTER_CLEANED_LEADS.csv")

    # 1. Added "personal_email" to the list of columns to keep
    columns_to_keep = [
        "first_name",
        "last_name",
        "job_title",
        "email",
        "personal_email", 
        "company_name",
        "company_phone",
        "company_website",
        "city",
        "linkedin"
    ]

    # 2. Filter the DataFrame to keep ONLY those columns
    existing_columns = [col for col in columns_to_keep if col in df.columns]
    
    # We use.copy() to prevent SettingWithCopy warnings in Pandas
    refined_df = df[existing_columns].copy()

    # Fill any blank spaces that pandas might have read as NaN with "N/A"
    refined_df.fillna("N/A", inplace=True)

    # 3. Quality Control: Check BOTH email columns
    print("Removing leads without any email address...")
    if "email" in refined_df.columns and "personal_email" in refined_df.columns:
        # Keep the row if 'email' is valid OR 'personal_email' is valid
        refined_df = refined_df[
            (refined_df["email"]!= "N/A") | (refined_df["personal_email"]!= "N/A")
        ]
    elif "email" in refined_df.columns:
        # Fallback just in case personal_email column is missing entirely
        refined_df = refined_df[refined_df["email"]!= "N/A"]

    # 4. Export the finalized list
    output_filename = "OUTBOUND_READY_LEADS.csv"
    refined_df.to_csv(output_filename, index=False)
    
    print(f"Success! {len(refined_df)} highly-targeted leads saved to {output_filename}.")

if __name__ == "__main__":
    refine_leads()