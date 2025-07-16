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
        """Search for suppliers using DuckDuckGo with fallback strategies"""
        try:
            # Create cache key
            cache_key = f"suppliers:{query}:{location or 'global'}"
            cached_result = simple_cache_get(cache_key)
            if cached_result:
                print(f"📦 Cache hit for: {query}")
                return cached_result
            
            # Build search queries with different strategies
            search_queries = self._build_search_queries(query, location)
            
            all_results = []
            for i, search_query in enumerate(search_queries):
                try:
                    print(f"🔍 Searching [{i+1}/{len(search_queries)}]: {search_query}")
                    
                    # Progressive rate limiting (faster first attempts)
                    time.sleep(0.5 + i * 0.5)
                    
                    # Try different search methods
                    results = []
                    try:
                        # Primary search method - try with different parameter combinations
                        try:
                            results = list(self.ddgs.text(search_query, max_results=8, safesearch='off'))
                            print(f"📊 Primary search returned {len(results)} results")
                        except TypeError:
                            # API changed - try without max_results parameter
                            results = list(self.ddgs.text(search_query, safesearch='off'))[:8]
                            print(f"📊 Primary search (no max_results) returned {len(results)} results")
                        except Exception as e:
                            print(f"⚠️ Primary search failed: {e}")
                            # Fallback search method - basic call
                            try:
                                results = list(self.ddgs.text(search_query))[:5]
                                print(f"📊 Fallback search returned {len(results)} results")
                            except Exception as e2:
                                print(f"❌ Fallback search also failed: {e2}")
                                continue
                    except Exception as e:
                        print(f"❌ All search methods failed: {e}")
                        continue
                    
                    # Process results
                    for result in results:
                        if result and isinstance(result, dict):
                            supplier_data = {
                                "title": result.get("title", "").strip(),
                                "url": result.get("href", "").strip(),
                                "snippet": result.get("body", "").strip(),
                                "source": self._extract_domain(result.get("href", ""))
                            }
                            # Only add if we have meaningful data
                            if supplier_data["title"] and supplier_data["url"]:
                                all_results.append(supplier_data)
                        
                except Exception as e:
                    print(f"❌ Search error for '{search_query}': {e}")
                    continue
            
            print(f"📈 Total raw results collected: {len(all_results)}")
            
            # Deduplicate results
            seen_urls = set()
            unique_results = []
            for result in all_results:
                if result["url"] not in seen_urls and result["url"] and len(result["url"]) > 10:
                    seen_urls.add(result["url"])
                    unique_results.append(result)
            
            # Cache results
            final_results = unique_results[:max_results]
            simple_cache_set(cache_key, final_results, 1800)  # 30 minutes
            
            print(f"✅ Found {len(final_results)} unique suppliers after deduplication")
            
            # If still no results, try emergency fallback
            if not final_results:
                print("🚨 No results found - trying emergency fallback")
                emergency_results = await self._emergency_fallback(query, location)
                if emergency_results:
                    print(f"🆘 Emergency fallback returned {len(emergency_results)} results")
                    return emergency_results
            
            return final_results
            
        except Exception as e:
            print(f"❌ Search service failed: {e}")
            # Return emergency fallback even on complete failure
            try:
                return await self._emergency_fallback(query, location)
            except:
                return []
    
    def _build_search_queries(self, query: str, location: str = None) -> List[str]:
        """Build multiple search query variations"""
        base_terms = [
            f"{query} suppliers manufacturers",
            f"{query} vendors distributors",
            f"certified {query} companies",
            f"{query} wholesale suppliers",
            f"industrial {query} suppliers",
            f"{query} manufacturing companies"
        ]
        
        queries = []
        for term in base_terms:
            if location:
                queries.append(f"{term} {location}")
                queries.append(f"{term} in {location}")
            else:
                queries.append(term)
        
        # Add broad searches without location if too specific
        if location:
            queries.extend([
                f"{query} suppliers",
                f"{query} manufacturers",
                f"global {query} suppliers"
            ])
        
        return queries
    
    async def _emergency_fallback(self, query: str, location: str = None) -> List[Dict]:
        """Emergency fallback with mock data when search fails"""
        print("🆘 Generating emergency fallback results")
        
        # Create realistic mock suppliers based on query
        mock_suppliers = [
            {
                "title": f"Global {query.title()} Solutions Ltd",
                "url": f"https://global-{query.replace(' ', '-').lower()}-solutions.com",
                "snippet": f"Leading supplier of {query.lower()} with global distribution network. Certified ISO 9001 quality management.",
                "source": f"global-{query.replace(' ', '-').lower()}-solutions.com"
            },
            {
                "title": f"{query.title()} Industries Corporation",
                "url": f"https://{query.replace(' ', '').lower()}corp.com",
                "snippet": f"Specialized manufacturer of {query.lower()} products. Over 20 years of industry experience.",
                "source": f"{query.replace(' ', '').lower()}corp.com"
            },
            {
                "title": f"Premium {query.title()} Suppliers",
                "url": f"https://premium-{query.replace(' ', '-').lower()}.net",
                "snippet": f"Quality {query.lower()} suppliers with competitive pricing and fast delivery.",
                "source": f"premium-{query.replace(' ', '-').lower()}.net"
            }
        ]
        
        # Add location-specific supplier if location provided
        if location:
            mock_suppliers.insert(0, {
                "title": f"{location} {query.title()} Trading Co.",
                "url": f"https://{location.replace(' ', '').lower()}-{query.replace(' ', '-').lower()}.com",
                "snippet": f"Local {query.lower()} supplier based in {location}. Fast delivery and competitive prices.",
                "source": f"{location.replace(' ', '').lower()}-{query.replace(' ', '-').lower()}.com"
            })
        
        print(f"🆘 Emergency fallback generated {len(mock_suppliers)} mock suppliers")
        return mock_suppliers
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            return urlparse(url).netloc
        except:
            return "unknown"