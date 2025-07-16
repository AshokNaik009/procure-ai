"""
Custom exceptions for the Procurement Intelligence System
"""

class ProcurementError(Exception):
    """Base exception for procurement-related errors"""
    def __init__(self, message: str, error_code: str = None, details: dict = None):
        super().__init__(message)
        self.error_code = error_code
        self.details = details or {}

class SearchError(ProcurementError):
    """Exception raised for search-related errors"""
    pass

class SupplierError(ProcurementError):
    """Exception raised for supplier-related errors"""
    pass

class MarketIntelligenceError(ProcurementError):
    """Exception raised for market intelligence errors"""
    pass

class LLMError(ProcurementError):
    """Exception raised for LLM service errors"""
    pass

class CacheError(ProcurementError):
    """Exception raised for cache-related errors"""
    pass

class RateLimitError(ProcurementError):
    """Exception raised for rate limiting errors"""
    pass

class ValidationError(ProcurementError):
    """Exception raised for validation errors"""
    pass

class ConfigurationError(ProcurementError):
    """Exception raised for configuration errors"""
    pass

class ExternalServiceError(ProcurementError):
    """Exception raised for external service errors"""
    pass

class DataProcessingError(ProcurementError):
    """Exception raised for data processing errors"""
    pass

# Error codes
class ErrorCodes:
    # Search errors
    SEARCH_FAILED = "SEARCH_001"
    SEARCH_TIMEOUT = "SEARCH_002"
    SEARCH_RATE_LIMITED = "SEARCH_003"
    SEARCH_INVALID_QUERY = "SEARCH_004"
    
    # Supplier errors
    SUPPLIER_NOT_FOUND = "SUPPLIER_001"
    SUPPLIER_VERIFICATION_FAILED = "SUPPLIER_002"
    SUPPLIER_DATA_INVALID = "SUPPLIER_003"
    
    # Market intelligence errors
    MARKET_DATA_UNAVAILABLE = "MARKET_001"
    MARKET_ANALYSIS_FAILED = "MARKET_002"
    MARKET_TRENDS_UNAVAILABLE = "MARKET_003"
    
    # LLM errors
    LLM_REQUEST_FAILED = "LLM_001"
    LLM_RESPONSE_INVALID = "LLM_002"
    LLM_QUOTA_EXCEEDED = "LLM_003"
    LLM_TIMEOUT = "LLM_004"
    
    # Cache errors
    CACHE_MISS = "CACHE_001"
    CACHE_WRITE_FAILED = "CACHE_002"
    CACHE_INVALID_KEY = "CACHE_003"
    
    # Rate limiting errors
    RATE_LIMIT_EXCEEDED = "RATE_001"
    RATE_LIMIT_WINDOW_EXCEEDED = "RATE_002"
    
    # Validation errors
    VALIDATION_FAILED = "VALIDATION_001"
    INVALID_INPUT = "VALIDATION_002"
    MISSING_REQUIRED_FIELD = "VALIDATION_003"
    
    # Configuration errors
    CONFIG_MISSING = "CONFIG_001"
    CONFIG_INVALID = "CONFIG_002"
    API_KEY_MISSING = "CONFIG_003"
    
    # External service errors
    EXTERNAL_SERVICE_UNAVAILABLE = "EXTERNAL_001"
    EXTERNAL_SERVICE_TIMEOUT = "EXTERNAL_002"
    EXTERNAL_SERVICE_AUTH_FAILED = "EXTERNAL_003"
    
    # Data processing errors
    DATA_PARSING_FAILED = "DATA_001"
    DATA_VALIDATION_FAILED = "DATA_002"
    DATA_TRANSFORMATION_FAILED = "DATA_003"

