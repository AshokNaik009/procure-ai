import json
import re
import time
import requests
from typing import List, Dict, Any, Optional
from groq import Groq
import google.generativeai as genai
from pydantic import BaseModel
import os
import yfinance as yf
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import ssl
import socket
from datetime import datetime
import whois as python_whois

class SupplierInfo(BaseModel):
    name: str
    location: str
    description: str
    website: str = None
    confidence_score: float
    certifications: List[str] = []
    rating: float = None
    logo_url: str = None
    financial_data: Optional[Dict[str, Any]] = None
    web_intelligence: Optional[Dict[str, Any]] = None
    risk_assessment: Optional[Dict[str, Any]] = None

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


class AdvancedIntelligenceAPI:
    """Advanced supplier intelligence with FREE APIs"""
    
    def __init__(self):
        self.clearbit_base_url = "https://logo.clearbit.com/"
        self.cache = {}
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        print("🧠 Advanced Intelligence API initialized (FREE tier)")
    
    def get_company_logo(self, website_url: str) -> Optional[str]:
        """Get company logo from Clearbit Logo API (100% FREE)"""
        try:
            if not website_url:
                return None
            
            # Extract domain from URL
            domain = urlparse(website_url).netloc
            if not domain:
                return None
            
            # Remove www. prefix
            domain = domain.replace('www.', '')
            
            # Construct Clearbit logo URL
            logo_url = f"{self.clearbit_base_url}{domain}"
            
            # Test if logo exists
            response = requests.head(logo_url, timeout=5)
            if response.status_code == 200:
                print(f"🖼️ Logo found for {domain}")
                return logo_url
            else:
                print(f"❌ No logo found for {domain}")
                return None
                
        except Exception as e:
            print(f"❌ Logo fetch error for {website_url}: {e}")
            return None
    
    def get_financial_intelligence(self, company_name: str) -> Optional[Dict]:
        """Get financial data from Yahoo Finance (FREE)"""
        try:
            # Common ticker symbol patterns
            potential_tickers = [
                company_name.upper().replace(' ', ''),
                company_name.split()[0].upper(),
                ''.join([word[0] for word in company_name.split()]).upper()
            ]
            
            for ticker_symbol in potential_tickers:
                try:
                    ticker = yf.Ticker(ticker_symbol)
                    info = ticker.info
                    
                    # Check if valid company data
                    if info.get('marketCap') or info.get('totalRevenue'):
                        financial_data = {
                            'ticker': ticker_symbol,
                            'market_cap': info.get('marketCap'),
                            'sector': info.get('sector'),
                            'industry': info.get('industry'),
                            'employee_count': info.get('fullTimeEmployees'),
                            'revenue': info.get('totalRevenue'),
                            'profit_margin': info.get('profitMargins'),
                            'pe_ratio': info.get('trailingPE'),
                            'debt_to_equity': info.get('debtToEquity'),
                            'return_on_equity': info.get('returnOnEquity'),
                            'financial_health_score': self._calculate_financial_health(info)
                        }
                        
                        print(f"💰 Financial data found for {company_name} ({ticker_symbol})")
                        return financial_data
                        
                except Exception:
                    continue
            
            print(f"❌ No financial data found for {company_name}")
            return None
            
        except Exception as e:
            print(f"❌ Financial intelligence error for {company_name}: {e}")
            return None
    
    def _calculate_financial_health(self, info: Dict) -> float:
        """Calculate financial health score (0-100)"""
        try:
            score = 50  # Base score
            
            # Market cap boost
            market_cap = info.get('marketCap', 0)
            if market_cap:
                if market_cap > 10_000_000_000:  # 10B+
                    score += 20
                elif market_cap > 1_000_000_000:  # 1B+
                    score += 15
                elif market_cap > 100_000_000:  # 100M+
                    score += 10
            
            # Profitability
            profit_margin = info.get('profitMargins', 0)
            if profit_margin and profit_margin > 0:
                score += min(profit_margin * 100, 15)  # Max 15 points
            
            # PE ratio (reasonable range)
            pe_ratio = info.get('trailingPE')
            if pe_ratio and 5 <= pe_ratio <= 25:
                score += 10
            
            # ROE
            roe = info.get('returnOnEquity')
            if roe and roe > 0.15:  # 15%+
                score += 10
            
            # Debt management
            debt_equity = info.get('debtToEquity')
            if debt_equity is not None:
                if debt_equity < 0.3:
                    score += 10
                elif debt_equity > 1.0:
                    score -= 10
            
            return min(max(score, 0), 100)
            
        except Exception:
            return 50
    
    def analyze_website_intelligence(self, website_url: str) -> Optional[Dict]:
        """Advanced web intelligence parsing"""
        try:
            if not website_url:
                return None
            
            print(f"🕷️ Analyzing website: {website_url}")
            
            # Fetch website content
            response = self.session.get(website_url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            intelligence = {
                'team_size_indicators': [],
                'certifications': [],
                'technology_stack': [],
                'founded_year': None,
                'social_media': {},
                'contact_methods': []
            }
            
            # Extract text content
            text_content = soup.get_text().lower()
            
            # Team size indicators
            team_patterns = [
                r'(\d+)\+?\s+employees?',
                r'team\s+of\s+(\d+)',
                r'(\d+)\s+people',
                r'staff\s+of\s+(\d+)'
            ]
            
            for pattern in team_patterns:
                matches = re.findall(pattern, text_content)
                if matches:
                    intelligence['team_size_indicators'].extend([int(m) for m in matches])
            
            # Certifications
            cert_keywords = ['iso', 'soc', 'gdpr', 'hipaa', 'pci', 'cmmi', 'certification', 'certified']
            for keyword in cert_keywords:
                if keyword in text_content:
                    intelligence['certifications'].append(keyword.upper())
            
            # Founded year
            year_pattern = r'(?:founded|established|since)\s+(\d{4})'
            year_match = re.search(year_pattern, text_content)
            if year_match:
                intelligence['founded_year'] = int(year_match.group(1))
            
            # Technology stack
            tech_indicators = {
                'wordpress': 'wp-content' in response.text,
                'react': 'react' in response.text.lower(),
                'angular': 'angular' in response.text.lower(),
                'google_analytics': 'google-analytics' in response.text,
                'cloudflare': 'cloudflare' in response.headers.get('server', '').lower(),
                'ssl': response.url.startswith('https://')
            }
            
            intelligence['technology_stack'] = [k for k, v in tech_indicators.items() if v]
            
            # Social media links
            social_patterns = {
                'linkedin': r'linkedin\.com/company/([^/\s"\']+)',
                'twitter': r'twitter\.com/([^/\s"\']+)',
                'facebook': r'facebook\.com/([^/\s"\']+)',
                'instagram': r'instagram\.com/([^/\s"\']+)'
            }
            
            for platform, pattern in social_patterns.items():
                match = re.search(pattern, response.text)
                if match:
                    intelligence['social_media'][platform] = match.group(1)
            
            # Contact methods
            if re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text_content):
                intelligence['contact_methods'].append('email')
            if re.search(r'\+?[\d\s\-\(\)]{10,}', text_content):
                intelligence['contact_methods'].append('phone')
            
            print(f"✅ Website intelligence extracted: {len(intelligence['certifications'])} certs, {len(intelligence['social_media'])} social")
            return intelligence
            
        except Exception as e:
            print(f"❌ Website intelligence error for {website_url}: {e}")
            return None
    
    def assess_company_risk(self, website_url: str, company_name: str) -> Optional[Dict]:
        """Risk assessment engine"""
        try:
            if not website_url:
                return None
            
            print(f"⚠️ Assessing risk for: {company_name}")
            
            risk_assessment = {
                'domain_age_years': None,
                'ssl_valid': False,
                'website_performance_score': 50,
                'risk_score': 50,  # Lower is better
                'risk_factors': []
            }
            
            domain = urlparse(website_url).netloc.replace('www.', '')
            
            # Domain age check
            try:
                domain_info = python_whois.whois(domain)
                if domain_info.creation_date:
                    creation_date = domain_info.creation_date
                    if isinstance(creation_date, list):
                        creation_date = creation_date[0]
                    
                    age_years = (datetime.now() - creation_date).days / 365.25
                    risk_assessment['domain_age_years'] = round(age_years, 1)
                    
                    if age_years < 1:
                        risk_assessment['risk_factors'].append('Very new domain')
                        risk_assessment['risk_score'] += 20
                    elif age_years < 3:
                        risk_assessment['risk_factors'].append('Young domain')
                        risk_assessment['risk_score'] += 10
                    else:
                        risk_assessment['risk_score'] -= 10
                        
            except Exception as e:
                print(f"   WHOIS lookup failed: {e}")
                risk_assessment['risk_factors'].append('Domain info unavailable')
            
            # SSL certificate check
            try:
                context = ssl.create_default_context()
                with socket.create_connection((domain, 443), timeout=5) as sock:
                    with context.wrap_socket(sock, server_hostname=domain) as ssock:
                        cert = ssock.getpeercert()
                        risk_assessment['ssl_valid'] = True
                        risk_assessment['risk_score'] -= 5
                        
            except Exception:
                risk_assessment['risk_factors'].append('Invalid/missing SSL certificate')
                risk_assessment['risk_score'] += 15
            
            # Website performance check
            try:
                start_time = time.time()
                response = requests.get(website_url, timeout=10)
                load_time = time.time() - start_time
                
                if load_time < 2:
                    risk_assessment['website_performance_score'] = 90
                elif load_time < 5:
                    risk_assessment['website_performance_score'] = 70
                else:
                    risk_assessment['website_performance_score'] = 40
                    risk_assessment['risk_factors'].append('Slow website performance')
                    
            except Exception:
                risk_assessment['risk_factors'].append('Website unreachable')
                risk_assessment['risk_score'] += 25
            
            # Cap risk score
            risk_assessment['risk_score'] = min(max(risk_assessment['risk_score'], 0), 100)
            
            print(f"✅ Risk assessment complete: {risk_assessment['risk_score']}/100 risk")
            return risk_assessment
            
        except Exception as e:
            print(f"❌ Risk assessment error for {website_url}: {e}")
            return None
    
    def calculate_smart_confidence_score(self, supplier_info: Dict, logo_url: str, 
                                       financial_data: Dict, web_intelligence: Dict, 
                                       risk_assessment: Dict) -> float:
        """Smart confidence scoring algorithm"""
        try:
            # Base score
            score = 30
            
            # Logo found (+20)
            if logo_url:
                score += 20
                print(f"   +20 for logo")
            
            # Financial data (+25)
            if financial_data:
                score += 25
                print(f"   +25 for financial data")
                
                # Additional boost for healthy financials
                health_score = financial_data.get('financial_health_score', 50)
                if health_score > 70:
                    score += 10
                    print(f"   +10 for healthy financials")
            
            # Certifications detected (+15)
            if web_intelligence and web_intelligence.get('certifications'):
                score += 15
                print(f"   +15 for certifications: {web_intelligence['certifications']}")
            
            # Social media presence (+10 each, max 30)
            if web_intelligence and web_intelligence.get('social_media'):
                social_count = len(web_intelligence['social_media'])
                social_boost = min(social_count * 10, 30)
                score += social_boost
                print(f"   +{social_boost} for {social_count} social media")
            
            # Years in business (+5 per year, max 25)
            if web_intelligence and web_intelligence.get('founded_year'):
                years_active = 2025 - web_intelligence['founded_year']
                years_boost = min(years_active * 5, 25)
                score += years_boost
                print(f"   +{years_boost} for {years_active} years in business")
            
            # Website unavailable (-10)
            if not supplier_info.get('website'):
                score -= 10
                print(f"   -10 for no website")
            
            # No contact info (-15)
            if web_intelligence and not web_intelligence.get('contact_methods'):
                score -= 15
                print(f"   -15 for no contact info")
            
            # Risk factors penalty
            if risk_assessment:
                risk_score = risk_assessment.get('risk_score', 50)
                if risk_score > 70:
                    score -= 20
                    print(f"   -20 for high risk ({risk_score})")
                elif risk_score < 30:
                    score += 10
                    print(f"   +10 for low risk ({risk_score})")
            
            # Normalize to 0.0-1.0 range
            final_score = min(max(score / 100, 0.0), 0.95)
            
            print(f"   Final confidence score: {final_score:.2f} (from {score}/100)")
            return final_score
            
        except Exception as e:
            print(f"❌ Confidence scoring error: {e}")
            return 0.5

