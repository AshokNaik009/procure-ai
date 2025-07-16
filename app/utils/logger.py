import logging
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

from app.config import settings

class CustomFormatter(logging.Formatter):
    """
    Custom formatter for structured logging
    """
    
    def __init__(self, include_extra: bool = True):
        super().__init__()
        self.include_extra = include_extra
    
    def format(self, record: logging.LogRecord) -> str:
        # Create base log structure
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add extra fields if available
        if self.include_extra and hasattr(record, 'extra'):
            log_entry.update(record.extra)
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # Add stack trace if available
        if record.stack_info:
            log_entry['stack_trace'] = record.stack_info
            
        return json.dumps(log_entry)

class RequestLogger:
    """
    Logger for HTTP requests
    """
    
    def __init__(self, logger_name: str = "request"):
        self.logger = logging.getLogger(logger_name)
    
    def log_request(self, request_id: str, method: str, url: str, headers: Dict[str, str], 
                   body: Optional[str] = None):
        """Log incoming request"""
        self.logger.info(
            "Incoming request",
            extra={
                'request_id': request_id,
                'method': method,
                'url': url,
                'headers': dict(headers),
                'body_size': len(body) if body else 0,
                'event_type': 'request_start'
            }
        )
    
    def log_response(self, request_id: str, status_code: int, response_time: float, 
                    response_size: int = 0):
        """Log outgoing response"""
        self.logger.info(
            "Response sent",
            extra={
                'request_id': request_id,
                'status_code': status_code,
                'response_time': response_time,
                'response_size': response_size,
                'event_type': 'request_end'
            }
        )
    
    def log_error(self, request_id: str, error: Exception, context: Dict[str, Any] = None):
        """Log request error"""
        self.logger.error(
            f"Request error: {str(error)}",
            extra={
                'request_id': request_id,
                'error_type': type(error).__name__,
                'error_message': str(error),
                'context': context or {},
                'event_type': 'request_error'
            },
            exc_info=True
        )

class SearchLogger:
    """
    Logger for search operations
    """
    
    def __init__(self, logger_name: str = "search"):
        self.logger = logging.getLogger(logger_name)
    
    def log_search_start(self, query: str, search_type: str, filters: Dict[str, Any] = None):
        """Log search operation start"""
        self.logger.info(
            "Search operation started",
            extra={
                'query': query,
                'search_type': search_type,
                'filters': filters or {},
                'event_type': 'search_start'
            }
        )
    
    def log_search_result(self, query: str, result_count: int, processing_time: float, 
                         confidence_score: float = None):
        """Log search results"""
        self.logger.info(
            "Search operation completed",
            extra={
                'query': query,
                'result_count': result_count,
                'processing_time': processing_time,
                'confidence_score': confidence_score,
                'event_type': 'search_result'
            }
        )
    
    def log_search_error(self, query: str, error: Exception, context: Dict[str, Any] = None):
        """Log search error"""
        self.logger.error(
            f"Search operation failed: {str(error)}",
            extra={
                'query': query,
                'error_type': type(error).__name__,
                'error_message': str(error),
                'context': context or {},
                'event_type': 'search_error'
            },
            exc_info=True
        )

class LLMLogger:
    """
    Logger for LLM operations
    """
    
    def __init__(self, logger_name: str = "llm"):
        self.logger = logging.getLogger(logger_name)
    
    def log_llm_request(self, provider: str, model: str, prompt_length: int, 
                       operation_type: str):
        """Log LLM request"""
        self.logger.info(
            "LLM request started",
            extra={
                'provider': provider,
                'model': model,
                'prompt_length': prompt_length,
                'operation_type': operation_type,
                'event_type': 'llm_request'
            }
        )
    
    def log_llm_response(self, provider: str, model: str, response_length: int, 
                        processing_time: float, tokens_used: int = None):
        """Log LLM response"""
        self.logger.info(
            "LLM response received",
            extra={
                'provider': provider,
                'model': model,
                'response_length': response_length,
                'processing_time': processing_time,
                'tokens_used': tokens_used,
                'event_type': 'llm_response'
            }
        )
    
    def log_llm_error(self, provider: str, model: str, error: Exception, 
                     context: Dict[str, Any] = None):
        """Log LLM error"""
        self.logger.error(
            f"LLM operation failed: {str(error)}",
            extra={
                'provider': provider,
                'model': model,
                'error_type': type(error).__name__,
                'error_message': str(error),
                'context': context or {},
                'event_type': 'llm_error'
            },
            exc_info=True
        )

