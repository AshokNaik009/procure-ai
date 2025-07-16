import time
import asyncio
import hashlib
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from search_service import SearchService
from llm_service import LLMService

class CompetitiveIntelligenceService:
    """Service for competitive intelligence and market benchmarking"""
    
    def __init__(self):
        self.search_service = SearchService()
        self.llm_service = LLMService()
        self.cache = {}  # In-memory cache with 24hr TTL
        self.cache_ttl = 24 * 60 * 60  # 24 hours in seconds
    
    def _generate_cache_key(self, product: str, location: Optional[str] = None) -> str:
        """Generate consistent cache key for product/location combination"""
        cache_data = f"{product.lower()}_{location or 'global'}"
        return hashlib.md5(cache_data.encode()).hexdigest()
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid (within TTL)"""
        if cache_key not in self.cache:
            return False
        
        cached_time = self.cache[cache_key].get('timestamp', 0)
        return (time.time() - cached_time) < self.cache_ttl
    
    def _cache_results(self, cache_key: str, data: Dict[str, Any]):
        """Cache results with timestamp"""
        self.cache[cache_key] = {
            'data': data,
            'timestamp': time.time()
        }
    
    async def analyze_market_benchmark(self, request) -> Dict[str, Any]:
        """
        Analyze market benchmarks and competitive positioning
        """
        start_time = time.time()
        
        try:
            print(f"🔍 Starting competitive analysis for: {request.product}")
            
            # Check cache first
            cache_key = self._generate_cache_key(request.product, request.location)
            if self._is_cache_valid(cache_key):
                print(f"📦 Using cached benchmark data for: {request.product}")
                cached_data = self.cache[cache_key]['data']
                # Update processing time but keep cached analysis
                cached_data['processing_time'] = time.time() - start_time
                return cached_data
            
            # Search for market data
            market_data = await self._search_market_benchmarks(request)
            
            # Analyze with LLM
            benchmark_analysis = await self._analyze_with_llm(market_data, request)
            
            # Cache results
            self._cache_results(cache_key, benchmark_analysis)
            
            processing_time = time.time() - start_time
            benchmark_analysis['processing_time'] = processing_time
            
            print(f"✅ Competitive analysis completed in {processing_time:.2f}s")
            return benchmark_analysis
            
        except Exception as e:
            print(f"❌ Competitive analysis failed: {e}")
            # Return fallback analysis
            return await self._generate_fallback_analysis(request, time.time() - start_time)
    
    async def _search_market_benchmarks(self, request) -> List[Dict[str, Any]]:
        """Search for market benchmark data using existing search service"""
        
        # Build focused search queries for competitive intelligence
        search_queries = [
            f"{request.product} industry average price benchmark 2025",
            f"{request.product} market pricing analysis competitive pricing",
            f"{request.product} cost comparison supplier pricing study"
        ]
        
        # Add location-specific queries if location provided
        if request.location:
            search_queries.extend([
                f"{request.product} pricing {request.location} market rates",
                f"{request.product} suppliers {request.location} cost analysis"
            ])
        
        all_results = []
        
        for i, query in enumerate(search_queries[:4]):  # Limit to 4 queries
            try:
                print(f"🔍 Searching market data [{i+1}/4]: {query}")
                
                # Use existing search service
                results = await self.search_service.search_suppliers(query, max_results=6)
                
                # Rate limiting for API calls
                if i < len(search_queries) - 1:
                    await asyncio.sleep(1.2)  # Respect API limits
                
                # Process and add results
                for result in results:
                    market_result = {
                        'title': result.get('title', ''),
                        'snippet': result.get('snippet', ''),
                        'url': result.get('url', ''),
                        'source': result.get('source', ''),
                        'query_context': query
                    }
                    all_results.append(market_result)
                    
            except Exception as e:
                print(f"❌ Search failed for query '{query}': {e}")
                continue
        
        print(f"📊 Collected {len(all_results)} market data points")
        return all_results
    
    async def _analyze_with_llm(self, market_data: List[Dict], request) -> Dict[str, Any]:
        """Use LLM to analyze market data and generate competitive insights"""
        
        # Prepare market data for LLM analysis
        market_snippets = []
        for item in market_data[:15]:  # Limit to prevent token overflow
            snippet = f"Source: {item['source']}\nTitle: {item['title']}\nContent: {item['snippet']}\n"
            market_snippets.append(snippet)
        
        market_context = "\n".join(market_snippets)
        
        # Build comprehensive analysis prompt
        analysis_prompt = f"""
        You are a procurement and competitive intelligence expert. Analyze the following market research data for competitive benchmarking.

        PRODUCT: {request.product}
        SUPPLIER QUOTE: ${request.supplier_quote or 'Not provided'}
        QUANTITY: {request.quantity or 'Not specified'}
        LOCATION: {request.location or 'Global'}
        COMPANY SIZE: {request.company_size or 'Not specified'}

        MARKET RESEARCH DATA:
        {market_context}

        Provide a detailed competitive analysis in the following JSON format:
        {{
            "market_average_price": <estimated average price as float or null>,
            "price_variance": <percentage variance from average as float or null>,
            "your_position": "<above_market|below_market|at_market>",
            "percentile_ranking": <0-100 percentile ranking or null>,
            "key_competitors": [
                {{
                    "name": "<competitor name>",
                    "price": <estimated price or null>,
                    "market_position": "<leader|challenger|follower>",
                    "strengths": ["<strength1>", "<strength2>"]
                }}
            ],
            "negotiation_strategy": {{
                "suggested_counter_offer": <recommended counter-offer price or null>,
                "leverage_points": ["<point1>", "<point2>", "<point3>"],
                "alternative_suppliers": ["<alt1>", "<alt2>"],
                "risk_factors": ["<risk1>", "<risk2>"],
                "timeline_recommendation": "<recommended negotiation timeline>",
                "opening_approach": "<suggested opening negotiation approach>"
            }},
            "market_insights": [
                "<key market insight 1>",
                "<key market insight 2>",
                "<key market insight 3>"
            ]
        }}

        IMPORTANT GUIDELINES:
        1. Extract specific price points and percentages where mentioned
        2. Identify actual competitor names from the data
        3. Base recommendations on concrete market evidence
        4. If supplier quote is provided, compare it to market rates
        5. Provide actionable negotiation strategies
        6. Focus on recent market trends and pricing factors
        7. If data is limited, clearly indicate uncertainty but provide best estimates
        """
        
        try:
            # Use existing LLM service
            print("🤖 Analyzing market data with LLM...")
            analysis_response = await self.llm_service.analyze_market_data(analysis_prompt)
            
            # Parse JSON response
            if isinstance(analysis_response, str):
                analysis_result = json.loads(analysis_response)
            else:
                analysis_result = analysis_response
            
            print("✅ LLM analysis completed")
            return analysis_result
            
        except Exception as e:
            print(f"❌ LLM analysis failed: {e}")
            return await self._generate_fallback_analysis(request, 0)
    
    async def _generate_fallback_analysis(self, request, processing_time: float) -> Dict[str, Any]:
        """Generate fallback analysis when search/LLM fails"""
        
        print("🆘 Generating fallback competitive analysis")
        
        # Basic fallback based on common market knowledge
        fallback_analysis = {
            "market_average_price": None,
            "price_variance": None,
            "your_position": "at_market",
            "percentile_ranking": 50,
            "key_competitors": [
                {
                    "name": f"Leading {request.product} Supplier",
                    "price": None,
                    "market_position": "leader",
                    "strengths": ["Market presence", "Competitive pricing"]
                },
                {
                    "name": f"Alternative {request.product} Provider",
                    "price": None,
                    "market_position": "challenger",
                    "strengths": ["Innovation", "Customer service"]
                }
            ],
            "negotiation_strategy": {
                "suggested_counter_offer": None,
                "leverage_points": [
                    "Request volume discount for large orders",
                    "Negotiate payment terms for better rates",
                    "Explore long-term contract pricing"
                ],
                "alternative_suppliers": [
                    "Research additional suppliers for comparison",
                    "Consider regional suppliers for cost savings"
                ],
                "risk_factors": [
                    "Limited market research data available",
                    "Pricing may vary significantly by region"
                ],
                "timeline_recommendation": "Allow 2-3 weeks for thorough market comparison",
                "opening_approach": "Start with market research presentation and request for competitive pricing"
            },
            "market_insights": [
                f"Limited market data available for {request.product}",
                "Consider conducting more detailed market research",
                "Pricing may vary significantly based on specifications and volume"
            ],
            "processing_time": processing_time
        }
        
        # Adjust based on supplier quote if provided
        if request.supplier_quote:
            fallback_analysis["negotiation_strategy"]["suggested_counter_offer"] = request.supplier_quote * 0.95
            fallback_analysis["negotiation_strategy"]["leverage_points"].insert(0, 
                f"Current quote of ${request.supplier_quote} needs market validation")
        
        return fallback_analysis
    
    async def get_cached_benchmark(self, product_hash: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached benchmark data"""
        if self._is_cache_valid(product_hash):
            return self.cache[product_hash]['data']
        return None