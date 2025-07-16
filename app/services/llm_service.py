import asyncio
import logging
from typing import Dict, Any, List, Optional
import json
from groq import Groq
import google.generativeai as genai
from app.config import settings
from app.models.responses import SupplierInfo, MarketIntelligence, MarketTrend, PriceInsight, VerificationStatus
from datetime import datetime
import re

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.groq_client = Groq(api_key=settings.groq_api_key)
        genai.configure(api_key=settings.gemini_api_key)
        self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
        
    async def verify_supplier_data(self, supplier_info: Dict[str, Any], search_context: str = "") -> SupplierInfo:
        """
        Use LLM to verify and enrich supplier information
        """
        try:
            prompt = f"""
            Analyze the following supplier information and provide a structured assessment:
            
            Supplier Data: {json.dumps(supplier_info, indent=2)}
            Search Context: {search_context}
            
            Please provide a JSON response with the following structure:
            {{
                "name": "verified company name",
                "location": "verified location",
                "confidence_score": 0.0-1.0,
                "certifications": ["list", "of", "certifications"],
                "specialties": ["list", "of", "specialties"],
                "company_size": "Small/Medium/Large/Enterprise",
                "verification_status": "verified/unverified/pending",
                "contact_info": {{"email": "", "phone": "", "address": ""}},
                "description": "brief company description",
                "rating": 0.0-5.0 or null
            }}
            
            Focus on:
            1. Data accuracy and consistency
            2. Extracting relevant certifications (ISO, industry-specific)
            3. Determining company size indicators
            4. Assessing data reliability
            5. Identifying key specialties
            """
            
            # Try Groq first, fallback to Gemini
            try:
                response = await self._query_groq(prompt)
                verified_data = self._parse_supplier_response(response)
            except Exception as e:
                logger.warning(f"Groq failed, using Gemini: {e}")
                response = await self._query_gemini(prompt)
                verified_data = self._parse_supplier_response(response)
            
            return self._create_supplier_info(verified_data, supplier_info)
            
        except Exception as e:
            logger.error(f"Supplier verification failed: {e}")
            return self._create_fallback_supplier_info(supplier_info)
    
    async def analyze_market_trends(self, market_data: List[Dict[str, Any]], product: str) -> MarketIntelligence:
        """
        Use LLM to synthesize market intelligence from search results
        """
        try:
            data_summary = self._prepare_market_data_summary(market_data)
            
            prompt = f"""
            Analyze the following market data for {product} and provide comprehensive market intelligence:
            
            Market Data: {data_summary}
            
            Please provide a JSON response with the following structure:
            {{
                "price_insights": {{
                    "price_range": {{"min": 0, "max": 0, "avg": 0}},
                    "currency": "USD",
                    "unit": "per unit/kg/etc",
                    "trend": "increasing/decreasing/stable",
                    "factors": ["factor1", "factor2"]
                }},
                "market_trends": [
                    {{
                        "trend_type": "pricing/demand/supply/technology",
                        "description": "trend description",
                        "impact": "high/medium/low",
                        "confidence": 0.0-1.0
                    }}
                ],
                "market_size": "market size information",
                "growth_rate": "growth rate percentage",
                "key_players": ["company1", "company2"],
                "opportunities": ["opportunity1", "opportunity2"],
                "risks": ["risk1", "risk2"],
                "recommendations": ["recommendation1", "recommendation2"]
            }}
            
            Focus on:
            1. Price trends and forecasts
            2. Market dynamics and drivers
            3. Competitive landscape
            4. Supply chain insights
            5. Procurement recommendations
            """
            
            try:
                response = await self._query_groq(prompt)
                market_analysis = self._parse_market_response(response)
            except Exception as e:
                logger.warning(f"Groq failed, using Gemini: {e}")
                response = await self._query_gemini(prompt)
                market_analysis = self._parse_market_response(response)
            
            return self._create_market_intelligence(market_analysis, product)
            
        except Exception as e:
            logger.error(f"Market analysis failed: {e}")
            return self._create_fallback_market_intelligence(product)
    
    async def generate_procurement_summary(self, suppliers: List[SupplierInfo], market_intel: MarketIntelligence, query: str) -> Dict[str, Any]:
        """
        Generate executive summary and recommendations
        """
        try:
            prompt = f"""
            Based on the following procurement analysis, generate an executive summary and recommendations:
            
            Original Query: {query}
            Number of Suppliers Found: {len(suppliers)}
            Top Suppliers: {[s.name for s in suppliers[:5]]}
            Market Intelligence: {market_intel.dict() if market_intel else "Limited data"}
            
            Please provide a JSON response with:
            {{
                "executive_summary": "2-3 sentence summary",
                "key_findings": ["finding1", "finding2", "finding3"],
                "recommendations": ["recommendation1", "recommendation2"],
                "next_steps": ["step1", "step2", "step3"],
                "confidence_score": 0.0-1.0,
                "risk_assessment": "low/medium/high",
                "timeline_estimate": "estimated timeline"
            }}
            """
            
            try:
                response = await self._query_groq(prompt)
                return self._parse_json_response(response)
            except Exception as e:
                logger.warning(f"Groq failed, using Gemini: {e}")
                response = await self._query_gemini(prompt)
                return self._parse_json_response(response)
                
        except Exception as e:
            logger.error(f"Summary generation failed: {e}")
            return self._create_fallback_summary(query, len(suppliers))
    
    async def _query_groq(self, prompt: str) -> str:
        """
        Query Groq API with error handling
        """
        try:
            response = self.groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a procurement intelligence analyst. Provide accurate, structured analysis in JSON format."},
                    {"role": "user", "content": prompt}
                ],
                model="llama3-8b-8192",
                temperature=0.3,
                max_tokens=2000
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            raise
    
    async def _query_gemini(self, prompt: str) -> str:
        """
        Query Gemini API with error handling
        """
        try:
            response = self.gemini_model.generate_content(
                f"You are a procurement intelligence analyst. {prompt}",
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,
                    max_output_tokens=2000
                )
            )
            return response.text
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise
    
    def _parse_supplier_response(self, response: str) -> Dict[str, Any]:
        """
        Parse LLM response for supplier data
        """
        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return {}
        except Exception as e:
            logger.error(f"Failed to parse supplier response: {e}")
            return {}
    
    def _parse_market_response(self, response: str) -> Dict[str, Any]:
        """
        Parse LLM response for market intelligence
        """
        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return {}
        except Exception as e:
            logger.error(f"Failed to parse market response: {e}")
            return {}
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """
        Generic JSON response parser
        """
        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return {}
        except Exception as e:
            logger.error(f"Failed to parse JSON response: {e}")
            return {}
    
    def _create_supplier_info(self, verified_data: Dict[str, Any], original_data: Dict[str, Any]) -> SupplierInfo:
        """
        Create SupplierInfo object from verified data
        """
        return SupplierInfo(
            name=verified_data.get('name', original_data.get('name', 'Unknown')),
            website=original_data.get('website'),
            location=verified_data.get('location', original_data.get('location', 'Unknown')),
            confidence_score=verified_data.get('confidence_score', 0.5),
            certifications=verified_data.get('certifications', []),
            contact_info=verified_data.get('contact_info', {}),
            verification_status=VerificationStatus(verified_data.get('verification_status', 'unverified')),
            specialties=verified_data.get('specialties', []),
            company_size=verified_data.get('company_size'),
            rating=verified_data.get('rating'),
            description=verified_data.get('description')
        )
    
    def _create_fallback_supplier_info(self, original_data: Dict[str, Any]) -> SupplierInfo:
        """
        Create fallback SupplierInfo when LLM fails
        """
        return SupplierInfo(
            name=original_data.get('name', 'Unknown'),
            website=original_data.get('website'),
            location=original_data.get('location', 'Unknown'),
            confidence_score=0.3,
            certifications=[],
            contact_info={},
            verification_status=VerificationStatus.UNVERIFIED,
            specialties=[],
            company_size=None,
            rating=None,
            description=None
        )
    
    def _create_market_intelligence(self, market_data: Dict[str, Any], product: str) -> MarketIntelligence:
        """
        Create MarketIntelligence object from analyzed data
        """
        price_data = market_data.get('price_insights', {})
        trends_data = market_data.get('market_trends', [])
        
        price_insight = PriceInsight(
            price_range=price_data.get('price_range', {'min': 0, 'max': 0, 'avg': 0}),
            currency=price_data.get('currency', 'USD'),
            unit=price_data.get('unit'),
            trend=price_data.get('trend', 'stable'),
            factors=price_data.get('factors', [])
        )
        
        market_trends = []
        for trend_data in trends_data:
            trend = MarketTrend(
                trend_type=trend_data.get('trend_type', 'general'),
                description=trend_data.get('description', ''),
                impact=trend_data.get('impact', 'medium'),
                confidence=trend_data.get('confidence', 0.5)
            )
            market_trends.append(trend)
        
        return MarketIntelligence(
            product_category=product,
            price_insights=price_insight,
            market_trends=market_trends,
            recommendations=market_data.get('recommendations', []),
            market_size=market_data.get('market_size'),
            growth_rate=market_data.get('growth_rate'),
            key_players=market_data.get('key_players', []),
            opportunities=market_data.get('opportunities', []),
            risks=market_data.get('risks', [])
        )
    
    def _create_fallback_market_intelligence(self, product: str) -> MarketIntelligence:
        """
        Create fallback MarketIntelligence when LLM fails
        """
        return MarketIntelligence(
            product_category=product,
            price_insights=PriceInsight(
                price_range={'min': 0, 'max': 0, 'avg': 0},
                currency='USD',
                trend='stable',
                factors=[]
            ),
            market_trends=[],
            recommendations=["Unable to generate recommendations due to limited data"],
            market_size="Data unavailable",
            growth_rate="Data unavailable",
            key_players=[],
            opportunities=[],
            risks=[]
        )
    
    def _prepare_market_data_summary(self, market_data: List[Dict[str, Any]]) -> str:
        """
        Prepare market data summary for LLM analysis
        """
        try:
            summary_items = []
            for item in market_data[:10]:  # Limit to avoid token limits
                summary_items.append({
                    'title': item.get('title', ''),
                    'snippet': item.get('snippet', ''),
                    'source': item.get('source', '')
                })
            return json.dumps(summary_items, indent=2)
        except Exception as e:
            logger.error(f"Failed to prepare market data summary: {e}")
            return "Limited market data available"
    
    def _create_fallback_summary(self, query: str, supplier_count: int) -> Dict[str, Any]:
        """
        Create fallback summary when LLM fails
        """
        return {
            "executive_summary": f"Found {supplier_count} potential suppliers for {query}. Further analysis recommended.",
            "key_findings": ["Multiple suppliers identified", "Manual verification recommended"],
            "recommendations": ["Contact top suppliers directly", "Request detailed quotes"],
            "next_steps": ["Verify supplier credentials", "Compare pricing", "Negotiate terms"],
            "confidence_score": 0.5,
            "risk_assessment": "medium",
            "timeline_estimate": "2-4 weeks"
        }