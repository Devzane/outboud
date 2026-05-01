import os
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import math

from pipeline.sheets_crm import get_all_leads_as_df, update_sheet_from_df
from pipeline.imap_sync import sync_replies
from pipeline.sender import execute_daily_sending
from pipeline.cleaner import merge_and_clean_new_leads
from pipeline.verifier import execute_cascading_verification


# =============================================================================
# Pydantic request schemas for endpoints that accept a JSON body.
# =============================================================================
class VerifyRequest(BaseModel):
    """POST /api/verify expects {"mode": "quick" | "power"}."""
    mode: str

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


# =============================================================================
# VERIFICATION ENDPOINT
# =============================================================================
# This is a long-running operation (~0.5s per lead × N leads). We dispatch it
# as a background task so the HTTP response returns immediately. The user
# clicks "Refresh Data" on the dashboard to see updated verification results.
# =============================================================================
def _run_verification_pipeline(mode: str):
    """
    Background task wrapper: fetches leads, runs cascading verification,
    and pushes verified results back to Google Sheets.
    """
    import pandas as pd

    try:
        df = get_all_leads_as_df()
        if df.empty:
            print("[VERIFY] No leads to verify.")
            return

        # Run the cascading verification engine with the selected mode.
        result = execute_cascading_verification(df, mode=mode)

        # Re-read the verified CSV and push results back to Google Sheets
        # so the dashboard's /api/leads endpoint returns fresh data.
        output_path = result.get("output_file", "")
        if output_path and os.path.exists(output_path):
            verified_df = pd.read_csv(output_path)
            update_sheet_from_df(verified_df)
            print(f"[VERIFY] Pushed {len(verified_df)} verified leads back to Sheets.")
    except Exception as e:
        print(f"[VERIFY] Pipeline error: {e}")


@app.post("/api/verify")
def run_verify(request: VerifyRequest, background_tasks: BackgroundTasks):
    """
    Triggers cascading email verification using the Reoon API.
    Accepts {"mode": "quick"} or {"mode": "power"} in the request body.

    The verification runs as a background task. Poll /api/leads or click
    'Refresh Data' on the dashboard to see updated results.
    """
    # Validate the mode value before queuing the task.
    valid_modes = ["quick", "power"]
    if request.mode not in valid_modes:
        return {
            "status": "error",
            "message": f"Invalid mode '{request.mode}'. Must be one of: {valid_modes}",
        }

    try:
        background_tasks.add_task(_run_verification_pipeline, request.mode)
        return {
            "status": "success",
            "message": f"Cascading verification started in {request.mode.upper()} mode.",
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8001, reload=True)
