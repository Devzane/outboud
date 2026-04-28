"""
campaign_manager.py - The CLI Orchestrator
==========================================
Root execution script for the outbound pipeline. Provides terminal flags to
run synchronizations and dispatch jobs cleanly from the command line.

Architecture:
    This script is purely an orchestrator — it contains ZERO business logic.
    All heavy lifting is delegated to the pipeline modules:
        - pipeline.imap_sync  -> Reply detection via IMAP + Telegram alerts
        - pipeline.sender     -> Prioritized email dispatch via Resend

    Both modules read/write autonomously from Google Sheets via the shared
    pipeline.sheets_crm service. No CSV files. No local databases.

Usage:
    python campaign_manager.py --sync          # Check for replies
    python campaign_manager.py --send          # Dispatch daily emails
    python campaign_manager.py --sync --send   # Full daily sweep
"""
import argparse
import sys

# Import our modular pipeline scripts
from pipeline import sender
from pipeline import imap_sync

def main():
    print("====================================")
    print("  VECTRA AUTOMATION COLD OUTBOUND   ")
    print("      (Cloud-Native Edition)        ")
    print("====================================")
    
    # 1. Set up the argument parser
    parser = argparse.ArgumentParser(
        description="CLI tool to manage and sequence cold outbound campaigns from Google Sheets."
    )
    
    # Two flags: --sync for IMAP reply detection, --send for email dispatch.
    # Both can be used together for a full daily sweep.
    parser.add_argument('--sync', action='store_true', 
                        help="Run IMAP reply detection and update Google Sheets with reply status.")
    parser.add_argument('--send', action='store_true', 
                        help="Execute daily sequencing and send pending emails via Resend.")
                        
    args = parser.parse_args()
    
    # 2. Guard: at least one flag must be provided
    if not args.sync and not args.send:
        print("[WARNING] No action specified. Use --sync, --send, or both.")
        parser.print_help()
        sys.exit(1)
        
    # 3. Logic Routing — sync runs FIRST so we catch replies before sending.
    if args.sync:
        print("\n--- INITIATING IMAP REPLY SYNC ---")
        imap_sync.sync_replies()
    
    if args.send:
        print("\n--- INITIATING DAILY CLOUD CAMPAIGN DISPATCH ---")
        sender.execute_daily_sending()

    print("\n====================================")
    print("  CAMPAIGN MANAGER: ALL JOBS DONE   ")
    print("====================================")

if __name__ == "__main__":
    main()
