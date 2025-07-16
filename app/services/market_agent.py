import asyncio
import logging
from typing import List, Dict, Any, Optional
import time
from app.services.search_service import SearchService
from app.services.llm_service import LLMService
from app.models.requests import MarketIntelligenceRequest
from app.models.responses import MarketIntelligence, MarketIntelligenceResponse
from app.config import settings
import re
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class MarketAgent:
    def __init__(self):
        self.search_service = SearchService()
        self.llm_service = LLMService()
        
    async def analyze_market(self, request: MarketIntelligenceRequest) -> MarketIntelligenceResponse:
        """
        Main market intelligence analysis orchestration
        """
        start_time = time.time()
        
        try:
            logger.info(f"Starting market analysis for: {request.product}")
            
            # Stage 1: Gather market data through search
            market_data = await self._gather_market_data(request)
            
            # Stage 2: Extract competitive intelligence if requested
            competitive_data = {}
            if request.include_competitors:
                competitive_data = await self._gather_competitive_data(request)
            
            # Stage 3: Analyze trends if requested
            trend_data = {}
            if request.include_trends:
                trend_data = await self._analyze_trends(request, market_data)
            
            # Stage 4: Synthesize intelligence using LLM
            market_intelligence = await self._synthesize_intelligence(
                market_data, request, competitive_data, trend_data
            )
            
            # Stage 5: Generate forecast
            forecast = await self._generate_forecast(market_intelligence, request)
            
            processing_time = time.time() - start_time
            
            logger.info(f"Market analysis completed in {processing_time:.2f}s")
            
            return MarketIntelligenceResponse(
                market_intelligence=market_intelligence,
                competitive_landscape=competitive_data,
                forecast=forecast,
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"Market analysis failed: {e}")
            # Return fallback response
            return MarketIntelligenceResponse(
                market_intelligence=await self._create_fallback_intelligence(request),
                competitive_landscape={},
                forecast={},
                processing_time=time.time() - start_time
            )
    
    async def _gather_market_data(self, request: MarketIntelligenceRequest) -> List[Dict[str, Any]]:
        """
        Gather comprehensive market data through searches
        """
        try:
            # Search for market data
            search_results = await self.search_service.search_market_data(
                product=request.product,
                timeframe=request.timeframe.value
            )
            
            # Convert search results to structured data
            market_data = []
            for result in search_results:
                data_point = {
                    'title': result.title,
                    'content': result.snippet,
                    'source': result.source,
                    'url': result.url,
                    'relevance': result.relevance_score,
                    'data_type': self._classify_data_type(result.title, result.snippet)
                }
                market_data.append(data_point)
            
            # Enrich with additional specific searches
            enriched_data = await self._enrich_market_data(request, market_data)
            
            return enriched_data
            
        except Exception as e:
            logger.error(f"Market data gathering failed: {e}")
            return []
    
    async def _enrich_market_data(self, request: MarketIntelligenceRequest, base_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Enrich market data with additional targeted searches
        """
        try:
            enrichment_queries = [
                f"{request.product} supply chain analysis",
                f"{request.product} raw material costs",
                f"{request.product} demand forecast",
                f"{request.product} industry challenges",
                f"{request.product} regulatory impact"
            ]
            
            if request.region:
                enrichment_queries.extend([
                    f"{request.product} {request.region} market analysis",
                    f"{request.product} {request.region} suppliers"
                ])
            
            enriched_data = base_data.copy()
            
            # Execute enrichment searches
            for query in enrichment_queries:
                try:
                    results = await self.search_service.search_general(query, max_results=3)
                    
                    for result in results:
                        enriched_data.append({
                            'title': result.title,
                            'content': result.snippet,
                            'source': result.source,
                            'url': result.url,
                            'relevance': result.relevance_score,
                            'data_type': 'enrichment',
                            'query_type': query
                        })
                    
                    await asyncio.sleep(0.3)  # Rate limiting
                    
                except Exception as e:
                    logger.warning(f"Enrichment search failed for '{query}': {e}")
                    continue
            
            return enriched_data
            
        except Exception as e:
            logger.error(f"Market data enrichment failed: {e}")
            return base_data
    
    async def _gather_competitive_data(self, request: MarketIntelligenceRequest) -> Dict[str, Any]:
        """
        Gather competitive intelligence
        """
        try:
            competitor_queries = [
                f"{request.product} market leaders",
                f"{request.product} top companies",
                f"{request.product} competitive analysis",
                f"{request.product} market share"
            ]
            
            competitive_data = {
                'key_players': [],
                'market_share': {},
                'competitive_advantages': [],
                'market_positioning': []
            }
            
            for query in competitor_queries:
                try:
                    results = await self.search_service.search_general(query, max_results=5)
                    
                    for result in results:
                        # Extract competitor information
                        competitors = self._extract_competitors(result.title, result.snippet)
                        competitive_data['key_players'].extend(competitors)
                        
                        # Extract market positioning insights
                        positioning = self._extract_positioning(result.snippet)
                        if positioning:
                            competitive_data['market_positioning'].append(positioning)
                    
                    await asyncio.sleep(0.3)  # Rate limiting
                    
                except Exception as e:
                    logger.warning(f"Competitive search failed for '{query}': {e}")
                    continue
            
            # Deduplicate competitors
            competitive_data['key_players'] = list(set(competitive_data['key_players']))
            
            return competitive_data
            
        except Exception as e:
            logger.error(f"Competitive data gathering failed: {e}")
            return {}
    
    async def _analyze_trends(self, request: MarketIntelligenceRequest, market_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze market trends from collected data
        """
        try:
            trend_indicators = {
                'price_trends': [],
                'demand_trends': [],
                'supply_trends': [],
                'technology_trends': [],
                'regulatory_trends': []
            }
            
            # Analyze each data point for trend indicators
            for data_point in market_data:
                content = f"{data_point['title']} {data_point['content']}"
                
                # Price trend detection
                price_trends = self._detect_price_trends(content)
                trend_indicators['price_trends'].extend(price_trends)
                
                # Demand trend detection
                demand_trends = self._detect_demand_trends(content)
                trend_indicators['demand_trends'].extend(demand_trends)
                
                # Supply trend detection
                supply_trends = self._detect_supply_trends(content)
                trend_indicators['supply_trends'].extend(supply_trends)
                
                # Technology trend detection
                tech_trends = self._detect_technology_trends(content)
                trend_indicators['technology_trends'].extend(tech_trends)
                
                # Regulatory trend detection
                reg_trends = self._detect_regulatory_trends(content)
                trend_indicators['regulatory_trends'].extend(reg_trends)
            
            # Consolidate and rank trends
            consolidated_trends = self._consolidate_trends(trend_indicators)
            
            return consolidated_trends
            
        except Exception as e:
            logger.error(f"Trend analysis failed: {e}")
            return {}
    
    async def _synthesize_intelligence(self, market_data: List[Dict[str, Any]], 
                                     request: MarketIntelligenceRequest,
                                     competitive_data: Dict[str, Any],
                                     trend_data: Dict[str, Any]) -> MarketIntelligence:
        """
        Synthesize all collected data into market intelligence using LLM
        """
        try:
            # Prepare comprehensive context for LLM
            context = {
                'product': request.product,
                'timeframe': request.timeframe.value,
                'region': request.region,
                'market_data_points': len(market_data),
                'competitive_data': competitive_data,
                'trend_data': trend_data,
                'data_summary': market_data[:10]  # Limit to avoid token limits
            }
            
            # Use LLM service to analyze market trends
            market_intelligence = await self.llm_service.analyze_market_trends(market_data, request.product)
            
            # Enrich with additional analysis
            if competitive_data:
                market_intelligence.key_players = competitive_data.get('key_players', [])
            
            return market_intelligence
            
        except Exception as e:
            logger.error(f"Intelligence synthesis failed: {e}")
            return await self._create_fallback_intelligence(request)
    
    async def _generate_forecast(self, market_intelligence: MarketIntelligence, 
                               request: MarketIntelligenceRequest) -> Dict[str, Any]:
        """
        Generate market forecast based on intelligence
        """
        try:
            forecast = {
                'timeframe': request.timeframe.value,
                'confidence_level': 'medium',
                'key_predictions': [],
                'risk_factors': [],
                'opportunities': market_intelligence.opportunities,
                'recommended_actions': []
            }
            
            # Analyze price trends for forecast
            if market_intelligence.price_insights:
                price_trend = market_intelligence.price_insights.trend
                
                if price_trend == 'increasing':
                    forecast['key_predictions'].append('Prices expected to continue rising')
                    forecast['recommended_actions'].append('Consider forward contracts or bulk purchasing')
                elif price_trend == 'decreasing':
                    forecast['key_predictions'].append('Prices may continue to decline')
                    forecast['recommended_actions'].append('Delay non-urgent purchases if possible')
                else:
                    forecast['key_predictions'].append('Prices expected to remain stable')
                    forecast['recommended_actions'].append('Normal procurement timing recommended')
            
            # Add risk factors
            forecast['risk_factors'] = market_intelligence.risks
            
            # Generate timeline-specific predictions
            timeline_predictions = self._generate_timeline_predictions(request.timeframe.value)
            forecast['key_predictions'].extend(timeline_predictions)
            
            return forecast
            
        except Exception as e:
            logger.error(f"Forecast generation failed: {e}")
            return {
                'timeframe': request.timeframe.value,
                'confidence_level': 'low',
                'key_predictions': ['Insufficient data for reliable forecast'],
                'risk_factors': ['Data quality limitations'],
                'opportunities': [],
                'recommended_actions': ['Conduct more detailed market research']
            }
    
    def _classify_data_type(self, title: str, content: str) -> str:
        """
        Classify the type of market data
        """
        text = f"{title} {content}".lower()
        
        if any(keyword in text for keyword in ['price', 'cost', 'pricing', 'rate']):
            return 'pricing'
        elif any(keyword in text for keyword in ['trend', 'forecast', 'outlook', 'prediction']):
            return 'trend'
        elif any(keyword in text for keyword in ['report', 'analysis', 'study', 'research']):
            return 'research'
        elif any(keyword in text for keyword in ['supplier', 'vendor', 'manufacturer']):
            return 'supplier'
        elif any(keyword in text for keyword in ['demand', 'supply', 'inventory']):
            return 'supply_demand'
        else:
            return 'general'
    
    def _extract_competitors(self, title: str, content: str) -> List[str]:
        """
        Extract competitor names from text
        """
        competitors = []
        text = f"{title} {content}"
        
        # Look for company name patterns
        company_patterns = [
            r'\b([A-Z][a-zA-Z]+\s+(?:Inc|LLC|Corp|Corporation|Company|Co\.|Ltd))\b',
            r'\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)\s+(?:is|are|has|have)\s+(?:leading|major|top)',
            r'(?:leading|major|top)\s+companies?\s+(?:include|are|such as)\s+([A-Z][a-zA-Z\s,]+)'
        ]
        
        for pattern in company_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, str) and len(match) > 2:
                    competitors.append(match.strip())
        
        return competitors[:5]  # Limit to top 5
    
    def _extract_positioning(self, content: str) -> Optional[str]:
        """
        Extract market positioning information
        """
        positioning_patterns = [
            r'positioned\s+(?:as|to)\s+([^.]+)',
            r'market\s+leader\s+in\s+([^.]+)',
            r'specializes?\s+in\s+([^.]+)',
            r'focus(?:es)?\s+on\s+([^.]+)'
        ]
        
        for pattern in positioning_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _detect_price_trends(self, content: str) -> List[str]:
        """
        Detect price trend indicators
        """
        trends = []
        content_lower = content.lower()
        
        if any(keyword in content_lower for keyword in ['price increase', 'rising cost', 'higher price']):
            trends.append('increasing')
        elif any(keyword in content_lower for keyword in ['price decrease', 'falling cost', 'lower price']):
            trends.append('decreasing')
        elif any(keyword in content_lower for keyword in ['stable price', 'steady cost', 'unchanged']):
            trends.append('stable')
        
        return trends
    
    def _detect_demand_trends(self, content: str) -> List[str]:
        """
        Detect demand trend indicators
        """
        trends = []
        content_lower = content.lower()
        
        if any(keyword in content_lower for keyword in ['growing demand', 'increased demand', 'rising demand']):
            trends.append('increasing_demand')
        elif any(keyword in content_lower for keyword in ['declining demand', 'decreased demand', 'falling demand']):
            trends.append('decreasing_demand')
        
        return trends
    
    def _detect_supply_trends(self, content: str) -> List[str]:
        """
        Detect supply trend indicators
        """
        trends = []
        content_lower = content.lower()
        
        if any(keyword in content_lower for keyword in ['supply shortage', 'limited supply', 'constrained supply']):
            trends.append('supply_shortage')
        elif any(keyword in content_lower for keyword in ['abundant supply', 'oversupply', 'surplus']):
            trends.append('supply_surplus')
        
        return trends
    
    def _detect_technology_trends(self, content: str) -> List[str]:
        """
        Detect technology trend indicators
        """
        trends = []
        content_lower = content.lower()
        
        tech_keywords = ['automation', 'ai', 'digital', 'innovation', 'technology']
        for keyword in tech_keywords:
            if keyword in content_lower:
                trends.append(f'technology_{keyword}')
        
        return trends
    
    def _detect_regulatory_trends(self, content: str) -> List[str]:
        """
        Detect regulatory trend indicators
        """
        trends = []
        content_lower = content.lower()
        
        if any(keyword in content_lower for keyword in ['regulation', 'compliance', 'policy', 'law']):
            trends.append('regulatory_change')
        
        return trends
    
    def _consolidate_trends(self, trend_indicators: Dict[str, List[str]]) -> Dict[str, Any]:
        """
        Consolidate and rank trends by frequency
        """
        consolidated = {}
        
        for trend_type, trends in trend_indicators.items():
            if trends:
                # Count frequency of each trend
                trend_counts = {}
                for trend in trends:
                    trend_counts[trend] = trend_counts.get(trend, 0) + 1
                
                # Sort by frequency
                sorted_trends = sorted(trend_counts.items(), key=lambda x: x[1], reverse=True)
                consolidated[trend_type] = sorted_trends[:3]  # Top 3 trends
        
        return consolidated
    
    def _generate_timeline_predictions(self, timeframe: str) -> List[str]:
        """
        Generate timeline-specific predictions
        """
        predictions = []
        
        if timeframe == '1month':
            predictions.append('Short-term price volatility expected')
        elif timeframe == '3months':
            predictions.append('Quarterly trends should become clearer')
        elif timeframe == '6months':
            predictions.append('Medium-term market patterns emerging')
        elif timeframe == '1year':
            predictions.append('Long-term structural changes may occur')
        
        return predictions
    
    async def _create_fallback_intelligence(self, request: MarketIntelligenceRequest) -> MarketIntelligence:
        """
        Create fallback market intelligence when analysis fails
        """
        from app.models.responses import PriceInsight, MarketTrend
        
        return MarketIntelligence(
            product_category=request.product,
            price_insights=PriceInsight(
                price_range={'min': 0, 'max': 0, 'avg': 0},
                currency='USD',
                trend='stable',
                factors=['Limited data available']
            ),
            market_trends=[
                MarketTrend(
                    trend_type='data_limitation',
                    description='Insufficient data for comprehensive analysis',
                    impact='medium',
                    confidence=0.3
                )
            ],
            recommendations=['Conduct more detailed market research', 'Consult industry experts'],
            market_size='Data unavailable',
            growth_rate='Data unavailable',
            key_players=[],
            opportunities=['Potential market opportunity due to limited data'],
            risks=['Data quality limitations may affect decision-making']
        )