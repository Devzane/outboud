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
"commercial HVAC contractors Baton Rouge LA",
"industrial HVAC design build Baton Rouge LA",
"commercial chiller repair Baton Rouge LA",
"rooftop unit RTU installation Baton Rouge LA",
"commercial HVAC preventative maintenance Baton Rouge LA",
"commercial HVAC contractors Toledo OH",
"industrial HVAC design build Toledo OH",
"commercial chiller repair Toledo OH",
"rooftop unit RTU installation Toledo OH",
"commercial HVAC preventative maintenance Toledo OH",
"commercial HVAC contractors Fort Wayne IN",
"industrial HVAC design build Fort Wayne IN",
"commercial chiller repair Fort Wayne IN",
"rooftop unit RTU installation Fort Wayne IN",
"commercial HVAC preventative maintenance Fort Wayne IN",
"commercial HVAC contractors Fargo ND",
"industrial HVAC design build Fargo ND",
"commercial chiller repair Fargo ND",
"rooftop unit RTU installation Fargo ND",
"commercial HVAC preventative maintenance Fargo ND",
"commercial HVAC contractors Little Rock AR",
"industrial HVAC design build Little Rock AR",
"commercial chiller repair Little Rock AR",
"rooftop unit RTU installation Little Rock AR",
"commercial HVAC preventative maintenance Little Rock AR",
"commercial HVAC contractors Sioux Falls SD",
"industrial HVAC design build Sioux Falls SD",
"commercial chiller repair Sioux Falls SD",
"rooftop unit RTU installation Sioux Falls SD",
"commercial HVAC preventative maintenance Sioux Falls SD",
"commercial HVAC contractors Chattanooga TN",
"industrial HVAC design build Chattanooga TN",
"commercial chiller repair Chattanooga TN",
"rooftop unit RTU installation Chattanooga TN",
"commercial HVAC preventative maintenance Chattanooga TN",
"commercial HVAC contractors Knoxville TN",
"industrial HVAC design build Knoxville TN",
"commercial chiller repair Knoxville TN",
"rooftop unit RTU installation Knoxville TN",
"commercial HVAC preventative maintenance Knoxville TN"
]
# The directory mapping for the final output
OUTPUT_CSV = r"C:\Users\Zeetha Robotics\Documents\Vectra-Automation\OutboundScript\Leads\hvac_smb_leads.csv"
