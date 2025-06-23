from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.models.schemas import RequirementsInput, UXSpecification, AIModel
from app.services.llm_service import LLMService
from app.services.ux_generator import UXGenerator
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

llm_service = LLMService()
ux_generator = UXGenerator(llm_service)

@router.post("/generate-design", response_model=UXSpecification)
async def generate_design(requirements: RequirementsInput, background_tasks: BackgroundTasks):
    """
    Generate comprehensive UX specifications from requirements
    Using multi-role AI analysis (Designer, BA, Architect)
    """
    try:
        logger.info(f"Generating UX design for purpose: {requirements.purpose}")
        
        # Generate UX specifications using multi-role AI analysis
        ux_specs = await ux_generator.generate_specifications(requirements)
        
        # Add background task for analytics/logging
        background_tasks.add_task(log_generation_event, requirements.purpose, "ux_specs")
        
        return ux_specs
        
    except Exception as e:
        logger.error(f"Error generating UX design: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to generate UX specifications: {str(e)}"
        )

@router.post("/generate-design-with-model")
async def generate_design_with_model(
    requirements: RequirementsInput, 
    model: AIModel = AIModel.LLAMA3_70B,
    background_tasks: BackgroundTasks = None
):
    """Generate UX specifications with specific AI model"""
    try:
        logger.info(f"Generating UX design with model {model}")
        
        ux_specs = await ux_generator.generate_specifications(
            requirements, 
            preferred_model=model
        )
        
        if background_tasks:
            background_tasks.add_task(log_generation_event, requirements.purpose, f"ux_specs_{model}")
            
        return ux_specs
        
    except Exception as e:
        logger.error(f"Error generating UX design with model {model}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate UX specifications with {model}: {str(e)}"
        )

async def log_generation_event(purpose: str, event_type: str):
    """Background task to log generation events"""
    try:
        # Here you could log to analytics service, database, etc.
        logger.info(f"Generation event: {event_type} for purpose: {purpose}")
    except Exception as e:
        logger.error(f"Failed to log generation event: {str(e)}") 