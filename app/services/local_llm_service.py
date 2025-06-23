import os
import json
import logging
import asyncio
from typing import Dict, Any, Optional, List
import torch
from transformers import (
    AutoTokenizer, 
    AutoModelForCausalLM, 
    pipeline,
    BitsAndBytesConfig
)
from threading import Lock
from concurrent.futures import ThreadPoolExecutor
import gc

from app.models.schemas import AIModel, RequirementsInput

logger = logging.getLogger(__name__)

class LocalLLMService:
    """
    Local LLM Service for running models directly within the application.
    Supports model bundling, caching, and optimized inference.
    """
    
    def __init__(self):
        self.models = {}
        self.tokenizers = {}
        self.pipelines = {}
        self.model_configs = self._get_model_configurations()
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model_lock = Lock()
        self.executor = ThreadPoolExecutor(max_workers=2)
        
        # Set models directory from environment
        models_path = os.getenv("LOCAL_MODELS_PATH", "../models")
        if not os.path.isabs(models_path):
            # Make relative path absolute from the backend directory
            backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            models_path = os.path.join(backend_dir, models_path)
        
        # Normalize path for Windows compatibility
        self.models_dir = os.path.normpath(os.path.abspath(models_path))
        
        logger.info(f"Models directory: {self.models_dir}")
        logger.info(f"Models directory exists: {os.path.exists(self.models_dir)}")
        
        # DISABLE quantization for compatibility
        self.quantization_config = None
        
        logger.info(f"Local LLM Service initialized on device: {self.device}")
        if self.device == "cuda":
            logger.info(f"CUDA available: {torch.cuda.is_available()}")
            logger.info(f"GPU: {torch.cuda.get_device_name(0)}")
            logger.info(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
        else:
            logger.info("Running on CPU - this is normal for production servers without GPU")

    def _get_model_configurations(self) -> Dict[str, Dict]:
        """Define configurations for local models optimized for UX generation"""
        return {
            "Phi-3-mini-4k-instruct": {
                "use_case": "requirements_analysis",
                "max_tokens": 1024,
                "temperature": 0.3,
                "description": "Efficient instruction-following model for analysis"
            },
            "StableLM-Zephyr-3B": {
                "use_case": "ux_generation",
                "max_tokens": 2048,
                "temperature": 0.4,
                "description": "Optimized for creative UX content generation"
            },
            "Qwen2-1.5B-Instruct": {
                "use_case": "html_generation",
                "max_tokens": 2048,
                "temperature": 0.2,
                "description": "Precise HTML/CSS code generation"
            }
        }

    async def load_model(self, model_name: str, use_case: str = "general") -> bool:
        """Load a model into memory for local inference"""
        try:
            if model_name in self.models:
                logger.info(f"Model {model_name} already loaded")
                return True

            logger.info(f"Loading local model: {model_name}")
            
            # Run model loading in thread to avoid blocking
            loop = asyncio.get_event_loop()
            success = await loop.run_in_executor(
                self.executor, 
                self._load_model_sync, 
                model_name, 
                use_case
            )
            
            if success:
                logger.info(f"Successfully loaded model: {model_name}")
                return True
            else:
                logger.error(f"Failed to load model: {model_name}")
                return False
                
        except Exception as e:
            logger.error(f"Error loading model {model_name}: {str(e)}")
            return False

    def _load_model_sync(self, model_name: str, use_case: str) -> bool:
        """Synchronous model loading (runs in thread)"""
        try:
            with self.model_lock:
                # Load tokenizer from local models directory
                model_path = os.path.join(self.models_dir, model_name)
                
                # Convert Windows path to forward slashes for HuggingFace compatibility
                model_path = model_path.replace('\\', '/')
                
                logger.info(f"Loading model from path: {model_path}")
                
                # Check if model directory exists
                if not os.path.exists(model_path):
                    logger.error(f"Model directory does not exist: {model_path}")
                    return False
                
                # Load tokenizer with error handling
                try:
                    tokenizer = AutoTokenizer.from_pretrained(
                        model_path,
                        trust_remote_code=True,
                        local_files_only=True
                    )
                except Exception as e:
                    logger.error(f"Failed to load tokenizer for {model_name}: {str(e)}")
                    # Try alternative tokenizer loading
                    try:
                        from transformers import LlamaTokenizer
                        tokenizer = LlamaTokenizer.from_pretrained(
                            model_path,
                            trust_remote_code=True,
                            local_files_only=True
                        )
                    except Exception as e2:
                        logger.error(f"Alternative tokenizer loading failed: {str(e2)}")
                        return False
                
                # Ensure pad token exists
                if tokenizer.pad_token is None:
                    tokenizer.pad_token = tokenizer.eos_token
                
                # Model loading arguments optimized for RTX 4070 Ti
                model_kwargs = {
                    "trust_remote_code": True,
                    "local_files_only": True,
                    "torch_dtype": torch.float16,  # Use float16 for GPU
                    "low_cpu_mem_usage": True,
                }
                
                # Don't use device_map="auto" to avoid splitting
                if self.device == "cuda":
                    # Load to CPU first, then move to GPU
                    model = AutoModelForCausalLM.from_pretrained(
                        model_path,
                        **model_kwargs
                    )
                    model = model.to("cuda")
                else:
                    model_kwargs["torch_dtype"] = torch.float32
                    model = AutoModelForCausalLM.from_pretrained(
                        model_path,
                        **model_kwargs
                    )
                
                # Store in cache
                self.models[model_name] = model
                self.tokenizers[model_name] = tokenizer
                
                logger.info(f"Successfully loaded model: {model_name} on {self.device}")
                if self.device == "cuda":
                    logger.info(f"Model memory usage: {torch.cuda.memory_allocated() / 1024**3:.2f} GB")
                return True
                
        except Exception as e:
            logger.error(f"Sync model loading failed for {model_name}: {str(e)}")
            return False

    async def generate_text(
        self, 
        prompt: str, 
        model_name: str = "Phi-3-mini-4k-instruct",
        max_tokens: int = 1024,
        temperature: float = 0.7,
        top_p: float = 0.9,
        use_case: str = "general"
    ) -> str:
        """Generate text using local model"""
        try:
            # Ensure model is loaded
            if model_name not in self.models:
                await self.load_model(model_name, use_case)
            
            if model_name not in self.models:
                raise Exception(f"Failed to load model: {model_name}")

            # Run inference in thread
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.executor,
                self._generate_text_sync,
                prompt,
                model_name,
                max_tokens,
                temperature,
                top_p
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating text with {model_name}: {str(e)}")
            # Return fallback response
            return self._get_fallback_response(prompt)

    def _generate_text_sync(
        self, 
        prompt: str, 
        model_name: str,
        max_tokens: int,
        temperature: float,
        top_p: float
    ) -> str:
        """Synchronous text generation (runs in thread)"""
        try:
            model = self.models[model_name]
            tokenizer = self.tokenizers[model_name]
            
            # Tokenize input
            inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=2048)
            
            # Move to device
            if self.device == "cuda":
                inputs = {k: v.to("cuda") for k, v in inputs.items()}
            
            # Generate
            with torch.no_grad():
                outputs = model.generate(
                    **inputs,
                    max_new_tokens=max_tokens,
                    temperature=temperature,
                    top_p=top_p,
                    do_sample=True,
                    pad_token_id=tokenizer.eos_token_id,
                    eos_token_id=tokenizer.eos_token_id
                )
            
            # Decode
            generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Clean up
            result = self._clean_generated_text(generated_text, prompt)
            
            return result
            
        except Exception as e:
            logger.error(f"Sync text generation failed: {str(e)}")
            return self._get_fallback_response(prompt)

    def _clean_generated_text(self, text: str, original_prompt: str) -> str:
        """Clean up generated text"""
        # Remove the original prompt from the response
        if original_prompt in text:
            text = text.replace(original_prompt, "").strip()
        
        # Remove any remaining special tokens
        text = text.replace("<|endoftext|>", "").replace("<|im_end|>", "").strip()
        
        return text

    async def generate_multi_role_analysis(
        self, 
        requirements: RequirementsInput
    ) -> Dict[str, str]:
        """Generate multi-role analysis of requirements"""
        try:
            prompt = f"""Analyze the following app requirements from three different perspectives:

App Idea: {requirements.purpose}
Target Audience: {requirements.target_audience}
Key Features: {', '.join(requirements.key_features)}
Technical Requirements: {requirements.technical_requirements}

Please provide insights from:

1. PRODUCT DESIGNER:
- UI/UX recommendations
- User experience considerations
- Design patterns to follow

2. BUSINESS ANALYST:
- Market positioning
- Feature prioritization
- Success metrics

3. UX ARCHITECT:
- Information architecture
- User flow recommendations
- Technical implementation approach

Format your response as:
DESIGNER: [insights]
ANALYST: [insights]
ARCHITECT: [insights]"""

            response = await self.generate_text(
                prompt=prompt,
                model_name="Phi-3-mini-4k-instruct",
                max_tokens=1024,
                temperature=0.3,
                use_case="requirements_analysis"
            )
            
            return self._extract_role_insights_fallback(response)
            
        except Exception as e:
            logger.error(f"Multi-role analysis failed: {str(e)}")
            return self._get_fallback_analysis(requirements)

    async def generate_ux_specifications(
        self, 
        requirements: RequirementsInput,
        role_insights: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Generate UX specifications"""
        try:
            prompt = f"""Create comprehensive UX specifications for this application:

App: {requirements.purpose}
Audience: {requirements.target_audience}
Features: {', '.join(requirements.key_features)}

Generate specifications including:
1. Component Library recommendations
2. Data Model structure
3. Interaction Patterns
4. Responsive Design rules
5. SEO/Performance guidelines

Return as structured JSON."""

            response = await self.generate_text(
                prompt=prompt,
                model_name="StableLM-Zephyr-3B",
                max_tokens=2048,
                temperature=0.4,
                use_case="ux_generation"
            )
            
            return self._extract_ux_specs_fallback(response, requirements)
            
        except Exception as e:
            logger.error(f"UX specification generation failed: {str(e)}")
            return self._get_fallback_ux_specs(requirements)

    async def generate_dynamic_questions(self, app_idea: str) -> list:
        """Generate dynamic questions based on app idea"""
        try:
            prompt = f"""Based on this app idea, generate 5-7 specific questions to gather requirements:

App: {app_idea}

Return questions in this format:
{{
    "questions": [
        {{
            "id": "q1",
            "question": "What is your target audience?",
            "type": "select",
            "options": ["General users", "Business users", "Developers"],
            "required": true
        }}
    ]
}}"""

            response = await self.generate_text(
                prompt=prompt,
                model_name="Phi-3-mini-4k-instruct",
                max_tokens=1024,
                temperature=0.3,
                use_case="requirements_analysis"
            )
            
            return self._parse_questions_response(response)
            
        except Exception as e:
            logger.error(f"Question generation failed: {str(e)}")
            return self._generate_app_specific_questions(app_idea)

    def _parse_questions_response(self, response: str) -> list:
        """Parse questions from model response"""
        try:
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                return data.get("questions", [])
        except:
            pass
        
        # Fallback to simple parsing
        return self._parse_simple_questions(response, "")

    def _parse_simple_questions(self, response: str, app_idea: str) -> list:
        """Parse questions using simple text parsing"""
        questions = []
        
        # Extract questions from text
        lines = response.split('\n')
        for i, line in enumerate(lines):
            if '?' in line and any(word in line.lower() for word in ['what', 'how', 'who', 'when', 'where', 'why']):
                questions.append({
                    "id": f"q{i+1}",
                    "question": line.strip(),
                    "type": "text",
                    "required": True
                })
        
        # Add default questions if none found
        if not questions:
            questions = self._generate_app_specific_questions(app_idea)
        
        return questions

    def _generate_app_specific_questions(self, app_idea: str) -> list:
        """Generate app-specific questions as fallback"""
        app_lower = app_idea.lower()
        
        base_questions = [
            {
                "id": "q1",
                "question": "What is your target audience?",
                "type": "select",
                "options": self._get_audience_options(app_lower),
                "required": True
            },
            {
                "id": "q2", 
                "question": "What are the top 3 features you want?",
                "type": "multiselect",
                "options": self._get_feature_options(app_lower),
                "required": True
            },
            {
                "id": "q3",
                "question": "What is your budget range?",
                "type": "select", 
                "options": ["$1K-5K", "$5K-10K", "$10K-25K", "$25K+"],
                "required": False
            }
        ]
        
        return base_questions

    def _get_audience_options(self, app_lower: str) -> list:
        """Get audience options based on app type"""
        if "business" in app_lower or "enterprise" in app_lower:
            return ["Small Business", "Enterprise", "Startups", "Freelancers"]
        elif "social" in app_lower or "community" in app_lower:
            return ["General Users", "Teenagers", "Young Adults", "Professionals"]
        else:
            return ["General Users", "Business Users", "Developers", "Students"]

    def _get_feature_options(self, app_lower: str) -> list:
        """Get feature options based on app type"""
        if "ecommerce" in app_lower or "shop" in app_lower:
            return ["Product Catalog", "Shopping Cart", "Payment Processing", "User Reviews", "Inventory Management"]
        elif "social" in app_lower:
            return ["User Profiles", "Messaging", "Content Sharing", "Notifications", "Search"]
        else:
            return ["User Authentication", "Dashboard", "Data Management", "Reporting", "Mobile App"]

    async def generate_html_layout(self, screen_prompt: str) -> str:
        """Generate HTML layout for a screen"""
        try:
            prompt = f"""Generate a complete HTML layout with inline CSS for this screen:

{screen_prompt}

Requirements:
- Complete HTML structure with inline CSS
- Modern, responsive design
- Use semantic HTML elements
- Include proper accessibility attributes
- Professional appearance
- No external dependencies

Return ONLY the HTML code, no explanations."""

            response = await self.generate_text(
                prompt=prompt,
                model_name="Qwen2-1.5B-Instruct",
                max_tokens=2048,
                temperature=0.2,
                use_case="html_generation"
            )
            
            return self._extract_html_from_response(response)
            
        except Exception as e:
            logger.error(f"HTML generation failed: {str(e)}")
            return self._generate_fallback_html(screen_prompt)

    def _extract_html_from_response(self, response: str) -> str:
        """Extract HTML from model response"""
        try:
            # Try to extract HTML from response
            import re
            html_match = re.search(r'<html.*?</html>', response, re.DOTALL | re.IGNORECASE)
            if html_match:
                return html_match.group()
            
            # Try to find any HTML structure
            html_match = re.search(r'<.*?>.*?</.*?>', response, re.DOTALL)
            if html_match:
                return html_match.group()
                
        except:
            pass
        
        # Fallback to simple HTML
        return self._generate_fallback_html(response)

    def _is_valid_html(self, html: str) -> bool:
        """Check if HTML is valid"""
        return '<' in html and '>' in html and len(html) > 50

    def _generate_fallback_html(self, prompt: str) -> str:
        """Generate fallback HTML"""
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{prompt[:50]}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }}
        h1 {{ color: #333; }}
        .content {{ margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{prompt[:50]}</h1>
        <div class="content">
            <p>Screen content for: {prompt}</p>
        </div>
    </div>
</body>
</html>"""

    def _get_fallback_response(self, prompt: str) -> str:
        """Get fallback response when model fails"""
        return f"I apologize, but I'm unable to generate a response for '{prompt[:50]}...' at the moment. Please try again or contact support."

    def _get_fallback_analysis(self, requirements: RequirementsInput) -> Dict[str, str]:
        """Get fallback multi-role analysis"""
        return {
            "designer": f"Based on the app idea '{requirements.purpose}', focus on creating an intuitive user interface that serves {requirements.target_audience} effectively.",
            "analyst": f"Consider the market opportunity for {requirements.purpose} and prioritize features that provide the most value to {requirements.target_audience}.",
            "architect": f"Design a scalable architecture that can support the key features: {', '.join(requirements.key_features)}."
        }

    def _extract_role_insights_fallback(self, text: str) -> Dict[str, str]:
        """Extract role insights from text"""
        roles = {
            "designer": "",
            "analyst": "", 
            "architect": ""
        }
        
        lines = text.split('\n')
        current_role = None
        
        for line in lines:
            line_lower = line.lower()
            if "designer" in line_lower:
                current_role = "designer"
            elif "analyst" in line_lower:
                current_role = "analyst"
            elif "architect" in line_lower:
                current_role = "architect"
            elif current_role and line.strip():
                roles[current_role] += line.strip() + " "
        
        return roles

    def _get_fallback_ux_specs(self, requirements: RequirementsInput) -> Dict[str, Any]:
        """Get fallback UX specifications"""
        return {
            "component_library": {
                "primary": "Material-UI",
                "reason": "Widely adopted, comprehensive component library",
                "alternatives": ["Ant Design", "Chakra UI"]
            },
            "data_model": {
                "entities": ["User", "Project", "Screen"],
                "relationships": "One-to-many between entities"
            },
            "interaction_patterns": {
                "button_states": ["hover", "active", "disabled"],
                "transitions": "Fade and slide animations"
            },
            "responsive_design": {
                "breakpoints": ["mobile: 0-767px", "tablet: 768-1023px", "desktop: 1024px+"]
            },
            "seo_performance": {
                "meta_tags": "Required for all pages",
                "performance_targets": "FCP < 1.8s, LCP < 2.5s"
            }
        }

    def _extract_ux_specs_fallback(self, text: str, requirements: RequirementsInput) -> Dict[str, Any]:
        """Extract UX specs from text"""
        # Try to parse JSON first
        try:
            import re
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        # Return fallback specs
        return self._get_fallback_ux_specs(requirements)

    async def unload_model(self, model_name: str):
        """Unload a model to free memory"""
        try:
            if model_name in self.models:
                del self.models[model_name]
                del self.tokenizers[model_name]
                
                if self.device == "cuda":
                    torch.cuda.empty_cache()
                    gc.collect()
                
                logger.info(f"Unloaded model: {model_name}")
        except Exception as e:
            logger.error(f"Error unloading model {model_name}: {str(e)}")

    def get_loaded_models(self) -> List[str]:
        """Get list of currently loaded models"""
        return list(self.models.keys())

    def get_memory_usage(self) -> Dict[str, Any]:
        """Get memory usage information"""
        if self.device == "cuda":
            return {
                "device": "cuda",
                "allocated_gb": torch.cuda.memory_allocated() / 1024**3,
                "cached_gb": torch.cuda.memory_reserved() / 1024**3,
                "total_gb": torch.cuda.get_device_properties(0).total_memory / 1024**3
            }
        else:
            return {
                "device": "cpu",
                "loaded_models": len(self.models)
            }