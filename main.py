import os
import time
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from agent_graph import procurement_agent

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="Procurement Intelligence System", version="1.0.0")

# Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GROQ_API_KEY or not GEMINI_API_KEY:
    raise ValueError("Missing required API keys. Please set GROQ_API_KEY and GEMINI_API_KEY in .env file")

# Pydantic models
class ProcurementRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=200)
    location: Optional[str] = None
    category: Optional[str] = None

class SupplierInfo(BaseModel):
    name: str
    location: str
    description: str
    website: Optional[str] = None
    confidence_score: float
    certifications: List[str] = []
    rating: Optional[float] = None

class MarketInsight(BaseModel):
    price_trend: str
    key_factors: List[str]
    recommendations: List[str]

class ProcurementResponse(BaseModel):
    suppliers: List[SupplierInfo]
    market_insights: MarketInsight
    summary: str
    processing_time: float

# Routes
@app.get("/", response_class=HTMLResponse)
async def get_dashboard():
    """Serve the main dashboard"""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Procurement Intelligence System</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }
            
            .container {
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                border-radius: 20px;
                padding: 30px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            }
            
            .header {
                text-align: center;
                margin-bottom: 40px;
            }
            
            .header h1 {
                color: #2c3e50;
                font-size: 2.5em;
                margin-bottom: 10px;
            }
            
            .header p {
                color: #7f8c8d;
                font-size: 1.2em;
            }
            
            .badge {
                display: inline-block;
                background: #667eea;
                color: white;
                padding: 4px 12px;
                border-radius: 20px;
                font-size: 0.9em;
                margin: 5px;
            }
            
            .form-container {
                background: #f8f9fa;
                padding: 30px;
                border-radius: 15px;
                margin-bottom: 30px;
            }
            
            .form-group {
                margin-bottom: 20px;
            }
            
            label {
                display: block;
                margin-bottom: 8px;
                font-weight: 600;
                color: #2c3e50;
            }
            
            input, select {
                width: 100%;
                padding: 12px;
                border: 2px solid #e1e8ed;
                border-radius: 8px;
                font-size: 16px;
                transition: border-color 0.3s ease;
            }
            
            input:focus, select:focus {
                outline: none;
                border-color: #667eea;
            }
            
            .btn {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 15px 30px;
                border: none;
                border-radius: 8px;
                font-size: 18px;
                font-weight: 600;
                cursor: pointer;
                transition: transform 0.2s ease;
                width: 100%;
            }
            
            .btn:hover {
                transform: translateY(-2px);
            }
            
            .btn:disabled {
                opacity: 0.6;
                cursor: not-allowed;
                transform: none;
            }
            
            .loading {
                text-align: center;
                padding: 40px;
                display: none;
            }
            
            .spinner {
                border: 4px solid #f3f3f3;
                border-top: 4px solid #667eea;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                animation: spin 1s linear infinite;
                margin: 0 auto 20px;
            }
            
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            
            .workflow-status {
                background: #e8f4f8;
                padding: 20px;
                border-radius: 10px;
                margin-bottom: 20px;
                display: none;
            }
            
            .workflow-step {
                padding: 10px;
                margin: 5px 0;
                border-radius: 5px;
                background: white;
                border-left: 4px solid #667eea;
            }
            
            .workflow-step.active {
                background: #fff3cd;
                border-left-color: #ffc107;
            }
            
            .workflow-step.completed {
                background: #d4edda;
                border-left-color: #28a745;
            }
            
            .results {
                display: none;
            }
            
            .summary {
                background: #e8f5e8;
                padding: 20px;
                border-radius: 10px;
                margin-bottom: 30px;
                border-left: 4px solid #28a745;
            }
            
            .suppliers-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }
            
            .supplier-card {
                background: white;
                border: 1px solid #e1e8ed;
                border-radius: 10px;
                padding: 20px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.05);
                transition: transform 0.2s ease;
            }
            
            .supplier-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 5px 20px rgba(0,0,0,0.1);
            }
            
            .supplier-name {
                font-weight: 700;
                color: #2c3e50;
                margin-bottom: 8px;
                font-size: 1.2em;
            }
            
            .supplier-location {
                color: #7f8c8d;
                margin-bottom: 10px;
            }
            
            .supplier-description {
                color: #555;
                line-height: 1.5;
                margin-bottom: 15px;
            }
            
            .confidence-score {
                display: inline-block;
                padding: 4px 12px;
                border-radius: 20px;
                font-size: 0.9em;
                font-weight: 600;
            }
            
            .confidence-high {
                background: #d4edda;
                color: #155724;
            }
            
            .confidence-medium {
                background: #fff3cd;
                color: #856404;
            }
            
            .confidence-low {
                background: #f8d7da;
                color: #721c24;
            }
            
            .certifications {
                margin-top: 10px;
            }
            
            .cert-badge {
                display: inline-block;
                background: #667eea;
                color: white;
                padding: 2px 8px;
                border-radius: 12px;
                font-size: 0.8em;
                margin-right: 5px;
                margin-bottom: 5px;
            }
            
            .market-insights {
                background: #f8f9fa;
                padding: 20px;
                border-radius: 10px;
                margin-top: 20px;
            }
            
            .insight-section {
                margin-bottom: 20px;
            }
            
            .insight-title {
                font-weight: 600;
                color: #2c3e50;
                margin-bottom: 10px;
            }
            
            .insight-list {
                list-style: none;
                padding: 0;
            }
            
            .insight-list li {
                padding: 5px 0;
                border-bottom: 1px solid #e1e8ed;
            }
            
            .insight-list li:last-child {
                border-bottom: none;
            }
            
            .error {
                background: #f8d7da;
                color: #721c24;
                padding: 15px;
                border-radius: 8px;
                border: 1px solid #f5c6cb;
                margin-bottom: 20px;
            }
            
            @media (max-width: 768px) {
                .suppliers-grid {
                    grid-template-columns: 1fr;
                }
                
                .container {
                    padding: 20px;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🤖 Procurement Intelligence</h1>
                <p>AI-powered supplier discovery with LangGraph workflow</p>
                <div class="badge">LangGraph Agent</div>
                <div class="badge">DuckDuckGo Search</div>
                <div class="badge">Groq + Gemini</div>
            </div>
            
            <div class="form-container">
                <form id="procurementForm">
                    <div class="form-group">
                        <label for="query">Product/Service *</label>
                        <input type="text" id="query" name="query" required 
                               placeholder="e.g., industrial steel, IT services, manufacturing equipment">
                    </div>
                    
                    <div class="form-group">
                        <label for="location">Location (Optional)</label>
                        <input type="text" id="location" name="location" 
                               placeholder="e.g., Texas, California, New York">
                    </div>
                    
                    <div class="form-group">
                        <label for="category">Category</label>
                        <select id="category" name="category">
                            <option value="">Select category...</option>
                            <option value="materials">Materials</option>
                            <option value="equipment">Equipment</option>
                            <option value="services">Services</option>
                            <option value="software">Software</option>
                            <option value="construction">Construction</option>
                            <option value="manufacturing">Manufacturing</option>
                        </select>
                    </div>
                    
                    <button type="submit" class="btn">🚀 Start Agent Workflow</button>
                </form>
            </div>
            
            <div class="workflow-status" id="workflowStatus">
                <h3>🔄 Agent Workflow Status</h3>
                <div class="workflow-step" id="step1">
                    <strong>Step 1:</strong> 🔍 Searching for suppliers...
                </div>
                <div class="workflow-step" id="step2">
                    <strong>Step 2:</strong> 🤖 Analyzing suppliers with LLM...
                </div>
                <div class="workflow-step" id="step3">
                    <strong>Step 3:</strong> 📊 Generating market insights...
                </div>
                <div class="workflow-step" id="step4">
                    <strong>Step 4:</strong> 📝 Creating executive summary...
                </div>
            </div>
            
            <div class="loading" id="loading">
                <div class="spinner"></div>
                <p>LangGraph agent is processing your request...</p>
            </div>
            
            <div class="results" id="results">
                <div class="summary" id="summary"></div>
                
                <h2>📊 Suppliers Found</h2>
                <div class="suppliers-grid" id="suppliersGrid"></div>
                
                <div class="market-insights">
                    <h3>📈 Market Insights</h3>
                    <div class="insight-section">
                        <div class="insight-title">Price Trend</div>
                        <div id="priceTrend"></div>
                    </div>
                    <div class="insight-section">
                        <div class="insight-title">Key Factors</div>
                        <ul class="insight-list" id="keyFactors"></ul>
                    </div>
                    <div class="insight-section">
                        <div class="insight-title">Recommendations</div>
                        <ul class="insight-list" id="recommendations"></ul>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            let workflowSteps = ['step1', 'step2', 'step3', 'step4'];
            let currentStep = 0;
            
            function updateWorkflowStatus() {
                // Reset all steps
                workflowSteps.forEach(step => {
                    document.getElementById(step).classList.remove('active', 'completed');
                });
                
                // Mark completed steps
                for (let i = 0; i < currentStep; i++) {
                    document.getElementById(workflowSteps[i]).classList.add('completed');
                }
                
                // Mark current step as active
                if (currentStep < workflowSteps.length) {
                    document.getElementById(workflowSteps[currentStep]).classList.add('active');
                }
            }
            
            function simulateWorkflow() {
                const interval = setInterval(() => {
                    currentStep++;
                    updateWorkflowStatus();
                    
                    if (currentStep >= workflowSteps.length) {
                        clearInterval(interval);
                    }
                }, 2000);
            }
            
            document.getElementById('procurementForm').addEventListener('submit', async function(e) {
                e.preventDefault();
                
                const query = document.getElementById('query').value;
                const location = document.getElementById('location').value;
                const category = document.getElementById('category').value;
                
                if (!query.trim()) {
                    alert('Please enter a product or service');
                    return;
                }
                
                // Show workflow status
                document.getElementById('workflowStatus').style.display = 'block';
                document.getElementById('loading').style.display = 'block';
                document.getElementById('results').style.display = 'none';
                document.querySelector('.btn').disabled = true;
                
                // Reset workflow
                currentStep = 0;
                updateWorkflowStatus();
                simulateWorkflow();
                
                try {
                    const response = await fetch('/analyze', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            query: query,
                            location: location || null,
                            category: category || null
                        })
                    });
                    
                    if (!response.ok) {
                        throw new Error('Analysis failed');
                    }
                    
                    const data = await response.json();
                    displayResults(data);
                    
                } catch (error) {
                    console.error('Error:', error);
                    document.getElementById('workflowStatus').style.display = 'none';
                    document.getElementById('loading').style.display = 'none';
                    document.getElementById('results').innerHTML = '<div class="error">🚨 Agent workflow failed. Please try again.</div>';
                    document.getElementById('results').style.display = 'block';
                } finally {
                    document.querySelector('.btn').disabled = false;
                }
            });
            
            function displayResults(data) {
                // Hide loading and workflow status
                document.getElementById('workflowStatus').style.display = 'none';
                document.getElementById('loading').style.display = 'none';
                
                // Show summary
                document.getElementById('summary').innerHTML = `
                    <h3>📋 Agent Analysis Summary</h3>
                    <p>${data.summary}</p>
                    <p><strong>⚡ Processing Time:</strong> ${data.processing_time.toFixed(2)} seconds</p>
                    <p><strong>🏢 Suppliers Found:</strong> ${data.suppliers.length}</p>
                `;
                
                // Show suppliers
                const suppliersGrid = document.getElementById('suppliersGrid');
                suppliersGrid.innerHTML = '';
                
                if (data.suppliers.length === 0) {
                    suppliersGrid.innerHTML = '<p>No suppliers found. Try a different search term.</p>';
                } else {
                    data.suppliers.forEach(supplier => {
                        const confidenceClass = supplier.confidence_score >= 0.8 ? 'confidence-high' : 
                                               supplier.confidence_score >= 0.6 ? 'confidence-medium' : 'confidence-low';
                        
                        const certifications = supplier.certifications.map(cert => 
                            `<span class="cert-badge">${cert}</span>`
                        ).join('');
                        
                        const supplierCard = `
                            <div class="supplier-card">
                                <div class="supplier-name">${supplier.name}</div>
                                <div class="supplier-location">📍 ${supplier.location}</div>
                                <div class="supplier-description">${supplier.description.substring(0, 150)}...</div>
                                <div class="confidence-score ${confidenceClass}">
                                    Confidence: ${(supplier.confidence_score * 100).toFixed(0)}%
                                </div>
                                ${supplier.rating ? `<div>⭐ Rating: ${supplier.rating.toFixed(1)}</div>` : ''}
                                ${certifications ? `<div class="certifications">${certifications}</div>` : ''}
                                ${supplier.website ? `<div style="margin-top: 10px;"><a href="${supplier.website}" target="_blank">🔗 Visit Website</a></div>` : ''}
                            </div>
                        `;
                        suppliersGrid.innerHTML += supplierCard;
                    });
                }
                
                // Show market insights
                document.getElementById('priceTrend').innerHTML = `<strong>📈 ${data.market_insights.price_trend.toUpperCase()}</strong>`;
                
                const keyFactors = document.getElementById('keyFactors');
                keyFactors.innerHTML = '';
                data.market_insights.key_factors.forEach(factor => {
                    keyFactors.innerHTML += `<li>• ${factor}</li>`;
                });
                
                const recommendations = document.getElementById('recommendations');
                recommendations.innerHTML = '';
                data.market_insights.recommendations.forEach(rec => {
                    recommendations.innerHTML += `<li>💡 ${rec}</li>`;
                });
                
                // Show results
                document.getElementById('results').style.display = 'block';
                document.getElementById('results').scrollIntoView({ behavior: 'smooth' });
            }
        </script>
    </body>
    </html>
    """
    return html_content

@app.post("/analyze", response_model=ProcurementResponse)
async def analyze_procurement(request: ProcurementRequest):
    """Main endpoint for procurement analysis using LangGraph agent"""
    try:
        print(f"🚀 Starting LangGraph workflow for: {request.query}")
        
        # Run the LangGraph agent workflow
        result = await procurement_agent.run_analysis(
            query=request.query,
            location=request.location,
            category=request.category
        )
        
        # Convert suppliers back to Pydantic models
        suppliers = [SupplierInfo(**supplier) for supplier in result["suppliers"]]
        
        # Create market insights
        market_insights = MarketInsight(**result["market_insights"])
        
        return ProcurementResponse(
            suppliers=suppliers,
            market_insights=market_insights,
            summary=result["summary"],
            processing_time=result["processing_time"]
        )
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.get("/health")
async def health_check():
    """Simple health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "agent": "LangGraph workflow active",
        "services": {
            "search": "operational",
            "llm": "operational",
            "langgraph": "operational"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)