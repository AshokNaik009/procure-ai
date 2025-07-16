import time
import os
from typing import List, Dict, Any, Optional
import requests
import re
from urllib.parse import urlparse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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
    """Brave Search API service for cloud deployment"""
    
    def __init__(self):
        try:
            print("🔧 Initializing Brave Search API...")
            
            # Get API key from environment
            self.api_key = os.getenv("BRAVE_API_KEY")
            if not self.api_key:
                print("❌ BRAVE_API_KEY not found in environment")
                print(f"   Available env vars: {[k for k in os.environ.keys() if 'BRAVE' in k or 'API' in k]}")
                self.api_key = None
                return
            
            print(f"✅ Found BRAVE_API_KEY: {self.api_key[:10]}...")
            
            # Brave Search API configuration
            self.base_url = "https://api.search.brave.com/res/v1"
            self.headers = {
                "X-Subscription-Token": self.api_key,
                "Accept": "application/json",
                "User-Agent": "ProcurementIntelligence/1.0"
            }
            
            # Test API connection
            test_response = requests.get(
                f"{self.base_url}/web/search",
                headers=self.headers,
                params={"q": "test", "count": 1},
                timeout=10
            )
            
            if test_response.status_code == 200:
                print("✅ Brave Search API initialized successfully")
                self.available = True
            else:
                print(f"❌ Brave Search API test failed: {test_response.status_code}")
                self.available = False
                
        except Exception as e:
            print(f"❌ Brave Search API initialization failed: {e}")
            self.available = False
    
    async def search_suppliers(self, query: str, location: str = None, max_results: int = 10) -> List[Dict]:
        """Search for suppliers using Brave Search API"""
        try:
            print(f"🔍 Starting Brave Search for: {query}")
            
            # Create cache key
            cache_key = f"suppliers:{query}:{location or 'global'}"
            cached_result = simple_cache_get(cache_key)
            if cached_result:
                print(f"📦 Cache hit for: {query}")
                return cached_result
            
            # Check if Brave Search API is available
            if not self.available:
                print("❌ Brave Search API not available")
                return []
            
            print("✅ Brave Search API is available, proceeding with search...")
            
            # Build search queries
            search_queries = self._build_search_queries(query, location)
            
            all_results = []
            for i, search_query in enumerate(search_queries[:3]):  # Limit to 3 queries
                try:
                    print(f"🔍 Brave Search [{i+1}/3]: {search_query}")
                    
                    # Rate limiting
                    if i > 0:
                        time.sleep(1)
                    
                    # Call Brave Search API
                    response = requests.get(
                        f"{self.base_url}/web/search",
                        headers=self.headers,
                        params={
                            "q": search_query,
                            "count": 10,
                            "offset": 0,
                            "search_lang": "en",
                            "country": "US",
                            "safesearch": "moderate"
                        },
                        timeout=15
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        web_results = data.get("web", {}).get("results", [])
                        
                        print(f"   ✅ Brave API returned {len(web_results)} results")
                        
                        # Process results
                        for result in web_results:
                            supplier_data = {
                                "title": result.get("title", "").strip(),
                                "url": result.get("url", "").strip(),
                                "snippet": result.get("description", "").strip(),
                                "source": self._extract_domain(result.get("url", ""))
                            }
                            
                            if supplier_data["title"] and supplier_data["url"]:
                                all_results.append(supplier_data)
                                print(f"   ✅ Processed: {supplier_data['title']}")
                    
                    elif response.status_code == 429:
                        print("   ⚠️ Rate limited - waiting before retry...")
                        time.sleep(2)
                        continue
                    
                    else:
                        print(f"   ❌ Brave API error: {response.status_code}")
                        print(f"   📋 Response: {response.text}")
                        continue
                        
                except Exception as e:
                    print(f"   ❌ Search error: {e}")
                    continue
            
            print(f"📈 Total results collected: {len(all_results)}")
            
            # Deduplicate results
            seen_urls = set()
            unique_results = []
            for result in all_results:
                if result["url"] not in seen_urls and result["url"]:
                    seen_urls.add(result["url"])
                    unique_results.append(result)
            
            # Cache and return
            final_results = unique_results[:max_results]
            simple_cache_set(cache_key, final_results, 1800)
            
            print(f"✅ Returning {len(final_results)} unique suppliers")
            return final_results
            
        except Exception as e:
            print(f"❌ Brave Search service failed: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _build_search_queries(self, query: str, location: str = None) -> List[str]:
        """Build focused search queries for Brave Search API"""
        base_terms = [
            f"{query} suppliers",
            f"{query} manufacturers",
            f"{query} vendors"
        ]
        
        queries = []
        for term in base_terms:
            if location:
                queries.append(f"{term} {location}")
            else:
                queries.append(term)
        
        return queries
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            return urlparse(url).netloc
        except:
            return "unknown"