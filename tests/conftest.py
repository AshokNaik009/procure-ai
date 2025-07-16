import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.config import settings
from app.services.search_service import SearchService
from app.services.llm_service import LLMService
from app.services.supplier_agent import SupplierAgent
from app.services.market_agent import MarketAgent
from app.models.responses import SearchResult, SupplierInfo, VerificationStatus

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_settings():
    """Mock settings for testing"""
    class MockSettings:
        groq_api_key = "test_groq_key"
        gemini_api_key = "test_gemini_key"
        redis_url = "redis://localhost:6379"
        log_level = "DEBUG"
        environment = "test"
        rate_limit_per_minute = 100
        cache_ttl_seconds = 300
        search_rate_limit_delay = 0.1
        max_search_results = 10
        request_timeout = 30
    
    return MockSettings()

@pytest.fixture
def mock_search_service():
    """Mock SearchService for testing"""
    service = MagicMock(spec=SearchService)
    service.search_suppliers = AsyncMock(return_value=[])
    service.search_market_data = AsyncMock(return_value=[])
    service.search_general = AsyncMock(return_value=[])
    service.get_search_suggestions = AsyncMock(return_value=[])
    return service

@pytest.fixture
def mock_llm_service():
    """Mock LLMService for testing"""
    service = MagicMock(spec=LLMService)
    service.verify_supplier_data = AsyncMock(return_value=SupplierInfo(
        name="Test Supplier",
        location="Test Location",
        confidence_score=0.8,
        certifications=[],
        verification_status=VerificationStatus.VERIFIED,
        contact_info={},
        specialties=[]
    ))
    service.analyze_market_trends = AsyncMock(return_value=MagicMock())
    service.generate_procurement_summary = AsyncMock(return_value={
        "executive_summary": "Test summary",
        "recommendations": ["Test recommendation"],
        "next_steps": ["Test step"]
    })
    return service

@pytest.fixture
def sample_search_results():
    """Sample search results for testing"""
    return [
        SearchResult(
            title="Test Supplier 1",
            url="https://test1.com",
            snippet="Test supplier description 1",
            source="test1.com",
            relevance_score=0.9
        ),
        SearchResult(
            title="Test Supplier 2",
            url="https://test2.com",
            snippet="Test supplier description 2",
            source="test2.com",
            relevance_score=0.8
        )
    ]

@pytest.fixture
def sample_supplier_info():
    """Sample supplier info for testing"""
    return SupplierInfo(
        name="Test Supplier",
        website="https://testsupplier.com",
        location="Test City, Test State",
        confidence_score=0.85,
        certifications=["ISO 9001", "AS9100"],
        contact_info={
            "email": "contact@testsupplier.com",
            "phone": "555-0123"
        },
        verification_status=VerificationStatus.VERIFIED,
        specialties=["industrial manufacturing", "custom fabrication"],
        company_size="Medium",
        year_established=2000,
        rating=4.2,
        description="Test supplier providing industrial manufacturing services"
    )

@pytest.fixture
def sample_market_intelligence():
    """Sample market intelligence for testing"""
    from app.models.responses import MarketIntelligence, PriceInsight, MarketTrend
    
    return MarketIntelligence(
        product_category="industrial steel",
        price_insights=PriceInsight(
            price_range={"min": 100, "max": 500, "avg": 300},
            currency="USD",
            unit="per ton",
            trend="increasing",
            factors=["Raw material costs", "Supply chain disruptions"]
        ),
        market_trends=[
            MarketTrend(
                trend_type="pricing",
                description="Steel prices increasing due to supply constraints",
                impact="high",
                confidence=0.85
            )
        ],
        recommendations=["Consider bulk purchasing", "Negotiate long-term contracts"],
        market_size="$50 billion",
        growth_rate="3.2% annually",
        key_players=["Steel Corp", "Industrial Steel Inc"],
        opportunities=["Emerging markets", "Green steel initiatives"],
        risks=["Supply chain disruptions", "Regulatory changes"]
    )

@pytest.fixture
def mock_cache():
    """Mock cache for testing"""
    class MockCache:
        def __init__(self):
            self.data = {}
        
        async def get(self, key):
            return self.data.get(key)
        
        async def set(self, key, value, ttl=None):
            self.data[key] = value
        
        async def delete(self, key):
            self.data.pop(key, None)
        
        async def clear(self):
            self.data.clear()
    
    return MockCache()

