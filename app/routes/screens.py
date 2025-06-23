from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime

from app.services.llm_service import LLMService
from app.services.vision_service import VisionService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()
vision_service = VisionService()

# Define schemas locally since they don't exist in the main schemas file
class ScreenSpec(BaseModel):
    name: str
    description: str
    elements: List[str]

class ScreenGenerationRequest(BaseModel):
    screens: List[ScreenSpec]
    ui_standards: str = "modern, clean, accessible"
    generation_mode: str = "hybrid"  # "html", "image", or "hybrid"
    image_style: Optional[str] = "clean wireframe"

class Element(BaseModel):
    id: str
    type: str
    content: str
    position: Dict[str, int]
    styles: Dict[str, str]

class Screen(BaseModel):
    id: str
    name: str
    description: str
    html_layout: str
    elements: List[Element]
    generated_at: datetime
    mockup_url: Optional[str] = None
    generation_method: Optional[str] = None

class ScreenGenerationResponse(BaseModel):
    screens: List[Screen]
    total_screens: int
    generated_at: datetime
    generation_method: str
    mockup_images: List[Dict[str, str]] = []

class HTMLScreenRequest(BaseModel):
    screen_name: str
    description: str
    elements: List[str]
    ui_standards: str
    color_scheme: Optional[str] = "professional"
    layout_type: Optional[str] = "responsive"

class HTMLScreenResponse(BaseModel):
    screen_id: str
    name: str
    description: str
    html_layout: str
    elements: List[Element]
    css_styles: str
    generated_at: datetime

@router.post("/generate-screens", response_model=ScreenGenerationResponse)
async def generate_screens(request: ScreenGenerationRequest):
    """
    Generate HTML/CSS screen layouts and optionally AI-generated mockup images.
    Supports three modes:
    - html: Generate only HTML/CSS layouts
    - image: Generate only AI mockup images
    - hybrid: Generate both HTML and images
    """
    try:
        logger.info(f"Generating screens in {request.generation_mode} mode for {len(request.screens)} screens")
        
        llm_service = LLMService()
        generated_screens = []
        
        # Generate HTML layouts if requested
        if request.generation_mode in ["html", "hybrid"]:
            for screen_spec in request.screens:
                try:
                    # Generate HTML layout using LLM
                    html_layout = await generate_html_layout(
                        llm_service, 
                        screen_spec.name, 
                        screen_spec.description,
                        screen_spec.elements,
                        request.ui_standards
                    )
                    
                    # Create editable elements list
                    editable_elements = create_editable_elements(screen_spec.elements)
                    
                    # Create screen object
                    screen = Screen(
                        id=f"screen_{screen_spec.name.lower().replace(' ', '_')}",
                        name=screen_spec.name,
                        description=screen_spec.description,
                        html_layout=html_layout,
                        elements=editable_elements,
                        generated_at=datetime.now()
                    )
                    
                    generated_screens.append(screen)
                    logger.info(f"Generated HTML layout for screen: {screen_spec.name}")
                    
                except Exception as e:
                    logger.error(f"Failed to generate HTML for screen {screen_spec.name}: {str(e)}")
                    continue
        
        # Generate AI mockup images if requested
        mockup_images = []
        if request.generation_mode in ["image", "hybrid"]:
            try:
                # Convert screen specs to format expected by vision service
                screen_dicts = [
                    {
                        "id": f"screen_{spec.name.lower().replace(' ', '_')}",
                        "name": spec.name,
                        "description": spec.description,
                        "elements": spec.elements
                    }
                    for spec in request.screens
                ]
                
                # Generate mockup images using vision service
                mockup_images = await vision_service.generate_mockup_images(
                    screen_dicts,
                    style=request.image_style
                )
                
                # If in image-only mode, convert to screen format
                if request.generation_mode == "image":
                    for mockup in mockup_images:
                        screen = Screen(
                            id=mockup["screen_id"],
                            name=mockup["screen_name"],
                            description=mockup["description"],
                            html_layout=mockup.get("html_content", ""),
                            elements=create_editable_elements(mockup["elements"]),
                            generated_at=datetime.now(),
                            mockup_url=mockup.get("image_url"),
                            generation_method=mockup.get("generation_method", "image")
                        )
                        generated_screens.append(screen)
                
                # If in hybrid mode, attach image URLs to existing screens
                elif request.generation_mode == "hybrid":
                    for i, mockup in enumerate(mockup_images):
                        if i < len(generated_screens):
                            generated_screens[i].mockup_url = mockup.get("image_url")
                            generated_screens[i].generation_method = "hybrid"
                
                logger.info(f"Generated {len(mockup_images)} mockup images")
                
            except Exception as e:
                logger.error(f"Failed to generate mockup images: {str(e)}")
                # Continue with HTML-only screens if image generation fails
        
        if not generated_screens:
            raise HTTPException(status_code=500, detail="Failed to generate any screens")
        
        return ScreenGenerationResponse(
            screens=generated_screens,
            total_screens=len(generated_screens),
            generated_at=datetime.now(),
            generation_method=request.generation_mode,
            mockup_images=mockup_images if request.generation_mode in ["image", "hybrid"] else []
        )
        
    except Exception as e:
        logger.error(f"Screen generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Screen generation failed: {str(e)}")

