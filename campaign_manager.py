"""
campaign_manager.py - The CLI Orchestrator
Root execution script for the campaign manager. Provides terminal flags to 
run synchronizations and dispatch jobs cleanly.
"""
import argparse
import sys

# Import our modular pipeline scripts
from pipeline import imap_sync
from pipeline import sender

def main():
    print("====================================")
    print("  VECTRA AUTOMATION COLD OUTBOUND   ")
    print("====================================")
    
    # 1. Set up the argument parser
    parser = argparse.ArgumentParser(description="CLI tool to manage and sequence cold outbound campaigns.")
    
    # The requirement: -f or --file to specify target list
    parser.add_argument('-f', '--file', type=str, required=True, 
                        help="Path to the target CSV leads file.")
                        
    # Action flags
    parser.add_argument('--sync', action='store_true', 
                        help="Check IMAP inbox and update 'has_replied' flags.")
                        
    parser.add_argument('--send', action='store_true', 
                        help="Execute daily sequencing and send pending emails.")
                        
    args = parser.parse_args()
    
    # 2. Logic Routing
    # If no action is provided, warn the user.
    if not args.sync and not args.send:
        print("[WARNING] No action specified. Use --sync or --send")
        parser.print_help()
        sys.exit(1)
        
    # Execute the requested tasks sequentially
    target_csv = args.file
    
    if args.sync:
        print("\n--- INITIATING IMAP SYNC ---")
        imap_sync.sync_replies(target_csv)
        
    if args.send:
        print("\n--- INITIATING DAILY CAMPAIGN DISPATCH ---")
        sender.execute_daily_sending(target_csv)

if __name__ == "__main__":
    main()
