import asyncio
import time
import logging
from typing import List, Dict, Any, Optional
from duckduckgo_search import DDGS
from app.config import settings
from app.models.responses import SearchResult
import re
from urllib.parse import urlparse
import json

logger = logging.getLogger(__name__)

class SearchService:
    def __init__(self):
        self.ddgs = DDGS()
        self.rate_limit_delay = settings.search_rate_limit_delay
        self.max_results = settings.max_search_results
        self.timeout = settings.request_timeout
        
    async def search_suppliers(self, query: str, location: Optional[str] = None, max_results: int = 10) -> List[SearchResult]:
        """
        Comprehensive supplier search using multiple query strategies
        """
        try:
            base_query = self._clean_query(query)
            location_filter = f" {location}" if location else ""
            
            search_queries = [
                f"{base_query} suppliers manufacturers{location_filter}",
                f"{base_query} vendors distributors{location_filter}",
                f"certified {base_query} companies{location_filter}",
                f"{base_query} industry directory{location_filter}",
                f"wholesale {base_query} suppliers{location_filter}"
            ]
            
            all_results = []
            for search_query in search_queries:
                try:
                    logger.info(f"Searching: {search_query}")
                    results = await self._execute_search(search_query, max_results=5)
                    all_results.extend(results)
                    await asyncio.sleep(self.rate_limit_delay)
                except Exception as e:
                    logger.error(f"Search failed for query '{search_query}': {e}")
                    continue
            
            deduplicated_results = self._deduplicate_results(all_results)
            filtered_results = self._filter_supplier_results(deduplicated_results)
            
            return self._rank_results(filtered_results, query)[:max_results]
            
        except Exception as e:
            logger.error(f"Supplier search failed: {e}")
            return []
    
    async def search_market_data(self, product: str, timeframe: str = "6months") -> List[SearchResult]:
        """
        Market intelligence focused search
        """
        try:
            base_query = self._clean_query(product)
            current_year = time.strftime("%Y")
            
            market_queries = [
                f"{base_query} market price {current_year}",
                f"{base_query} pricing trends analysis {timeframe}",
                f"{base_query} industry report market size",
                f"{base_query} cost analysis {current_year}",
                f"{base_query} market forecast pricing",
                f"{base_query} supply chain costs"
            ]
            
            all_results = []
            for search_query in market_queries:
                try:
                    logger.info(f"Market search: {search_query}")
                    results = await self._execute_search(search_query, max_results=5)
                    all_results.extend(results)
                    await asyncio.sleep(self.rate_limit_delay)
                except Exception as e:
                    logger.error(f"Market search failed for query '{search_query}': {e}")
                    continue
            
            deduplicated_results = self._deduplicate_results(all_results)
            filtered_results = self._filter_market_results(deduplicated_results)
            
            return self._rank_results(filtered_results, product)[:self.max_results]
            
        except Exception as e:
            logger.error(f"Market data search failed: {e}")
            return []
    
    async def search_general(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """
        General search functionality
        """
        try:
            cleaned_query = self._clean_query(query)
            results = await self._execute_search(cleaned_query, max_results)
            return self._rank_results(results, query)
            
        except Exception as e:
            logger.error(f"General search failed: {e}")
            return []
    
    async def _execute_search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """
        Execute DuckDuckGo search with error handling
        """
        try:
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None, 
                lambda: self.ddgs.text(query, max_results=max_results)
            )
            
            search_results = []
            for result in results:
                try:
                    search_result = SearchResult(
                        title=result.get('title', ''),
                        url=result.get('href', ''),
                        snippet=result.get('body', ''),
                        source=self._extract_domain(result.get('href', '')),
                        relevance_score=0.5  # Default score, will be updated by ranking
                    )
                    search_results.append(search_result)
                except Exception as e:
                    logger.warning(f"Failed to parse search result: {e}")
                    continue
            
            return search_results
            
        except Exception as e:
            logger.error(f"DuckDuckGo search execution failed: {e}")
            return []
    
    def _clean_query(self, query: str) -> str:
        """
        Clean and optimize search query
        """
        cleaned = re.sub(r'[^\w\s-]', '', query.strip())
        cleaned = re.sub(r'\s+', ' ', cleaned)
        return cleaned.lower()
    
    def _extract_domain(self, url: str) -> str:
        """
        Extract domain from URL
        """
        try:
            parsed = urlparse(url)
            return parsed.netloc
        except:
            return "unknown"
    
    def _deduplicate_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """
        Remove duplicate results based on URL and title similarity
        """
        seen_urls = set()
        seen_titles = set()
        unique_results = []
        
        for result in results:
            url_normalized = result.url.lower().strip('/')
            title_normalized = result.title.lower().strip()
            
            if url_normalized not in seen_urls and title_normalized not in seen_titles:
                seen_urls.add(url_normalized)
                seen_titles.add(title_normalized)
                unique_results.append(result)
        
        return unique_results
    
    def _filter_supplier_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """
        Filter results to prioritize supplier-related content
        """
        supplier_keywords = [
            'supplier', 'manufacturer', 'vendor', 'distributor', 'company',
            'corporation', 'inc', 'llc', 'ltd', 'wholesale', 'industrial',
            'factory', 'producer', 'exporter', 'importer'
        ]
        
        filtered_results = []
        for result in results:
            content = f"{result.title} {result.snippet}".lower()
            
            if any(keyword in content for keyword in supplier_keywords):
                result.relevance_score = min(result.relevance_score + 0.2, 1.0)
            
            if not self._is_spam_or_irrelevant(result):
                filtered_results.append(result)
        
        return filtered_results
    
    def _filter_market_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """
        Filter results to prioritize market intelligence content
        """
        market_keywords = [
            'market', 'price', 'pricing', 'cost', 'analysis', 'report',
            'trend', 'forecast', 'industry', 'research', 'data',
            'statistics', 'survey', 'outlook', 'intelligence'
        ]
        
        filtered_results = []
        for result in results:
            content = f"{result.title} {result.snippet}".lower()
            
            if any(keyword in content for keyword in market_keywords):
                result.relevance_score = min(result.relevance_score + 0.3, 1.0)
            
            if not self._is_spam_or_irrelevant(result):
                filtered_results.append(result)
        
        return filtered_results
    
    def _is_spam_or_irrelevant(self, result: SearchResult) -> bool:
        """
        Detect and filter spam or irrelevant results
        """
        spam_indicators = [
            'download', 'free', 'click here', 'sign up', 'register now',
            'limited time', 'special offer', 'discount', 'sale',
            'wikipedia', 'amazon.com', 'ebay.com', 'social media'
        ]
        
        content = f"{result.title} {result.snippet}".lower()
        return any(indicator in content for indicator in spam_indicators)
    
    def _rank_results(self, results: List[SearchResult], original_query: str) -> List[SearchResult]:
        """
        Rank results by relevance to original query
        """
        query_terms = set(self._clean_query(original_query).split())
        
        for result in results:
            title_terms = set(self._clean_query(result.title).split())
            snippet_terms = set(self._clean_query(result.snippet).split())
            
            title_overlap = len(query_terms.intersection(title_terms))
            snippet_overlap = len(query_terms.intersection(snippet_terms))
            
            relevance_boost = (title_overlap * 0.3 + snippet_overlap * 0.1) / len(query_terms)
            result.relevance_score = min(result.relevance_score + relevance_boost, 1.0)
        
        return sorted(results, key=lambda x: x.relevance_score, reverse=True)
    
    async def get_search_suggestions(self, query: str) -> List[str]:
        """
        Get search suggestions for auto-complete
        """
        try:
            base_query = self._clean_query(query)
            suggestions = [
                f"{base_query} suppliers",
                f"{base_query} manufacturers",
                f"{base_query} vendors",
                f"{base_query} distributors",
                f"{base_query} companies"
            ]
            return suggestions[:5]
        except Exception as e:
            logger.error(f"Failed to get suggestions: {e}")
            return []