async def generate_html_layout(llm_service: LLMService, screen_name: str, description: str, elements: List[str], ui_standards: str) -> str:
    """
    Generate HTML/CSS layout using LLM instead of image generation.
    """
    prompt = f"""
    Generate a complete HTML layout for a screen called "{screen_name}".
    
    Description: {description}
    Required Elements: {', '.join(elements)}
    UI Standards: {ui_standards}
    
    Requirements:
    1. Create a complete HTML layout with inline CSS styles
    2. Use modern, professional design principles
    3. Make it responsive and accessible
    4. Include proper semantic HTML structure
    5. Use a clean, modern color scheme
    6. Ensure proper spacing and typography
    7. Make elements easily identifiable for editing
    8. Include proper CSS Grid/Flexbox layouts
    
    Return ONLY the HTML code with inline styles, no explanations.
    The HTML should be production-ready and pixel-perfect.
    """
    
    try:
        response = await llm_service.generate_html_layout(prompt)
        return response.strip()
    except Exception as e:
        logger.error(f"LLM HTML generation failed: {str(e)}")
        # Return a fallback HTML layout
        return generate_fallback_html(screen_name, description, elements)

def generate_fallback_html(screen_name: str, description: str, elements: List[str]) -> str:
    """
    Generate a basic fallback HTML layout when LLM fails.
    """
    return f"""
    <div class="screen-container" style="width: 100%; min-height: 100vh; background: #f8fafc; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
        <header style="background: #3b82f6; color: white; padding: 1rem 2rem; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <h1 style="margin: 0; font-size: 1.5rem; font-weight: 600;">{screen_name}</h1>
        </header>
        
        <main style="padding: 2rem; max-width: 1200px; margin: 0 auto;">
            <div style="background: white; border-radius: 8px; padding: 2rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 2rem;">
                <h2 style="margin: 0 0 1rem 0; color: #1f2937; font-size: 1.25rem;">{description}</h2>
                <div style="display: grid; gap: 1rem; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));">
                    {generate_element_html(elements)}
                </div>
            </div>
        </main>
    </div>
    """

