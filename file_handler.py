import pandas as pd
import os

def load_leads(filepath):
    try:
        if not os.path.exists(filepath):
            print(f"File not found: {filepath}")
            return pd.DataFrame()
        return pd.read_csv(filepath)
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return pd.DataFrame()

def save_leads(df, filepath):
    try:
        df.to_csv(filepath, index=False)
        print(f"Successfully saved enriched leads to {filepath}")
    except Exception as e:
        print(f"Error saving {filepath}: {e}")
