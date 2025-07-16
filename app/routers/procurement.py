from fastapi import APIRouter, HTTPException, BackgroundTasks, Request
from typing import List
import logging
import time
import asyncio
from app.models.requests import (
    ProcurementAnalysisRequest,
    SupplierDiscoveryRequest,
    MarketIntelligenceRequest
)
from app.models.responses import (
    ProcurementAnalysisResponse,
    SupplierDiscoveryResponse,
    MarketIntelligenceResponse,
    ErrorResponse
)
from app.services.supplier_agent import SupplierAgent
from app.services.market_agent import MarketAgent
from app.services.llm_service import LLMService
from app.utils.rate_limiter import rate_limit
from app.utils.cache import cache_search_results, cache_supplier_data, cache_market_data
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["procurement"])

# Initialize services
supplier_agent = SupplierAgent()
market_agent = MarketAgent()
llm_service = LLMService()

@router.post("/procurement/analyze", response_model=ProcurementAnalysisResponse)
@rate_limit(max_requests=5, window_seconds=60)
async def analyze_procurement(
    request: ProcurementAnalysisRequest,
    background_tasks: BackgroundTasks,
    http_request: Request
):
    """
    Complete procurement analysis combining supplier discovery and market intelligence
    """
    start_time = time.time()
    
    try:
        logger.info(f"Starting procurement analysis for: {request.query}")
        
        # Convert to individual service requests
        supplier_request = SupplierDiscoveryRequest(
            product=request.query,
            location=request.location,
            max_results=10
        )
        
        market_request = MarketIntelligenceRequest(
            product=request.query,
            timeframe="6months",
            region=request.location,
            include_competitors=True,
            include_trends=True
        )
        
        # Execute supplier discovery and market analysis in parallel
        supplier_task = supplier_agent.discover_suppliers(supplier_request)
        market_task = market_agent.analyze_market(market_request)
        
        # Wait for both tasks to complete
        supplier_response, market_response = await asyncio.gather(
            supplier_task,
            market_task,
            return_exceptions=True
        )
        
        # Handle exceptions
        if isinstance(supplier_response, Exception):
            logger.error(f"Supplier discovery failed: {supplier_response}")
            raise HTTPException(
                status_code=500,
                detail=f"Supplier discovery failed: {str(supplier_response)}"
            )
        
        if isinstance(market_response, Exception):
            logger.error(f"Market analysis failed: {market_response}")
            raise HTTPException(
                status_code=500,
                detail=f"Market analysis failed: {str(market_response)}"
            )
        
        # Generate executive summary
        summary_data = await llm_service.generate_procurement_summary(
            supplier_response.suppliers,
            market_response.market_intelligence,
            request.query
        )
        
        # Calculate overall confidence score
        supplier_confidence = sum(s.confidence_score for s in supplier_response.suppliers) / len(supplier_response.suppliers) if supplier_response.suppliers else 0
        market_confidence = 0.8  # Default market confidence
        overall_confidence = (supplier_confidence + market_confidence) / 2
        
        processing_time = time.time() - start_time
        
        # Create comprehensive response
        response = ProcurementAnalysisResponse(
            suppliers=supplier_response.suppliers,
            market_intelligence=market_response.market_intelligence,
            summary=summary_data.get("executive_summary", "Analysis completed successfully"),
            recommendations=summary_data.get("recommendations", []),
            processing_time=processing_time,
            confidence_score=overall_confidence,
            next_steps=summary_data.get("next_steps", [])
        )
        
        logger.info(f"Procurement analysis completed in {processing_time:.2f}s")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Procurement analysis failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@router.post("/suppliers/discover", response_model=SupplierDiscoveryResponse)
@rate_limit(max_requests=10, window_seconds=60)
@cache_supplier_data(ttl=1800)  # Cache for 30 minutes
async def discover_suppliers(
    request: SupplierDiscoveryRequest,
    background_tasks: BackgroundTasks,
    http_request: Request
):
    """
    Discover suppliers for specific products/services
    """
    start_time = time.time()
    
    try:
        logger.info(f"Starting supplier discovery for: {request.product}")
        
        # Validate request
        if not request.product or len(request.product.strip()) < 2:
            raise HTTPException(
                status_code=400,
                detail="Product name must be at least 2 characters long"
            )
        
        # Execute supplier discovery
        response = await supplier_agent.discover_suppliers(request)
        
        processing_time = time.time() - start_time
        response.processing_time = processing_time
        
        logger.info(f"Supplier discovery completed in {processing_time:.2f}s, found {len(response.suppliers)} suppliers")
        
        # Background task for analytics
        background_tasks.add_task(
            log_supplier_discovery_metrics,
            request.product,
            len(response.suppliers),
            processing_time
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Supplier discovery failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Supplier discovery failed: {str(e)}"
        )

