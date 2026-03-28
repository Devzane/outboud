"""
Configuration module for Vectra Automation Outbound Scraper.
Isolates environment variable logic and hardcoded search parameters.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

_BASE_DIR = Path(__file__).resolve().parent

def load_config():
    """
    Load and validate the Apify API token from the .env file.
    """
    load_dotenv(dotenv_path=_BASE_DIR.parent / ".env")
    api_token = os.environ.get("APIFY_API_TOKEN")

    if not api_token or api_token == "your_token_here":
        print("❌  ERROR: APIFY_API_TOKEN is not set.")
        print("   → Open the .env file and paste your Apify API token.")
        sys.exit(1)

    return api_token

# Define the search queries for the Apify actor
SEARCH_QUERIES = [
   "industrial HVAC design build Houston TX",
   "industrial HVAC design build Dallas TX",
   "commercial chiller repair Austin TX",
   "commercial chiller repair San Antonio TX",
   "rooftop unit RTU installation Dallas TX",
   "rooftop unit RTU installation Houston TX",
   "multi-family HVAC contractors Austin TX",
   "multi-family HVAC contractors Dallas TX",
   "commercial HVAC preventative maintenance Houston TX",
   "commercial HVAC preventative maintenance San Antonio TX"
]

# The directory mapping for the final output
OUTPUT_CSV = r"C:\Users\Zeetha Robotics\Documents\Vectra-Automation\OutboundScript\Leads\hvac_smb_leads.csv"
