 # tux-backend/app/routes/analytics.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

router = APIRouter()

class AnalyticsData(BaseModel):
    event: str
    user_id: Optional[str] = None
    metadata: Optional[dict] = None

@router.post("/track")
async def track_event(analytics_data: AnalyticsData):
    # Log the analytics event
    with open("analytics.log", "a") as log_file:
        log_file.write(f"{datetime.now()}: {analytics_data.event} - User: {analytics_data.user_id} - Metadata: {analytics_data.metadata}\n")
    return {"message": "Event tracked successfully"}

@router.get("/events")
async def get_events():
    # Read and return the analytics events
    try:
        with open("analytics.log", "r") as log_file:
            events = log_file.readlines()
        return {"events": events}
    except FileNotFoundError:
        return {"events": []}
