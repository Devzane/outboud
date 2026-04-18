import pandas as pd
import glob
import os

def process_leads():
    print("Locating CSV files...")
    # 1. Find all CSV files in the current folder
    joined_files = os.path.join(".", "*.csv")
    file_list = glob.glob(joined_files)
    
    if not file_list:
        print("No CSV files found. Make sure this script is in the same folder as your leads.")
        return

    print(f"Found {len(file_list)} files. Merging...")
    
    # 2. Read all files and stitch them together along the row axis
    df = pd.concat(map(pd.read_csv, file_list), ignore_index=True)
    
    print(f"Total raw leads merged: {len(df)}")

    # 3. DATA CLEANING PHASE
    print("Cleaning data...")
    
    # Drop exact duplicate rows to ensure you don't message the same owner twice
    df.drop_duplicates(inplace=True)
    
    # 4. Export the Master List
    output_filename = "MASTER_CLEANED_LEADS.csv"
    
    # THE FIX: na_rep="N/A" automatically replaces any blank/null values with "N/A" during the save
    df.to_csv(output_filename, index=False, na_rep="N/A")
    
    print(f"Success! Cleaned master list saved as {output_filename} with {len(df)} unique leads.")

if __name__ == "__main__":
    process_leads()