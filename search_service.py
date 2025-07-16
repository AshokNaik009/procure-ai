import time
from typing import List, Dict, Any, Optional
from duckduckgo_search import DDGS
import re
from urllib.parse import urlparse

# Simple in-memory cache
search_cache = {}

def simple_cache_get(key: str) -> Optional[Any]:
    """Get item from cache if not expired"""
    if key in search_cache:
        item = search_cache[key]
        if item["expires"] > time.time():
            return item["data"]
        else:
            del search_cache[key]
    return None

def simple_cache_set(key: str, data: Any, ttl: int = 3600):
    """Set item in cache with TTL"""
    search_cache[key] = {
        "data": data,
        "expires": time.time() + ttl
    }

class SearchService:
    """Simple DuckDuckGo search service"""
    
    def __init__(self):
        self.ddgs = DDGS()
    
    async def search_suppliers(self, query: str, location: str = None, max_results: int = 10) -> List[Dict]:
        """Search for suppliers using DuckDuckGo"""
        try:
            # Create cache key
            cache_key = f"suppliers:{query}:{location or 'global'}"
            cached_result = simple_cache_get(cache_key)
            if cached_result:
                print(f"📦 Cache hit for: {query}")
                return cached_result
            
            # Build search queries
            base_query = f"{query} suppliers manufacturers"
            if location:
                base_query += f" {location}"
            
            search_queries = [
                base_query,
                f"{query} vendors distributors" + (f" {location}" if location else ""),
                f"certified {query} companies" + (f" {location}" if location else "")
            ]
            
            all_results = []
            for search_query in search_queries:
                try:
                    print(f"🔍 Searching: {search_query}")
                    
                    # Basic rate limiting
                    time.sleep(1)
                    
                    results = self.ddgs.text(search_query, max_results=5)
                    for result in results:
                        supplier_data = {
                            "title": result.get("title", ""),
                            "url": result.get("href", ""),
                            "snippet": result.get("body", ""),
                            "source": self._extract_domain(result.get("href", ""))
                        }
                        all_results.append(supplier_data)
                        
                except Exception as e:
                    print(f"❌ Search error for '{search_query}': {e}")
                    continue
            
            # Deduplicate results
            seen_urls = set()
            unique_results = []
            for result in all_results:
                if result["url"] not in seen_urls and result["url"]:
                    seen_urls.add(result["url"])
                    unique_results.append(result)
            
            # Cache results
            final_results = unique_results[:max_results]
            simple_cache_set(cache_key, final_results, 1800)  # 30 minutes
            
            print(f"✅ Found {len(final_results)} unique suppliers")
            return final_results
            
        except Exception as e:
            print(f"❌ Search service failed: {e}")
            return []
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            return urlparse(url).netloc
        except:
            return "unknown"