def generate_element_html(elements: List[str]) -> str:
    """
    Generate HTML for individual elements.
    """
    html_parts = []
    
    for element in elements:
        element_lower = element.lower()
        
        if 'button' in element_lower:
            html_parts.append(f"""
                <button style="background: #10b981; color: white; border: none; border-radius: 6px; padding: 0.75rem 1.5rem; font-weight: 500; cursor: pointer; transition: all 0.2s;">
                    {element}
                </button>
            """)
        elif 'input' in element_lower or 'form' in element_lower:
            html_parts.append(f"""
                <div style="margin-bottom: 1rem;">
                    <label style="display: block; margin-bottom: 0.5rem; font-weight: 500; color: #374151;">{element}</label>
                    <input type="text" placeholder="Enter {element.lower()}" style="width: 100%; padding: 0.75rem; border: 1px solid #d1d5db; border-radius: 6px; font-size: 1rem;">
                </div>
            """)
        elif 'text' in element_lower or 'paragraph' in element_lower:
            html_parts.append(f"""
                <p style="color: #6b7280; line-height: 1.6; margin-bottom: 1rem;">
                    {element}: Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
                </p>
            """)
        else:
            html_parts.append(f"""
                <div style="background: #f3f4f6; border: 1px solid #e5e7eb; border-radius: 6px; padding: 1rem; margin-bottom: 1rem;">
                    <h3 style="margin: 0 0 0.5rem 0; color: #111827; font-size: 1.125rem;">{element}</h3>
                    <p style="margin: 0; color: #6b7280; font-size: 0.875rem;">Placeholder content for {element}</p>
                </div>
            """)
    
    return ''.join(html_parts)

def create_editable_elements(elements: List[str]) -> List[Element]:
    """
    Create editable element objects from screen elements.
    """
    editable_elements = []
    
    for i, element in enumerate(elements):
        element_type = determine_element_type(element)
        
        editable_element = Element(
            id=f"element_{i}_{element.lower().replace(' ', '_')}",
            type=element_type,
            content=element,
            position={"x": 50 + (i * 20), "y": 100 + (i * 80)},
            styles={
                "width": "auto",
                "height": "auto",
                "backgroundColor": "#ffffff" if element_type != "button" else "#3b82f6",
                "color": "#000000" if element_type != "button" else "#ffffff",
                "padding": "8px 16px",
                "borderRadius": "6px",
                "border": "1px solid #e5e7eb"
            }
        )
        
        editable_elements.append(editable_element)
    
    return editable_elements

def determine_element_type(element: str) -> str:
    """
    Determine the UI element type based on the element name.
    """
    element_lower = element.lower()
    
    if any(keyword in element_lower for keyword in ['button', 'btn', 'submit', 'action']):
        return "button"
    elif any(keyword in element_lower for keyword in ['input', 'field', 'form', 'text']):
        return "input"
    elif any(keyword in element_lower for keyword in ['image', 'img', 'photo', 'picture']):
        return "image"
    elif any(keyword in element_lower for keyword in ['header', 'title', 'heading']):
        return "header"
    elif any(keyword in element_lower for keyword in ['nav', 'menu', 'navigation']):
        return "navigation"
    elif any(keyword in element_lower for keyword in ['card', 'container', 'box']):
        return "container"
    else:
        return "text"

@router.get("/screens/{screen_id}/html")
async def get_screen_html(screen_id: str):
    """
    Get the HTML layout for a specific screen.
    """
    try:
        # This would typically fetch from a database
        # For now, return a simple response
        return {"screen_id": screen_id, "html": "<div>Screen HTML would be here</div>"}
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Screen not found: {str(e)}")

@router.post("/screens/{screen_id}/update-element")
async def update_screen_element(screen_id: str, element_updates: Dict[str, Any]):
    """
    Update a specific element in a screen.
    """
    try:
        # This would typically update the element in a database
        # For now, return a simple response
        return {"screen_id": screen_id, "updated": True, "changes": element_updates}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update element: {str(e)}")

@router.post("/generate-image-variations")
async def generate_image_variations(
    screen_id: str,
    screen_data: Dict[str, Any],
    styles: List[str] = ["clean wireframe", "modern ui", "dark mode"]
):
    """Generate multiple style variations of a screen mockup"""
    try:
        variations = await vision_service.generate_style_variations(
            screen_data,
            styles
        )
        
        return {
            "screen_id": screen_id,
            "variations": variations,
            "total_variations": len(variations)
        }
        
    except Exception as e:
        logger.error(f"Failed to generate variations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 