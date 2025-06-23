import os
import httpx
import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import replicate

logger = logging.getLogger(__name__)

class VisionService:
    """
    Vision model service for generating UI mockups using Stable Diffusion XL
    Integrates with Replicate.com API for serverless image generation
    """
    
    def __init__(self):
        self.replicate_token = os.getenv("REPLICATE_API_TOKEN")
        self.use_replicate = bool(self.replicate_token)
        
        if self.use_replicate:
            # Initialize Replicate client
            os.environ["REPLICATE_API_TOKEN"] = self.replicate_token
            logger.info("Replicate API initialized for image generation")
        else:
            logger.warning("No Replicate API token found - falling back to HTML generation only")
    
    async def generate_mockup_images(
        self, 
        screens: List[Dict[str, Any]], 
        style: str = "clean wireframe"
    ) -> List[Dict[str, Any]]:
        """
        Generate UI mockup images for multiple screens
        
        Args:
            screens: List of screen specifications
            style: Visual style for the mockups
            
        Returns:
            List of mockup data with image URLs
        """
        if not self.use_replicate:
            logger.info("Replicate not configured - returning HTML-only mockups")
            return self._generate_html_fallback(screens)
        
        mockups = []
        
        # Process screens in parallel for better performance
        tasks = []
        for screen in screens:
            task = self._generate_single_mockup(screen, style)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Failed to generate mockup for screen {i}: {str(result)}")
                # Use HTML fallback for failed images
                mockups.append(self._generate_single_html_fallback(screens[i]))
            else:
                mockups.append(result)
        
        return mockups
    
    async def _generate_single_mockup(
        self, 
        screen: Dict[str, Any], 
        style: str
    ) -> Dict[str, Any]:
        """Generate a single mockup image using Stable Diffusion XL"""
        try:
            # Build optimized prompt for UI/UX mockup generation
            prompt = self._build_mockup_prompt(screen, style)
            
            # Use Stable Diffusion XL via Replicate
            model = replicate.models.get("stability-ai/sdxl")
            version = model.versions.get("39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b")
            
            # Generate image with UI-optimized parameters
            output = await asyncio.to_thread(
                version.predict,
                prompt=prompt,
                negative_prompt="blurry, low quality, distorted, unrealistic, photograph, 3d render",
                width=1024,
                height=1024,
                num_outputs=1,
                scheduler="K_EULER",
                num_inference_steps=25,
                guidance_scale=7.5,
                prompt_strength=0.8,
                refine="expert_ensemble_refiner",
                high_noise_frac=0.8
            )
            
            image_url = output[0] if isinstance(output, list) else output
            
            return {
                "screen_id": screen.get("id", screen.get("name", "").lower().replace(" ", "_")),
                "screen_name": screen.get("name", "Untitled Screen"),
                "description": screen.get("description", ""),
                "image_url": image_url,
                "image_format": "png",
                "generation_method": "stable_diffusion_xl",
                "prompt_used": prompt,
                "generated_at": datetime.now().isoformat(),
                "elements": screen.get("elements", [])
            }
            
        except Exception as e:
            logger.error(f"Error generating mockup with SDXL: {str(e)}")
            raise
    
    def _build_mockup_prompt(self, screen: Dict[str, Any], style: str) -> str:
        """Build an optimized prompt for UI mockup generation"""
        
        screen_name = screen.get("name", "App Screen")
        description = screen.get("description", "")
        elements = screen.get("elements", [])
        
        # Base prompt structure
        prompt_parts = [
            f"{style} UI mockup design",
            f"screen name: {screen_name}",
            description
        ]
        
        # Add UI elements
        if elements:
            elements_str = ", ".join(elements[:10])  # Limit to avoid prompt overflow
            prompt_parts.append(f"UI elements: {elements_str}")
        
        # Style modifiers for better UI generation
        style_modifiers = {
            "clean wireframe": "minimal black and white wireframe, simple lines, no colors, schematic",
            "modern ui": "modern flat design, material design, clean interface, professional",
            "colorful mockup": "vibrant colors, modern UI design, clean layout, professional app interface",
            "dark mode": "dark theme UI, modern interface, high contrast, elegant design",
            "mobile app": "mobile app interface, iOS/Android style, touch-friendly, responsive"
        }
        
        if style.lower() in style_modifiers:
            prompt_parts.append(style_modifiers[style.lower()])
        
        # Technical specifications
        prompt_parts.extend([
            "high quality UI design",
            "professional mockup",
            "clean layout",
            "proper spacing and alignment",
            "consistent design system"
        ])
        
        return ", ".join(prompt_parts)
    
    async def generate_style_variations(
        self, 
        screen: Dict[str, Any], 
        styles: List[str]
    ) -> List[Dict[str, Any]]:
        """Generate multiple style variations of the same screen"""
        variations = []
        
        for style in styles:
            try:
                mockup = await self._generate_single_mockup(screen, style)
                mockup["style"] = style
                variations.append(mockup)
            except Exception as e:
                logger.error(f"Failed to generate {style} variation: {str(e)}")
                continue
        
        return variations
    
    def _generate_html_fallback(self, screens: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate HTML-based mockups as fallback"""
        mockups = []
        
        for screen in screens:
            mockups.append(self._generate_single_html_fallback(screen))
        
        return mockups
    
    def _generate_single_html_fallback(self, screen: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a single HTML mockup as fallback"""
        return {
            "screen_id": screen.get("id", screen.get("name", "").lower().replace(" ", "_")),
            "screen_name": screen.get("name", "Untitled Screen"),
            "description": screen.get("description", ""),
            "html_content": self._create_html_mockup(screen),
            "generation_method": "html_fallback",
            "generated_at": datetime.now().isoformat(),
            "elements": screen.get("elements", [])
        }
    
    def _create_html_mockup(self, screen: Dict[str, Any]) -> str:
        """Create a basic HTML mockup"""
        elements_html = ""
        for element in screen.get("elements", []):
            elements_html += f'<div class="element">{element}</div>\n'
        
        return f"""
        <div class="mockup-container">
            <h2>{screen.get("name", "Screen")}</h2>
            <p>{screen.get("description", "")}</p>
            <div class="elements">
                {elements_html}
            </div>
        </div>
        """
    
    async def enhance_with_playground_v2(
        self, 
        screen: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Alternative: Use Playground v2 model for enhanced UI generation
        This model is specifically trained for design work
        """
        try:
            if not self.use_replicate:
                return None
            
            # Playground v2 is optimized for design work
            model = replicate.models.get("playgroundai/playground-v2-1024px-aesthetic")
            version = model.versions.get("42fe626e41cc811eaf02c94b892774839268ce1994ea778eba97103fe1ef51b8")
            
            prompt = self._build_mockup_prompt(screen, "modern ui design")
            
            output = await asyncio.to_thread(
                version.predict,
                prompt=prompt,
                width=1024,
                height=1024,
                scheduler="K_EULER_ANCESTRAL",
                guidance_scale=3,
                num_inference_steps=50,
                negative_prompt="low quality, blurry, distorted"
            )
            
            return {
                "screen_id": screen.get("id"),
                "image_url": output[0] if isinstance(output, list) else output,
                "model": "playground_v2",
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Playground v2 generation failed: {str(e)}")
            return None 