from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage
import json
import time
import re
from search_service import SearchService
from llm_service import LLMService

class ProcurementState(TypedDict):
    """State for the procurement agent workflow"""
    query: str
    location: str
    category: str
    search_results: List[Dict[str, Any]]
    suppliers: List[Dict[str, Any]]
    market_insights: Dict[str, Any]
    summary: str
    processing_time: float
    error: str

class ProcurementAgent:
    """LangGraph agent for procurement intelligence workflow"""
    
    def __init__(self):
        self.search_service = SearchService()
        self.llm_service = LLMService()
        self.graph = self._create_graph()
    
    def _create_graph(self):
        """Create the LangGraph workflow"""
        workflow = StateGraph(ProcurementState)
        
        # Add nodes
        workflow.add_node("search_suppliers", self._search_suppliers)
        workflow.add_node("analyze_suppliers", self._analyze_suppliers)
        workflow.add_node("generate_market_insights", self._generate_market_insights)
        workflow.add_node("create_summary", self._create_summary)
        
        # Add edges
        workflow.set_entry_point("search_suppliers")
        workflow.add_edge("search_suppliers", "analyze_suppliers")
        workflow.add_edge("analyze_suppliers", "generate_market_insights")
        workflow.add_edge("generate_market_insights", "create_summary")
        workflow.add_edge("create_summary", END)
        
        return workflow.compile()
    
    async def _search_suppliers(self, state: ProcurementState) -> ProcurementState:
        """Search for suppliers using DuckDuckGo"""
        try:
            print(f"🔍 Searching for suppliers: {state['query']}")
            
            search_results = await self.search_service.search_suppliers(
                state["query"], 
                state.get("location"), 
                max_results=10
            )
            
            state["search_results"] = search_results
            print(f"✅ Found {len(search_results)} search results")
            
        except Exception as e:
            print(f"❌ Search failed: {e}")
            state["error"] = f"Search failed: {str(e)}"
            state["search_results"] = []
        
        return state
    
    async def _analyze_suppliers(self, state: ProcurementState) -> ProcurementState:
        """Analyze search results to extract supplier information"""
        try:
            print("🤖 Analyzing suppliers with LLM...")
            
            if not state["search_results"]:
                state["suppliers"] = []
                return state
            
            suppliers = await self.llm_service.analyze_suppliers(state["search_results"])
            
            # Convert to dict for JSON serialization
            state["suppliers"] = [supplier.dict() for supplier in suppliers]
            print(f"✅ Analyzed {len(suppliers)} suppliers")
            
        except Exception as e:
            print(f"❌ Supplier analysis failed: {e}")
            state["error"] = f"Supplier analysis failed: {str(e)}"
            state["suppliers"] = []
        
        return state
    
    async def _generate_market_insights(self, state: ProcurementState) -> ProcurementState:
        """Generate market insights based on query and suppliers"""
        try:
            print("📊 Generating market insights...")
            
            # Create mock supplier info objects for the LLM service
            from main import SupplierInfo
            suppliers = [SupplierInfo(**supplier) for supplier in state["suppliers"]]
            
            market_insights = await self.llm_service.generate_market_insights(
                state["query"], 
                suppliers
            )
            
            state["market_insights"] = market_insights.dict()
            print("✅ Market insights generated")
            
        except Exception as e:
            print(f"❌ Market insights failed: {e}")
            state["error"] = f"Market insights failed: {str(e)}"
            state["market_insights"] = {
                "price_trend": "stable",
                "key_factors": ["Limited data available"],
                "recommendations": ["Conduct further research"]
            }
        
        return state
    
    async def _create_summary(self, state: ProcurementState) -> ProcurementState:
        """Create executive summary of the analysis"""
        try:
            print("📝 Creating executive summary...")
            
            supplier_count = len(state["suppliers"])
            location_text = f" in {state['location']}" if state.get("location") else ""
            trend = state["market_insights"]["price_trend"]
            
            summary = f"Found {supplier_count} suppliers for '{state['query']}'{location_text}. " \
                     f"Market trend: {trend}. "
            
            if supplier_count > 0:
                high_confidence = sum(1 for s in state["suppliers"] if s["confidence_score"] >= 0.8)
                if high_confidence > 0:
                    summary += f"{high_confidence} high-confidence suppliers identified. "
            
            summary += "Analysis complete."
            
            state["summary"] = summary
            print("✅ Summary created")
            
        except Exception as e:
            print(f"❌ Summary creation failed: {e}")
            state["summary"] = "Analysis completed with limited data."
        
        return state
    
    async def run_analysis(self, query: str, location: str = None, category: str = None) -> Dict[str, Any]:
        """Run the complete procurement analysis workflow"""
        start_time = time.time()
        
        initial_state = ProcurementState(
            query=query,
            location=location or "",
            category=category or "",
            search_results=[],
            suppliers=[],
            market_insights={},
            summary="",
            processing_time=0.0,
            error=""
        )
        
        try:
            # Run the graph
            print("🚀 Starting procurement analysis workflow...")
            final_state = await self.graph.ainvoke(initial_state)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            final_state["processing_time"] = processing_time
            
            print(f"🎉 Analysis complete in {processing_time:.2f}s")
            
            return final_state
            
        except Exception as e:
            print(f"❌ Workflow failed: {e}")
            return {
                "query": query,
                "location": location or "",
                "category": category or "",
                "search_results": [],
                "suppliers": [],
                "market_insights": {
                    "price_trend": "stable",
                    "key_factors": ["Analysis failed"],
                    "recommendations": ["Try again later"]
                },
                "summary": f"Analysis failed: {str(e)}",
                "processing_time": time.time() - start_time,
                "error": str(e)
            }

# Global agent instance
procurement_agent = ProcurementAgent()