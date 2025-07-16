import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.search_service import SearchService
from app.models.responses import SearchResult

class TestSearchService:
    """Test cases for SearchService"""
    
    @pytest.fixture
    def search_service(self):
        """Create SearchService instance for testing"""
        return SearchService()
    
    @pytest.fixture
    def mock_ddgs_results(self):
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
    
    @pytest.mark.asyncio
    async def test_search_suppliers_success(self, search_service, mock_ddgs_results):
        """Test successful supplier search"""
        with patch.object(search_service, '_execute_search') as mock_execute:
            mock_execute.return_value = [
                SearchResult(
                    title=result['title'],
                    url=result['href'],
                    snippet=result['body'],
                    source='steelsuppliers.com',
                    relevance_score=0.8
                ) for result in mock_ddgs_results
            ]
            
            results = await search_service.search_suppliers("steel suppliers", "Texas", 5)
            
            assert len(results) > 0
            assert all(isinstance(result, SearchResult) for result in results)
            assert "steel" in results[0].title.lower()
    
    @pytest.mark.asyncio
    async def test_search_suppliers_empty_query(self, search_service):
        """Test search with empty query"""
        results = await search_service.search_suppliers("", "Texas", 5)
        assert len(results) == 0
    
    @pytest.mark.asyncio
    async def test_search_market_data_success(self, search_service, mock_ddgs_results):
        """Test successful market data search"""
        with patch.object(search_service, '_execute_search') as mock_execute:
            mock_execute.return_value = [
                SearchResult(
                    title="Steel Market Analysis 2025",
                    url="https://marketanalysis.com",
                    snippet="Steel market trends and pricing analysis for 2025",
                    source="marketanalysis.com",
                    relevance_score=0.9
                )
            ]
            
            results = await search_service.search_market_data("steel", "6months")
            
            assert len(results) > 0
            assert "market" in results[0].title.lower() or "analysis" in results[0].title.lower()
    
    @pytest.mark.asyncio
    async def test_execute_search_with_mock_ddgs(self, search_service, mock_ddgs_results):
        """Test _execute_search with mocked DuckDuckGo"""
        with patch.object(search_service.ddgs, 'text', return_value=mock_ddgs_results):
            results = await search_service._execute_search("steel suppliers", 3)
            
            assert len(results) == 3
            assert all(isinstance(result, SearchResult) for result in results)
            assert results[0].title == "Steel Suppliers Inc - Industrial Steel Products"
    
    @pytest.mark.asyncio
    async def test_execute_search_error_handling(self, search_service):
        """Test error handling in _execute_search"""
        with patch.object(search_service.ddgs, 'text', side_effect=Exception("API Error")):
            results = await search_service._execute_search("steel suppliers", 3)
            
            assert len(results) == 0
    
    def test_clean_query(self, search_service):
        """Test query cleaning functionality"""
        test_cases = [
            ("Steel Suppliers!", "steel suppliers"),
            ("  Multiple   Spaces  ", "multiple spaces"),
            ("Special@#$%Characters", "specialcharacters"),
            ("UPPERCASE QUERY", "uppercase query"),
            ("", "")
        ]
        
        for input_query, expected in test_cases:
            result = search_service._clean_query(input_query)
            assert result == expected
    
    def test_extract_domain(self, search_service):
        """Test domain extraction from URLs"""
        test_cases = [
            ("https://example.com/path", "example.com"),
            ("http://subdomain.example.com", "subdomain.example.com"),
            ("https://example.com:8080/path", "example.com:8080"),
            ("invalid-url", "unknown"),
            ("", "unknown")
        ]
        
        for url, expected in test_cases:
            result = search_service._extract_domain(url)
            assert result == expected
    
    def test_deduplicate_results(self, search_service):
        """Test result deduplication"""
        duplicate_results = [
            SearchResult(
                title="Steel Suppliers Inc",
                url="https://steelsuppliers.com",
                snippet="Steel supplier",
                source="steelsuppliers.com",
                relevance_score=0.8
            ),
            SearchResult(
                title="Steel Suppliers Inc",  # Duplicate title
                url="https://steelsuppliers.com",  # Duplicate URL
                snippet="Steel supplier",
                source="steelsuppliers.com",
                relevance_score=0.8
            ),
            SearchResult(
                title="Different Steel Company",
                url="https://different.com",
                snippet="Different supplier",
                source="different.com",
                relevance_score=0.7
            )
        ]
        
        deduplicated = search_service._deduplicate_results(duplicate_results)
        assert len(deduplicated) == 2
        assert deduplicated[0].title == "Steel Suppliers Inc"
        assert deduplicated[1].title == "Different Steel Company"
    
    def test_filter_supplier_results(self, search_service):
        """Test supplier result filtering"""
        results = [
            SearchResult(
                title="Steel Suppliers Inc - Manufacturing",
                url="https://steelsuppliers.com",
                snippet="Leading manufacturer of steel products",
                source="steelsuppliers.com",
                relevance_score=0.5
            ),
            SearchResult(
                title="Download Free Steel Guide",
                url="https://spam.com",
                snippet="Click here for free download",
                source="spam.com",
                relevance_score=0.5
            )
        ]
        
        filtered = search_service._filter_supplier_results(results)
        assert len(filtered) == 1
        assert "Steel Suppliers Inc" in filtered[0].title
    
    def test_filter_market_results(self, search_service):
        """Test market result filtering"""
        results = [
            SearchResult(
                title="Steel Market Analysis Report",
                url="https://marketanalysis.com",
                snippet="Comprehensive market analysis and pricing trends",
                source="marketanalysis.com",
                relevance_score=0.5
            ),
            SearchResult(
                title="Buy Steel Products Now",
                url="https://sales.com",
                snippet="Special offer on steel products",
                source="sales.com",
                relevance_score=0.5
            )
        ]
        
        filtered = search_service._filter_market_results(results)
        assert len(filtered) == 1
        assert "Market Analysis" in filtered[0].title
    
    def test_is_spam_or_irrelevant(self, search_service):
        """Test spam detection"""
        spam_result = SearchResult(
            title="Free Download - Click Here",
            url="https://spam.com",
            snippet="Limited time offer, download now",
            source="spam.com",
            relevance_score=0.5
        )
        
        legitimate_result = SearchResult(
            title="Steel Manufacturing Company",
            url="https://steelco.com",
            snippet="Professional steel manufacturing services",
            source="steelco.com",
            relevance_score=0.8
        )
        
        assert search_service._is_spam_or_irrelevant(spam_result) == True
        assert search_service._is_spam_or_irrelevant(legitimate_result) == False
    
    def test_rank_results(self, search_service):
        """Test result ranking"""
        results = [
            SearchResult(
                title="Steel Company",
                url="https://steel.com",
                snippet="We provide steel",
                source="steel.com",
                relevance_score=0.3
            ),
            SearchResult(
                title="Steel Suppliers Manufacturing",
                url="https://steelsuppliers.com",
                snippet="Steel suppliers and manufacturers",
                source="steelsuppliers.com",
                relevance_score=0.5
            )
        ]
        
        ranked = search_service._rank_results(results, "steel suppliers")
        
        # Should be ranked by relevance score
        assert ranked[0].relevance_score >= ranked[1].relevance_score
    
    @pytest.mark.asyncio
    async def test_get_search_suggestions(self, search_service):
        """Test search suggestions"""
        suggestions = await search_service.get_search_suggestions("steel")
        
        assert len(suggestions) <= 5
        assert all("steel" in suggestion.lower() for suggestion in suggestions)
    
    @pytest.mark.asyncio
    async def test_search_with_rate_limiting(self, search_service):
        """Test that search respects rate limiting"""
        with patch('asyncio.sleep') as mock_sleep:
            with patch.object(search_service, '_execute_search') as mock_execute:
                mock_execute.return_value = []
                
                await search_service.search_suppliers("steel", "Texas", 3)
                
                # Should have called sleep for rate limiting
                assert mock_sleep.called
    
    @pytest.mark.asyncio
    async def test_search_suppliers_with_location(self, search_service):
        """Test supplier search with location filter"""
        with patch.object(search_service, '_execute_search') as mock_execute:
            mock_execute.return_value = [
                SearchResult(
                    title="Texas Steel Suppliers",
                    url="https://texassteel.com",
                    snippet="Steel suppliers in Texas",
                    source="texassteel.com",
                    relevance_score=0.8
                )
            ]
            
            results = await search_service.search_suppliers("steel", "Texas", 5)
            
            # Should have made multiple search calls with location
            assert mock_execute.call_count > 1
            
            # Check that location was included in search queries
            call_args = [call[0][0] for call in mock_execute.call_args_list]
            assert any("Texas" in arg for arg in call_args)
    
    @pytest.mark.asyncio
    async def test_concurrent_searches(self, search_service):
        """Test concurrent search operations"""
        async def search_task(query):
            return await search_service.search_suppliers(query, None, 3)
        
        # Run multiple searches concurrently
        tasks = [
            search_task("steel"),
            search_task("aluminum"),
            search_task("copper")
        ]
        
        with patch.object(search_service, '_execute_search') as mock_execute:
            mock_execute.return_value = []
            
            results = await asyncio.gather(*tasks)
            
            assert len(results) == 3
            assert all(isinstance(result, list) for result in results)

if __name__ == "__main__":
    pytest.main([__file__])