class PerformanceLogger:
    """
    Logger for performance metrics
    """
    
    def __init__(self, logger_name: str = "performance"):
        self.logger = logging.getLogger(logger_name)
    
    def log_performance_metric(self, metric_name: str, value: float, unit: str = 'ms', 
                              context: Dict[str, Any] = None):
        """Log performance metric"""
        self.logger.info(
            f"Performance metric: {metric_name}",
            extra={
                'metric_name': metric_name,
                'value': value,
                'unit': unit,
                'context': context or {},
                'event_type': 'performance_metric'
            }
        )
    
    def log_slow_operation(self, operation: str, duration: float, threshold: float = 5.0):
        """Log slow operation"""
        if duration > threshold:
            self.logger.warning(
                f"Slow operation detected: {operation}",
                extra={
                    'operation': operation,
                    'duration': duration,
                    'threshold': threshold,
                    'event_type': 'slow_operation'
                }
            )

def setup_logging():
    """
    Setup logging configuration
    """
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level.upper()))
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    if settings.environment == "production":
        # Use JSON formatter for production
        console_handler.setFormatter(CustomFormatter())
    else:
        # Use simple formatter for development
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
    
    root_logger.addHandler(console_handler)
    
    # File handler for all logs
    file_handler = logging.FileHandler(log_dir / "app.log")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(CustomFormatter())
    root_logger.addHandler(file_handler)
    
    # Error file handler
    error_handler = logging.FileHandler(log_dir / "errors.log")
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(CustomFormatter())
    root_logger.addHandler(error_handler)
    
    # Performance file handler
    performance_handler = logging.FileHandler(log_dir / "performance.log")
    performance_handler.setLevel(logging.INFO)
    performance_handler.addFilter(lambda record: hasattr(record, 'extra') and 
                                 record.extra.get('event_type') == 'performance_metric')
    performance_handler.setFormatter(CustomFormatter())
    root_logger.addHandler(performance_handler)
    
    logging.info(f"Logging setup completed - Level: {settings.log_level}")

# Global logger instances
request_logger = RequestLogger()
search_logger = SearchLogger()
llm_logger = LLMLogger()
performance_logger = PerformanceLogger()

# Context manager for operation logging
class LoggedOperation:
    """
    Context manager for logging operations with timing
    """
    
    def __init__(self, operation_name: str, logger: logging.Logger, 
                 log_level: int = logging.INFO, context: Dict[str, Any] = None):
        self.operation_name = operation_name
        self.logger = logger
        self.log_level = log_level
        self.context = context or {}
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.utcnow()
        self.logger.log(
            self.log_level,
            f"Starting operation: {self.operation_name}",
            extra={
                'operation': self.operation_name,
                'event_type': 'operation_start',
                **self.context
            }
        )
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        end_time = datetime.utcnow()
        duration = (end_time - self.start_time).total_seconds()
        
        if exc_type is None:
            self.logger.log(
                self.log_level,
                f"Completed operation: {self.operation_name}",
                extra={
                    'operation': self.operation_name,
                    'duration': duration,
                    'event_type': 'operation_success',
                    **self.context
                }
            )
            
            # Also log to performance logger
            performance_logger.log_performance_metric(
                self.operation_name,
                duration * 1000,  # Convert to milliseconds
                'ms',
                self.context
            )
        else:
            self.logger.error(
                f"Failed operation: {self.operation_name}",
                extra={
                    'operation': self.operation_name,
                    'duration': duration,
                    'error_type': exc_type.__name__,
                    'error_message': str(exc_val),
                    'event_type': 'operation_error',
                    **self.context
                },
                exc_info=True
            )

# Decorator for logging function calls
def log_function_call(logger: logging.Logger, log_level: int = logging.DEBUG):
    """
    Decorator to log function calls
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            with LoggedOperation(
                f"{func.__module__}.{func.__name__}",
                logger,
                log_level,
                {
                    'function': func.__name__,
                    'module': func.__module__,
                    'args_count': len(args),
                    'kwargs_count': len(kwargs)
                }
            ):
                return func(*args, **kwargs)
        return wrapper
    return decorator