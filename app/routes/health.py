from fastapi import APIRouter
from datetime import datetime
from app.models.schemas import HealthResponse

router = APIRouter()

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        version="1.0.0",
        ai_services={
            "llm_service": "available",
            "vision_service": "available",
            "huggingface": "available",
            "replicate": "available"
        }
    ) 