# Error handlers
def handle_search_error(error: Exception, query: str = None) -> SearchError:
    """Convert generic errors to SearchError"""
    if isinstance(error, TimeoutError):
        return SearchError(
            f"Search operation timed out for query: {query}",
            ErrorCodes.SEARCH_TIMEOUT,
            {"query": query}
        )
    elif "rate limit" in str(error).lower():
        return SearchError(
            f"Search rate limit exceeded for query: {query}",
            ErrorCodes.SEARCH_RATE_LIMITED,
            {"query": query}
        )
    else:
        return SearchError(
            f"Search failed for query: {query}. Error: {str(error)}",
            ErrorCodes.SEARCH_FAILED,
            {"query": query, "original_error": str(error)}
        )

def handle_llm_error(error: Exception, provider: str = None, model: str = None) -> LLMError:
    """Convert generic errors to LLMError"""
    error_message = str(error).lower()
    
    if "timeout" in error_message:
        return LLMError(
            f"LLM request timed out for {provider}/{model}",
            ErrorCodes.LLM_TIMEOUT,
            {"provider": provider, "model": model}
        )
    elif "quota" in error_message or "limit" in error_message:
        return LLMError(
            f"LLM quota exceeded for {provider}/{model}",
            ErrorCodes.LLM_QUOTA_EXCEEDED,
            {"provider": provider, "model": model}
        )
    elif "authentication" in error_message or "unauthorized" in error_message:
        return LLMError(
            f"LLM authentication failed for {provider}/{model}",
            ErrorCodes.EXTERNAL_SERVICE_AUTH_FAILED,
            {"provider": provider, "model": model}
        )
    else:
        return LLMError(
            f"LLM request failed for {provider}/{model}. Error: {str(error)}",
            ErrorCodes.LLM_REQUEST_FAILED,
            {"provider": provider, "model": model, "original_error": str(error)}
        )

def handle_supplier_error(error: Exception, supplier_name: str = None) -> SupplierError:
    """Convert generic errors to SupplierError"""
    if "not found" in str(error).lower():
        return SupplierError(
            f"Supplier not found: {supplier_name}",
            ErrorCodes.SUPPLIER_NOT_FOUND,
            {"supplier_name": supplier_name}
        )
    elif "verification" in str(error).lower():
        return SupplierError(
            f"Supplier verification failed for: {supplier_name}",
            ErrorCodes.SUPPLIER_VERIFICATION_FAILED,
            {"supplier_name": supplier_name}
        )
    else:
        return SupplierError(
            f"Supplier operation failed for: {supplier_name}. Error: {str(error)}",
            ErrorCodes.SUPPLIER_DATA_INVALID,
            {"supplier_name": supplier_name, "original_error": str(error)}
        )

def handle_market_error(error: Exception, product: str = None) -> MarketIntelligenceError:
    """Convert generic errors to MarketIntelligenceError"""
    if "data unavailable" in str(error).lower():
        return MarketIntelligenceError(
            f"Market data unavailable for product: {product}",
            ErrorCodes.MARKET_DATA_UNAVAILABLE,
            {"product": product}
        )
    elif "analysis failed" in str(error).lower():
        return MarketIntelligenceError(
            f"Market analysis failed for product: {product}",
            ErrorCodes.MARKET_ANALYSIS_FAILED,
            {"product": product}
        )
    else:
        return MarketIntelligenceError(
            f"Market intelligence operation failed for: {product}. Error: {str(error)}",
            ErrorCodes.MARKET_TRENDS_UNAVAILABLE,
            {"product": product, "original_error": str(error)}
        )

def handle_validation_error(error: Exception, field: str = None) -> ValidationError:
    """Convert generic errors to ValidationError"""
    if "required" in str(error).lower():
        return ValidationError(
            f"Missing required field: {field}",
            ErrorCodes.MISSING_REQUIRED_FIELD,
            {"field": field}
        )
    elif "invalid" in str(error).lower():
        return ValidationError(
            f"Invalid input for field: {field}",
            ErrorCodes.INVALID_INPUT,
            {"field": field}
        )
    else:
        return ValidationError(
            f"Validation failed for field: {field}. Error: {str(error)}",
            ErrorCodes.VALIDATION_FAILED,
            {"field": field, "original_error": str(error)}
        )

