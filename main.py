import os
import time
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from agent_graph import procurement_agent
from competitive_service import CompetitiveIntelligenceService

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="Procurement Intelligence System", version="1.0.0")

# Initialize services
competitive_service = CompetitiveIntelligenceService()

# Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GROQ_API_KEY or not GEMINI_API_KEY:
    raise ValueError("Missing required API keys. Please set GROQ_API_KEY and GEMINI_API_KEY in .env file")

# Pydantic models
class ProcurementRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=200)
    location: Optional[str] = None
    category: Optional[str] = None

class SupplierInfo(BaseModel):
    name: str
    location: str
    description: str
    website: Optional[str] = None
    confidence_score: float
    certifications: List[str] = []
    rating: Optional[float] = None

class MarketInsight(BaseModel):
    price_trend: str
    key_factors: List[str]
    recommendations: List[str]

class ProcurementResponse(BaseModel):
    suppliers: List[SupplierInfo]
    market_insights: MarketInsight
    summary: str
    processing_time: float

# Competitive Intelligence Models
class CompetitiveBenchmarkRequest(BaseModel):
    product: str = Field(..., min_length=3, max_length=200)
    supplier_quote: Optional[float] = None
    currency: str = "USD"
    quantity: Optional[int] = None
    location: Optional[str] = None
    company_size: Optional[str] = None

class CompetitorInfo(BaseModel):
    name: str
    price: Optional[float] = None
    market_position: str
    strengths: List[str] = []

class NegotiationStrategy(BaseModel):
    suggested_counter_offer: Optional[float] = None
    leverage_points: List[str] = []
    alternative_suppliers: List[str] = []
    risk_factors: List[str] = []
    timeline_recommendation: str
    opening_approach: str

# New models for enhanced market intelligence
class PriceHistoryPoint(BaseModel):
    month: str
    price: float
    market_events: List[str] = []

class TrendAnalysis(BaseModel):
    direction: str  # "upward", "downward", "stable"
    volatility: str  # "high", "medium", "low"
    seasonal_pattern: str
    current_position: str

class HistoricalTrends(BaseModel):
    price_history: List[PriceHistoryPoint] = []
    trend_analysis: TrendAnalysis
    insights: List[str] = []

class PriceForecast(BaseModel):
    direction: str  # "up", "down", "stable"
    range: str  # percentage range

class OptimalWindow(BaseModel):
    start_date: str
    end_date: str
    reasoning: str

class SavingsOpportunity(BaseModel):
    amount_per_unit: str
    total_potential: str
    risk_of_waiting: str

class TimingIntelligence(BaseModel):
    recommendation: str  # "BUY_NOW", "WAIT", "MONITOR"
    urgency_level: str  # "HIGH", "MEDIUM", "LOW"
    price_forecast: Dict[str, PriceForecast]  # "30_days", "60_days"
    optimal_window: OptimalWindow
    savings_opportunity: SavingsOpportunity

class BenchmarkResult(BaseModel):
    market_average_price: Optional[float] = None
    price_variance: Optional[float] = None
    your_position: str  # "above_market", "below_market", "at_market"
    percentile_ranking: Optional[int] = None
    key_competitors: List[CompetitorInfo] = []
    negotiation_strategy: NegotiationStrategy
    historical_trends: Optional[HistoricalTrends] = None
    timing_intelligence: Optional[TimingIntelligence] = None
    market_insights: List[str] = []
    processing_time: float

# Mount static files
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

# Setup templates
templates = Jinja2Templates(directory="frontend/templates")

# Routes
@app.get("/", response_class=HTMLResponse)
async def get_dashboard(request: Request):
    """Serve the main dashboard"""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.post("/analyze", response_model=ProcurementResponse)
async def analyze_procurement(request: ProcurementRequest):
    """Main endpoint for procurement analysis using LangGraph agent"""
    try:
        print(f"🚀 Starting LangGraph workflow for: {request.query}")
        
        # Run the LangGraph agent workflow
        result = await procurement_agent.run_analysis(
            query=request.query,
            location=request.location,
            category=request.category
        )
        
        # Convert suppliers back to Pydantic models
        suppliers = [SupplierInfo(**supplier) for supplier in result["suppliers"]]
        
        # Create market insights
        market_insights = MarketInsight(**result["market_insights"])
        
        return ProcurementResponse(
            suppliers=suppliers,
            market_insights=market_insights,
            summary=result["summary"],
            processing_time=result["processing_time"]
        )
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.post("/api/v1/competitive/benchmark", response_model=BenchmarkResult)
async def analyze_competitive_benchmark(request: CompetitiveBenchmarkRequest):
    """Analyze competitive positioning and industry benchmarks"""
    try:
        print(f"🎯 Starting competitive benchmark analysis for: {request.product}")
        
        # Run competitive analysis
        result = await competitive_service.analyze_market_benchmark(request)
        
        return result
        
    except Exception as e:
        print(f"❌ Competitive benchmark analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Competitive analysis failed: {str(e)}")

# Additional endpoints and health checks can be added here

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
