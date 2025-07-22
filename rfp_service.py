import time
import asyncio
import hashlib
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from search_service import SearchService
from llm_service import LLMService

class RFPGenerationService:
    """Service for AI-powered RFP/RFI/RFQ document generation"""
    
    def __init__(self):
        self.search_service = SearchService()
        self.llm_service = LLMService()
        self.cache = {}  # In-memory cache with TTL
        self.cache_ttl = 2 * 60 * 60  # 2 hours in seconds
        
        # RFP templates and sections
        self.document_templates = {
            "RFP": {
                "sections": [
                    "executive_summary",
                    "project_background", 
                    "scope_of_work",
                    "technical_requirements",
                    "evaluation_criteria",
                    "timeline_milestones",
                    "submission_guidelines",
                    "terms_conditions"
                ]
            },
            "RFI": {
                "sections": [
                    "project_overview",
                    "information_required",
                    "vendor_qualifications",
                    "response_format",
                    "timeline",
                    "contact_information"
                ]
            },
            "RFQ": {
                "sections": [
                    "product_description",
                    "specifications",
                    "quantity_requirements",
                    "delivery_requirements",
                    "pricing_format",
                    "terms_payment"
                ]
            }
        }
    
    def _generate_cache_key(self, project_title: str, doc_type: str) -> str:
        """Generate consistent cache key for RFP generation"""
        cache_data = f"{doc_type.lower()}_{project_title.lower()}_{time.strftime('%Y-%m-%d')}"
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
    
    async def generate_document(self, request) -> Dict[str, Any]:
        """
        Generate RFP/RFI/RFQ document using AI
        """
        start_time = time.time()
        
        try:
            print(f"🚀 Starting {request.document_type} generation for: {request.project_title}")
            
            # Check cache first
            cache_key = self._generate_cache_key(request.project_title, request.document_type)
            if self._is_cache_valid(cache_key):
                print(f"📦 Using cached RFP data for: {request.project_title}")
                cached_data = self.cache[cache_key]['data']
                cached_data['processing_time'] = time.time() - start_time
                return cached_data
            
            # Step 1: Analyze project requirements
            requirements_analysis = await self._analyze_requirements(request)
            
            # Step 2: Research industry standards and benchmarks
            industry_data = await self._research_industry_standards(request)
            
            # Step 3: Generate document sections
            document_sections = await self._generate_sections(request, requirements_analysis, industry_data)
            
            # Step 4: Create final document
            final_document = await self._assemble_final_document(request, document_sections)
            
            result = {
                "document_type": request.document_type,
                "project_title": request.project_title,
                "requirements_analysis": requirements_analysis,
                "industry_benchmarks": industry_data,
                "sections": document_sections,
                "final_document": final_document,
                "generation_metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "sections_count": len(document_sections),
                    "document_length": len(final_document),
                    "complexity_score": self._calculate_complexity_score(request)
                },
                "processing_time": time.time() - start_time
            }
            
            # Cache results
            self._cache_results(cache_key, result)
            
            print(f"✅ {request.document_type} generation completed in {result['processing_time']:.2f}s")
            return result
            
        except Exception as e:
            print(f"❌ RFP generation failed: {e}")
            return await self._generate_fallback_document(request, time.time() - start_time)
    
    async def _analyze_requirements(self, request) -> Dict[str, Any]:
        """Step 1: Analyze project requirements using LLM"""
        
        analysis_prompt = f"""
        You are a procurement specialist analyzing a {request.document_type} request. 
        
        PROJECT DETAILS:
        Title: {request.project_title}
        Description: {request.description}
        Requirements: {request.requirements}
        Budget Range: {request.budget_range or 'Not specified'}
        Timeline: {request.timeline or 'Not specified'}
        Industry: {request.industry or 'General'}
        Company Size: {request.company_size or 'Not specified'}
        
        Provide a comprehensive analysis in JSON format with these keys:
        {{
            "complexity_level": "<Simple|Medium|Complex|Enterprise>",
            "project_category": "<IT|Construction|Professional Services|Manufacturing|Other>",
            "key_challenges": ["challenge1", "challenge2", "challenge3"],
            "critical_requirements": ["req1", "req2", "req3"],
            "recommended_sections": ["section1", "section2"],
            "compliance_considerations": ["compliance1", "compliance2"],
            "evaluation_factors": [
                {{"factor": "Technical Capability", "weight": "30%"}},
                {{"factor": "Cost", "weight": "25%"}},
                {{"factor": "Timeline", "weight": "20%"}},
                {{"factor": "Experience", "weight": "25%"}}
            ],
            "risk_factors": ["risk1", "risk2"],
            "success_criteria": ["criteria1", "criteria2"]
        }}
        
        Focus on practical procurement considerations and industry best practices.
        """
        
        try:
            print("🔍 Analyzing project requirements...")
            analysis = await self.llm_service.analyze_market_data(analysis_prompt)
            return analysis
            
        except Exception as e:
            print(f"❌ Requirements analysis failed: {e}")
            return self._generate_fallback_analysis(request)
    
    async def _research_industry_standards(self, request) -> Dict[str, Any]:
        """Step 2: Research industry standards and benchmarks"""
        
        # Search for industry-specific RFP standards
        search_queries = [
            f"{request.document_type} {request.industry or 'best practices'} template standards",
            f"{request.project_title} procurement requirements industry standards",
            f"{request.document_type} evaluation criteria {request.industry or 'general'}"
        ]
        
        industry_data = []
        
        for query in search_queries[:2]:  # Limit to 2 searches
            try:
                print(f"🔍 Researching industry standards: {query}")
                results = await self.search_service.search_suppliers(query, max_results=5)
                
                for result in results:
                    industry_data.append({
                        'title': result.get('title', ''),
                        'content': result.get('snippet', ''),
                        'source': result.get('source', ''),
                        'relevance': 'High' if request.industry and request.industry.lower() in result.get('title', '').lower() else 'Medium'
                    })
                
                await asyncio.sleep(1)  # Rate limiting
                
            except Exception as e:
                print(f"❌ Industry research failed for query '{query}': {e}")
                continue
        
        # Analyze industry data with LLM
        if industry_data:
            industry_analysis_prompt = f"""
            Based on the following industry research data, provide insights for creating a {request.document_type}:
            
            Industry Data:
            {json.dumps(industry_data[:8], indent=2)}
            
            Project Context: {request.project_title} in {request.industry or 'general'} industry
            
            Provide JSON response with:
            {{
                "industry_standards": ["standard1", "standard2", "standard3"],
                "typical_timeline": "timeframe",
                "budget_benchmarks": "typical range or considerations",
                "common_evaluation_criteria": ["criteria1", "criteria2"],
                "compliance_requirements": ["req1", "req2"],
                "best_practices": ["practice1", "practice2"],
                "market_trends": ["trend1", "trend2"]
            }}
            """
            
            try:
                print("📊 Analyzing industry standards...")
                analysis = await self.llm_service.analyze_market_data(industry_analysis_prompt)
                return analysis
                
            except Exception as e:
                print(f"❌ Industry analysis failed: {e}")
                
        return self._generate_fallback_industry_data(request)
    
    async def _generate_sections(self, request, requirements_analysis: Dict, industry_data: Dict) -> Dict[str, str]:
        """Step 3: Generate individual document sections"""
        
        sections = {}
        template = self.document_templates.get(request.document_type, self.document_templates["RFP"])
        
        for section_name in template["sections"]:
            try:
                print(f"📝 Generating section: {section_name}")
                
                section_prompt = self._build_section_prompt(
                    request, section_name, requirements_analysis, industry_data
                )
                
                section_content = await self.llm_service.analyze_market_data(section_prompt)
                
                # Extract content from LLM response (handle various formats)
                if isinstance(section_content, dict):
                    if 'content' in section_content:
                        sections[section_name] = section_content['content']
                    else:
                        # Convert dict to readable text
                        sections[section_name] = self._dict_to_readable_text(section_content)
                elif isinstance(section_content, str):
                    sections[section_name] = section_content
                else:
                    sections[section_name] = str(section_content)
                
                await asyncio.sleep(0.5)  # Rate limiting between sections
                
            except Exception as e:
                print(f"❌ Section generation failed for {section_name}: {e}")
                sections[section_name] = self._generate_fallback_section(section_name, request)
        
        return sections
    
    def _build_section_prompt(self, request, section_name: str, requirements_analysis: Dict, industry_data: Dict) -> str:
        """Build section-specific prompts for LLM"""
        
        base_context = f"""
        Project: {request.project_title}
        Description: {request.description}
        Document Type: {request.document_type}
        Industry: {request.industry or 'General'}
        Requirements: {request.requirements}
        Budget: {request.budget_range or 'Not specified'}
        Timeline: {request.timeline or 'To be determined'}
        Complexity: {requirements_analysis.get('complexity_level', 'Medium')}
        """
        
        section_prompts = {
            "executive_summary": f"""
            Write a professional executive summary for this {request.document_type}.
            
            {base_context}
            
            The executive summary should include:
            - Project overview and objectives
            - Scope and expected outcomes
            - Key requirements summary
            - Selection criteria overview
            - Timeline and next steps
            
            Keep it concise (2-3 paragraphs) but comprehensive. Use professional procurement language.
            """,
            
            "project_background": f"""
            Write a detailed project background section for this {request.document_type}.
            
            {base_context}
            
            Include:
            - Business context and drivers
            - Current situation and challenges
            - Project objectives and success criteria
            - Strategic importance
            - Stakeholder impact
            
            Be specific and provide context that helps vendors understand the project's importance.
            """,
            
            "scope_of_work": f"""
            Define the detailed scope of work for this {request.document_type}.
            
            {base_context}
            
            Requirements Analysis: {requirements_analysis.get('critical_requirements', [])}
            
            Structure the scope as:
            1. Primary deliverables
            2. Secondary deliverables
            3. Out of scope items
            4. Dependencies and assumptions
            5. Success metrics
            
            Be specific and measurable in your descriptions.
            """,
            
            "technical_requirements": f"""
            List detailed technical requirements for this {request.document_type}.
            
            {base_context}
            
            Key Requirements: {request.requirements}
            Industry Standards: {industry_data.get('industry_standards', [])}
            
            Organize as:
            - Functional requirements
            - Technical specifications
            - Performance requirements
            - Security and compliance requirements
            - Integration requirements
            - Support and maintenance requirements
            
            Use measurable criteria where possible.
            """,
            
            "evaluation_criteria": f"""
            Define comprehensive evaluation criteria for vendor selection.
            
            {base_context}
            
            Recommended Factors: {requirements_analysis.get('evaluation_factors', [])}
            
            Structure as:
            1. Technical evaluation (with weights)
            2. Commercial evaluation (with weights)
            3. Vendor qualifications (with weights)
            4. Risk assessment criteria
            5. Scoring methodology
            
            Provide specific weights and scoring methods.
            """,
            
            "timeline_milestones": f"""
            Create a detailed project timeline with key milestones.
            
            {base_context}
            
            Target Timeline: {request.timeline or 'To be determined'}
            Industry Typical Timeline: {industry_data.get('typical_timeline', 'Standard')}
            
            Include:
            - RFP response deadline
            - Evaluation phases
            - Vendor presentations/demos
            - Contract negotiation
            - Project kickoff
            - Key project milestones
            - Go-live date
            
            Be realistic and allow adequate time for each phase.
            """,
            
            "submission_guidelines": f"""
            Provide clear submission guidelines for vendors responding to this {request.document_type}.
            
            Include:
            - Submission format and structure
            - Required documents and certifications
            - Page limits and formatting requirements
            - Submission deadline and method
            - Contact information for questions
            - Evaluation process overview
            - Next steps after submission
            
            Be specific and clear to ensure consistent responses.
            """
        }
        
        # Default prompt for any missing sections
        default_prompt = f"""
        Write professional content for the "{section_name}" section of this {request.document_type}.
        
        {base_context}
        
        Follow procurement best practices and industry standards. Be specific, professional, and comprehensive.
        """
        
        return section_prompts.get(section_name, default_prompt)
    
    async def _assemble_final_document(self, request, sections: Dict[str, str]) -> str:
        """Step 4: Assemble final document with formatting"""
        
        # Document header
        document_title = f"{request.document_type}: {request.project_title}"
        current_date = datetime.now().strftime("%B %d, %Y")
        
        final_document = f"""# {document_title}

**Document Type:** {request.document_type} - {self._get_document_full_name(request.document_type)}
**Project:** {request.project_title}
**Date:** {current_date}
**Industry:** {request.industry or 'General'}

---

"""
        
        # Add sections in logical order
        section_order = self.document_templates.get(request.document_type, self.document_templates["RFP"])["sections"]
        
        for section_name in section_order:
            if section_name in sections and sections[section_name].strip():
                section_title = self._format_section_title(section_name)
                final_document += f"## {section_title}\n\n{sections[section_name]}\n\n---\n\n"
        
        # Document footer
        final_document += f"""
**Document Information:**
- Generated: {current_date}
- Document ID: {request.document_type}-{int(time.time())}
- Total Sections: {len([s for s in sections.values() if s.strip()])}

*This document was generated using AI-powered procurement intelligence.*
"""
        
        return final_document
    
    def _get_document_full_name(self, doc_type: str) -> str:
        """Get full document type name"""
        names = {
            "RFP": "Request for Proposal",
            "RFI": "Request for Information", 
            "RFQ": "Request for Quote"
        }
        return names.get(doc_type, doc_type)
    
    def _format_section_title(self, section_name: str) -> str:
        """Format section name for display"""
        return section_name.replace('_', ' ').title()
    
    def _calculate_complexity_score(self, request) -> float:
        """Calculate project complexity score"""
        score = 0.5  # Base score
        
        # Adjust based on requirements count
        if hasattr(request, 'requirements') and request.requirements:
            req_count = len(request.requirements)
            if req_count > 10:
                score += 0.3
            elif req_count > 5:
                score += 0.2
            else:
                score += 0.1
        
        # Adjust based on description length
        if hasattr(request, 'description') and request.description:
            if len(request.description) > 500:
                score += 0.2
            elif len(request.description) > 200:
                score += 0.1
        
        return min(score, 1.0)
    
    def _generate_fallback_analysis(self, request) -> Dict[str, Any]:
        """Generate fallback analysis when LLM fails"""
        return {
            "complexity_level": "Medium",
            "project_category": "General",
            "key_challenges": ["Vendor selection", "Timeline management", "Quality assurance"],
            "critical_requirements": request.requirements[:3] if hasattr(request, 'requirements') else [],
            "recommended_sections": ["Technical Requirements", "Evaluation Criteria", "Timeline"],
            "compliance_considerations": ["Data security", "Contract terms"],
            "evaluation_factors": [
                {"factor": "Technical Capability", "weight": "30%"},
                {"factor": "Cost", "weight": "30%"},
                {"factor": "Experience", "weight": "25%"},
                {"factor": "Timeline", "weight": "15%"}
            ],
            "risk_factors": ["Delivery delays", "Budget overruns"],
            "success_criteria": ["On-time delivery", "Quality standards met"]
        }
    
    def _generate_fallback_industry_data(self, request) -> Dict[str, Any]:
        """Generate fallback industry data when research fails"""
        return {
            "industry_standards": ["Industry best practices", "Quality standards", "Compliance requirements"],
            "typical_timeline": "3-6 months",
            "budget_benchmarks": "Varies by scope and complexity",
            "common_evaluation_criteria": ["Technical capability", "Cost", "Timeline", "Experience"],
            "compliance_requirements": ["Standard compliance", "Security requirements"],
            "best_practices": ["Clear requirements definition", "Comprehensive evaluation", "Risk assessment"],
            "market_trends": ["Digital transformation", "Vendor consolidation"]
        }
    
    def _generate_fallback_section(self, section_name: str, request) -> str:
        """Generate fallback section content"""
        fallback_sections = {
            "executive_summary": f"""
This {request.document_type} outlines the requirements for {request.project_title}. 
We are seeking qualified vendors to provide comprehensive solutions that meet our 
technical and business requirements within the specified timeline and budget.
            """,
            "project_background": f"""
Our organization is undertaking {request.project_title} to enhance our capabilities 
and achieve strategic objectives. This project represents a significant initiative 
that requires expert vendor partnership and proven solutions.
            """,
            "scope_of_work": f"""
The selected vendor will be responsible for delivering a complete solution for 
{request.project_title} including all necessary components, implementation, 
and support services as outlined in the requirements.
            """
        }
        
        return fallback_sections.get(
            section_name, 
            f"Content for {section_name.replace('_', ' ').title()} section will be provided based on project requirements."
        ).strip()
    
    async def _generate_fallback_document(self, request, processing_time: float) -> Dict[str, Any]:
        """Generate fallback document when generation fails"""
        
        print("🆘 Generating fallback RFP document")
        
        fallback_sections = {
            "executive_summary": self._generate_fallback_section("executive_summary", request),
            "project_background": self._generate_fallback_section("project_background", request),  
            "scope_of_work": self._generate_fallback_section("scope_of_work", request)
        }
        
        fallback_document = f"""# {request.document_type}: {request.project_title}

## Executive Summary
{fallback_sections['executive_summary']}

## Project Background  
{fallback_sections['project_background']}

## Scope of Work
{fallback_sections['scope_of_work']}

---
*Document generation completed with limited data. Please review and enhance as needed.*
"""
        
        return {
            "document_type": request.document_type,
            "project_title": request.project_title,
            "requirements_analysis": self._generate_fallback_analysis(request),
            "industry_benchmarks": self._generate_fallback_industry_data(request),
            "sections": fallback_sections,
            "final_document": fallback_document,
            "generation_metadata": {
                "generated_at": datetime.now().isoformat(),
                "sections_count": len(fallback_sections),
                "document_length": len(fallback_document),
                "complexity_score": 0.5,
                "fallback_mode": True
            },
            "processing_time": processing_time
        }

    async def get_document_templates(self) -> Dict[str, Any]:
        """Get available document templates and their descriptions"""
        return {
            "templates": {
                "RFP": {
                    "name": "Request for Proposal",
                    "description": "Comprehensive document for complex procurement projects requiring detailed proposals",
                    "typical_use": "Software development, construction projects, professional services",
                    "sections": len(self.document_templates["RFP"]["sections"]),
                    "complexity": "High"
                },
                "RFI": {
                    "name": "Request for Information",
                    "description": "Information gathering document for market research and vendor capabilities",
                    "typical_use": "Market research, vendor capability assessment, feasibility studies",
                    "sections": len(self.document_templates["RFI"]["sections"]),
                    "complexity": "Medium"
                },
                "RFQ": {
                    "name": "Request for Quote", 
                    "description": "Price-focused document for straightforward product or service purchases",
                    "typical_use": "Product purchases, standard services, equipment procurement",
                    "sections": len(self.document_templates["RFQ"]["sections"]),
                    "complexity": "Low"
                }
            }
        }
    
    def _dict_to_readable_text(self, data: dict) -> str:
        """Convert dictionary data to readable text format"""
        if not isinstance(data, dict):
            return str(data)
        
        readable_parts = []
        for key, value in data.items():
            if isinstance(value, list):
                list_items = '\n'.join([f"• {item}" for item in value])
                readable_parts.append(f"{key.replace('_', ' ').title()}:\n{list_items}")
            elif isinstance(value, dict):
                nested_text = self._dict_to_readable_text(value)
                readable_parts.append(f"{key.replace('_', ' ').title()}:\n{nested_text}")
            else:
                readable_parts.append(f"{key.replace('_', ' ').title()}: {value}")
        
        return '\n\n'.join(readable_parts)