import os
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import math

from pipeline.sheets_crm import get_all_leads_as_df
from pipeline.imap_sync import sync_replies
from pipeline.sender import execute_daily_sending
from pipeline.cleaner import merge_and_clean_new_leads

app = FastAPI(title="Outbound Automation API")

# Allow all origins for the local dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/leads")
def get_leads():
    """
    Fetches all leads from Google Sheets.
    """
    try:
        df = get_all_leads_as_df()
        
        # Replace NaNs with empty strings to make it JSON serializable
        df = df.fillna("")
        
        # Convert to a list of dictionaries
        leads = df.to_dict(orient="records")
        return {"status": "success", "leads": leads}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/sync")
def run_sync(background_tasks: BackgroundTasks):
    """
    Triggers the IMAP sync script.
    """
    try:
        # Run in background to avoid blocking the HTTP response
        background_tasks.add_task(sync_replies)
        return {"status": "success", "message": "IMAP sync started."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/send")
def run_send(background_tasks: BackgroundTasks):
    """
    Triggers the daily sending sequence.
    """
    try:
        # Run in background to avoid blocking the HTTP response
        background_tasks.add_task(execute_daily_sending)
        return {"status": "success", "message": "Daily sending sequence started."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/clean")
def run_clean():
    """
    Merges, cleans, and ingests raw Apify CSV exports from the Leads/ folder
    into the master RECOVERED_LEADS.csv. Processed files are archived.
    
    This runs synchronously because it is a fast local I/O operation —
    no external API calls, no network latency.
    """
    try:
        result = merge_and_clean_new_leads()
        return result
    except Exception as e:
        return {"status": "error", "message": str(e), "new_leads": 0}

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8001, reload=True)