@pytest.fixture
def mock_rate_limiter():
    """Mock rate limiter for testing"""
    class MockRateLimiter:
        def is_allowed(self, key):
            return True
        
        def get_reset_time(self, key):
            return 0.0
    
    return MockRateLimiter()

@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch):
    """Setup test environment with mocked dependencies"""
    # Mock environment variables
    monkeypatch.setenv("GROQ_API_KEY", "test_groq_key")
    monkeypatch.setenv("GEMINI_API_KEY", "test_gemini_key")
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")

@pytest.fixture
def mock_ddgs_results():
    """Mock DuckDuckGo search results"""
    return [
        {
            'title': 'Steel Suppliers Inc - Industrial Steel Products',
            'href': 'https://steelsuppliers.com',
            'body': 'Leading supplier of industrial steel products in Texas. Certified ISO 9001.'
        },
        {
            'title': 'Texas Steel Manufacturing - Steel Suppliers',
            'href': 'https://texassteel.com',
            'body': 'Manufacturing steel products for industrial use since 1985.'
        },
        {
            'title': 'Industrial Steel Directory - Find Steel Suppliers',
            'href': 'https://industrialsteeldirectory.com',
            'body': 'Directory of steel suppliers and manufacturers in the USA.'
        }
    ]

@pytest.fixture
def mock_groq_response():
    """Mock Groq API response"""
    return {
        "name": "Test Supplier Inc",
        "location": "Texas",
        "confidence_score": 0.85,
        "certifications": ["ISO 9001"],
        "specialties": ["industrial steel"],
        "company_size": "Large",
        "verification_status": "verified",
        "contact_info": {"email": "test@supplier.com"},
        "rating": 4.5
    }

@pytest.fixture
def mock_gemini_response():
    """Mock Gemini API response"""
    return {
        "price_insights": {
            "price_range": {"min": 100, "max": 500, "avg": 300},
            "currency": "USD",
            "trend": "increasing",
            "factors": ["Supply chain issues"]
        },
        "market_trends": [
            {
                "trend_type": "pricing",
                "description": "Prices increasing",
                "impact": "high",
                "confidence": 0.8
            }
        ],
        "recommendations": ["Monitor market closely"]
    }

# Test data factories
class TestDataFactory:
    """Factory for creating test data"""
    
    @staticmethod
    def create_search_result(title="Test Result", url="https://test.com", 
                           snippet="Test description", source="test.com", 
                           relevance_score=0.8):
        return SearchResult(
            title=title,
            url=url,
            snippet=snippet,
            source=source,
            relevance_score=relevance_score
        )
    
    @staticmethod
    def create_supplier_info(name="Test Supplier", location="Test Location",
                           confidence_score=0.8, certifications=None,
                           verification_status=VerificationStatus.VERIFIED):
        return SupplierInfo(
            name=name,
            location=location,
            confidence_score=confidence_score,
            certifications=certifications or [],
            verification_status=verification_status,
            contact_info={},
            specialties=[]
        )

@pytest.fixture
def test_data_factory():
    """Test data factory fixture"""
    return TestDataFactory()

# Async test helpers
@pytest.fixture
def async_test_timeout():
    """Timeout for async tests"""
    return 30.0

# Database fixtures (if needed)
@pytest.fixture
def mock_database():
    """Mock database for testing"""
    class MockDatabase:
        def __init__(self):
            self.data = {}
        
        async def get(self, key):
            return self.data.get(key)
        
        async def set(self, key, value):
            self.data[key] = value
        
        async def delete(self, key):
            self.data.pop(key, None)
    
    return MockDatabase()

# Error simulation fixtures
@pytest.fixture
def network_error():
    """Network error for testing"""
    return ConnectionError("Network connection failed")

@pytest.fixture
def timeout_error():
    """Timeout error for testing"""
    return TimeoutError("Request timed out")

@pytest.fixture
def api_error():
    """API error for testing"""
    return Exception("API request failed")

# Performance testing fixtures
@pytest.fixture
def performance_benchmark():
    """Performance benchmark for testing"""
    return {
        "max_response_time": 5.0,  # seconds
        "max_memory_usage": 100,   # MB
        "max_cpu_usage": 80        # percent
    }

# Cleanup fixtures
@pytest.fixture(autouse=True)
def cleanup_after_test():
    """Cleanup after each test"""
    yield
    # Cleanup code here if needed
    pass