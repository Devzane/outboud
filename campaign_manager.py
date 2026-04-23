"""
campaign_manager.py - The CLI Orchestrator
Root execution script for the campaign manager. Provides terminal flags to 
run synchronizations and dispatch jobs cleanly.
"""
import argparse
import sys

# Import our modular pipeline scripts
from pipeline import sender

def main():
    print("====================================")
    print("  VECTRA AUTOMATION COLD OUTBOUND   ")
    print("      (Cloud-Native Edition)        ")
    print("====================================")
    
    # 1. Set up the argument parser
    parser = argparse.ArgumentParser(description="CLI tool to manage and sequence cold outbound campaigns from Google Sheets.")
    
    # We no longer need the local CSV file since we're using Google Sheets
    # But we can allow an optional --sheet flag if we want to support multiple sheets in the future
    parser.add_argument('--send', action='store_true', 
                        help="Execute daily sequencing and send pending emails via Google Sheets.")
                        
    args = parser.parse_args()
    
    # 2. Logic Routing
    if not args.send:
        print("[WARNING] No action specified. Use --send")
        parser.print_help()
        sys.exit(1)
        
    if args.send:
        print("\n--- INITIATING DAILY CLOUD CAMPAIGN DISPATCH ---")
        # No file needed, it pulls directly from Google Sheets
        sender.execute_daily_sending()

if __name__ == "__main__":
    main()
