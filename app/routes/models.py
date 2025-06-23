from fastapi import APIRouter, HTTPException
from app.models.schemas import AIModel, VisionModel
import os
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/models")
async def get_available_models():
    """Get available AI models and their status"""
    try:
        # Check which API keys are configured
        hf_available = bool(os.getenv("HUGGINGFACE_API_KEY"))
        together_available = bool(os.getenv("TOGETHER_API_KEY"))
        replicate_available = bool(os.getenv("REPLICATE_API_TOKEN"))
        
        available_llm_models = []
        available_vision_models = []
        
        # LLM Models
        if together_available:
            available_llm_models.extend([
                {"name": "Llama 3 70B", "id": AIModel.LLAMA3_70B, "provider": "Together.ai", "status": "available"},
                {"name": "Llama 3 8B", "id": AIModel.LLAMA3_8B, "provider": "Together.ai", "status": "available"}
            ])
        
        if hf_available:
            available_llm_models.extend([
                {"name": "Mistral 7B", "id": AIModel.MISTRAL_7B, "provider": "HuggingFace", "status": "available"},
                {"name": "Mistral 8x7B", "id": AIModel.MISTRAL_8X7B, "provider": "HuggingFace", "status": "available"},
                {"name": "Phi-3 Mini", "id": AIModel.PHI3_MINI, "provider": "HuggingFace", "status": "available"},
                {"name": "Qwen2 72B", "id": AIModel.QWEN2_72B, "provider": "HuggingFace", "status": "available"}
            ])
        
        # Vision Models
        if replicate_available:
            available_vision_models.extend([
                {"name": "Stable Diffusion XL", "id": VisionModel.STABLE_DIFFUSION_XL, "provider": "Replicate", "status": "available"},
                {"name": "Playground v2", "id": VisionModel.PLAYGROUND_V2, "provider": "Replicate", "status": "available"}
            ])
        
        # If no API keys configured, show demo models
        if not any([hf_available, together_available, replicate_available]):
            available_llm_models = [
                {"name": "Demo LLM", "id": "demo-llm", "provider": "Demo", "status": "demo_mode"}
            ]
            available_vision_models = [
                {"name": "Demo Vision", "id": "demo-vision", "provider": "Demo", "status": "demo_mode"}
            ]
        
        return {
            "llm_models": available_llm_models,
            "vision_models": available_vision_models,
            "api_keys_configured": {
                "huggingface": hf_available,
                "together": together_available,
                "replicate": replicate_available
            },
            "recommended_llm": AIModel.LLAMA3_70B if together_available else AIModel.MISTRAL_7B if hf_available else "demo-llm",
            "recommended_vision": VisionModel.STABLE_DIFFUSION_XL if replicate_available else "demo-vision"
        }
        
    except Exception as e:
        logger.error(f"Error getting available models: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 