from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum

class CategoryEnum(str, Enum):
    MATERIALS = "materials"
    EQUIPMENT = "equipment"
    SERVICES = "services"
    SOFTWARE = "software"
    CONSTRUCTION = "construction"
    MANUFACTURING = "manufacturing"

class TimeframeEnum(str, Enum):
    ONE_MONTH = "1month"
    THREE_MONTHS = "3months"
    SIX_MONTHS = "6months"
    ONE_YEAR = "1year"

class ProcurementAnalysisRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=200, description="Search query for procurement analysis")
    category: CategoryEnum = Field(..., description="Product/service category")
    location: Optional[str] = Field(None, max_length=100, description="Geographic location filter")
    budget_range: Optional[Dict[str, float]] = Field(None, description="Budget constraints")
    timeline: Optional[str] = Field(None, description="Required timeline")
    
    @validator('query')
    def validate_query(cls, v):
        if not v or v.strip() == "":
            raise ValueError("Query cannot be empty")
        return v.strip()

class SupplierDiscoveryRequest(BaseModel):
    product: str = Field(..., min_length=2, max_length=150, description="Product or service name")
    location: Optional[str] = Field(None, max_length=100, description="Preferred location")
    requirements: List[str] = Field(default=[], description="Specific requirements list")
    certifications: List[str] = Field(default=[], description="Required certifications")
    min_rating: Optional[float] = Field(None, ge=1.0, le=5.0, description="Minimum supplier rating")
    max_results: Optional[int] = Field(10, ge=1, le=50, description="Maximum number of results")
    
    @validator('product')
    def validate_product(cls, v):
        if not v or v.strip() == "":
            raise ValueError("Product name cannot be empty")
        return v.strip()

class MarketIntelligenceRequest(BaseModel):
    product: str = Field(..., min_length=2, max_length=150, description="Product name")
    timeframe: TimeframeEnum = Field(..., description="Analysis timeframe")
    region: Optional[str] = Field(None, max_length=100, description="Regional focus")
    include_competitors: bool = Field(True, description="Include competitor analysis")
    include_trends: bool = Field(True, description="Include market trends")
    
    @validator('product')
    def validate_product(cls, v):
        if not v or v.strip() == "":
            raise ValueError("Product name cannot be empty")
        return v.strip()

class SearchQuery(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    max_results: int = Field(10, ge=1, le=100)
    search_type: str = Field("general", regex="^(supplier|market|general)$")
    
    @validator('query')
    def validate_query(cls, v):
        return v.strip()

class WebSocketMessage(BaseModel):
    message_type: str = Field(..., regex="^(status|progress|result|error)$")
    data: Dict[str, Any] = Field(default={})
    timestamp: Optional[str] = Field(None)
    request_id: Optional[str] = Field(None)