def handle_cache_error(error: Exception, key: str = None) -> CacheError:
    """Convert generic errors to CacheError"""
    if "miss" in str(error).lower():
        return CacheError(
            f"Cache miss for key: {key}",
            ErrorCodes.CACHE_MISS,
            {"key": key}
        )
    elif "write" in str(error).lower():
        return CacheError(
            f"Cache write failed for key: {key}",
            ErrorCodes.CACHE_WRITE_FAILED,
            {"key": key}
        )
    else:
        return CacheError(
            f"Cache operation failed for key: {key}. Error: {str(error)}",
            ErrorCodes.CACHE_INVALID_KEY,
            {"key": key, "original_error": str(error)}
        )

def handle_rate_limit_error(error: Exception, endpoint: str = None) -> RateLimitError:
    """Convert generic errors to RateLimitError"""
    return RateLimitError(
        f"Rate limit exceeded for endpoint: {endpoint}",
        ErrorCodes.RATE_LIMIT_EXCEEDED,
        {"endpoint": endpoint, "original_error": str(error)}
    )

def handle_external_service_error(error: Exception, service: str = None) -> ExternalServiceError:
    """Convert generic errors to ExternalServiceError"""
    error_message = str(error).lower()
    
    if "timeout" in error_message:
        return ExternalServiceError(
            f"External service timeout: {service}",
            ErrorCodes.EXTERNAL_SERVICE_TIMEOUT,
            {"service": service}
        )
    elif "unavailable" in error_message or "connection" in error_message:
        return ExternalServiceError(
            f"External service unavailable: {service}",
            ErrorCodes.EXTERNAL_SERVICE_UNAVAILABLE,
            {"service": service}
        )
    elif "authentication" in error_message or "unauthorized" in error_message:
        return ExternalServiceError(
            f"External service authentication failed: {service}",
            ErrorCodes.EXTERNAL_SERVICE_AUTH_FAILED,
            {"service": service}
        )
    else:
        return ExternalServiceError(
            f"External service error: {service}. Error: {str(error)}",
            ErrorCodes.EXTERNAL_SERVICE_UNAVAILABLE,
            {"service": service, "original_error": str(error)}
        )

def handle_data_processing_error(error: Exception, operation: str = None) -> DataProcessingError:
    """Convert generic errors to DataProcessingError"""
    error_message = str(error).lower()
    
    if "parsing" in error_message:
        return DataProcessingError(
            f"Data parsing failed for operation: {operation}",
            ErrorCodes.DATA_PARSING_FAILED,
            {"operation": operation}
        )
    elif "validation" in error_message:
        return DataProcessingError(
            f"Data validation failed for operation: {operation}",
            ErrorCodes.DATA_VALIDATION_FAILED,
            {"operation": operation}
        )
    elif "transformation" in error_message:
        return DataProcessingError(
            f"Data transformation failed for operation: {operation}",
            ErrorCodes.DATA_TRANSFORMATION_FAILED,
            {"operation": operation}
        )
    else:
        return DataProcessingError(
            f"Data processing failed for operation: {operation}. Error: {str(error)}",
            ErrorCodes.DATA_PARSING_FAILED,
            {"operation": operation, "original_error": str(error)}
        )

# Error response formatter
def format_error_response(error: ProcurementError, request_id: str = None) -> dict:
    """Format error for API response"""
    return {
        "error": str(error),
        "error_code": error.error_code,
        "details": error.details,
        "request_id": request_id,
        "timestamp": "2025-07-15T21:30:00Z"
    }

# Retry decorator for handling transient errors
def retry_on_error(max_retries: int = 3, backoff_factor: float = 1.0, 
                   retry_on: tuple = (Exception,)):
    """Decorator to retry function calls on specific errors"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            import time
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except retry_on as e:
                    if attempt == max_retries:
                        raise
                    
                    wait_time = backoff_factor * (2 ** attempt)
                    time.sleep(wait_time)
                    
                    # Log retry attempt
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Retrying {func.__name__} (attempt {attempt + 1}/{max_retries}) after {wait_time}s")
                    
            return None
        return wrapper
    return decorator