from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

class VerificationStatus(str, Enum):
    VERIFIED = "verified"
    UNVERIFIED = "unverified"
    PENDING = "pending"
    FAILED = "failed"

class SupplierInfo(BaseModel):
    name: str = Field(..., description="Supplier company name")
    website: Optional[str] = Field(None, description="Company website URL")
    location: str = Field(..., description="Supplier location")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Data confidence score")
    certifications: List[str] = Field(default=[], description="List of certifications")
    contact_info: Dict[str, str] = Field(default={}, description="Contact information")
    verification_status: VerificationStatus = Field(..., description="Verification status")
    specialties: List[str] = Field(default=[], description="Areas of specialization")
    company_size: Optional[str] = Field(None, description="Company size category")
    year_established: Optional[int] = Field(None, description="Year company was established")
    rating: Optional[float] = Field(None, ge=1.0, le=5.0, description="Supplier rating")
    description: Optional[str] = Field(None, description="Company description")

class MarketTrend(BaseModel):
    trend_type: str = Field(..., description="Type of trend")
    description: str = Field(..., description="Trend description")
    impact: str = Field(..., description="Market impact")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Trend confidence score")

class PriceInsight(BaseModel):
    price_range: Dict[str, float] = Field(..., description="Price range (min, max, avg)")
    currency: str = Field("USD", description="Currency code")
    unit: Optional[str] = Field(None, description="Price unit")
    trend: str = Field(..., description="Price trend direction")
    factors: List[str] = Field(default=[], description="Price influencing factors")

class MarketIntelligence(BaseModel):
    product_category: str = Field(..., description="Product category")
    price_insights: PriceInsight = Field(..., description="Pricing information")
    market_trends: List[MarketTrend] = Field(default=[], description="Market trends")
    recommendations: List[str] = Field(default=[], description="Procurement recommendations")
    data_freshness: datetime = Field(default_factory=datetime.now, description="Data timestamp")
    market_size: Optional[str] = Field(None, description="Market size information")
    growth_rate: Optional[str] = Field(None, description="Market growth rate")
    key_players: List[str] = Field(default=[], description="Key market players")
    opportunities: List[str] = Field(default=[], description="Market opportunities")
    risks: List[str] = Field(default=[], description="Market risks")

class SupplierDiscoveryResponse(BaseModel):
    suppliers: List[SupplierInfo] = Field(..., description="List of discovered suppliers")
    total_found: int = Field(..., description="Total suppliers found")
    search_query: str = Field(..., description="Original search query")
    location_filter: Optional[str] = Field(None, description="Applied location filter")
    processing_time: float = Field(..., description="Response time in seconds")
    data_sources: List[str] = Field(default=[], description="Data sources used")

class ProcurementAnalysisResponse(BaseModel):
    suppliers: List[SupplierInfo] = Field(..., description="Supplier information")
    market_intelligence: MarketIntelligence = Field(..., description="Market analysis")
    summary: str = Field(..., description="Executive summary")
    recommendations: List[str] = Field(default=[], description="Top recommendations")
    processing_time: float = Field(..., description="Total processing time")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Overall confidence")
    next_steps: List[str] = Field(default=[], description="Suggested next steps")

class MarketIntelligenceResponse(BaseModel):
    market_intelligence: MarketIntelligence = Field(..., description="Market analysis data")
    competitive_landscape: Dict[str, Any] = Field(default={}, description="Competitive analysis")
    forecast: Dict[str, Any] = Field(default={}, description="Market forecast")
    processing_time: float = Field(..., description="Response time in seconds")

class HealthResponse(BaseModel):
    status: str = Field(..., description="Service health status")
    version: str = Field("1.0.0", description="API version")
    timestamp: datetime = Field(default_factory=datetime.now, description="Health check timestamp")
    services: Dict[str, str] = Field(default={}, description="Service statuses")
    uptime: Optional[float] = Field(None, description="Service uptime in seconds")

class ErrorResponse(BaseModel):
    error: str = Field(..., description="Error message")
    error_code: str = Field(..., description="Error code")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")
    request_id: Optional[str] = Field(None, description="Request ID for tracking")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")

class SearchResult(BaseModel):
    title: str = Field(..., description="Result title")
    url: str = Field(..., description="Result URL")
    snippet: str = Field(..., description="Result snippet")
    source: str = Field(..., description="Data source")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Relevance score")
    
class WebSocketStatusResponse(BaseModel):
    status: str = Field(..., description="Current operation status")
    progress: int = Field(..., ge=0, le=100, description="Progress percentage")
    message: str = Field(..., description="Status message")
    timestamp: datetime = Field(default_factory=datetime.now, description="Status timestamp")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional data")