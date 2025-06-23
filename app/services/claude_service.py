# app/services/claude_service.py - Enhanced with smart answer suggestions

import os
from typing import Dict, List, Any, Optional
from anthropic import Anthropic
import json
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

class ClaudeService:
    def __init__(self):
        # Use ANTHROPIC_API_KEY (that's what's in your .env file)
        self.api_key = os.getenv('ANTHROPIC_API_KEY')
        
        if not self.api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not found in environment variables. "
                "Please check your .env file in the backend root directory."
            )
        
        self.client = Anthropic(api_key=self.api_key)
        self.default_model = "claude-3-5-sonnet-20241022"
        self.fast_model = "claude-3-haiku-20240307"
    
    def generate_dynamic_questions(self, app_idea: str) -> List[Dict[str, Any]]:
        """Generate comprehensive UX design questions with smart answer options"""
        
        prompt = f"""You are a senior UX designer conducting a thorough requirements gathering session for a new app. 
The client wants to build: "{app_idea}"

Generate a comprehensive set of questions with SMART ANSWER OPTIONS that a professional UX designer would ask.
For each question, provide intelligent, context-aware answer choices that the user can simply select.

IMPORTANT: Every question should have selectable options. Even for seemingly open-ended questions, provide smart suggestions based on the app type.

Categories to cover:
1. Target Audience & User Research
2. Core Features & Functionality  
3. Business Goals & Success Metrics
4. User Experience & Interface
5. Technical & Operational Requirements
6. Content & Data Management

Generate 12-15 questions. For each question, provide 3-5 intelligent answer options based on the {app_idea} context.

Return as a JSON array with this structure:
[
  {{
    "id": 1,
    "question": "Clear, specific question text",
    "type": "single_select|multi_select|priority_rank",
    "category": "target_audience|features|business|ux_design|technical|content",
    "options": [
      {{
        "value": "option_key",
        "label": "Descriptive option text",
        "description": "Optional brief explanation of what this choice means"
      }}
    ],
    "allow_custom": true/false, // Whether to show "Other" option with text input
    "why_asking": "Brief explanation of why this matters for UX design"
  }}
]

Example for a library app:
{{
  "question": "Who will be the primary users of this library app?",
  "type": "multi_select",
  "options": [
    {{"value": "students", "label": "Students", "description": "High school and college students looking for study materials"}},
    {{"value": "casual_readers", "label": "Casual Readers", "description": "People who read for pleasure and entertainment"}},
    {{"value": "researchers", "label": "Researchers", "description": "Academic researchers and professionals"}},
    {{"value": "book_clubs", "label": "Book Club Members", "description": "Groups that read and discuss books together"}},
    {{"value": "parents", "label": "Parents with Children", "description": "Looking for children's books and educational materials"}}
  ]
}}

Make ALL questions specific to {app_idea} with smart, contextual answer options."""

        try:
            response = self.client.messages.create(
                model=self.default_model,
                max_tokens=4000,
                temperature=0.7,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            # Extract JSON from response
            content = response.content[0].text
            
            # Clean up the response to get just the JSON
            if "```json" in content:
                json_start = content.find("```json") + 7
                json_end = content.find("```", json_start)
                json_str = content[json_start:json_end].strip()
            elif "[" in content:
                json_start = content.find("[")
                json_end = content.rfind("]") + 1
                json_str = content[json_start:json_end]
            else:
                json_str = content
            
            questions = json.loads(json_str)
            
            # Ensure we have enough questions
            if len(questions) < 10:
                logger.warning(f"Only generated {len(questions)} questions, expected at least 10")
            
            # Process and validate questions
            for i, q in enumerate(questions):
                if 'id' not in q:
                    q['id'] = i + 1
                if 'type' not in q:
                    q['type'] = 'single_select'
                if 'category' not in q:
                    q['category'] = 'general'
                if 'allow_custom' not in q:
                    q['allow_custom'] = True
                    
                # Ensure options have proper structure
                if 'options' in q and isinstance(q['options'], list):
                    for j, opt in enumerate(q['options']):
                        if isinstance(opt, str):
                            # Convert simple string to proper structure
                            q['options'][j] = {
                                'value': f"option_{j}",
                                'label': opt
                            }
            
            return questions
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            return self._get_fallback_questions(app_idea)
        except Exception as e:
            logger.error(f"Error generating questions with Claude: {e}")
            return self._get_fallback_questions(app_idea)
    
    def _get_fallback_questions(self, app_idea: str) -> List[Dict[str, Any]]:
        """Fallback questions with smart options if Claude fails"""
        return [
            {
                "id": 1,
                "question": "Who is your primary target audience?",
                "type": "multi_select",
                "category": "target_audience",
                "options": [
                    {"value": "gen_z", "label": "Gen Z (18-25)", "description": "Digital natives, mobile-first"},
                    {"value": "millennials", "label": "Millennials (26-40)", "description": "Tech-savvy professionals"},
                    {"value": "gen_x", "label": "Gen X (41-55)", "description": "Established professionals"},
                    {"value": "seniors", "label": "Seniors (55+)", "description": "May need larger fonts, simpler navigation"},
                    {"value": "business", "label": "Business Users", "description": "B2B, professional tools"},
                    {"value": "everyone", "label": "General Public", "description": "Broad appeal across ages"}
                ],
                "allow_custom": True,
                "why_asking": "Understanding the target audience helps design appropriate UI patterns and features"
            },
            {
                "id": 2,
                "question": "What is the primary purpose of your app?",
                "type": "single_select",
                "category": "features",
                "options": [
                    {"value": "social", "label": "Social/Community", "description": "Connect people, share content"},
                    {"value": "productivity", "label": "Productivity/Tools", "description": "Help users get work done"},
                    {"value": "entertainment", "label": "Entertainment", "description": "Games, media, fun content"},
                    {"value": "education", "label": "Education/Learning", "description": "Teach skills or knowledge"},
                    {"value": "commerce", "label": "E-commerce/Marketplace", "description": "Buy, sell, or trade"},
                    {"value": "health", "label": "Health/Wellness", "description": "Fitness, medical, mental health"},
                    {"value": "utility", "label": "Utility/Service", "description": "Solve specific problems"}
                ],
                "allow_custom": True,
                "why_asking": "The app's purpose drives fundamental design decisions"
            },
            {
                "id": 3,
                "question": "How often will users typically engage with your app?",
                "type": "single_select",
                "category": "target_audience",
                "options": [
                    {"value": "multiple_daily", "label": "Multiple times per day", "description": "Like social media or messaging"},
                    {"value": "daily", "label": "Once daily", "description": "Like news or fitness apps"},
                    {"value": "few_weekly", "label": "Few times per week", "description": "Like shopping or planning apps"},
                    {"value": "weekly", "label": "Weekly", "description": "Like meal planning or finance apps"},
                    {"value": "occasionally", "label": "Occasionally/As needed", "description": "Like travel or service apps"}
                ],
                "allow_custom": False,
                "why_asking": "Usage frequency affects design for quick access vs detailed exploration"
            },
            {
                "id": 4,
                "question": "Select the key features your app needs (choose all that apply):",
                "type": "multi_select",
                "category": "features",
                "options": [
                    {"value": "user_auth", "label": "User Accounts/Login", "description": "Personal profiles and data"},
                    {"value": "social_features", "label": "Social Features", "description": "Comments, likes, sharing"},
                    {"value": "search", "label": "Search & Filters", "description": "Find content quickly"},
                    {"value": "notifications", "label": "Push Notifications", "description": "Keep users engaged"},
                    {"value": "offline", "label": "Offline Mode", "description": "Work without internet"},
                    {"value": "payments", "label": "Payments/Transactions", "description": "Process money"},
                    {"value": "maps", "label": "Maps/Location", "description": "Location-based features"},
                    {"value": "camera", "label": "Camera/Media Upload", "description": "User-generated content"},
                    {"value": "realtime", "label": "Real-time Updates", "description": "Live data or chat"},
                    {"value": "analytics", "label": "Analytics/Reports", "description": "Data visualization"}
                ],
                "allow_custom": True,
                "why_asking": "Core features determine the app's architecture and main screens"
            },
            {
                "id": 5,
                "question": "What platform should we prioritize for launch?",
                "type": "single_select",
                "category": "technical",
                "options": [
                    {"value": "ios_first", "label": "iOS First", "description": "iPhone users, then Android"},
                    {"value": "android_first", "label": "Android First", "description": "Android users, then iOS"},
                    {"value": "mobile_both", "label": "Both Mobile Platforms", "description": "iOS and Android together"},
                    {"value": "web_first", "label": "Web First", "description": "Browser-based, then mobile"},
                    {"value": "web_mobile", "label": "Web + Mobile", "description": "All platforms from start"},
                    {"value": "desktop", "label": "Desktop App", "description": "Windows/Mac application"}
                ],
                "allow_custom": False,
                "why_asking": "Platform choice affects design patterns and development approach"
            },
            {
                "id": 6,
                "question": "What visual style best fits your brand?",
                "type": "single_select",
                "category": "ux_design",
                "options": [
                    {"value": "minimal", "label": "Minimal/Clean", "description": "Simple, lots of white space"},
                    {"value": "playful", "label": "Playful/Fun", "description": "Colorful, animated, friendly"},
                    {"value": "professional", "label": "Professional/Corporate", "description": "Serious, trustworthy"},
                    {"value": "bold", "label": "Bold/Modern", "description": "Strong colors, big typography"},
                    {"value": "elegant", "label": "Elegant/Premium", "description": "Sophisticated, luxury feel"},
                    {"value": "tech", "label": "Tech/Futuristic", "description": "Cutting-edge, innovative"}
                ],
                "allow_custom": True,
                "why_asking": "Visual style guides the entire design system"
            },
            {
                "id": 7,
                "question": "What's your primary business model?",
                "type": "single_select",
                "category": "business",
                "options": [
                    {"value": "free", "label": "Completely Free", "description": "No monetization planned"},
                    {"value": "ads", "label": "Ad-Supported", "description": "Free with advertisements"},
                    {"value": "freemium", "label": "Freemium", "description": "Free base, paid upgrades"},
                    {"value": "subscription", "label": "Subscription", "description": "Monthly/yearly fees"},
                    {"value": "one_time", "label": "One-Time Purchase", "description": "Pay once to download"},
                    {"value": "marketplace", "label": "Transaction Fees", "description": "Take cut of sales"},
                    {"value": "b2b", "label": "B2B/Enterprise", "description": "Sell to businesses"}
                ],
                "allow_custom": True,
                "why_asking": "Business model affects UI elements like paywalls and upgrade prompts"
            },
            {
                "id": 8,
                "question": "Rank these qualities by importance for your app:",
                "type": "priority_rank",
                "category": "ux_design",
                "options": [
                    {"value": "easy_to_use", "label": "Easy to Use", "description": "Intuitive for anyone"},
                    {"value": "fast", "label": "Fast Performance", "description": "Quick load times"},
                    {"value": "beautiful", "label": "Beautiful Design", "description": "Visually impressive"},
                    {"value": "feature_rich", "label": "Feature Rich", "description": "Lots of functionality"},
                    {"value": "secure", "label": "Secure/Private", "description": "Protect user data"}
                ],
                "allow_custom": False,
                "why_asking": "Priorities help make design trade-offs"
            }
        ]
    
    def generate_ux_specifications(self, app_idea: str, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Generate detailed UX specifications based on requirements"""
        
        # Format the requirements nicely for the prompt
        formatted_reqs = self._format_requirements(requirements)
        
        prompt = f"""You are a senior UX designer creating detailed specifications for: "{app_idea}"

Based on these requirements gathered from the client:
{formatted_reqs}

Create comprehensive UX specifications including:

1. **User Personas** (2-3 detailed personas based on the target audience selected)
2. **Core User Flows** (step-by-step workflows for the main features selected)
3. **Information Architecture** (site map based on features and navigation needs)
4. **Screen List** (comprehensive list of all screens needed)
5. **Design System Guidelines** 
   - Color palette (based on visual style selected)
   - Typography system
   - Spacing and layout grid
   - Component library
6. **Key Interaction Patterns** (based on platform and features)
7. **Responsive Design Strategy** (how it adapts across selected platforms)
8. **Accessibility Considerations**

Provide specific, actionable details that a UI designer could use to create the actual screens.
Make all recommendations based on the specific requirements provided.

Return as a structured JSON object."""

        try:
            response = self.client.messages.create(
                model=self.default_model,
                max_tokens=4000,
                temperature=0.7,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            content = response.content[0].text
            
            # Parse JSON from response
            if "```json" in content:
                json_start = content.find("```json") + 7
                json_end = content.find("```", json_start)
                json_str = content[json_start:json_end].strip()
            else:
                json_str = content
            
            return json.loads(json_str)
            
        except Exception as e:
            logger.error(f"Error generating UX specs: {e}")
            raise
    
    def _format_requirements(self, requirements: Dict[str, Any]) -> str:
        """Format requirements into readable text for the prompt"""
        formatted = []
        
        if 'input' in requirements:
            formatted.append(f"Original Request: {requirements['input']}")
        
        if 'dynamicAnswers' in requirements:
            formatted.append("\nUser Requirements:")
            for question_id, answer in requirements['dynamicAnswers'].items():
                formatted.append(f"- Question {question_id}: {answer}")
        
        return "\n".join(formatted)

    def generate_html_from_specs(self, specs: Dict[str, Any], screen_name: str) -> str:
        """Generate HTML/CSS for a specific screen based on UX specs"""
        
        prompt = f"""You are a expert UI developer implementing a specific screen based on these UX specifications:

{json.dumps(specs, indent=2)}

Create a production-ready HTML page for: {screen_name}

Requirements:
1. Modern, responsive design using CSS Grid/Flexbox
2. Follow the exact design system specified (colors, fonts, spacing)
3. Semantic HTML5 with accessibility features
4. Interactive elements with hover states and micro-animations
5. Mobile-first responsive design
6. Smooth animations and transitions
7. Follow the specific interaction patterns defined in the UX specs

Include:
- Complete HTML structure
- Embedded CSS with the specified design system
- Basic JavaScript for interactions
- Font Awesome icons (via CDN)
- Google Fonts as specified
- Loading states and micro-interactions
- Proper responsive breakpoints

Make it look like a real, polished application screen that matches the specifications exactly."""

        try:
            response = self.client.messages.create(
                model=self.default_model,
                max_tokens=8000,
                temperature=0.7,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            return response.content[0].text
            
        except Exception as e:
            logger.error(f"Error generating HTML: {e}")
            raise

# Initialize service
claude_service = ClaudeService()