from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, Any, Union
from datetime import datetime
from enum import Enum


# Enums
class QuestionType(str, Enum):
    TEXT = "text"
    SELECT = "select"
    MULTISELECT = "multiselect"
    NUMBER = "number"
    TEXTAREA = "textarea"


class GenerationMode(str, Enum):
    HTML = "html"
    IMAGE = "image"
    HYBRID = "hybrid"


class ExportFormat(str, Enum):
    HTML = "html"
    JSON = "json"
    SVG = "svg"
    PNG = "png"


# Request/Response Models
class Question(BaseModel):
    id: str
    question: str
    type: QuestionType
    options: Optional[List[str]] = None
    required: bool = True
    help_text: Optional[str] = None
    default_value: Optional[Union[str, List[str]]] = None
    placeholder: Optional[str] = None
    validation: Optional[Dict[str, Any]] = None


class AppIdeaInput(BaseModel):
    app_idea: str = Field(..., min_length=10, max_length=1000)


class RequirementsInput(BaseModel):
    purpose: str
    audience: Union[str, List[str]]
    demographics: Optional[str] = None
    goals: Union[str, List[str]]
    use_cases: List[str] = Field(default_factory=list)
    technical_requirements: Optional[List[str]] = None
    accessibility: Optional[List[str]] = None
    simulate_roles: bool = True


class UIElement(BaseModel):
    id: str
    type: str
    content: str
    position: Dict[str, float] = {"x": 0, "y": 0}
    size: Dict[str, Union[str, float]] = {"width": "auto", "height": "auto"}
    styles: Dict[str, str] = Field(default_factory=dict)


class ScreenSpec(BaseModel):
    id: Optional[str] = None
    name: str
    description: str
    elements: List[Union[str, UIElement]]
    user_flow: Optional[str] = None
    interactions: Optional[List[str]] = None
    layout_type: Optional[str] = "responsive"


class ComponentRecommendation(BaseModel):
    primary_library: Dict[str, Any]
    alternative_libraries: Optional[List[Dict[str, Any]]] = None
    component_mapping: Dict[str, List[str]] = Field(default_factory=dict)
    custom_components: List[str] = Field(default_factory=list)


class DataModel(BaseModel):
    entities: List[Dict[str, Any]] = Field(default_factory=list)
    relationships: Optional[List[str]] = None
    api_endpoints: List[Dict[str, str]] = Field(default_factory=list)
    validation_rules: Dict[str, Any] = Field(default_factory=dict)


class InteractionPatterns(BaseModel):
    global_patterns: Dict[str, Dict[str, str]] = Field(default_factory=dict)
    transitions: Dict[str, str] = Field(default_factory=dict)
    micro_interactions: List[str] = Field(default_factory=list)


class ResponsiveDesign(BaseModel):
    breakpoints: Dict[str, str]
    layout_rules: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    typography: Dict[str, Dict[str, str]] = Field(default_factory=dict)
    touch_targets: Dict[str, str] = Field(default_factory=dict)


class SEOPerformance(BaseModel):
    seo: Dict[str, Any]
    performance: Dict[str, Any]
    image_optimization: Optional[Dict[str, Any]] = None


class RoleInsight(BaseModel):
    designer: str
    analyst: str
    architect: str
    info_architect: Optional[str] = None
    content_producer: Optional[str] = None
    ux_engineer: Optional[str] = None


class UXSpecification(BaseModel):
    screens: List[ScreenSpec]
    role_insights: Optional[RoleInsight] = None
    component_library: Optional[ComponentRecommendation] = None
    data_model: Optional[DataModel] = None
    interaction_patterns: Optional[InteractionPatterns] = None
    responsive_design: Optional[ResponsiveDesign] = None
    seo_performance: Optional[SEOPerformance] = None
    ia_structure: Optional[Dict[str, Any]] = None
    standards: Optional[Dict[str, Any]] = None


class Screen(BaseModel):
    id: str
    name: str
    description: str
    html_layout: str
    elements: List[UIElement]
    mockup_url: Optional[str] = None
    generation_method: Optional[str] = None
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class GenerateQuestionsResponse(BaseModel):
    questions: List[Question]
    total_questions: int
    skip_option: Optional[Dict[str, Any]] = None
    follow_up_rules: Optional[List[Dict[str, Any]]] = None


class GenerateScreensRequest(BaseModel):
    specs: UXSpecification
    generation_mode: GenerationMode = GenerationMode.HTML
    image_style: Optional[str] = "clean wireframe"


class GenerateScreensResponse(BaseModel):
    screens: List[Screen]
    total_screens: int
    generation_mode: str
    mockup_images: Optional[List[Dict[str, Any]]] = None


class SessionData(BaseModel):
    id: str
    created_at: datetime
    updated_at: datetime
    data: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None


class ExportRequest(BaseModel):
    screens: List[Screen]
    project_name: str = "TUX Project"
    ux_specs: Optional[UXSpecification] = None
    requirements: Optional[RequirementsInput] = None
    format: ExportFormat


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str
    services: Optional[Dict[str, str]] = None


class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Validation examples
# not recognised by the AI, but useful for ensuring data integrity
class GenerateDesignRequest(BaseModel):
    requirements: RequirementsInput
    
    @validator('requirements')
    def validate_requirements(cls, v):
        if not v.purpose:
            raise ValueError("Purpose is required")
        if not v.audience:
            raise ValueError("Audience is required")
        return 