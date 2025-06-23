import asyncio
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.llm_service import LLMService
from app.services.ux_generator import UXGenerator
from app.models.schemas import RequirementsInput

async def test_ux_generation():
    # Initialize services
    llm_service = LLMService()
    ux_generator = UXGenerator(llm_service)
    
    # Test requirements
    requirements = RequirementsInput(
        purpose="gaming app",
        audience=["Casual gamers", "Teenagers"],
        goals=["Entertainment", "Social interaction"],
        useCases=["Play games", "Compete with friends", "Track progress"]
    )
    
    try:
        print("Testing UX generation...")
        result = await ux_generator.generate_specifications(requirements)
        print(f"Success! Generated specs with {len(result.screens)} screens")
        print(f"First screen: {result.screens[0].name if result.screens else 'No screens'}")
    except Exception as e:
        print(f"Error: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()

asyncio.run(test_ux_generation())