@router.post("/market/intelligence", response_model=MarketIntelligenceResponse)
@rate_limit(max_requests=10, window_seconds=60)
@cache_market_data(ttl=3600)  # Cache for 1 hour
async def get_market_intelligence(
    request: MarketIntelligenceRequest,
    background_tasks: BackgroundTasks,
    http_request: Request
):
    """
    Get market intelligence for specific products
    """
    start_time = time.time()
    
    try:
        logger.info(f"Starting market intelligence for: {request.product}")
        
        # Validate request
        if not request.product or len(request.product.strip()) < 2:
            raise HTTPException(
                status_code=400,
                detail="Product name must be at least 2 characters long"
            )
        
        # Execute market analysis
        response = await market_agent.analyze_market(request)
        
        processing_time = time.time() - start_time
        response.processing_time = processing_time
        
        logger.info(f"Market intelligence completed in {processing_time:.2f}s")
        
        # Background task for analytics
        background_tasks.add_task(
            log_market_intelligence_metrics,
            request.product,
            request.timeframe.value,
            processing_time
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Market intelligence failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Market intelligence failed: {str(e)}"
        )

@router.get("/suppliers/suggestions", response_model=List[str])
@rate_limit(max_requests=20, window_seconds=60)
async def get_supplier_suggestions(query: str, limit: int = 5):
    """
    Get search suggestions for supplier queries
    """
    try:
        if not query or len(query.strip()) < 2:
            return []
        
        from app.services.search_service import SearchService
        search_service = SearchService()
        suggestions = await search_service.get_search_suggestions(query)
        
        return suggestions[:limit]
        
    except Exception as e:
        logger.error(f"Supplier suggestions failed: {e}")
        return []

@router.get("/market/trends", response_model=dict)
@rate_limit(max_requests=10, window_seconds=60)
async def get_market_trends(product: str, timeframe: str = "6months"):
    """
    Get market trends for specific product
    """
    try:
        if not product or len(product.strip()) < 2:
            raise HTTPException(
                status_code=400,
                detail="Product name must be at least 2 characters long"
            )
        
        # Create market intelligence request
        request = MarketIntelligenceRequest(
            product=product,
            timeframe=timeframe,
            include_competitors=False,
            include_trends=True
        )
        
        # Get market intelligence
        response = await market_agent.analyze_market(request)
        
        # Return just the trends
        return {
            "product": product,
            "timeframe": timeframe,
            "trends": [trend.dict() for trend in response.market_intelligence.market_trends],
            "price_insights": response.market_intelligence.price_insights.dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Market trends failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Market trends failed: {str(e)}"
        )

@router.get("/suppliers/{supplier_id}/details", response_model=dict)
@rate_limit(max_requests=20, window_seconds=60)
async def get_supplier_details(supplier_id: str):
    """
    Get detailed information about a specific supplier
    """
    try:
        # In a real implementation, this would lookup supplier by ID
        # For now, return a placeholder response
        return {
            "supplier_id": supplier_id,
            "message": "Supplier details endpoint - to be implemented with persistent storage",
            "suggestion": "Use supplier discovery endpoint to get current supplier information"
        }
        
    except Exception as e:
        logger.error(f"Supplier details failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Supplier details failed: {str(e)}"
        )

# Background task functions
async def log_supplier_discovery_metrics(product: str, supplier_count: int, processing_time: float):
    """
    Log supplier discovery metrics
    """
    try:
        logger.info(f"Supplier Discovery Metrics - Product: {product}, Count: {supplier_count}, Time: {processing_time:.2f}s")
        # In production, send to analytics service
    except Exception as e:
        logger.error(f"Failed to log supplier discovery metrics: {e}")

async def log_market_intelligence_metrics(product: str, timeframe: str, processing_time: float):
    """
    Log market intelligence metrics
    """
    try:
        logger.info(f"Market Intelligence Metrics - Product: {product}, Timeframe: {timeframe}, Time: {processing_time:.2f}s")
        # In production, send to analytics service
    except Exception as e:
        logger.error(f"Failed to log market intelligence metrics: {e}")

# Error handlers
@router.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Handle HTTP exceptions
    """
    return ErrorResponse(
        error=exc.detail,
        error_code=str(exc.status_code),
        request_id=request.headers.get("x-request-id")
    )

@router.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    Handle general exceptions
    """
    logger.error(f"Unhandled exception: {exc}")
    return ErrorResponse(
        error="Internal server error",
        error_code="500",
        request_id=request.headers.get("x-request-id"),
        details={"message": str(exc)} if settings.environment == "development" else None
    )