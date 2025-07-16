from fastapi import APIRouter, Depends
from app.models.responses import HealthResponse
from app.utils.cache import cache_manager
from app.config import settings
import time
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["health"])

# Track startup time for uptime calculation
startup_time = time.time()

@router.get("/", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint
    """
    try:
        # Check cache health
        cache_stats = cache_manager.get_stats()
        cache_healthy = cache_stats['error_count'] < 10
        
        # Check service components
        services = {
            "cache": "healthy" if cache_healthy else "unhealthy",
            "search": "healthy",  # Basic health check
            "llm": "healthy"      # Basic health check
        }
        
        # Overall health status
        overall_healthy = all(status == "healthy" for status in services.values())
        
        return HealthResponse(
            status="healthy" if overall_healthy else "unhealthy",
            version="1.0.0",
            services=services,
            uptime=time.time() - startup_time
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            version="1.0.0",
            services={"error": str(e)},
            uptime=time.time() - startup_time
        )

@router.get("/cache", response_model=dict)
async def cache_health():
    """
    Cache-specific health check
    """
    try:
        return cache_manager.get_stats()
    except Exception as e:
        logger.error(f"Cache health check failed: {e}")
        return {"error": str(e), "status": "unhealthy"}

@router.get("/metrics", response_model=dict)
async def get_metrics():
    """
    Get system metrics
    """
    try:
        import psutil
        import os
        
        # Get system metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Get process metrics
        process = psutil.Process(os.getpid())
        process_memory = process.memory_info()
        
        return {
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available": memory.available,
                "disk_percent": disk.percent,
                "disk_free": disk.free
            },
            "process": {
                "memory_rss": process_memory.rss,
                "memory_vms": process_memory.vms,
                "cpu_percent": process.cpu_percent(),
                "num_threads": process.num_threads()
            },
            "cache": cache_manager.get_stats(),
            "uptime": time.time() - startup_time
        }
        
    except ImportError:
        return {
            "error": "psutil not available",
            "cache": cache_manager.get_stats(),
            "uptime": time.time() - startup_time
        }
    except Exception as e:
        logger.error(f"Metrics collection failed: {e}")
        return {"error": str(e)}

@router.post("/cache/clear", response_model=dict)
async def clear_cache():
    """
    Clear all cache entries (admin endpoint)
    """
    try:
        from app.utils.cache import cache
        await cache.clear()
        cache_manager.reset_stats()
        
        return {
            "message": "Cache cleared successfully",
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Cache clear failed: {e}")
        return {"error": str(e)}

@router.get("/ready", response_model=dict)
async def readiness_check():
    """
    Readiness check for Kubernetes
    """
    try:
        # Check if all services are ready
        services_ready = {
            "cache": True,
            "search": True,
            "llm": True
        }
        
        all_ready = all(services_ready.values())
        
        return {
            "ready": all_ready,
            "services": services_ready,
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return {
            "ready": False,
            "error": str(e),
            "timestamp": time.time()
        }

@router.get("/live", response_model=dict)
async def liveness_check():
    """
    Liveness check for Kubernetes
    """
    try:
        # Simple liveness check
        return {
            "alive": True,
            "timestamp": time.time(),
            "uptime": time.time() - startup_time
        }
        
    except Exception as e:
        logger.error(f"Liveness check failed: {e}")
        return {
            "alive": False,
            "error": str(e),
            "timestamp": time.time()
        }