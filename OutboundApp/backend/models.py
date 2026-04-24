from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime, timezone

class Lead(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = Field(default=None, index=True)
    title: Optional[str] = None
    company_name: Optional[str] = None
    linkedin_url: Optional[str] = Field(default=None, index=True)
    website: Optional[str] = None
    source_file: str
    status: str = Field(default="pending") # pending, verified, catch-all, bounced, replied, etc.
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
