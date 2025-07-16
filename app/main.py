from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import logging
import time
import asyncio
from contextlib import asynccontextmanager

from app.config import settings
from app.routers import procurement, health
from app.utils.rate_limiter import RateLimitMiddleware
from app.utils.cache import cache_cleanup_task

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Background tasks
background_tasks = []

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler
    """
    # Startup
    logger.info("Starting Procurement Intelligence System")
    
    # Start background tasks
    cleanup_task = asyncio.create_task(cache_cleanup_task())
    background_tasks.append(cleanup_task)
    
    # Initialize services
    logger.info("Initializing services...")
    
    # Health check
    logger.info("System startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Procurement Intelligence System")
    
    # Cancel background tasks
    for task in background_tasks:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
    
    logger.info("Shutdown complete")

# Create FastAPI app
app = FastAPI(
    title="Procurement Intelligence System",
    description="AI-powered procurement intelligence platform for supplier discovery and market analysis",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"] if settings.environment == "development" else ["localhost", "127.0.0.1"]
)

# Rate limiting middleware
app.add_middleware(RateLimitMiddleware)

# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Request ID middleware
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    import uuid
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

# Mount static files
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

# Templates
templates = Jinja2Templates(directory="frontend/templates")

# Include routers
app.include_router(health.router)
app.include_router(procurement.router)

# Frontend routes
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """
    Serve the main dashboard
    """
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """
    Serve the dashboard page
    """
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/suppliers", response_class=HTMLResponse)
async def suppliers_page(request: Request):
    """
    Serve the suppliers page
    """
    return templates.TemplateResponse("suppliers.html", {"request": request})

@app.get("/market", response_class=HTMLResponse)
async def market_page(request: Request):
    """
    Serve the market intelligence page
    """
    return templates.TemplateResponse("market.html", {"request": request})

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler
    """
    logger.error(f"Unhandled exception: {exc}")
    
    if settings.environment == "development":
        raise HTTPException(status_code=500, detail=str(exc))
    else:
        raise HTTPException(status_code=500, detail="Internal server error")

# Health check endpoint (basic)
@app.get("/ping")
async def ping():
    """
    Simple ping endpoint
    """
    return {"message": "pong", "timestamp": time.time()}

# API info endpoint
@app.get("/api/info")
async def api_info():
    """
    API information endpoint
    """
    return {
        "title": "Procurement Intelligence System",
        "version": "1.0.0",
        "description": "AI-powered procurement intelligence platform",
        "endpoints": {
            "procurement_analysis": "/api/v1/procurement/analyze",
            "supplier_discovery": "/api/v1/suppliers/discover",
            "market_intelligence": "/api/v1/market/intelligence",
            "health": "/health",
            "docs": "/docs"
        },
        "features": [
            "Real-time supplier discovery",
            "Market intelligence analysis",
            "AI-powered insights",
            "Rate limiting",
            "Caching",
            "Error handling"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.environment == "development",
        log_level=settings.log_level.lower()
    )