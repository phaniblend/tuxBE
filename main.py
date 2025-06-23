# Update for main.py - Enhanced question generation endpoint

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging

# Import the enhanced Claude service
from app.services.claude_service import claude_service

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:5175", "http://127.0.0.1:5175"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QuestionRequest(BaseModel):
    app_idea: str

class QuestionResponse(BaseModel):
    questions: List[Dict[str, Any]]
    metadata: Dict[str, Any]

@app.post("/api/generate-questions", response_model=QuestionResponse)
async def generate_questions(request: QuestionRequest):
    """Generate comprehensive UX design questions"""
    try:
        logger.info(f"Generating questions for app idea: {request.app_idea}")
        
        # Generate questions using enhanced Claude service
        questions = claude_service.generate_dynamic_questions(request.app_idea)
        
        # Ensure we have substantial questions
        if len(questions) < 10:
            logger.warning(f"Only generated {len(questions)} questions, attempting to generate more...")
            # You could retry here or merge with additional questions
        
        # Add metadata about the questions
        metadata = {
            "total_questions": len(questions),
            "categories": list(set(q.get('category', 'general') for q in questions)),
            "question_types": list(set(q.get('type', 'text') for q in questions)),
            "app_type": _detect_app_type(request.app_idea)
        }
        
        logger.info(f"Generated {len(questions)} questions across {len(metadata['categories'])} categories")
        
        return QuestionResponse(
            questions=questions,
            metadata=metadata
        )
        
    except Exception as e:
        logger.error(f"Error generating questions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def _detect_app_type(app_idea: str) -> str:
    """Detect the type of app from the description"""
    app_idea_lower = app_idea.lower()
    
    if any(word in app_idea_lower for word in ['shop', 'store', 'commerce', 'market']):
        return "e-commerce"
    elif any(word in app_idea_lower for word in ['social', 'community', 'network']):
        return "social"
    elif any(word in app_idea_lower for word in ['learn', 'education', 'course']):
        return "education"
    elif any(word in app_idea_lower for word in ['health', 'fitness', 'medical']):
        return "health"
    elif any(word in app_idea_lower for word in ['game', 'play', 'gaming']):
        return "gaming"
    elif any(word in app_idea_lower for word in ['productivity', 'task', 'manage']):
        return "productivity"
    else:
        return "general"

# Test endpoint to verify question quality
@app.get("/api/test-questions/{app_type}")
async def test_questions(app_type: str):
    """Test question generation for different app types"""
    
    test_ideas = {
        "library": "A community library app for sharing books",
        "fitness": "A personal fitness tracking app with workout plans",
        "marketplace": "An online marketplace for handmade crafts",
        "education": "An online learning platform for coding",
        "social": "A social network for pet owners"
    }
    
    app_idea = test_ideas.get(app_type, "A mobile app")
    
    try:
        questions = claude_service.generate_dynamic_questions(app_idea)
        return {
            "app_idea": app_idea,
            "question_count": len(questions),
            "categories": list(set(q.get('category', 'general') for q in questions)),
            "sample_questions": questions[:3] if questions else []
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)