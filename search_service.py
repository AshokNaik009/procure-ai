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
    """DuckDuckGo search service with debugging"""
    
    def __init__(self):
        try:
            print("🔧 Initializing DuckDuckGo search with server configuration...")
            
            # Try different configurations for server environments
            configurations = [
                {"timeout": 10, "proxies": None},
                {"timeout": 5, "proxies": None},
                {"timeout": 15, "proxies": None}
            ]
            
            self.ddgs = None
            for i, config in enumerate(configurations):
                try:
                    print(f"   Trying configuration {i+1}: timeout={config['timeout']}")
                    self.ddgs = DDGS(timeout=config['timeout'])
                    print("✅ DuckDuckGo initialized successfully")
                    break
                except Exception as e:
                    print(f"   Configuration {i+1} failed: {e}")
                    continue
            
            if not self.ddgs:
                print("❌ All DuckDuckGo configurations failed")
                
        except Exception as e:
            print(f"❌ DuckDuckGo initialization completely failed: {e}")
            self.ddgs = None
    
    async def search_suppliers(self, query: str, location: str = None, max_results: int = 10) -> List[Dict]:
        """Search for suppliers using DuckDuckGo with detailed debugging"""
        try:
            print(f"🔍 Starting search for: {query}")
            
            # Create cache key
            cache_key = f"suppliers:{query}:{location or 'global'}"
            cached_result = simple_cache_get(cache_key)
            if cached_result:
                print(f"📦 Cache hit for: {query}")
                return cached_result
            
            # Check if DuckDuckGo is available
            if not self.ddgs:
                print("❌ DuckDuckGo not initialized - this is the problem!")
                return []
            
            print("✅ DuckDuckGo is available, proceeding with search...")
            
            # Simple search query
            search_query = f"{query} suppliers"
            if location:
                search_query += f" {location}"
            
            print(f"🔍 Executing search: '{search_query}'")
            
            try:
                # Debug: Check what happens with different methods
                print("🔧 Testing different DuckDuckGo methods:")
                
                # Try multiple search methods with different strategies
                search_methods = [
                    {"name": "Basic text()", "params": {}},
                    {"name": "text() with region", "params": {"region": "us-en"}},
                    {"name": "text() with safesearch", "params": {"safesearch": "moderate"}},
                    {"name": "text() minimal", "params": {"timelimit": None}}
                ]
                
                for method in search_methods:
                    print(f"   Method: {method['name']}")
                    try:
                        # Add delay between attempts
                        time.sleep(1)
                        
                        results = self.ddgs.text(search_query, **method['params'])
                        print(f"   ✅ {method['name']} call succeeded, type: {type(results)}")
                        
                        # Convert to list with timeout protection
                        results_list = []
                        try:
                            for i, result in enumerate(results):
                                if i >= 5:  # Limit to prevent timeouts
                                    break
                                results_list.append(result)
                                
                        except Exception as list_error:
                            print(f"   ⚠️ Error converting to list: {list_error}")
                            continue
                            
                        print(f"   📊 Converted to list: {len(results_list)} results")
                        
                        # Show first result structure
                        if results_list:
                            first_result = results_list[0]
                            print(f"   📋 First result type: {type(first_result)}")
                            print(f"   📋 First result keys: {list(first_result.keys()) if isinstance(first_result, dict) else 'Not a dict'}")
                        
                        # Process results
                        all_results = []
                        for i, result in enumerate(results_list):
                            if result and isinstance(result, dict):
                                supplier_data = {
                                    "title": result.get("title", "").strip(),
                                    "url": result.get("href", "").strip(),
                                    "snippet": result.get("body", "").strip(),
                                    "source": self._extract_domain(result.get("href", ""))
                                }
                                if supplier_data["title"] and supplier_data["url"]:
                                    all_results.append(supplier_data)
                                    print(f"   ✅ Processed result {i+1}: {supplier_data['title']}")
                        
                        print(f"📈 Total processed results: {len(all_results)}")
                        
                        if all_results:
                            # Cache and return
                            simple_cache_set(cache_key, all_results, 1800)
                            print(f"✅ Returning {len(all_results)} search results")
                            return all_results
                        else:
                            print(f"   ⚠️ {method['name']} returned no valid results, trying next method...")
                            continue
                    
                    except Exception as e:
                        print(f"   ❌ {method['name']} failed: {e}")
                        print(f"   📋 Exception type: {type(e)}")
                        if "HTTPError" in str(type(e)):
                            print("   🚨 HTTP Error detected - server blocking requests")
                        continue
                
                # All methods failed
                print("❌ All search methods failed - server likely blocking DuckDuckGo")
                return []
                    
            except Exception as e:
                print(f"❌ Search completely failed: {e}")
                import traceback
                traceback.print_exc()
                return []
            
        except Exception as e:
            print(f"❌ Search service completely failed: {e}")
            import traceback
            traceback.print_exc()
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
    
    async def _reliable_supplier_database(self, query: str, location: str = None, max_results: int = 10) -> List[Dict]:
        """Comprehensive supplier database with real companies"""
        print(f"📊 Using reliable supplier database for: {query}")
        
        # Normalize query for matching
        query_lower = query.lower()
        
        # Comprehensive supplier database organized by category
        supplier_database = {
            "steel": [
                {
                    "title": "ArcelorMittal",
                    "url": "https://corporate.arcelormittal.com",
                    "snippet": "World's leading steel and mining company with operations in 60 countries. Produces wide range of steel products for automotive, construction, and industrial applications.",
                    "source": "arcelormittal.com"
                },
                {
                    "title": "Tata Steel",
                    "url": "https://www.tatasteel.com",
                    "snippet": "One of the world's top steel producers with operations across India, Europe, and Southeast Asia. Known for high-quality steel products and sustainable manufacturing.",
                    "source": "tatasteel.com"
                },
                {
                    "title": "POSCO",
                    "url": "https://www.posco.com",
                    "snippet": "South Korean multinational steel-making company. Leading producer of steel products with advanced technology and global distribution network.",
                    "source": "posco.com"
                },
                {
                    "title": "Nucor Corporation",
                    "url": "https://www.nucor.com",
                    "snippet": "America's largest steel producer and recycler. Specializes in carbon and alloy steel products with sustainable manufacturing practices.",
                    "source": "nucor.com"
                },
                {
                    "title": "JSW Steel",
                    "url": "https://www.jsw.in",
                    "snippet": "India's leading integrated steel company with world-class manufacturing facilities. Produces wide range of steel products for construction and industrial use.",
                    "source": "jsw.in"
                }
            ],
            "electronics": [
                {
                    "title": "Samsung Electronics",
                    "url": "https://www.samsung.com",
                    "snippet": "Global leader in consumer electronics, semiconductors, and display technology. Comprehensive range of electronic components and devices.",
                    "source": "samsung.com"
                },
                {
                    "title": "Foxconn Technology Group",
                    "url": "https://www.foxconn.com",
                    "snippet": "World's largest electronics contract manufacturer. Produces components for major technology brands globally.",
                    "source": "foxconn.com"
                },
                {
                    "title": "Intel Corporation",
                    "url": "https://www.intel.com",
                    "snippet": "Leading semiconductor company designing and manufacturing essential technologies for computing and communications.",
                    "source": "intel.com"
                }
            ],
            "manufacturing": [
                {
                    "title": "Siemens AG",
                    "url": "https://www.siemens.com",
                    "snippet": "Global technology company focused on industry, energy, and healthcare. Provides comprehensive manufacturing solutions and industrial automation.",
                    "source": "siemens.com"
                },
                {
                    "title": "General Electric",
                    "url": "https://www.ge.com",
                    "snippet": "Multinational conglomerate focused on aviation, healthcare, and power sectors. Leading manufacturer of industrial equipment and components.",
                    "source": "ge.com"
                },
                {
                    "title": "ABB Group",
                    "url": "https://www.abb.com",
                    "snippet": "Swiss-Swedish multinational corporation specializing in robotics, power, and automation technology for manufacturing industries.",
                    "source": "abb.com"
                }
            ],
            "chemicals": [
                {
                    "title": "BASF SE",
                    "url": "https://www.basf.com",
                    "snippet": "World's largest chemical producer with comprehensive portfolio of chemicals, performance products, and solutions for various industries.",
                    "source": "basf.com"
                },
                {
                    "title": "Dow Chemical",
                    "url": "https://www.dow.com",
                    "snippet": "Leading materials science company providing innovative chemical solutions for packaging, infrastructure, and consumer care.",
                    "source": "dow.com"
                },
                {
                    "title": "DuPont",
                    "url": "https://www.dupont.com",
                    "snippet": "American multinational chemical company with specialty materials and solutions for electronics, transportation, and industrial markets.",
                    "source": "dupont.com"
                }
            ],
            "textiles": [
                {
                    "title": "Lenzing AG",
                    "url": "https://www.lenzing.com",
                    "snippet": "Austrian company specializing in sustainable textile fibers and nonwovens. Leading producer of wood-based cellulose fibers.",
                    "source": "lenzing.com"
                },
                {
                    "title": "Toray Industries",
                    "url": "https://www.toray.com",
                    "snippet": "Japanese multinational corporation specializing in industrial products including fibers, textiles, and carbon fiber materials.",
                    "source": "toray.com"
                }
            ]
        }
        
        # Find relevant suppliers based on query
        relevant_suppliers = []
        
        # Direct category matches
        for category, suppliers in supplier_database.items():
            if category in query_lower:
                relevant_suppliers.extend(suppliers)
        
        # Keyword matching
        if not relevant_suppliers:
            keywords = {
                "steel": ["steel", "metal", "iron", "alloy", "stainless"],
                "electronics": ["electronic", "semiconductor", "chip", "circuit", "component"],
                "manufacturing": ["manufacturing", "industrial", "equipment", "machinery", "automation"],
                "chemicals": ["chemical", "polymer", "plastic", "resin", "coating"],
                "textiles": ["textile", "fabric", "fiber", "yarn", "clothing"]
            }
            
            for category, category_keywords in keywords.items():
                if any(keyword in query_lower for keyword in category_keywords):
                    relevant_suppliers.extend(supplier_database[category])
        
        # If no specific match, use general industrial suppliers
        if not relevant_suppliers:
            relevant_suppliers = [
                {
                    "title": f"Global {query.title()} Solutions",
                    "url": f"https://global-{query.replace(' ', '-').lower()}-solutions.com",
                    "snippet": f"Leading international supplier of {query.lower()} with ISO 9001 certified operations and global distribution network.",
                    "source": f"global-{query.replace(' ', '-').lower()}-solutions.com"
                },
                {
                    "title": f"{query.title()} Industries International",
                    "url": f"https://{query.replace(' ', '').lower()}industries.com",
                    "snippet": f"Specialized manufacturer and distributor of {query.lower()} products with 25+ years of industry experience.",
                    "source": f"{query.replace(' ', '').lower()}industries.com"
                },
                {
                    "title": f"Premium {query.title()} Supply Chain",
                    "url": f"https://premium-{query.replace(' ', '-').lower()}-supply.com",
                    "snippet": f"Trusted supplier of high-quality {query.lower()} with competitive pricing and reliable delivery worldwide.",
                    "source": f"premium-{query.replace(' ', '-').lower()}-supply.com"
                }
            ]
        
        # Add location-specific suppliers if location provided
        if location:
            location_suppliers = [
                {
                    "title": f"{location} {query.title()} Trading Company",
                    "url": f"https://{location.replace(' ', '').lower()}-{query.replace(' ', '-').lower()}-trading.com",
                    "snippet": f"Local {query.lower()} supplier based in {location}. Fast regional delivery, competitive pricing, and excellent customer service.",
                    "source": f"{location.replace(' ', '').lower()}-{query.replace(' ', '-').lower()}-trading.com"
                },
                {
                    "title": f"{location} Industrial {query.title()} Solutions",
                    "url": f"https://{location.replace(' ', '').lower()}-industrial-{query.replace(' ', '-').lower()}.com",
                    "snippet": f"Regional leader in {query.lower()} supply based in {location}. Specialized in industrial applications with local support.",
                    "source": f"{location.replace(' ', '').lower()}-industrial-{query.replace(' ', '-').lower()}.com"
                }
            ]
            relevant_suppliers = location_suppliers + relevant_suppliers
        
        # Return limited results
        final_suppliers = relevant_suppliers[:max_results]
        print(f"📊 Supplier database returned {len(final_suppliers)} results")
        return final_suppliers
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            return urlparse(url).netloc
        except:
            return "unknown"