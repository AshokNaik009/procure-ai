import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.supplier_agent import SupplierAgent
from app.models.requests import SupplierDiscoveryRequest
from app.models.responses import SupplierInfo, SupplierDiscoveryResponse, VerificationStatus, SearchResult

class TestSupplierAgent:
    """Test cases for SupplierAgent"""
    
    @pytest.fixture
    def supplier_agent(self):
        """Create SupplierAgent instance for testing"""
        return SupplierAgent()
    
    @pytest.fixture
    def sample_request(self):
        """Create sample supplier discovery request"""
        return SupplierDiscoveryRequest(
            product="industrial steel",
            location="Texas",
            requirements=["ISO 9001", "24/7 support"],
            certifications=["ISO 9001"],
            min_rating=4.0,
            max_results=10
        )
    
    @pytest.fixture
    def mock_search_results(self):
        """Mock search results"""
        return [
            SearchResult(
                title="Steel Suppliers Inc - Industrial Steel Products",
                url="https://steelsuppliers.com",
                snippet="Leading supplier of industrial steel products in Texas. ISO 9001 certified.",
                source="steelsuppliers.com",
                relevance_score=0.9
            ),
            SearchResult(
                title="Texas Steel Manufacturing Corporation",
                url="https://texassteel.com",
                snippet="Manufacturing steel products for industrial use since 1985. Located in Houston, Texas.",
                source="texassteel.com",
                relevance_score=0.8
            )
        ]
    
    @pytest.fixture
    def mock_verified_supplier(self):
        """Mock verified supplier info"""
        return SupplierInfo(
            name="Steel Suppliers Inc",
            website="https://steelsuppliers.com",
            location="Texas",
            confidence_score=0.9,
            certifications=["ISO 9001", "AS9100"],
            contact_info={"email": "contact@steelsuppliers.com", "phone": "555-0123"},
            verification_status=VerificationStatus.VERIFIED,
            specialties=["industrial steel", "custom fabrication"],
            company_size="Large",
            year_established=1995,
            rating=4.5,
            description="Leading supplier of industrial steel products"
        )
    
    @pytest.mark.asyncio
    async def test_discover_suppliers_success(self, supplier_agent, sample_request, mock_search_results, mock_verified_supplier):
        """Test successful supplier discovery"""
        with patch.object(supplier_agent.search_service, 'search_suppliers', return_value=mock_search_results):
            with patch.object(supplier_agent.llm_service, 'verify_supplier_data', return_value=mock_verified_supplier):
                
                response = await supplier_agent.discover_suppliers(sample_request)
                
                assert isinstance(response, SupplierDiscoveryResponse)
                assert len(response.suppliers) > 0
                assert response.total_found > 0
                assert response.search_query == sample_request.product
                assert response.location_filter == sample_request.location
                assert response.processing_time > 0
    
    @pytest.mark.asyncio
    async def test_discover_suppliers_no_results(self, supplier_agent, sample_request):
        """Test supplier discovery with no search results"""
        with patch.object(supplier_agent.search_service, 'search_suppliers', return_value=[]):
            
            response = await supplier_agent.discover_suppliers(sample_request)
            
            assert isinstance(response, SupplierDiscoveryResponse)
            assert len(response.suppliers) == 0
            assert response.total_found == 0
    
    @pytest.mark.asyncio
    async def test_discover_suppliers_with_error(self, supplier_agent, sample_request):
        """Test supplier discovery with search error"""
        with patch.object(supplier_agent.search_service, 'search_suppliers', side_effect=Exception("Search failed")):
            
            response = await supplier_agent.discover_suppliers(sample_request)
            
            assert isinstance(response, SupplierDiscoveryResponse)
            assert len(response.suppliers) == 0
            assert response.total_found == 0
    
    @pytest.mark.asyncio
    async def test_extract_supplier_info(self, supplier_agent, mock_search_results, sample_request):
        """Test supplier information extraction"""
        supplier_candidates = await supplier_agent._extract_supplier_info(mock_search_results, sample_request)
        
        assert len(supplier_candidates) == 2
        assert supplier_candidates[0]['name'] == "Steel Suppliers Inc"
        assert supplier_candidates[0]['website'] == "https://steelsuppliers.com"
        assert "Texas" in supplier_candidates[0]['location']
    
    @pytest.mark.asyncio
    async def test_verify_suppliers(self, supplier_agent, sample_request, mock_verified_supplier):
        """Test supplier verification"""
        supplier_candidates = [
            {
                'name': 'Steel Suppliers Inc',
                'website': 'https://steelsuppliers.com',
                'location': 'Texas',
                'description': 'Industrial steel supplier'
            }
        ]
        
        with patch.object(supplier_agent.llm_service, 'verify_supplier_data', return_value=mock_verified_supplier):
            
            verified_suppliers = await supplier_agent._verify_suppliers(supplier_candidates, sample_request)
            
            assert len(verified_suppliers) == 1
            assert isinstance(verified_suppliers[0], SupplierInfo)
            assert verified_suppliers[0].name == "Steel Suppliers Inc"
    
    def test_apply_filters(self, supplier_agent, sample_request):
        """Test supplier filtering"""
        suppliers = [
            SupplierInfo(
                name="High Rating Supplier",
                location="Texas",
                confidence_score=0.9,
                certifications=["ISO 9001"],
                rating=4.5,
                verification_status=VerificationStatus.VERIFIED,
                contact_info={},
                specialties=[]
            ),
            SupplierInfo(
                name="Low Rating Supplier",
                location="California",
                confidence_score=0.8,
                certifications=[],
                rating=3.0,
                verification_status=VerificationStatus.UNVERIFIED,
                contact_info={},
                specialties=[]
            )
        ]
        
        filtered = supplier_agent._apply_filters(suppliers, sample_request)
        
        # Should filter out low rating and non-matching location
        assert len(filtered) == 1
        assert filtered[0].name == "High Rating Supplier"
    
    def test_rank_suppliers(self, supplier_agent, sample_request):
        """Test supplier ranking"""
        suppliers = [
            SupplierInfo(
                name="Lower Confidence",
                location="Texas",
                confidence_score=0.6,
                certifications=["ISO 9001"],
                rating=4.0,
                verification_status=VerificationStatus.VERIFIED,
                contact_info={},
                specialties=[]
            ),
            SupplierInfo(
                name="Higher Confidence",
                location="Texas",
                confidence_score=0.9,
                certifications=["ISO 9001", "AS9100"],
                rating=4.5,
                verification_status=VerificationStatus.VERIFIED,
                contact_info={},
                specialties=["industrial steel"]
            )
        ]
        
        ranked = supplier_agent._rank_suppliers(suppliers, sample_request)
        
        # Should be ranked by confidence score
        assert ranked[0].name == "Higher Confidence"
        assert ranked[1].name == "Lower Confidence"
    
    def test_extract_company_name(self, supplier_agent):
        """Test company name extraction"""
        test_cases = [
            ("Steel Suppliers Inc - Industrial Steel Products", "Steel Suppliers Inc"),
            ("Texas Steel Manufacturing Corporation", "Texas Steel Manufacturing Corporation"),
            ("1. ABC Steel Company | Steel Products", "ABC Steel Company"),
            ("Steel Products - Best in Texas", "Steel Products"),
            ("XYZ Corp", "XYZ Corp"),
            ("", "")
        ]
        
        for title, expected in test_cases:
            result = supplier_agent._extract_company_name(title)
            assert expected in result or result == expected
    
    def test_extract_location(self, supplier_agent):
        """Test location extraction"""
        test_cases = [
            ("Company located in Houston, Texas", "Houston, Texas"),
            ("Based in California", "California"),
            ("Headquarters in New York, NY", "New York, NY"),
            ("Office at Dallas, Texas", "Dallas, Texas"),
            ("No location mentioned", "Location not specified")
        ]
        
        for snippet, expected in test_cases:
            result = supplier_agent._extract_location(snippet)
            assert expected in result or result == "Location not specified"
    
    def test_location_matches(self, supplier_agent):
        """Test location matching"""
        test_cases = [
            ("Houston, Texas", "Texas", True),
            ("Dallas, TX", "Texas", True),
            ("California", "Texas", False),
            ("New York", "NY", True),
            ("Los Angeles, CA", "California", True),
            ("", "Texas", False)
        ]
        
        for supplier_location, requested_location, expected in test_cases:
            result = supplier_agent._location_matches(supplier_location, requested_location)
            assert result == expected
    
    def test_meets_requirements(self, supplier_agent):
        """Test requirements checking"""
        supplier = SupplierInfo(
            name="Test Supplier",
            location="Texas",
            confidence_score=0.8,
            certifications=["ISO 9001"],
            description="24/7 support available for all customers",
            specialties=["industrial steel", "custom fabrication"],
            verification_status=VerificationStatus.VERIFIED,
            contact_info={}
        )
        
        requirements = ["ISO 9001", "24/7 support"]
        
        result = supplier_agent._meets_requirements(supplier, requirements)
        assert result == True
        
        # Test with unmet requirements
        requirements = ["ISO 14001", "offshore support"]
        result = supplier_agent._meets_requirements(supplier, requirements)
        assert result == False
    
    def test_calculate_specialty_relevance(self, supplier_agent):
        """Test specialty relevance calculation"""
        specialties = ["industrial steel", "custom fabrication", "metal processing"]
        product = "industrial steel fabrication"
        
        relevance = supplier_agent._calculate_specialty_relevance(specialties, product)
        
        assert 0.0 <= relevance <= 1.0
        assert relevance > 0  # Should have some relevance
    
    @pytest.mark.asyncio
    async def test_batch_processing(self, supplier_agent, sample_request):
        """Test batch processing of supplier verification"""
        supplier_candidates = [
            {'name': f'Supplier {i}', 'website': f'https://supplier{i}.com', 'location': 'Texas'}
            for i in range(10)
        ]
        
        mock_supplier = SupplierInfo(
            name="Test Supplier",
            location="Texas",
            confidence_score=0.8,
            certifications=[],
            verification_status=VerificationStatus.VERIFIED,
            contact_info={},
            specialties=[]
        )
        
        with patch.object(supplier_agent.llm_service, 'verify_supplier_data', return_value=mock_supplier):
            with patch('asyncio.sleep'):  # Mock rate limiting sleep
                
                verified_suppliers = await supplier_agent._verify_suppliers(supplier_candidates, sample_request)
                
                assert len(verified_suppliers) == 10
                assert all(isinstance(supplier, SupplierInfo) for supplier in verified_suppliers)
    
    @pytest.mark.asyncio
    async def test_error_handling_in_verification(self, supplier_agent, sample_request):
        """Test error handling during supplier verification"""
        supplier_candidates = [
            {'name': 'Test Supplier', 'website': 'https://test.com', 'location': 'Texas'}
        ]
        
        with patch.object(supplier_agent.llm_service, 'verify_supplier_data', side_effect=Exception("Verification failed")):
            
            verified_suppliers = await supplier_agent._verify_suppliers(supplier_candidates, sample_request)
            
            # Should handle errors gracefully
            assert len(verified_suppliers) == 0
    
    @pytest.mark.asyncio
    async def test_max_results_limit(self, supplier_agent, mock_search_results):
        """Test that max_results is respected"""
        request = SupplierDiscoveryRequest(
            product="steel",
            max_results=1
        )
        
        # Mock multiple search results
        extended_results = mock_search_results * 5  # 10 results total
        
        with patch.object(supplier_agent.search_service, 'search_suppliers', return_value=extended_results):
            with patch.object(supplier_agent.llm_service, 'verify_supplier_data') as mock_verify:
                mock_verify.return_value = SupplierInfo(
                    name="Test Supplier",
                    location="Texas",
                    confidence_score=0.8,
                    certifications=[],
                    verification_status=VerificationStatus.VERIFIED,
                    contact_info={},
                    specialties=[]
                )
                
                response = await supplier_agent.discover_suppliers(request)
                
                assert len(response.suppliers) <= request.max_results
    
    @pytest.mark.asyncio
    async def test_processing_time_tracking(self, supplier_agent, sample_request):
        """Test that processing time is tracked"""
        with patch.object(supplier_agent.search_service, 'search_suppliers', return_value=[]):
            
            response = await supplier_agent.discover_suppliers(sample_request)
            
            assert response.processing_time > 0
            assert isinstance(response.processing_time, float)

if __name__ == "__main__":
    pytest.main([__file__])