from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel
from app.models.schemas import RequirementsInput
from app.services.requirements_processor import RequirementsProcessor
from app.services.llm_service import LLMService

router = APIRouter()
requirements_processor = RequirementsProcessor()
llm_service = LLMService()

class AppIdeaInput(BaseModel):
    app_idea: str

@router.post("/process-requirements")
async def process_requirements(requirements: RequirementsInput):
    """Process and validate user requirements"""
    try:
        processed = await requirements_processor.process(requirements)
        return {
            "status": "processed",
            "data": processed,
            "suggestions": await requirements_processor.get_suggestions(requirements)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/validate-requirements")
async def validate_requirements(requirements: RequirementsInput):
    """Validate requirements completeness"""
    try:
        validation_result = await requirements_processor.validate(requirements)
        return validation_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-questions")
async def generate_questions(request: Request):
    data = await request.json()
    print("[DEBUG] Raw body:", data)
    app_idea = data.get("app_idea")
    print("[DEBUG] app_idea:", app_idea)
    try:
        questions = await llm_service.generate_dynamic_questions(app_idea)
        return {
            "status": "success",
            "app_idea": app_idea,
            "questions": questions
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 