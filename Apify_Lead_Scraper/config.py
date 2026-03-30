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
"rooftop unit RTU installation Raleigh NC",
"commercial HVAC preventative maintenance Raleigh NC",
"commercial HVAC contractors Salt Lake City UT",
"industrial HVAC design build Salt Lake City UT",
"commercial chiller repair Salt Lake City UT",
"rooftop unit RTU installation Salt Lake City UT",
"commercial HVAC preventative maintenance Salt Lake City UT",
"commercial HVAC contractors Kansas City MO",
"industrial HVAC design build Kansas City MO",
"commercial chiller repair Kansas City MO",
"rooftop unit RTU installation Kansas City MO",
"commercial HVAC preventative maintenance Kansas City MO",
"commercial HVAC contractors Minneapolis MN",
"industrial HVAC design build Minneapolis MN",
"commercial chiller repair Minneapolis MN",
"rooftop unit RTU installation Minneapolis MN",
"commercial HVAC preventative maintenance Minneapolis MN",
"commercial HVAC contractors Portland OR",
"industrial HVAC design build Portland OR",
"commercial chiller repair Portland OR",
"rooftop unit RTU installation Portland OR",
"commercial HVAC preventative maintenance Portland OR",
"commercial HVAC contractors San Jose CA",
"industrial HVAC design build San Jose CA",
"commercial chiller repair San Jose CA",
"rooftop unit RTU installation San Jose CA",
"commercial HVAC preventative maintenance San Jose CA",
"commercial HVAC contractors Jacksonville FL",
"industrial HVAC design build Jacksonville FL",
"commercial chiller repair Jacksonville FL"

]
# The directory mapping for the final output
OUTPUT_CSV = r"C:\Users\Zeetha Robotics\Documents\Vectra-Automation\OutboundScript\Leads\hvac_smb_leads.csv"