class LLMService:
    """Simple LLM service with Groq and Gemini"""
    
    def __init__(self):
        self.groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Initialize Advanced Intelligence API
        self.advanced_intel = AdvancedIntelligenceAPI()
    
    async def analyze_suppliers(self, search_results: List[Dict]) -> List[SupplierInfo]:
        """Analyze search results to extract supplier information with advanced intelligence"""
        suppliers = []
        
        for result in search_results:
            try:
                print(f"\n🔍 Analyzing supplier: {result.get('title', 'Unknown')}")
                
                # Extract basic supplier info
                supplier_info = self._extract_supplier_info(result)
                
                if not supplier_info["name"] or len(supplier_info["name"]) < 2:
                    continue
                
                # Initialize intelligence data
                logo_url = None
                financial_data = None
                web_intelligence = None
                risk_assessment = None
                registration_data = None
                
                # 1. Get company logo (Clearbit - FREE)
                if supplier_info.get("website"):
                    logo_url = self.advanced_intel.get_company_logo(supplier_info["website"])
                
                # 2. Get financial intelligence (Yahoo Finance - FREE)
                financial_data = self.advanced_intel.get_financial_intelligence(supplier_info["name"])
                
                # 3. Advanced web intelligence
                if supplier_info.get("website"):
                    web_intelligence = self.advanced_intel.analyze_website_intelligence(supplier_info["website"])
                
                # 4. Risk assessment
                if supplier_info.get("website"):
                    risk_assessment = self.advanced_intel.assess_company_risk(
                        supplier_info["website"], 
                        supplier_info["name"]
                    )
                
                # 5. Skip OpenCorporates (removed)
                registration_data = None
                
                # 6. Calculate smart confidence score
                smart_confidence = self.advanced_intel.calculate_smart_confidence_score(
                    supplier_info, logo_url, financial_data, web_intelligence, risk_assessment
                )
                
                # 7. Enhance with LLM analysis
                enhanced_info = await self._enhance_supplier_data_advanced(
                    supplier_info, logo_url, financial_data, 
                    web_intelligence, risk_assessment, smart_confidence
                )
                
                suppliers.append(enhanced_info)
                print(f"✅ Supplier analysis complete: {enhanced_info.name} (confidence: {enhanced_info.confidence_score:.2f})")
                
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
    
    async def _enhance_supplier_data_advanced(self, supplier_info: Dict, 
                                            logo_url: str = None, financial_data: Dict = None, 
                                            web_intelligence: Dict = None, risk_assessment: Dict = None,
                                            smart_confidence: float = None) -> SupplierInfo:
        """Enhanced supplier data with advanced intelligence"""
        try:
            # Check cache first
            cache_key = f"supplier_advanced:{supplier_info['name']}:{hash(supplier_info['description'])}"
            cached_result = llm_cache_get(cache_key)
            if cached_result:
                print(f"📦 Advanced LLM cache hit for: {supplier_info['name']}")
                # Update cached result with new intelligence data
                cached_result.update({
                    'logo_url': logo_url,
                    'financial_data': financial_data,
                    'web_intelligence': web_intelligence,
                    'risk_assessment': risk_assessment,
                    'confidence_score': smart_confidence or cached_result.get('confidence_score', 0.5)
                })
                return SupplierInfo(**cached_result)
            
            # Build enhanced prompt with all intelligence data
            context_parts = []
            
