from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select
from contextlib import asynccontextmanager
import pandas as pd
import io

from database import create_db_and_tables, get_session
from models import Lead

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(title="Outbound Engine API", lifespan=lifespan)

# Allow Next.js frontend to access the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Outbound Engine API is running"}

@app.post("/api/upload-leads")
async def upload_leads(file: UploadFile = File(...), session: Session = Depends(get_session)):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed.")
    
    contents = await file.read()
    try:
        df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error parsing CSV: {e}")
        
    # Standardize column names slightly (lowercase, strip whitespace)
    df.columns = [str(c).strip().lower() for c in df.columns]
    
    # Map possible Apify column names to our schema
    # Add more variations as needed
    col_mapping = {
        'first name': 'first_name',
        'firstname': 'first_name',
        'last name': 'last_name',
        'lastname': 'last_name',
        'email address': 'email',
        'e-mail': 'email',
        'company': 'company_name',
        'company name': 'company_name',
        'job title': 'title',
        'linkedin': 'linkedin_url',
        'linkedin url': 'linkedin_url',
        'linkedin profile': 'linkedin_url'
    }
    df = df.rename(columns=col_mapping)
    
    leads_added = 0
    leads_skipped = 0
    
    for _, row in df.iterrows():
        # Get essential fields
        email = str(row.get('email', '')).strip()
        linkedin_url = str(row.get('linkedin_url', '')).strip()
        
        # Deduplication check
        if email and email.lower() != 'nan':
            existing = session.exec(select(Lead).where(Lead.email == email)).first()
            if existing:
                leads_skipped += 1
                continue
                
        if linkedin_url and linkedin_url.lower() != 'nan':
            existing = session.exec(select(Lead).where(Lead.linkedin_url == linkedin_url)).first()
            if existing:
                leads_skipped += 1
                continue
                
        # Create Lead
        new_lead = Lead(
            first_name=str(row.get('first_name', '')).strip() if pd.notna(row.get('first_name')) else None,
            last_name=str(row.get('last_name', '')).strip() if pd.notna(row.get('last_name')) else None,
            email=email if email and email.lower() != 'nan' else None,
            title=str(row.get('title', '')).strip() if pd.notna(row.get('title')) else None,
            company_name=str(row.get('company_name', '')).strip() if pd.notna(row.get('company_name')) else None,
            linkedin_url=linkedin_url if linkedin_url and linkedin_url.lower() != 'nan' else None,
            website=str(row.get('website', '')).strip() if pd.notna(row.get('website')) else None,
            source_file=file.filename
        )
        session.add(new_lead)
        leads_added += 1
        
    session.commit()
    
    return {
        "message": "Upload successful",
        "file_name": file.filename,
        "leads_added": leads_added,
        "leads_skipped_duplicates": leads_skipped
    }

@app.get("/api/leads")
def get_leads(skip: int = 0, limit: int = 100, session: Session = Depends(get_session)):
    leads = session.exec(select(Lead).offset(skip).limit(limit)).all()
    total = session.exec(select(Lead)).all() # In a real app use count
    return {"data": leads, "total": len(total)}
