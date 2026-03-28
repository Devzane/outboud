import concurrent.futures
import pandas as pd
from file_handler import load_leads, save_leads
from scraper import get_html, find_subpages, extract_text
from parser import extract_email, extract_name, extract_summary
import signal
import sys
import os

def signal_handler(sig, frame):
    print('\nExecution interrupted by user.')
    os._exit(0)
signal.signal(signal.SIGINT, signal_handler)

def process_row(index, website):
    result = {'index': index, 'email': None, 'name': None, 'summary': None}
    
    if pd.isna(website) or str(website).strip().lower() in ['n/a', 'nan', '']:
        return result
        
    print(f"[{index}] Processing {website}...")
    html = get_html(website, timeout=10)
    
    if html:
        base_text = extract_text(html)
        subpages = find_subpages(html, website)
        
        all_text = base_text
        for page in subpages[:3]:
            sub_html = get_html(page, timeout=7)
            sub_text = extract_text(sub_html)
            all_text += " " + sub_text
            
        result['email'] = extract_email(all_text)
        result['name'] = extract_name(all_text)
        result['summary'] = extract_summary(all_text)
        
    return result

def main():
    input_file = '../Apify_Lead_Scraper/Leads/smb_leads.csv'
    output_file = '../Apify_Lead_Scraper/Leads/master_enriched_leads.csv'
    
    print("Loading leads...")
    df = load_leads(input_file)
    if df.empty:
        print("No data to process. Exiting.")
        return
        
    emails = [None] * len(df)
    names = [None] * len(df)
    summaries = [None] * len(df)
    
    print(f"Starting pipeline on {len(df)} leads...")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(process_row, i, row.get('Website', '')): i for i, row in df.iterrows()}
        
        for future in concurrent.futures.as_completed(futures):
            try:
                res = future.result()
                i = res['index']
                emails[i] = res['email']
                names[i] = res['name']
                summaries[i] = res['summary']
                
                # Dynamic terminal feedback
                success_keys = sum(1 for k in ['email', 'name', 'summary'] if res[k])
                if success_keys > 0:
                    print(f"[{i}] Success: Found {success_keys} data points.")
            except Exception as e:
                print(f"Row generated an exception: {e}")
                
    df['Owner_Name'] = names
    df['Email'] = emails
    df['Company_Summary'] = summaries
    
    print("Saving enriched leads...")
    save_leads(df, output_file)
    print("Pipeline complete.")

if __name__ == '__main__':
    main()
