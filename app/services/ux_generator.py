import logging
from typing import Dict, Any, Optional
from app.models.schemas import RequirementsInput, UXSpecification, RoleInsight, ScreenElement, AIModel
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)

class UXGenerator:
    """
    UX Generator service that orchestrates the generation of UX specifications
    using multi-role AI analysis and LLM services
    """
    
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service
    
    async def generate_specifications(
        self, 
        requirements: RequirementsInput,
        preferred_model: AIModel = AIModel.LLAMA3_70B
    ) -> UXSpecification:
        """Generate comprehensive UX specifications with enhanced features"""
        try:
            # Step 1: Multi-role analysis
            role_insights = await self.llm_service.generate_multi_role_analysis(
                requirements, 
                preferred_model
            )
            
            # Step 2: Generate enhanced UX specifications
            ux_specs_data = await self._generate_enhanced_specs(requirements, role_insights)
            
            # Step 3: Generate component library recommendations
            component_recommendations = await self._generate_component_recommendations(requirements, ux_specs_data)
            
            # Step 4: Generate data model suggestions
            data_model = await self._generate_data_model(requirements, ux_specs_data)
            
            # Step 5: Generate interaction patterns
            interaction_patterns = await self._generate_interaction_patterns(ux_specs_data)
            
            # Step 6: Generate responsive breakpoints
            responsive_design = await self._generate_responsive_design(ux_specs_data)
            
            # Step 7: Generate SEO and performance guidelines
            seo_performance = await self._generate_seo_performance_guidelines(requirements, ux_specs_data)
            
            # Combine all specifications
            final_specs = {
                **ux_specs_data,
                "roleInsights": role_insights,
                "componentLibrary": component_recommendations,
                "dataModel": data_model,
                "interactionPatterns": interaction_patterns,
                "responsiveDesign": responsive_design,
                "seoPerformance": seo_performance
            }
            
            return UXSpecification(**final_specs)
            
        except Exception as e:
            logger.error(f"Error generating UX specifications: {str(e)}")
            raise
    
    async def _generate_enhanced_specs(self, requirements: RequirementsInput, role_insights: Dict[str, str]) -> Dict[str, Any]:
        """Generate enhanced UX specifications with detailed information"""
        prompt = f"""
Based on the following requirements and multi-role insights, generate comprehensive UX specifications:

Requirements:
- Purpose: {requirements.purpose}
- Target Audience: {requirements.audience}
- User Goals: {requirements.goals}
- Use Cases: {', '.join(requirements.useCases)}

Role Insights:
- Designer: {role_insights.get('designer', '')}
- Analyst: {role_insights.get('analyst', '')}
- Architect: {role_insights.get('architect', '')}

Generate detailed specifications including:
1. Complete screen definitions with all UI elements
2. User flows and navigation paths
3. Information architecture
4. Accessibility requirements (WCAG 2.1 AA)
5. Design system recommendations

Return as JSON with structure:
{{
    "screens": [
        {{
            "id": "screen_id",
            "name": "Screen Name",
            "description": "Detailed description",
            "elements": ["element1", "element2"],
            "userFlow": "How users interact",
            "interactions": ["click", "hover", "swipe"],
            "accessibility": ["screen reader support", "keyboard navigation"]
        }}
    ],
    "iaStructure": {{
        "navigation": "Main navigation structure",
        "hierarchy": "Information hierarchy",
        "relationships": "Screen relationships"
    }},
    "standards": {{
        "accessibility": "WCAG 2.1 AA compliance details",
        "responsive": "Mobile-first approach",
        "patterns": "Material Design / Human Interface Guidelines"
    }}
}}
"""
        
        response = await self.llm_service.generate_ux_specifications(requirements, role_insights)
        return response
    
    async def _generate_component_recommendations(self, requirements: RequirementsInput, ux_specs: Dict[str, Any]) -> Dict[str, Any]:
        """Generate component library recommendations"""
        prompt = f"""
Based on the app requirements and UX specifications, recommend UI component libraries:

App Type: {requirements.purpose}
Target Platform: Web application
Design Style: Modern, accessible, responsive

Analyze and recommend:
1. Primary component library (React-based)
2. Specific components needed for each screen
3. Custom component requirements
4. Third-party integrations

Return as JSON:
{{
    "primaryLibrary": {{
        "name": "Library name",
        "reason": "Why this library",
        "pros": ["pro1", "pro2"],
        "cons": ["con1", "con2"]
    }},
    "alternativeLibraries": [{{}}],
    "componentMapping": {{
        "screen_name": ["Component1", "Component2"]
    }},
    "customComponents": ["Custom component descriptions"],
    "thirdPartyIntegrations": ["Charts library", "Date picker", etc.]
}}
"""
        
        response = await self.llm_service.generate_text(
            prompt, 
            'Phi-3-mini-4k-instruct', 
            max_tokens=1024, 
            temperature=0.3
        )
        return self._parse_json_response(response, {
            "primaryLibrary": {"name": "Material-UI", "reason": "Comprehensive and accessible"},
            "componentMapping": {},
            "customComponents": []
        })
    
    async def _generate_data_model(self, requirements: RequirementsInput, ux_specs: Dict[str, Any]) -> Dict[str, Any]:
        """Generate data model suggestions"""
        prompt = f"""
Design a data model for the application based on:

Purpose: {requirements.purpose}
Screens: {[s['name'] for s in ux_specs.get('screens', [])]}

Create:
1. Entity definitions with attributes
2. Relationships between entities
3. API endpoint suggestions
4. Data validation rules

Return as JSON:
{{
    "entities": [
        {{
            "name": "User",
            "attributes": [
                {{"name": "id", "type": "UUID", "required": true}},
                {{"name": "email", "type": "string", "validation": "email"}}
            ],
            "relationships": ["has many Posts"]
        }}
    ],
    "apiEndpoints": [
        {{
            "method": "GET",
            "path": "/api/users",
            "description": "List all users"
        }}
    ],
    "validationRules": {{}}
}}
"""
        
        response = await self.llm_service.generate_text(
            prompt, 
            'Phi-3-mini-4k-instruct', 
            max_tokens=1024, 
            temperature=0.3
        )
        return self._parse_json_response(response, {
            "entities": [],
            "apiEndpoints": [],
            "validationRules": {}
        })
    
    async def _generate_interaction_patterns(self, ux_specs: Dict[str, Any]) -> Dict[str, Any]:
        """Generate interaction patterns and micro-interactions"""
        prompt = f"""
Define interaction patterns for the UI based on these screens:
{[s['name'] for s in ux_specs.get('screens', [])]}

Include:
1. Hover states for interactive elements
2. Click/tap behaviors
3. Transitions and animations
4. Loading states
5. Error states
6. Success feedback

Return as JSON:
{{
    "globalPatterns": {{
        "buttons": {{
            "hover": "Scale 1.05, shadow increase",
            "click": "Scale 0.98, ripple effect",
            "disabled": "Opacity 0.5, cursor not-allowed"
        }},
        "forms": {{
            "validation": "Real-time with debounce",
            "error": "Red border, error message below",
            "success": "Green checkmark"
        }}
    }},
    "transitions": {{
        "pageTransition": "Fade in 300ms ease-out",
        "modalAnimation": "Slide up 200ms ease-in-out"
    }},
    "microInteractions": ["Button ripple", "Form field focus", "Checkbox animation"]
}}
"""
        
        response = await self.llm_service.generate_text(
            prompt, 
            'Phi-3-mini-4k-instruct', 
            max_tokens=1024, 
            temperature=0.3
        )
        return self._parse_json_response(response, {
            "globalPatterns": {},
            "transitions": {},
            "microInteractions": []
        })
    
    async def _generate_responsive_design(self, ux_specs: Dict[str, Any]) -> Dict[str, Any]:
        """Generate mobile-first responsive breakpoints"""
        prompt = """
Design a mobile-first responsive system with breakpoints:

Define:
1. Breakpoint values (mobile, tablet, desktop, wide)
2. Layout changes at each breakpoint
3. Typography scaling
4. Component behavior changes
5. Touch target sizes

Return as JSON:
{{
    "breakpoints": {{
        "mobile": "0-767px",
        "tablet": "768px-1023px", 
        "desktop": "1024px-1439px",
        "wide": "1440px+"
    }},
    "layoutRules": {{
        "mobile": {{"columns": 1, "padding": "16px"}},
        "tablet": {{"columns": 2, "padding": "24px"}},
        "desktop": {{"columns": 3, "padding": "32px"}}
    }},
    "typography": {{
        "mobile": {{"h1": "24px", "body": "14px"}},
        "desktop": {{"h1": "48px", "body": "16px"}}
    }},
    "touchTargets": {{
        "minimum": "44x44px",
        "recommended": "48x48px"
    }}
}}
"""
        
        response = await self.llm_service.generate_text(
            prompt, 
            'Phi-3-mini-4k-instruct', 
            max_tokens=1024, 
            temperature=0.3
        )
        return self._parse_json_response(response, {
            "breakpoints": {
                "mobile": "0-767px",
                "tablet": "768px-1023px",
                "desktop": "1024px+"
            },
            "layoutRules": {},
            "typography": {}
        })
    
    async def _generate_seo_performance_guidelines(self, requirements: RequirementsInput, ux_specs: Dict[str, Any]) -> Dict[str, Any]:
        """Generate SEO and performance optimization guidelines"""
        prompt = f"""
Create SEO and performance guidelines for: {requirements.purpose}

Include:
1. SEO best practices
2. Performance targets and metrics
3. Image optimization strategies
4. Code splitting recommendations
5. Caching strategies

Return as JSON:
{{
    "seo": {{
        "metaTags": ["title", "description", "keywords"],
        "structuredData": "Schema.org recommendations",
        "urlStructure": "SEO-friendly URL patterns",
        "contentGuidelines": ["Heading hierarchy", "Alt text"]
    }},
    "performance": {{
        "targets": {{
            "fcp": "< 1.8s",
            "lcp": "< 2.5s",
            "cls": "< 0.1",
            "tti": "< 3.8s"
        }},
        "optimization": ["Lazy loading", "Code splitting", "Tree shaking"]
    }},
    "imageOptimization": {{
        "formats": ["WebP with JPEG fallback"],
        "sizing": "Responsive images with srcset",
        "lazyLoading": true
    }}
}}
"""
        
        response = await self.llm_service.generate_text(
            prompt, 
            'Phi-3-mini-4k-instruct', 
            max_tokens=1024, 
            temperature=0.3
        )
        return self._parse_json_response(response, {
            "seo": {},
            "performance": {},
            "imageOptimization": {}
        })
    
    def _parse_json_response(self, response: str, default: Dict[str, Any]) -> Dict[str, Any]:
        """Parse JSON response with fallback"""
        try:
            import json
            
            # Handle dictionary response from generate_ux_specifications
            if isinstance(response, dict):
                return response
                
            # Handle string responses
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
            else:
                json_str = response.strip()
            
            return json.loads(json_str)
        except Exception as e:
            logger.warning(f"Failed to parse JSON response: {str(e)}")
            return default