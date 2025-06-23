import os
import logging
from typing import Dict, Any, Optional, List
import json
from app.models.schemas import AIModel, RequirementsInput
from app.services.claude_service import ClaudeService

logger = logging.getLogger(__name__)

class LLMService:
    """
    Production-ready LLM Service using Claude with comprehensive fallbacks
    Designed to never crash and always provide helpful responses to users
    """
    
    def __init__(self):
        self.claude = None
        self.initialized = False
        
        # Try to initialize Claude
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if api_key and api_key != "your_anthropic_api_key_here":
            try:
                self.claude = ClaudeService()
                self.initialized = True
                logger.info("✅ LLM Service initialized with Claude")
            except Exception as e:
                logger.warning(f"⚠️ Claude initialization failed, using intelligent fallbacks: {str(e)}")
        else:
            logger.info("ℹ️ Running in fallback mode - no Claude API key configured")
    
    async def generate_text(
        self, 
        prompt: str, 
        model_name: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        top_p: float = 0.9,
        use_case: str = "general"
    ) -> str:
        """Generate text - always returns something useful"""
        if self.initialized and self.claude:
            try:
                return await self.claude.generate_html_layout(prompt)
            except Exception as e:
                logger.error(f"Claude text generation failed: {str(e)}")
        
        # Smart fallback based on use case
        if "html" in prompt.lower() or "layout" in prompt.lower():
            return self._generate_smart_html_fallback(prompt)
        return self._generate_helpful_response(prompt)
    
    async def generate_dynamic_questions(self, app_idea: str) -> List[Dict[str, Any]]:
        """Generate context-aware questions - never fails"""
        if self.initialized and self.claude:
            try:
                questions = await self.claude.generate_dynamic_questions(app_idea)
                if questions and len(questions) > 0:
                    return questions
            except Exception as e:
                logger.error(f"Claude question generation failed: {str(e)}")
        
        # Smart fallback with context-aware questions
        return self._generate_smart_questions(app_idea)
    
    async def generate_multi_role_analysis(
        self, 
        requirements: RequirementsInput,
        preferred_model: AIModel = None
    ) -> Dict[str, str]:
        """Generate expert analysis - always provides insights"""
        req_dict = self._requirements_to_dict(requirements)
        
        if self.initialized and self.claude:
            try:
                insights = await self.claude.generate_multi_role_analysis(req_dict)
                if insights and all(k in insights for k in ["designer", "analyst", "architect"]):
                    return insights
            except Exception as e:
                logger.error(f"Claude analysis failed: {str(e)}")
        
        # Smart context-aware fallback
        return self._generate_smart_role_insights(req_dict)
    
    async def generate_ux_specifications(
        self, 
        requirements: RequirementsInput,
        role_insights: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Generate comprehensive UX specs - never returns empty"""
        req_dict = self._requirements_to_dict(requirements)
        
        if self.initialized and self.claude:
            try:
                specs = await self.claude.generate_ux_specifications(req_dict, role_insights)
                if specs and "screens" in specs and len(specs["screens"]) > 0:
                    return self._ensure_complete_specs(specs)
            except Exception as e:
                logger.error(f"Claude UX generation failed: {str(e)}")
        
        # Generate intelligent specs based on app type
        return self._generate_smart_ux_specs(req_dict, role_insights)
    
    async def generate_html_layout(self, screen_prompt: str) -> str:
        """Generate HTML layout - always returns valid HTML"""
        if self.initialized and self.claude:
            try:
                html = await self.claude.generate_html_layout(screen_prompt)
                if html and self._is_valid_html(html):
                    return html
            except Exception as e:
                logger.error(f"Claude HTML generation failed: {str(e)}")
        
        # Generate contextual HTML based on screen description
        return self._generate_smart_html_fallback(screen_prompt)
    
    def _requirements_to_dict(self, requirements: RequirementsInput) -> Dict[str, Any]:
        """Safely convert requirements to dictionary"""
        return {
            "purpose": getattr(requirements, 'purpose', ''),
            "audience": getattr(requirements, 'audience', getattr(requirements, 'target_audience', 'general users')),
            "demographics": getattr(requirements, 'demographics', ''),
            "goals": getattr(requirements, 'goals', ''),
            "use_cases": getattr(requirements, 'useCases', getattr(requirements, 'use_cases', []))
        }
    
    def _generate_smart_questions(self, app_idea: str) -> List[Dict[str, Any]]:
        """Generate intelligent questions based on app type"""
        app_lower = app_idea.lower()
        questions = []
        
        # Universal first question
        questions.append({
            "id": "target_audience",
            "question": "Who is your primary target audience?",
            "type": "select",
            "options": self._get_audience_options(app_lower),
            "required": True,
            "help_text": "This helps us design the right user experience",
            "default_if_unsure": "General users"
        })
        
        # App-specific questions
        if any(term in app_lower for term in ["ecommerce", "shop", "store", "marketplace"]):
            questions.extend([
                {
                    "id": "product_types",
                    "question": "What types of products will you sell?",
                    "type": "multiselect",
                    "options": ["Physical Goods", "Digital Products", "Services", "Subscriptions"],
                    "required": True
                },
                {
                    "id": "payment_methods",
                    "question": "Which payment methods do you need?",
                    "type": "multiselect",
                    "options": ["Credit/Debit Cards", "PayPal", "Stripe", "Cryptocurrency", "Bank Transfer"],
                    "required": True
                }
            ])
        elif any(term in app_lower for term in ["social", "community", "network", "chat"]):
            questions.extend([
                {
                    "id": "social_features",
                    "question": "What social features are most important?",
                    "type": "multiselect",
                    "options": ["User Profiles", "Direct Messaging", "Groups/Communities", "Content Sharing", "Live Streaming"],
                    "required": True
                },
                {
                    "id": "content_moderation",
                    "question": "How will you handle content moderation?",
                    "type": "select",
                    "options": ["Automated Filtering", "Community Reporting", "Manual Review", "AI Moderation"],
                    "required": True
                }
            ])
        elif any(term in app_lower for term in ["fitness", "health", "workout", "exercise"]):
            questions.extend([
                {
                    "id": "fitness_features",
                    "question": "What fitness tracking features do you need?",
                    "type": "multiselect",
                    "options": ["Workout Logging", "Progress Tracking", "Meal Planning", "Goal Setting", "Social Challenges"],
                    "required": True
                },
                {
                    "id": "device_integration",
                    "question": "Will you integrate with fitness devices?",
                    "type": "select",
                    "options": ["Yes - Wearables", "Yes - Gym Equipment", "No Integration", "Future Consideration"],
                    "required": False
                }
            ])
        else:
            # Generic app questions
            questions.extend([
                {
                    "id": "key_features",
                    "question": "What are the 3-5 most important features?",
                    "type": "textarea",
                    "placeholder": "List the core features your app must have",
                    "required": True,
                    "help_text": "Be specific about what users can do"
                },
                {
                    "id": "user_goals",
                    "question": "What should users achieve with your app?",
                    "type": "textarea",
                    "placeholder": "Describe the main user goals and outcomes",
                    "required": True
                }
            ])
        
        # Common final questions
        questions.extend([
            {
                "id": "design_style",
                "question": "What design style best fits your brand?",
                "type": "select",
                "options": ["Modern & Minimal", "Bold & Colorful", "Professional & Corporate", "Playful & Fun", "Dark & Elegant"],
                "required": True,
                "default_if_unsure": "Modern & Minimal"
            },
            {
                "id": "platform",
                "question": "What platforms will you target?",
                "type": "multiselect",
                "options": ["Web (Desktop)", "Web (Mobile)", "iOS App", "Android App"],
                "required": True,
                "help_text": "Select all that apply"
            }
        ])
        
        return questions
    
    def _get_audience_options(self, app_lower: str) -> List[str]:
        """Get context-aware audience options"""
        if any(term in app_lower for term in ["business", "enterprise", "b2b", "saas"]):
            return ["Small Businesses", "Enterprise Companies", "Startups", "Freelancers", "Agencies"]
        elif any(term in app_lower for term in ["kids", "children", "education", "school"]):
            return ["Children (6-12)", "Teenagers (13-17)", "Parents", "Teachers", "Schools"]
        elif any(term in app_lower for term in ["fitness", "health", "medical"]):
            return ["Fitness Enthusiasts", "Beginners", "Athletes", "Health Professionals", "Patients"]
        elif any(term in app_lower for term in ["game", "gaming", "play"]):
            return ["Casual Gamers", "Hardcore Gamers", "Mobile Gamers", "Families", "Competitive Players"]
        else:
            return ["General Public", "Young Adults (18-34)", "Professionals", "Students", "Seniors"]
    
    def _generate_smart_role_insights(self, req_dict: Dict[str, Any]) -> Dict[str, str]:
        """Generate intelligent role-based insights"""
        purpose = req_dict.get('purpose', 'app')
        audience = req_dict.get('audience', 'users')
        
        return {
            "designer": f"For a {purpose} targeting {audience}, focus on intuitive navigation and clear visual hierarchy. Use familiar patterns that {audience} expect, with consistent interactions and delightful micro-animations that enhance usability without overwhelming users.",
            
            "analyst": f"The {purpose} must address core user needs through well-defined user stories. Key metrics should include user adoption, task completion rates, and retention. Consider competitive analysis and ensure features align with {audience} expectations and business goals.",
            
            "architect": f"Design a scalable architecture supporting the {purpose}'s growth. Implement proper data models, API structures, and security measures. Consider performance optimization, offline capabilities, and third-party integrations that {audience} might expect."
        }
    
    def _generate_smart_ux_specs(self, req_dict: Dict[str, Any], role_insights: Optional[Dict[str, str]]) -> Dict[str, Any]:
        """Generate comprehensive UX specifications based on app type"""
        purpose = req_dict.get('purpose', 'application')
        
        # Determine app type and generate appropriate screens
        screens = self._generate_screens_for_app_type(purpose)
        
        return {
            "screens": screens,
            "componentLibrary": {
                "primaryLibrary": {
                    "name": "Material-UI" if "business" in purpose.lower() else "Ant Design",
                    "reason": "Comprehensive component set with excellent documentation and community support",
                    "pros": ["Production-ready components", "Accessibility built-in", "Theming support"],
                    "cons": ["Learning curve for customization", "Bundle size considerations"]
                },
                "alternativeLibraries": [
                    {"name": "Chakra UI", "reason": "Modern and highly customizable"},
                    {"name": "Tailwind UI", "reason": "Utility-first with pre-built components"}
                ]
            },
            "dataModel": self._generate_data_model(purpose),
            "interactionPatterns": {
                "globalPatterns": {
                    "buttons": {
                        "hover": "Slight scale (1.02) with shadow",
                        "active": "Scale down (0.98)",
                        "disabled": "Opacity 0.5, cursor not-allowed"
                    },
                    "forms": {
                        "validation": "Real-time with debounce",
                        "errors": "Inline with red color",
                        "success": "Green checkmark with message"
                    },
                    "cards": {
                        "hover": "Elevate with shadow",
                        "click": "Ripple effect from click point"
                    }
                },
                "transitions": {
                    "pageTransition": "Fade 200ms ease-out",
                    "modalAnimation": "Slide up 300ms ease-out",
                    "tabSwitch": "Slide horizontal 150ms"
                },
                "microInteractions": [
                    "Button press feedback",
                    "Loading spinners",
                    "Success checkmarks",
                    "Error shake animation",
                    "Tooltip on hover"
                ]
            },
            "responsiveDesign": {
                "breakpoints": {
                    "mobile": "0-767px",
                    "tablet": "768px-1023px",
                    "desktop": "1024px-1439px",
                    "wide": "1440px+"
                },
                "layoutRules": {
                    "mobile": {"columns": 1, "padding": "16px", "fontSize": "14px"},
                    "tablet": {"columns": 2, "padding": "24px", "fontSize": "16px"},
                    "desktop": {"columns": 3, "padding": "32px", "fontSize": "16px"}
                },
                "typography": {
                    "mobile": {"h1": "24px", "h2": "20px", "body": "14px"},
                    "desktop": {"h1": "32px", "h2": "24px", "body": "16px"}
                }
            },
            "seoPerformance": {
                "seo": {
                    "metaTags": ["title", "description", "og:image", "og:title", "og:description"],
                    "structuredData": "Use schema.org markup",
                    "contentGuidelines": ["Semantic HTML5", "Proper heading hierarchy", "Alt text for images"]
                },
                "performance": {
                    "targets": {
                        "fcp": "< 1.8s",
                        "lcp": "< 2.5s",
                        "cls": "< 0.1",
                        "tti": "< 3.8s"
                    },
                    "optimization": [
                        "Lazy load images",
                        "Code splitting",
                        "Minimize bundle size",
                        "Cache static assets"
                    ]
                }
            },
            "roleInsights": role_insights or self._generate_smart_role_insights(req_dict)
        }
    
    def _generate_screens_for_app_type(self, purpose: str) -> List[Dict[str, Any]]:
        """Generate appropriate screens based on app type"""
        purpose_lower = purpose.lower()
        
        # Base screens every app needs
        base_screens = [
            {
                "id": "landing",
                "name": "Landing Page",
                "description": "First impression with clear value proposition",
                "elements": ["hero_section", "navigation", "cta_button", "features_overview"],
                "userFlow": "Entry point for new users",
                "interactions": ["smooth_scroll", "hover_effects", "cta_click"]
            }
        ]
        
        # Add app-specific screens
        if any(term in purpose_lower for term in ["ecommerce", "shop", "store"]):
            base_screens.extend([
                {
                    "id": "product_list",
                    "name": "Product Catalog",
                    "description": "Browse and filter products",
                    "elements": ["search_bar", "filters", "product_grid", "sort_options", "pagination"],
                    "userFlow": "Users browse products, apply filters, and select items",
                    "interactions": ["filter_toggle", "quick_view", "add_to_cart"]
                },
                {
                    "id": "product_detail",
                    "name": "Product Details",
                    "description": "Detailed product information",
                    "elements": ["image_gallery", "product_info", "add_to_cart", "reviews", "related_products"],
                    "userFlow": "Users view details and make purchase decision",
                    "interactions": ["image_zoom", "variant_selection", "quantity_change"]
                },
                {
                    "id": "shopping_cart",
                    "name": "Shopping Cart",
                    "description": "Review and modify cart items",
                    "elements": ["cart_items", "quantity_controls", "price_summary", "checkout_button"],
                    "userFlow": "Users review cart and proceed to checkout",
                    "interactions": ["quantity_update", "remove_item", "apply_coupon"]
                }
            ])
        elif any(term in purpose_lower for term in ["social", "community"]):
            base_screens.extend([
                {
                    "id": "feed",
                    "name": "Activity Feed",
                    "description": "Main social content stream",
                    "elements": ["post_cards", "create_post", "filters", "trending_topics"],
                    "userFlow": "Users scroll through content and interact",
                    "interactions": ["like", "comment", "share", "infinite_scroll"]
                },
                {
                    "id": "profile",
                    "name": "User Profile",
                    "description": "User information and activity",
                    "elements": ["profile_header", "bio", "activity_tabs", "followers_count"],
                    "userFlow": "Users view and edit their profile",
                    "interactions": ["edit_profile", "follow_button", "tab_switching"]
                }
            ])
        else:
            # Generic app screens
            base_screens.extend([
                {
                    "id": "dashboard",
                    "name": "Dashboard",
                    "description": "Main application interface",
                    "elements": ["navigation", "summary_cards", "quick_actions", "recent_activity"],
                    "userFlow": "Central hub for user activities",
                    "interactions": ["card_click", "navigation", "quick_action_buttons"]
                },
                {
                    "id": "settings",
                    "name": "Settings",
                    "description": "User preferences and configuration",
                    "elements": ["settings_menu", "form_fields", "save_button", "danger_zone"],
                    "userFlow": "Users customize their experience",
                    "interactions": ["toggle_switches", "form_input", "save_changes"]
                }
            ])
        
        return base_screens
    
    def _generate_data_model(self, purpose: str) -> Dict[str, Any]:
        """Generate appropriate data model based on app type"""
        base_entities = [
            {
                "name": "User",
                "attributes": [
                    {"name": "id", "type": "UUID", "required": True},
                    {"name": "email", "type": "string", "required": True},
                    {"name": "username", "type": "string", "required": True},
                    {"name": "created_at", "type": "timestamp", "required": True}
                ],
                "relationships": ["has many Sessions"]
            }
        ]
        
        base_endpoints = [
            {"method": "POST", "path": "/api/auth/register", "description": "User registration"},
            {"method": "POST", "path": "/api/auth/login", "description": "User login"},
            {"method": "GET", "path": "/api/users/profile", "description": "Get user profile"}
        ]
        
        # Add app-specific entities
        if "ecommerce" in purpose.lower():
            base_entities.extend([
                {
                    "name": "Product",
                    "attributes": [
                        {"name": "id", "type": "UUID", "required": True},
                        {"name": "name", "type": "string", "required": True},
                        {"name": "price", "type": "decimal", "required": True},
                        {"name": "stock", "type": "integer", "required": True}
                    ],
                    "relationships": ["belongs to Category", "has many Reviews"]
                },
                {
                    "name": "Order",
                    "attributes": [
                        {"name": "id", "type": "UUID", "required": True},
                        {"name": "user_id", "type": "UUID", "required": True},
                        {"name": "total", "type": "decimal", "required": True},
                        {"name": "status", "type": "enum", "required": True}
                    ],
                    "relationships": ["belongs to User", "has many OrderItems"]
                }
            ])
            base_endpoints.extend([
                {"method": "GET", "path": "/api/products", "description": "List products"},
                {"method": "POST", "path": "/api/orders", "description": "Create order"}
            ])
        
        return {
            "entities": base_entities,
            "apiEndpoints": base_endpoints
        }
    
    def _generate_smart_html_fallback(self, screen_prompt: str) -> str:
        """Generate contextual HTML based on screen description"""
        # Extract screen type from prompt
        prompt_lower = screen_prompt.lower()
        
        if "dashboard" in prompt_lower:
            return self._generate_dashboard_html()
        elif "login" in prompt_lower or "signin" in prompt_lower:
            return self._generate_login_html()
        elif "product" in prompt_lower:
            return self._generate_product_html()
        elif "profile" in prompt_lower:
            return self._generate_profile_html()
        else:
            return self._generate_generic_html(screen_prompt)
    
    def _generate_dashboard_html(self) -> str:
        """Generate a dashboard HTML template"""
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f7fa;
            color: #2d3748;
        }
        .header {
            background: white;
            padding: 1rem 2rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        .header h1 {
            font-size: 1.5rem;
            font-weight: 600;
        }
        .container {
            max-width: 1200px;
            margin: 2rem auto;
            padding: 0 1rem;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }
        .stat-card {
            background: white;
            padding: 1.5rem;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        .stat-card h3 {
            color: #718096;
            font-size: 0.875rem;
            font-weight: 500;
            margin-bottom: 0.5rem;
        }
        .stat-value {
            font-size: 2rem;
            font-weight: 600;
            color: #1a202c;
        }
        .main-content {
            background: white;
            padding: 2rem;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
    </style>
</head>
<body>
    <header class="header">
        <h1>Dashboard</h1>
    </header>
    <div class="container">
        <div class="stats-grid">
            <div class="stat-card">
                <h3>Total Users</h3>
                <div class="stat-value">1,234</div>
            </div>
            <div class="stat-card">
                <h3>Active Sessions</h3>
                <div class="stat-value">56</div>
            </div>
            <div class="stat-card">
                <h3>Revenue</h3>
                <div class="stat-value">$12,345</div>
            </div>
            <div class="stat-card">
                <h3>Growth</h3>
                <div class="stat-value">+23%</div>
            </div>
        </div>
        <div class="main-content">
            <h2>Recent Activity</h2>
            <p>Your recent activity will appear here.</p>
        </div>
    </div>
</body>
</html>"""
    
    def _generate_login_html(self) -> str:
        """Generate a login page HTML template"""
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .login-container {
            background: white;
            padding: 2.5rem;
            border-radius: 12px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.1);
            width: 100%;
            max-width: 400px;
        }
        .login-header {
            text-align: center;
            margin-bottom: 2rem;
        }
        .login-header h1 {
            font-size: 2rem;
            color: #1a202c;
            margin-bottom: 0.5rem;
        }
        .login-header p {
            color: #718096;
        }
        .form-group {
            margin-bottom: 1.5rem;
        }
        label {
            display: block;
            margin-bottom: 0.5rem;
            color: #4a5568;
            font-weight: 500;
        }
        input {
            width: 100%;
            padding: 0.75rem;
            border: 1px solid #e2e8f0;
            border-radius: 6px;
            font-size: 1rem;
            transition: border-color 0.2s;
        }
        input:focus {
            outline: none;
            border-color: #667eea;
        }
        button {
            width: 100%;
            padding: 0.75rem;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 6px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.2s;
        }
        button:hover {
            background: #5a67d8;
        }
        .form-footer {
            text-align: center;
            margin-top: 1.5rem;
            color: #718096;
        }
        .form-footer a {
            color: #667eea;
            text-decoration: none;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="login-header">
            <h1>Welcome Back</h1>
            <p>Sign in to your account</p>
        </div>
        <form>
            <div class="form-group">
                <label for="email">Email</label>
                <input type="email" id="email" placeholder="you@example.com" required>
            </div>
            <div class="form-group">
                <label for="password">Password</label>
                <input type="password" id="password" placeholder="••••••••" required>
            </div>
            <button type="submit">Sign In</button>
        </form>
        <div class="form-footer">
            <p>Don't have an account? <a href="#">Sign up</a></p>
        </div>
    </div>
</body>
</html>"""
    
    def _generate_product_html(self) -> str:
        """Generate a product page HTML template"""
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Product Details</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f7fa;
            color: #2d3748;
        }
        .container {
            max-width: 1200px;
            margin: 2rem auto;
            padding: 0 1rem;
        }
        .product-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 3rem;
            background: white;
            padding: 2rem;
            border-radius: 12px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        .product-image {
            background: #e2e8f0;
            border-radius: 8px;
            aspect-ratio: 1;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #718096;
        }
        .product-info h1 {
            font-size: 2rem;
            margin-bottom: 1rem;
        }
        .price {
            font-size: 1.5rem;
            font-weight: 600;
            color: #667eea;
            margin-bottom: 1.5rem;
        }
        .description {
            color: #4a5568;
            line-height: 1.6;
            margin-bottom: 2rem;
        }
        .add-to-cart {
            background: #667eea;
            color: white;
            border: none;
            padding: 1rem 2rem;
            border-radius: 6px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.2s;
        }
        .add-to-cart:hover {
            background: #5a67d8;
        }
        @media (max-width: 768px) {
            .product-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="product-grid">
            <div class="product-image">
                [Product Image]
            </div>
            <div class="product-info">
                <h1>Product Name</h1>
                <div class="price">$99.99</div>
                <div class="description">
                    This is a high-quality product that meets all your needs. 
                    It features excellent build quality and innovative design.
                </div>
                <button class="add-to-cart">Add to Cart</button>
            </div>
        </div>
    </div>
</body>
</html>"""
    
    def _generate_profile_html(self) -> str:
        """Generate a profile page HTML template"""
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>User Profile</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f7fa;
            color: #2d3748;
        }
        .profile-header {
            background: white;
            padding: 2rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        .profile-header-content {
            max-width: 1200px;
            margin: 0 auto;
            display: flex;
            align-items: center;
            gap: 2rem;
        }
        .avatar {
            width: 120px;
            height: 120px;
            background: #667eea;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 3rem;
            font-weight: 600;
        }
        .profile-info h1 {
            font-size: 2rem;
            margin-bottom: 0.5rem;
        }
        .profile-info p {
            color: #718096;
        }
        .container {
            max-width: 1200px;
            margin: 2rem auto;
            padding: 0 1rem;
        }
        .content-tabs {
            display: flex;
            gap: 2rem;
            margin-bottom: 2rem;
            border-bottom: 1px solid #e2e8f0;
        }
        .tab {
            padding: 1rem 0;
            color: #718096;
            text-decoration: none;
            border-bottom: 2px solid transparent;
            transition: all 0.2s;
        }
        .tab.active {
            color: #667eea;
            border-bottom-color: #667eea;
        }
        .content-area {
            background: white;
            padding: 2rem;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
    </style>
</head>
<body>
    <div class="profile-header">
        <div class="profile-header-content">
            <div class="avatar">JD</div>
            <div class="profile-info">
                <h1>John Doe</h1>
                <p>john.doe@example.com</p>
            </div>
        </div>
    </div>
    <div class="container">
        <div class="content-tabs">
            <a href="#" class="tab active">Overview</a>
            <a href="#" class="tab">Activity</a>
            <a href="#" class="tab">Settings</a>
        </div>
        <div class="content-area">
            <h2>Profile Overview</h2>
            <p>Welcome to your profile page. Here you can view and manage your account information.</p>
        </div>
    </div>
</body>
</html>"""
    
    def _generate_generic_html(self, screen_prompt: str) -> str:
        """Generate generic HTML for any screen type"""
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Generated Screen</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f7fa;
            color: #2d3748;
            line-height: 1.6;
        }}
        .header {{
            background: white;
            padding: 1.5rem 2rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        .header h1 {{
            font-size: 1.75rem;
            font-weight: 600;
        }}
        .container {{
            max-width: 1200px;
            margin: 2rem auto;
            padding: 0 1rem;
        }}
        .content {{
            background: white;
            padding: 2rem;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        .action-group {{
            margin-top: 2rem;
            display: flex;
            gap: 1rem;
        }}
        .btn {{
            padding: 0.75rem 1.5rem;
            border: none;
            border-radius: 6px;
            font-size: 1rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
        }}
        .btn-primary {{
            background: #667eea;
            color: white;
        }}
        .btn-primary:hover {{
            background: #5a67d8;
        }}
        .btn-secondary {{
            background: #e2e8f0;
            color: #4a5568;
        }}
        .btn-secondary:hover {{
            background: #cbd5e0;
        }}
    </style>
</head>
<body>
    <header class="header">
        <h1>Generated Screen</h1>
    </header>
    <div class="container">
        <div class="content">
            <h2>Screen Content</h2>
            <p>This screen was generated based on: {screen_prompt}</p>
            <div class="action-group">
                <button class="btn btn-primary">Primary Action</button>
                <button class="btn btn-secondary">Secondary Action</button>
            </div>
        </div>
    </div>
</body>
</html>"""
    
    def _is_valid_html(self, html: str) -> bool:
        """Check if HTML is valid"""
        return (
            html and 
            len(html) > 100 and 
            ('<html' in html or '<!DOCTYPE' in html) and
            '</html>' in html
        )
    
    def _ensure_complete_specs(self, specs: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure specs have all required fields"""
        # Add missing fields with sensible defaults
        if "componentLibrary" not in specs:
            specs["componentLibrary"] = {
                "primaryLibrary": {"name": "Material-UI", "reason": "Comprehensive component library"}
            }
        
        if "interactionPatterns" not in specs:
            specs["interactionPatterns"] = {
                "globalPatterns": {},
                "transitions": {},
                "microInteractions": []
            }
        
        if "responsiveDesign" not in specs:
            specs["responsiveDesign"] = {
                "breakpoints": {"mobile": "0-767px", "tablet": "768px-1023px", "desktop": "1024px+"}
            }
        
        if "seoPerformance" not in specs:
            specs["seoPerformance"] = {"seo": {}, "performance": {}}
        
        return specs
    
    def _generate_helpful_response(self, prompt: str) -> str:
        """Generate a helpful response for any prompt"""
        return f"I understand you need help with: {prompt[:100]}... While I cannot generate the full response right now, I recommend breaking this down into smaller, specific requirements for better results."