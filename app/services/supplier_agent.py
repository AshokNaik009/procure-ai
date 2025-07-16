import asyncio
import logging
from typing import List, Dict, Any, Optional
import time
from app.services.search_service import SearchService
from app.services.llm_service import LLMService
from app.models.requests import SupplierDiscoveryRequest
from app.models.responses import SupplierInfo, SupplierDiscoveryResponse
from app.config import settings
import re
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class SupplierAgent:
    def __init__(self):
        self.search_service = SearchService()
        self.llm_service = LLMService()
        
    async def discover_suppliers(self, request: SupplierDiscoveryRequest) -> SupplierDiscoveryResponse:
        """
        Main supplier discovery orchestration
        """
        start_time = time.time()
        
        try:
            logger.info(f"Starting supplier discovery for: {request.product}")
            
            # Stage 1: Search for suppliers
            search_results = await self.search_service.search_suppliers(
                query=request.product,
                location=request.location,
                max_results=request.max_results * 2  # Get more results for filtering
            )
            
            if not search_results:
                logger.warning(f"No search results found for: {request.product}")
                return SupplierDiscoveryResponse(
                    suppliers=[],
                    total_found=0,
                    search_query=request.product,
                    location_filter=request.location,
                    processing_time=time.time() - start_time,
                    data_sources=[]
                )
            
            # Stage 2: Extract supplier information from search results
            supplier_candidates = await self._extract_supplier_info(search_results, request)
            
            # Stage 3: Verify and enrich supplier data using LLM
            verified_suppliers = await self._verify_suppliers(supplier_candidates, request)
            
            # Stage 4: Apply filters and ranking
            filtered_suppliers = self._apply_filters(verified_suppliers, request)
            
            # Stage 5: Final ranking and selection
            ranked_suppliers = self._rank_suppliers(filtered_suppliers, request)
            
            processing_time = time.time() - start_time
            
            logger.info(f"Supplier discovery completed in {processing_time:.2f}s, found {len(ranked_suppliers)} suppliers")
            
            return SupplierDiscoveryResponse(
                suppliers=ranked_suppliers[:request.max_results],
                total_found=len(ranked_suppliers),
                search_query=request.product,
                location_filter=request.location,
                processing_time=processing_time,
                data_sources=list(set([result.source for result in search_results]))
            )
            
        except Exception as e:
            logger.error(f"Supplier discovery failed: {e}")
            return SupplierDiscoveryResponse(
                suppliers=[],
                total_found=0,
                search_query=request.product,
                location_filter=request.location,
                processing_time=time.time() - start_time,
                data_sources=[]
            )
    
    async def _extract_supplier_info(self, search_results, request: SupplierDiscoveryRequest) -> List[Dict[str, Any]]:
        """
        Extract supplier information from search results
        """
        supplier_candidates = []
        
        for result in search_results:
            try:
                supplier_info = {
                    'name': self._extract_company_name(result.title),
                    'website': result.url,
                    'location': self._extract_location(result.snippet, request.location),
                    'description': result.snippet,
                    'source_title': result.title,
                    'source_snippet': result.snippet,
                    'domain': urlparse(result.url).netloc,
                    'search_relevance': result.relevance_score
                }
                
                # Basic validation
                if supplier_info['name'] and len(supplier_info['name']) > 2:
                    supplier_candidates.append(supplier_info)
                    
            except Exception as e:
                logger.warning(f"Failed to extract supplier info from result: {e}")
                continue
        
        return supplier_candidates
    
    async def _verify_suppliers(self, supplier_candidates: List[Dict[str, Any]], request: SupplierDiscoveryRequest) -> List[SupplierInfo]:
        """
        Verify supplier data using LLM service
        """
        verified_suppliers = []
        
        # Process suppliers in batches to avoid rate limits
        batch_size = 5
        for i in range(0, len(supplier_candidates), batch_size):
            batch = supplier_candidates[i:i+batch_size]
            
            tasks = []
            for supplier_data in batch:
                context = f"Product: {request.product}, Requirements: {request.requirements}"
                task = self.llm_service.verify_supplier_data(supplier_data, context)
                tasks.append(task)
            
            # Process batch concurrently
            try:
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for result in batch_results:
                    if isinstance(result, Exception):
                        logger.error(f"Supplier verification failed: {result}")
                        continue
                    
                    if isinstance(result, SupplierInfo):
                        verified_suppliers.append(result)
                        
            except Exception as e:
                logger.error(f"Batch processing failed: {e}")
                continue
            
            # Rate limiting between batches
            await asyncio.sleep(0.5)
        
        return verified_suppliers
    
    def _apply_filters(self, suppliers: List[SupplierInfo], request: SupplierDiscoveryRequest) -> List[SupplierInfo]:
        """
        Apply filters based on request criteria
        """
        filtered_suppliers = []
        
        for supplier in suppliers:
            # Location filter
            if request.location and supplier.location:
                if not self._location_matches(supplier.location, request.location):
                    continue
            
            # Rating filter
            if request.min_rating and supplier.rating:
                if supplier.rating < request.min_rating:
                    continue
            
            # Certification filter
            if request.certifications:
                if not any(cert.lower() in [c.lower() for c in supplier.certifications] 
                          for cert in request.certifications):
                    continue
            
            # Requirements filter
            if request.requirements:
                if not self._meets_requirements(supplier, request.requirements):
                    continue
            
            filtered_suppliers.append(supplier)
        
        return filtered_suppliers
    
    def _rank_suppliers(self, suppliers: List[SupplierInfo], request: SupplierDiscoveryRequest) -> List[SupplierInfo]:
        """
        Rank suppliers based on multiple criteria
        """
        def calculate_score(supplier: SupplierInfo) -> float:
            score = 0.0
            
            # Base confidence score (40% weight)
            score += supplier.confidence_score * 0.4
            
            # Verification status (20% weight)
            verification_weights = {
                'verified': 1.0,
                'unverified': 0.5,
                'pending': 0.3,
                'failed': 0.0
            }
            score += verification_weights.get(supplier.verification_status.value, 0.0) * 0.2
            
            # Rating (15% weight)
            if supplier.rating:
                score += (supplier.rating / 5.0) * 0.15
            
            # Certifications (10% weight)
            if supplier.certifications:
                cert_score = min(len(supplier.certifications) / 5.0, 1.0)
                score += cert_score * 0.1
            
            # Location relevance (10% weight)
            if request.location and supplier.location:
                if self._location_matches(supplier.location, request.location):
                    score += 0.1
            
            # Specialties relevance (5% weight)
            if supplier.specialties:
                specialty_relevance = self._calculate_specialty_relevance(
                    supplier.specialties, request.product
                )
                score += specialty_relevance * 0.05
            
            return min(score, 1.0)
        
        # Calculate scores and sort
        for supplier in suppliers:
            supplier.confidence_score = calculate_score(supplier)
        
        return sorted(suppliers, key=lambda s: s.confidence_score, reverse=True)
    
    def _extract_company_name(self, title: str) -> str:
        """
        Extract company name from search result title
        """
        try:
            # Remove common prefixes and suffixes
            title = re.sub(r'^\d+\.\s*', '', title)  # Remove numbered lists
            title = re.sub(r'\s*-\s*.*$', '', title)  # Remove descriptions after dash
            title = re.sub(r'\s*\|\s*.*$', '', title)  # Remove descriptions after pipe
            
            # Extract potential company name
            company_patterns = [
                r'([A-Z][a-zA-Z0-9\s&.,]+(?:Inc|LLC|Ltd|Corp|Company|Co\.|Corporation))',
                r'([A-Z][a-zA-Z0-9\s&.,]{2,30})',
                r'^([^-|]+)',
            ]
            
            for pattern in company_patterns:
                match = re.search(pattern, title)
                if match:
                    company_name = match.group(1).strip()
                    if len(company_name) > 2:
                        return company_name
            
            return title.strip()
            
        except Exception as e:
            logger.warning(f"Failed to extract company name from '{title}': {e}")
            return title.strip()
    
    def _extract_location(self, snippet: str, preferred_location: Optional[str] = None) -> str:
        """
        Extract location information from snippet
        """
        try:
            # Common location patterns
            location_patterns = [
                r'(?:located|based|headquarters|office)\s+(?:in|at)\s+([A-Z][a-zA-Z\s,]+)',
                r'([A-Z][a-zA-Z\s]+,\s*[A-Z]{2})',  # City, State
                r'([A-Z][a-zA-Z\s]+,\s*[A-Z][a-zA-Z\s]+)',  # City, Country
            ]
            
            for pattern in location_patterns:
                matches = re.findall(pattern, snippet)
                if matches:
                    location = matches[0].strip()
                    if len(location) > 2:
                        return location
            
            # If preferred location is provided, check if it's mentioned
            if preferred_location:
                if preferred_location.lower() in snippet.lower():
                    return preferred_location
            
            return "Location not specified"
            
        except Exception as e:
            logger.warning(f"Failed to extract location: {e}")
            return "Location not specified"
    
    def _location_matches(self, supplier_location: str, requested_location: str) -> bool:
        """
        Check if supplier location matches requested location
        """
        try:
            supplier_lower = supplier_location.lower()
            requested_lower = requested_location.lower()
            
            # Exact match
            if requested_lower in supplier_lower:
                return True
            
            # State/country abbreviations
            state_abbrev = {
                'california': 'ca', 'texas': 'tx', 'new york': 'ny',
                'florida': 'fl', 'illinois': 'il', 'pennsylvania': 'pa'
            }
            
            for full_name, abbrev in state_abbrev.items():
                if (full_name in requested_lower and abbrev in supplier_lower) or \
                   (abbrev in requested_lower and full_name in supplier_lower):
                    return True
            
            return False
            
        except Exception as e:
            logger.warning(f"Location matching failed: {e}")
            return False
    
    def _meets_requirements(self, supplier: SupplierInfo, requirements: List[str]) -> bool:
        """
        Check if supplier meets specified requirements
        """
        try:
            searchable_text = f"{supplier.description} {' '.join(supplier.specialties)} {' '.join(supplier.certifications)}".lower()
            
            matches = 0
            for requirement in requirements:
                if requirement.lower() in searchable_text:
                    matches += 1
            
            # Require at least 50% of requirements to be met
            return matches >= len(requirements) * 0.5
            
        except Exception as e:
            logger.warning(f"Requirements checking failed: {e}")
            return True  # Default to True if checking fails
    
    def _calculate_specialty_relevance(self, specialties: List[str], product: str) -> float:
        """
        Calculate relevance of specialties to the requested product
        """
        try:
            product_words = set(product.lower().split())
            specialty_words = set(' '.join(specialties).lower().split())
            
            overlap = len(product_words.intersection(specialty_words))
            total_words = len(product_words)
            
            return overlap / total_words if total_words > 0 else 0.0
            
        except Exception as e:
            logger.warning(f"Specialty relevance calculation failed: {e}")
            return 0.0