# OpenCorporates integration removed
            
            if financial_data:
                market_cap = financial_data.get('market_cap')
                revenue = financial_data.get('revenue')
                context_parts.append(f"""
                FINANCIAL DATA (Yahoo Finance):
                - Ticker: {financial_data.get('ticker', 'N/A')}
                - Market Cap: {"${:,} USD".format(market_cap) if market_cap else "N/A"}
                - Revenue: {"${:,} USD".format(revenue) if revenue else "N/A"}
                - Sector: {financial_data.get('sector', 'N/A')}
                - Industry: {financial_data.get('industry', 'N/A')}
                - Employees: {financial_data.get('employee_count', 'N/A')}
                - Financial Health: {financial_data.get('financial_health_score', 'N/A')}/100
                """)
            
            if web_intelligence:
                context_parts.append(f"""
                WEB INTELLIGENCE:
                - Certifications: {', '.join(web_intelligence.get('certifications', []))}
                - Founded: {web_intelligence.get('founded_year', 'N/A')}
                - Team Size: {web_intelligence.get('team_size_indicators', [])}
                - Social Media: {', '.join(web_intelligence.get('social_media', {}).keys())}
                - Contact Methods: {', '.join(web_intelligence.get('contact_methods', []))}
                - Tech Stack: {', '.join(web_intelligence.get('technology_stack', []))}
                """)
            
            if risk_assessment:
                context_parts.append(f"""
                RISK ASSESSMENT:
                - Domain Age: {risk_assessment.get('domain_age_years', 'N/A')} years
                - SSL Valid: {risk_assessment.get('ssl_valid', False)}
                - Performance: {risk_assessment.get('website_performance_score', 'N/A')}/100
                - Risk Score: {risk_assessment.get('risk_score', 'N/A')}/100 (lower is better)
                - Risk Factors: {', '.join(risk_assessment.get('risk_factors', []))}
                """)
            
            intelligence_context = '\n'.join(context_parts)
            
            # Try Groq first
            prompt = f"""
            Analyze this supplier with comprehensive intelligence data and provide JSON response:
            
            BASIC INFO:
            Name: {supplier_info['name']}
            Location: {supplier_info['location']}
            Description: {supplier_info['description']}
            
            {intelligence_context}
            
            Provide JSON with these fields:
            {{
                "certifications": ["list", "of", "industry", "certifications"],
                "rating": 1.0-5.0 or null,
                "enhanced_description": "Professional summary incorporating all intelligence data"
            }}
            
            Focus on professional assessment considering financial health, risk factors, and market position.
            """
            
            try:
                print(f"🤖 Enhanced analysis with Groq: {supplier_info['name']}")
                response = self.groq_client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": "You are a senior procurement analyst with access to comprehensive supplier intelligence. Respond with valid JSON only."},
                        {"role": "user", "content": prompt}
                    ],
                    model="llama3-8b-8192",
                    temperature=0.3,
                    max_tokens=800
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
            
            # Use smart confidence score or fallback to original method
            final_confidence = smart_confidence if smart_confidence is not None else 0.5
            
            # Merge certifications from web intelligence and LLM analysis
            all_certifications = set()
            if web_intelligence and web_intelligence.get('certifications'):
                all_certifications.update(web_intelligence['certifications'])
            if enhanced_data.get('certifications'):
                all_certifications.update(enhanced_data['certifications'])
            
            result = SupplierInfo(
                name=supplier_info["name"],
                location=supplier_info["location"],
                description=enhanced_data.get("enhanced_description", supplier_info["description"]),
                website=supplier_info.get("website"),
                confidence_score=final_confidence,
                certifications=list(all_certifications),
                rating=enhanced_data.get("rating"),
                logo_url=logo_url,
                financial_data=financial_data,
                web_intelligence=web_intelligence,
                risk_assessment=risk_assessment
            )
            
            # Cache the result
            llm_cache_set(cache_key, result.dict())
            
            return result
            
        except Exception as e:
            print(f"❌ Advanced enhancement failed: {e}")
            return SupplierInfo(
                name=supplier_info["name"],
                location=supplier_info["location"],
                description=supplier_info["description"],
                website=supplier_info.get("website"),
                confidence_score=smart_confidence or 0.5,
                certifications=[],
                rating=None,
                logo_url=logo_url,
                financial_data=financial_data,
                web_intelligence=web_intelligence,
                risk_assessment=risk_assessment
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