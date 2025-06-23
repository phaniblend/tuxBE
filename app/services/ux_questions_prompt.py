# ux_questions_prompt.py - Professional UX question generation system

UX_QUESTION_SYSTEM_PROMPT = """You are a Senior UX Designer with 15+ years of experience at top tech companies. 
You're conducting a comprehensive requirements gathering session for a new app project.

Your approach is:
- Thorough and methodical, covering all aspects needed for successful UX design
- Professional yet approachable in tone
- Focused on understanding user needs, business goals, and technical constraints
- Based on industry best practices and modern UX methodologies

When generating questions:
1. Ask specific, actionable questions that lead to clear design decisions
2. Cover all essential UX areas systematically
3. Mix question types to maintain engagement
4. Ensure questions are relevant to the specific app type
5. Include context about why each question matters"""

def get_enhanced_question_prompt(app_idea: str) -> str:
    """Generate enhanced prompt for professional UX questions"""
    
    return f"""As a Senior UX Designer, generate a comprehensive set of questions for a new app project.

The client wants to build: "{app_idea}"

Create 15-20 professional questions that cover:

### 1. USER RESEARCH & PERSONAS (3-4 questions)
- Target demographics and psychographics
- User goals, needs, and pain points  
- Accessibility requirements
- User technology comfort level

### 2. CORE FUNCTIONALITY & FEATURES (3-4 questions)
- Primary features and their priority
- User workflows and task flows
- Feature complexity and depth
- Integration with other tools/services

### 3. BUSINESS STRATEGY & GOALS (2-3 questions)
- Success metrics and KPIs
- Business model and monetization
- Market positioning and competition
- Growth and scaling plans

### 4. DESIGN & BRAND IDENTITY (2-3 questions)
- Visual design preferences
- Brand personality and tone
- Existing brand guidelines
- Competitor design references

### 5. INFORMATION ARCHITECTURE (2-3 questions)
- Content types and organization
- Navigation patterns
- Search and discovery needs
- Data relationships

### 6. TECHNICAL & PLATFORM (2-3 questions)
- Platform priorities (mobile, web, etc.)
- Performance requirements
- Security and privacy needs
- Third-party integrations

### 7. USER ENGAGEMENT & RETENTION (2-3 questions)
- Expected usage frequency
- Engagement mechanisms
- Social features
- Notification strategy

For each question:
- Make it specific to {app_idea} context
- Focus on extracting actionable information
- Avoid yes/no questions when possible
- Include follow-up context when helpful

Return as a JSON array with this structure:
[
  {{
    "id": 1,
    "question": "Specific, clear question text",
    "type": "multiple_choice|text|scale|multi_select|ranking",
    "category": "user_research|features|business|design|architecture|technical|engagement",
    "options": ["option1", "option2", ...], // for choice-based questions
    "placeholder": "Helpful example answer", // for text questions
    "why_asking": "Brief explanation of why this matters for UX design",
    "follow_up": "Optional follow-up prompt for more detail"
  }}
]

Example for a library app:
- "How do you envision users discovering books in your library? (search, browse, recommendations, social)"
- "What information is critical to display for each book? Rank by importance."
- "How should the borrowing process work from request to return?"

Make all questions this specific and thoughtful."""

def get_app_specific_prompts(app_idea: str) -> dict:
    """Get app-specific prompt enhancements based on app type"""
    
    app_idea_lower = app_idea.lower()
    
    # E-commerce related
    if any(word in app_idea_lower for word in ['shop', 'store', 'commerce', 'market', 'sell', 'buy']):
        return {
            "focus_areas": ["product discovery", "checkout flow", "payment methods", "inventory management"],
            "specific_questions": [
                "How should products be categorized and filtered?",
                "What payment methods need to be supported?",
                "How will order tracking and fulfillment work?"
            ]
        }
    
    # Social/Community related
    elif any(word in app_idea_lower for word in ['social', 'community', 'network', 'connect', 'share']):
        return {
            "focus_areas": ["user profiles", "content sharing", "privacy controls", "moderation"],
            "specific_questions": [
                "What types of content can users create and share?",
                "How should user connections/relationships work?",
                "What privacy controls do users need?"
            ]
        }
    
    # Education/Learning related
    elif any(word in app_idea_lower for word in ['learn', 'education', 'course', 'training', 'study']):
        return {
            "focus_areas": ["course structure", "progress tracking", "assessments", "collaboration"],
            "specific_questions": [
                "How should learning content be structured?",
                "What types of assessments or quizzes are needed?",
                "How will student progress be tracked?"
            ]
        }
    
    # Health/Fitness related
    elif any(word in app_idea_lower for word in ['health', 'fitness', 'medical', 'wellness', 'exercise']):
        return {
            "focus_areas": ["data tracking", "goal setting", "privacy/HIPAA", "professional integration"],
            "specific_questions": [
                "What health metrics need to be tracked?",
                "How will users set and monitor goals?",
                "Are there regulatory compliance requirements?"
            ]
        }
    
    # Productivity/Tools
    elif any(word in app_idea_lower for word in ['productivity', 'task', 'project', 'manage', 'organize']):
        return {
            "focus_areas": ["workflow management", "collaboration", "integrations", "reporting"],
            "specific_questions": [
                "What is the primary workflow users will follow?",
                "How will team collaboration work?",
                "What external tools need integration?"
            ]
        }
    
    # Default for other app types
    else:
        return {
            "focus_areas": ["core functionality", "user workflows", "data management", "user engagement"],
            "specific_questions": [
                "What is the primary action users will take?",
                "How frequently will users engage with the app?",
                "What makes this different from existing solutions?"
            ]
        }

def validate_questions(questions: list) -> list:
    """Validate and enhance questions to ensure quality"""
    
    required_categories = {
        'user_research': 2,
        'features': 3,
        'business': 2,
        'design': 2,
        'technical': 2
    }
    
    # Count questions by category
    category_counts = {}
    for q in questions:
        cat = q.get('category', 'general')
        category_counts[cat] = category_counts.get(cat, 0) + 1
    
    # Check if we have minimum questions per category
    for category, min_count in required_categories.items():
        if category_counts.get(category, 0) < min_count:
            print(f"Warning: Only {category_counts.get(category, 0)} questions in {category} category, expected at least {min_count}")
    
    # Ensure all questions have required fields
    for i, q in enumerate(questions):
        if 'id' not in q:
            q['id'] = i + 1
        
        if 'why_asking' not in q or not q['why_asking']:
            q['why_asking'] = "This helps understand user needs and design appropriate solutions"
        
        if q.get('type') == 'text' and 'placeholder' not in q:
            q['placeholder'] = "Please provide detailed information..."
        
        if q.get('type') in ['multiple_choice', 'multi_select'] and not q.get('options'):
            print(f"Warning: Question {q['id']} missing options for {q['type']} type")
    
    return questions

# Example usage in the service
def generate_comprehensive_questions(app_idea: str) -> list:
    """Generate comprehensive UX questions with validation"""
    
    # Get enhanced prompt
    prompt = get_enhanced_question_prompt(app_idea)
    
    # Get app-specific enhancements
    app_specific = get_app_specific_prompts(app_idea)
    
    # Add app-specific context to prompt
    if app_specific['specific_questions']:
        prompt += f"\n\nFor this type of app, also consider asking about:\n"
        prompt += "\n".join(f"- {q}" for q in app_specific['specific_questions'])
    
    # Generate questions (this would call Claude)
    # questions = claude_service.generate_questions_with_prompt(prompt)
    
    # Validate and enhance questions
    # questions = validate_questions(questions)
    
    # return questions
    
    return prompt  # For now, return the prompt for reference