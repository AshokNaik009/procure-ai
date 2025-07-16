import json
import re
import time
from typing import List, Dict, Any
from groq import Groq
import google.generativeai as genai
from pydantic import BaseModel
import os

class SupplierInfo(BaseModel):
    name: str
    location: str
    description: str
    website: str = None
    confidence_score: float
    certifications: List[str] = []
    rating: float = None

class MarketInsight(BaseModel):
    price_trend: str
    key_factors: List[str]
    recommendations: List[str]

# Simple LLM cache
llm_cache = {}

def llm_cache_get(key: str) -> Any:
    """Get LLM response from cache"""
    if key in llm_cache:
        item = llm_cache[key]
        if item["expires"] > time.time():
            return item["data"]
        else:
            del llm_cache[key]
    return None

def llm_cache_set(key: str, data: Any, ttl: int = 7200):  # 2 hours
    """Cache LLM response"""
    llm_cache[key] = {
        "data": data,
        "expires": time.time() + ttl
    }

class LLMService:
    """Simple LLM service with Groq and Gemini"""
    
    def __init__(self):
        self.groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
    
    async def analyze_suppliers(self, search_results: List[Dict]) -> List[SupplierInfo]:
        """Analyze search results to extract supplier information"""
        suppliers = []
        
        for result in search_results:
            try:
                # Extract basic supplier info
                supplier_info = self._extract_supplier_info(result)
                
                # Enhance with LLM if we have good data
                if supplier_info["name"] and len(supplier_info["name"]) > 2:
                    enhanced_info = await self._enhance_supplier_data(supplier_info)
                    suppliers.append(enhanced_info)
                    
            except Exception as e:
                print(f"❌ Supplier analysis error: {e}")
                continue
        
        return suppliers
    
    def _extract_supplier_info(self, result: Dict) -> Dict:
        """Extract basic supplier info from search result"""
        title = result.get("title", "")
        snippet = result.get("snippet", "")
        url = result.get("url", "")
        
        # Extract company name (simple approach)
        company_name = title.split(" - ")[0].strip()
        if not company_name:
            company_name = title.split("|")[0].strip()
        
        # Extract location (simple regex)
        location = "Location not specified"
        location_patterns = [
            r"(?:located|based|headquarters|office)\s+(?:in|at)\s+([A-Z][a-zA-Z\s,]+)",
            r"([A-Z][a-zA-Z\s]+,\s*[A-Z]{2})",
            r"([A-Z][a-zA-Z\s]+,\s*[A-Z][a-zA-Z\s]+)"
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, snippet)
            if match:
                location = match.group(1).strip()
                break
        
        return {
            "name": company_name,
            "location": location,
            "description": snippet,
            "website": url,
            "source_title": title
        }
    
    async def _enhance_supplier_data(self, supplier_info: Dict) -> SupplierInfo:
        """Enhance supplier data using LLM"""
        try:
            # Check cache first
            cache_key = f"supplier:{supplier_info['name']}:{hash(supplier_info['description'])}"
            cached_result = llm_cache_get(cache_key)
            if cached_result:
                print(f"📦 LLM cache hit for: {supplier_info['name']}")
                return SupplierInfo(**cached_result)
            
            # Try Groq first
            prompt = f"""
            Analyze this supplier information and provide a JSON response:
            
            Name: {supplier_info['name']}
            Location: {supplier_info['location']}
            Description: {supplier_info['description']}
            
            Provide JSON with these fields:
            {{
                "confidence_score": 0.0-1.0,
                "certifications": ["list", "of", "certifications"],
                "rating": 1.0-5.0 or null
            }}
            
            Focus on extracting certifications (ISO, industry-specific) and estimating quality rating.
            """
            
            try:
                print(f"🤖 Analyzing supplier with Groq: {supplier_info['name']}")
                response = self.groq_client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": "You are a procurement analyst. Respond with valid JSON only."},
                        {"role": "user", "content": prompt}
                    ],
                    model="llama3-8b-8192",
                    temperature=0.3,
                    max_tokens=500
                )
                
                llm_response = response.choices[0].message.content
                
                # Parse JSON response
                json_match = re.search(r'\{.*\}', llm_response, re.DOTALL)
                if json_match:
                    enhanced_data = json.loads(json_match.group())
                else:
                    enhanced_data = {}
                    
            except Exception as e:
                print(f"❌ Groq error, trying Gemini: {e}")
                try:
                    response = self.gemini_model.generate_content(prompt)
                    json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
                    if json_match:
                        enhanced_data = json.loads(json_match.group())
                    else:
                        enhanced_data = {}
                except Exception as e2:
                    print(f"❌ Gemini error: {e2}")
                    enhanced_data = {}
            
            result = SupplierInfo(
                name=supplier_info["name"],
                location=supplier_info["location"],
                description=supplier_info["description"],
                website=supplier_info.get("website"),
                confidence_score=enhanced_data.get("confidence_score", 0.5),
                certifications=enhanced_data.get("certifications", []),
                rating=enhanced_data.get("rating")
            )
            
            # Cache the result
            llm_cache_set(cache_key, result.dict())
            
            return result
            
        except Exception as e:
            print(f"❌ Enhancement failed: {e}")
            return SupplierInfo(
                name=supplier_info["name"],
                location=supplier_info["location"],
                description=supplier_info["description"],
                website=supplier_info.get("website"),
                confidence_score=0.5,
                certifications=[],
                rating=None
            )
    
    async def generate_market_insights(self, query: str, suppliers: List[SupplierInfo]) -> MarketInsight:
        """Generate market insights"""
        try:
            # Check cache first
            cache_key = f"market:{query}:{len(suppliers)}"
            cached_result = llm_cache_get(cache_key)
            if cached_result:
                print(f"📦 Market insights cache hit for: {query}")
                return MarketInsight(**cached_result)
            
            prompt = f"""
            Generate market insights for: {query}
            
            Found {len(suppliers)} suppliers. Generate insights about:
            1. Price trends (increasing/decreasing/stable)
            2. Key market factors (3-5 factors)
            3. Procurement recommendations (3-5 recommendations)
            
            Respond in JSON format:
            {{
                "price_trend": "increasing/decreasing/stable",
                "key_factors": ["factor1", "factor2", "factor3"],
                "recommendations": ["rec1", "rec2", "rec3"]
            }}
            """
            
            try:
                print(f"📊 Generating market insights with Groq for: {query}")
                response = self.groq_client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": "You are a market analyst. Respond with valid JSON only."},
                        {"role": "user", "content": prompt}
                    ],
                    model="llama3-8b-8192",
                    temperature=0.3,
                    max_tokens=500
                )
                
                llm_response = response.choices[0].message.content
                json_match = re.search(r'\{.*\}', llm_response, re.DOTALL)
                if json_match:
                    insights = json.loads(json_match.group())
                else:
                    insights = {}
                    
            except Exception as e:
                print(f"❌ Market insights error: {e}")
                insights = {}
            
            result = MarketInsight(
                price_trend=insights.get("price_trend", "stable"),
                key_factors=insights.get("key_factors", ["Limited market data available"]),
                recommendations=insights.get("recommendations", ["Conduct further market research"])
            )
            
            # Cache the result
            llm_cache_set(cache_key, result.dict())
            
            return result
            
        except Exception as e:
            print(f"❌ Market insights failed: {e}")
            return MarketInsight(
                price_trend="stable",
                key_factors=["Limited market data available"],
                recommendations=["Conduct further market research"]
            )
    
    async def analyze_market_data(self, prompt: str) -> Dict[str, Any]:
        """Analyze market data for competitive intelligence"""
        try:
            # Check cache first
            cache_key = f"competitive:{hash(prompt)}"
            cached_result = llm_cache_get(cache_key)
            if cached_result:
                print("📦 Competitive analysis cache hit")
                return cached_result
            
            try:
                print("🤖 Analyzing competitive data with Groq...")
                response = self.groq_client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": "You are a procurement and competitive intelligence expert. Respond with valid JSON only."},
                        {"role": "user", "content": prompt}
                    ],
                    model="llama3-8b-8192",
                    temperature=0.3,
                    max_tokens=1500
                )
                
                llm_response = response.choices[0].message.content
                
                # Parse JSON response
                json_match = re.search(r'\{.*\}', llm_response, re.DOTALL)
                if json_match:
                    analysis_result = json.loads(json_match.group())
                else:
                    raise ValueError("No valid JSON found in response")
                    
            except Exception as e:
                print(f"❌ Groq error, trying Gemini: {e}")
                try:
                    response = self.gemini_model.generate_content(prompt)
                    json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
                    if json_match:
                        analysis_result = json.loads(json_match.group())
                    else:
                        raise ValueError("No valid JSON found in Gemini response")
                except Exception as e2:
                    print(f"❌ Gemini error: {e2}")
                    raise e2
            
            # Cache the result
            llm_cache_set(cache_key, analysis_result)
            
            return analysis_result
            
        except Exception as e:
            print(f"❌ Competitive analysis failed: {e}")
            # Return minimal fallback structure
            return {
                "market_average_price": None,
                "price_variance": None,
                "your_position": "at_market",
                "percentile_ranking": 50,
                "key_competitors": [],
                "negotiation_strategy": {
                    "suggested_counter_offer": None,
                    "leverage_points": ["Request competitive quotes", "Negotiate payment terms"],
                    "alternative_suppliers": ["Research additional suppliers"],
                    "risk_factors": ["Limited market data available"],
                    "timeline_recommendation": "Allow 2-3 weeks for thorough analysis",
                    "opening_approach": "Start with market research presentation"
                },
                "market_insights": ["Limited market data available for analysis"]
            }