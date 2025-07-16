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
from competitive_service import CompetitiveIntelligenceService

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="Procurement Intelligence System", version="1.0.0")

# Initialize services
competitive_service = CompetitiveIntelligenceService()

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

# Competitive Intelligence Models
class CompetitiveBenchmarkRequest(BaseModel):
    product: str = Field(..., min_length=3, max_length=200)
    supplier_quote: Optional[float] = None
    currency: str = "USD"
    quantity: Optional[int] = None
    location: Optional[str] = None
    company_size: Optional[str] = None

class CompetitorInfo(BaseModel):
    name: str
    price: Optional[float] = None
    market_position: str
    strengths: List[str] = []

class NegotiationStrategy(BaseModel):
    suggested_counter_offer: Optional[float] = None
    leverage_points: List[str] = []
    alternative_suppliers: List[str] = []
    risk_factors: List[str] = []
    timeline_recommendation: str
    opening_approach: str

class BenchmarkResult(BaseModel):
    market_average_price: Optional[float] = None
    price_variance: Optional[float] = None
    your_position: str  # "above_market", "below_market", "at_market"
    percentile_ranking: Optional[int] = None
    key_competitors: List[CompetitorInfo] = []
    negotiation_strategy: NegotiationStrategy
    market_insights: List[str] = []
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
            
            :root {
                --gradient-primary: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                --gradient-secondary: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                --gradient-success: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
                --gradient-warning: linear-gradient(135deg, #fdbb2d 0%, #22c1c3 100%);
                --glass-bg: rgba(255, 255, 255, 0.1);
                --glass-border: rgba(255, 255, 255, 0.2);
                --glass-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
                --bg-primary: #0f0f23;
                --bg-secondary: #1a1a2e;
                --text-primary: #ffffff;
                --text-secondary: #b4b4b4;
            }
            
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: var(--bg-primary);
                color: var(--text-primary);
                min-height: 100vh;
                padding: 20px;
            }
            
            .container {
                max-width: 1400px;
                margin: 0 auto;
            }
            
            .glass-card {
                background: var(--glass-bg);
                backdrop-filter: blur(10px);
                border: 1px solid var(--glass-border);
                border-radius: 20px;
                padding: 30px;
                box-shadow: var(--glass-shadow);
            }
            
            .nav-tabs {
                display: flex;
                margin-bottom: 30px;
                gap: 10px;
            }
            
            .nav-tab {
                padding: 15px 30px;
                border-radius: 15px;
                background: var(--glass-bg);
                border: 1px solid var(--glass-border);
                color: var(--text-primary);
                cursor: pointer;
                transition: all 0.3s ease;
                font-weight: 600;
            }
            
            .nav-tab.active {
                background: var(--gradient-primary);
                border-color: transparent;
                transform: translateY(-2px);
            }
            
            .nav-tab:hover {
                background: var(--glass-bg);
                border-color: var(--glass-border);
                transform: translateY(-1px);
            }
            
            .tab-content {
                display: none;
            }
            
            .tab-content.active {
                display: block;
            }
            
            .header {
                text-align: center;
                margin-bottom: 40px;
            }
            
            .header h1 {
                background: var(--gradient-primary);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                font-size: 2.5em;
                margin-bottom: 10px;
            }
            
            .header p {
                color: var(--text-secondary);
                font-size: 1.2em;
            }
            
            /* Fix existing content text colors */
            #summary, #results, #loading, #workflowStatus {
                color: var(--text-primary);
            }
            
            #summary h3, #results h3, #suppliersGrid h3 {
                color: var(--text-primary);
                margin-bottom: 15px;
            }
            
            #summary p, #results p {
                color: var(--text-secondary);
                line-height: 1.6;
            }
            
            .supplier-card {
                background: var(--glass-bg);
                backdrop-filter: blur(10px);
                border: 1px solid var(--glass-border);
                border-radius: 15px;
                padding: 20px;
                margin-bottom: 20px;
                box-shadow: var(--glass-shadow);
            }
            
            .supplier-name {
                color: var(--text-primary);
                font-weight: 600;
                font-size: 1.3em;
                margin-bottom: 8px;
            }
            
            .supplier-location {
                color: var(--text-secondary);
                margin-bottom: 10px;
            }
            
            .supplier-description {
                color: var(--text-secondary);
                line-height: 1.5;
                margin-bottom: 15px;
            }
            
            .confidence-score {
                padding: 5px 12px;
                border-radius: 20px;
                font-size: 0.9em;
                font-weight: 600;
                display: inline-block;
                margin-bottom: 10px;
            }
            
            .confidence-high {
                background: var(--gradient-success);
                color: white;
            }
            
            .confidence-medium {
                background: var(--gradient-warning);
                color: white;
            }
            
            .confidence-low {
                background: var(--gradient-secondary);
                color: white;
            }
            
            .cert-badge {
                background: var(--glass-bg);
                border: 1px solid var(--glass-border);
                color: var(--text-primary);
                padding: 3px 8px;
                border-radius: 12px;
                font-size: 0.8em;
                margin-right: 5px;
                display: inline-block;
            }
            
            .certifications {
                margin-top: 10px;
            }
            
            .workflow-step {
                background: var(--glass-bg);
                border: 1px solid var(--glass-border);
                color: var(--text-primary);
                padding: 10px 15px;
                border-radius: 10px;
                margin-bottom: 10px;
                transition: all 0.3s ease;
            }
            
            .workflow-step.active {
                background: var(--gradient-primary);
                color: white;
                border-color: transparent;
            }
            
            .workflow-step.completed {
                background: var(--gradient-success);
                color: white;
                border-color: transparent;
            }
            
            .market-insights {
                background: var(--glass-bg);
                border: 1px solid var(--glass-border);
                border-radius: 15px;
                padding: 20px;
                margin-top: 20px;
            }
            
            .market-insights h3 {
                color: var(--text-primary);
                margin-bottom: 15px;
            }
            
            .market-insights ul {
                list-style: none;
                padding: 0;
            }
            
            .market-insights li {
                color: var(--text-secondary);
                margin-bottom: 8px;
                padding-left: 20px;
                position: relative;
            }
            
            .market-insights li:before {
                content: "•";
                color: #667eea;
                position: absolute;
                left: 0;
                font-size: 1.2em;
            }
            
            .loading-spinner {
                border: 4px solid var(--glass-border);
                border-top: 4px solid #667eea;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                animation: spin 1s linear infinite;
                margin: 20px auto;
            }
            
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            
            .error {
                background: var(--gradient-secondary);
                color: white;
                padding: 15px;
                border-radius: 10px;
                margin: 20px 0;
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
                background: var(--glass-bg);
                backdrop-filter: blur(10px);
                border: 1px solid var(--glass-border);
                padding: 30px;
                border-radius: 20px;
                margin-bottom: 30px;
            }
            
            .form-group {
                margin-bottom: 20px;
            }
            
            .form-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin-bottom: 20px;
            }
            
            label {
                display: block;
                margin-bottom: 8px;
                font-weight: 600;
                color: var(--text-primary);
                font-size: 14px;
            }
            
            input, select {
                width: 100%;
                padding: 12px;
                border: 1px solid var(--glass-border);
                border-radius: 12px;
                font-size: 16px;
                background: var(--glass-bg);
                color: var(--text-primary);
                transition: all 0.3s ease;
                backdrop-filter: blur(5px);
            }
            
            input:focus, select:focus {
                outline: none;
                border-color: #667eea;
                box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.2);
            }
            
            input::placeholder {
                color: var(--text-secondary);
            }
            
            .btn {
                background: var(--gradient-primary);
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
                <div class="badge">Brave Search</div>
                <div class="badge">Groq + Gemini</div>
            </div>
            
            <!-- Navigation Tabs -->
            <div class="nav-tabs">
                <div class="nav-tab active" onclick="switchTab('supplier-discovery')">
                    🔍 Supplier Discovery
                </div>
                <div class="nav-tab" onclick="switchTab('competitive-intelligence')">
                    📊 Competitive Intelligence
                </div>
            </div>
            
            <!-- Supplier Discovery Tab -->
            <div id="supplier-discovery" class="tab-content active">
            
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
            
            </div> <!-- End supplier-discovery tab -->
            
            <!-- Competitive Intelligence Tab -->
            <div id="competitive-intelligence" class="tab-content">
                <div class="glass-card">
                    <h2 class="text-2xl font-semibold text-white mb-6">🎯 Competitive Analysis</h2>
                    
                    <form id="competitiveForm">
                        <div class="form-grid">
                            <div class="form-group">
                                <label for="comp-product">Product/Service *</label>
                                <input type="text" id="comp-product" name="product" required 
                                       placeholder="e.g., Steel pipes, CRM Software, Office chairs">
                            </div>
                            
                            <div class="form-group">
                                <label for="comp-quote">Your Quote (Optional)</label>
                                <input type="number" id="comp-quote" name="supplier_quote" step="0.01"
                                       placeholder="500.00">
                            </div>
                            
                            <div class="form-group">
                                <label for="comp-quantity">Quantity</label>
                                <input type="number" id="comp-quantity" name="quantity" 
                                       placeholder="100">
                            </div>
                            
                            <div class="form-group">
                                <label for="comp-location">Location</label>
                                <input type="text" id="comp-location" name="location" 
                                       placeholder="e.g., Texas, Dubai, Global">
                            </div>
                            
                            <div class="form-group">
                                <label for="comp-size">Company Size</label>
                                <select id="comp-size" name="company_size">
                                    <option value="">Select size</option>
                                    <option value="startup">Startup (1-50 employees)</option>
                                    <option value="sme">SME (51-500 employees)</option>
                                    <option value="enterprise">Enterprise (500+ employees)</option>
                                </select>
                            </div>
                            
                            <div class="form-group">
                                <label for="comp-currency">Currency</label>
                                <select id="comp-currency" name="currency">
                                    <option value="USD">USD</option>
                                    <option value="EUR">EUR</option>
                                    <option value="GBP">GBP</option>
                                    <option value="AED">AED</option>
                                </select>
                            </div>
                        </div>
                        
                        <button type="submit" class="btn w-full">
                            🚀 Analyze Market Position
                        </button>
                    </form>
                </div>
                
                <!-- Competitive Results -->
                <div id="competitive-results" class="hidden" style="display: none;">
                    <div class="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6 mt-8">
                        <!-- Market Position Card -->
                        <div class="glass-card">
                            <h3 class="text-xl font-semibold text-white mb-4">📈 Market Position</h3>
                            <div id="market-position-content"></div>
                        </div>
                        
                        <!-- Negotiation Strategy Card -->
                        <div class="glass-card">
                            <h3 class="text-xl font-semibold text-white mb-4">🎯 Negotiation Strategy</h3>
                            <div id="negotiation-strategy-content"></div>
                        </div>
                        
                        <!-- Competitive Landscape Card -->
                        <div class="glass-card">
                            <h3 class="text-xl font-semibold text-white mb-4">🏆 Competitive Landscape</h3>
                            <div id="competitive-landscape-content"></div>
                        </div>
                    </div>
                </div>
                
                <!-- Loading State -->
                <div id="competitive-loading" class="hidden text-center py-8" style="display: none;">
                    <div class="loading-spinner mx-auto"></div>
                    <p class="text-white mt-4">Analyzing market position...</p>
                    <p class="text-gray-400 text-sm">Searching industry benchmarks</p>
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
            
            // Tab switching functionality
            function switchTab(tabName) {
                // Hide all tab contents
                const tabContents = document.querySelectorAll('.tab-content');
                tabContents.forEach(content => {
                    content.classList.remove('active');
                });
                
                // Remove active class from all tabs
                const tabs = document.querySelectorAll('.nav-tab');
                tabs.forEach(tab => {
                    tab.classList.remove('active');
                });
                
                // Show selected tab content
                document.getElementById(tabName).classList.add('active');
                
                // Add active class to clicked tab
                event.target.classList.add('active');
            }
            
            // Competitive Intelligence Form Handler
            document.getElementById('competitiveForm').addEventListener('submit', async function(e) {
                e.preventDefault();
                
                const formData = new FormData(e.target);
                const data = Object.fromEntries(formData.entries());
                
                if (!data.product.trim()) {
                    alert('Please enter a product or service');
                    return;
                }
                
                // Show loading state
                document.getElementById('competitive-loading').style.display = 'block';
                document.getElementById('competitive-results').style.display = 'none';
                
                try {
                    const response = await fetch('/api/v1/competitive/benchmark', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify(data)
                    });
                    
                    if (!response.ok) {
                        throw new Error('Analysis failed');
                    }
                    
                    const result = await response.json();
                    displayCompetitiveResults(result);
                    
                } catch (error) {
                    console.error('Error:', error);
                    alert('🚨 Competitive analysis failed. Please try again.');
                } finally {
                    document.getElementById('competitive-loading').style.display = 'none';
                }
            });
            
            function displayCompetitiveResults(data) {
                // Market Position
                const marketPositionContent = document.getElementById('market-position-content');
                let positionHtml = '';
                
                if (data.market_average_price) {
                    positionHtml += `
                        <div class="space-y-4">
                            <div class="flex justify-between items-center">
                                <span class="text-gray-300">Market Average:</span>
                                <span class="text-xl text-white">$${data.market_average_price}</span>
                            </div>
                    `;
                    
                    if (data.price_variance) {
                        const varianceColor = data.price_variance > 0 ? 'text-red-400' : 'text-green-400';
                        positionHtml += `
                            <div class="flex justify-between items-center">
                                <span class="text-gray-300">Variance:</span>
                                <span class="text-lg ${varianceColor}">${data.price_variance > 0 ? '+' : ''}${data.price_variance.toFixed(1)}%</span>
                            </div>
                        `;
                    }
                }
                
                if (data.percentile_ranking) {
                    positionHtml += `
                        <div class="space-y-2">
                            <div class="flex justify-between text-sm text-gray-400">
                                <span>25th</span><span>50th</span><span>75th</span><span>90th</span>
                            </div>
                            <div class="h-3 bg-gray-700 rounded-full relative">
                                <div class="h-3 bg-gradient-to-r from-blue-400 to-purple-500 rounded-full" style="width: ${data.percentile_ranking}%"></div>
                            </div>
                            <p class="text-sm text-gray-400 text-center">${data.percentile_ranking}th percentile</p>
                        </div>
                    `;
                }
                
                marketPositionContent.innerHTML = positionHtml || '<p class="text-gray-400">Limited market data available</p>';
                
                // Negotiation Strategy
                const negotiationContent = document.getElementById('negotiation-strategy-content');
                let negotiationHtml = '';
                
                if (data.negotiation_strategy.suggested_counter_offer) {
                    negotiationHtml += `
                        <div class="p-4 rounded-xl bg-gradient-to-r from-blue-500/20 to-purple-500/20 border border-blue-400/30 mb-4">
                            <h4 class="font-semibold text-blue-400 mb-2">💬 Suggested Counter-offer</h4>
                            <p class="text-white text-lg font-bold">$${data.negotiation_strategy.suggested_counter_offer}</p>
                        </div>
                    `;
                }
                
                if (data.negotiation_strategy.leverage_points.length > 0) {
                    negotiationHtml += `
                        <div class="space-y-3">
                            <h4 class="font-semibold text-white">📋 Leverage Points:</h4>
                            <ul class="space-y-2">
                    `;
                    
                    data.negotiation_strategy.leverage_points.forEach(point => {
                        negotiationHtml += `
                            <li class="flex items-start space-x-2">
                                <span class="text-green-400">✓</span>
                                <span class="text-gray-300">${point}</span>
                            </li>
                        `;
                    });
                    
                    negotiationHtml += '</ul></div>';
                }
                
                negotiationContent.innerHTML = negotiationHtml || '<p class="text-gray-400">Negotiation strategy analysis in progress</p>';
                
                // Competitive Landscape
                const competitiveContent = document.getElementById('competitive-landscape-content');
                let competitiveHtml = '';
                
                if (data.key_competitors.length > 0) {
                    data.key_competitors.forEach(competitor => {
                        competitiveHtml += `
                            <div class="flex justify-between items-center p-3 rounded-lg bg-white/5 mb-3">
                                <div>
                                    <p class="font-medium text-white">${competitor.name}</p>
                                    <p class="text-sm text-gray-400">${competitor.market_position}</p>
                                </div>
                                ${competitor.price ? `<span class="text-blue-400 font-semibold">$${competitor.price}</span>` : ''}
                            </div>
                        `;
                    });
                } else {
                    competitiveHtml = '<p class="text-gray-400">Competitive landscape analysis in progress</p>';
                }
                
                competitiveContent.innerHTML = competitiveHtml;
                
                // Show results
                document.getElementById('competitive-results').style.display = 'block';
                document.getElementById('competitive-results').scrollIntoView({ behavior: 'smooth' });
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

@app.post("/api/v1/competitive/benchmark", response_model=BenchmarkResult)
async def analyze_competitive_benchmark(request: CompetitiveBenchmarkRequest):
    """Analyze competitive positioning and industry benchmarks"""
    try:
        print(f"🎯 Starting competitive benchmark analysis for: {request.product}")
        
        # Run competitive analysis
        result = await competitive_service.analyze_market_benchmark(request)
        
        # Convert to response model
        return BenchmarkResult(**result)
        
    except Exception as e:
        print(f"❌ Competitive benchmark analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Competitive analysis failed: {str(e)}")

@app.get("/api/v1/competitive/cache/{product_hash}")
async def get_cached_benchmark(product_hash: str):
    """Retrieve cached benchmark data (24hr TTL)"""
    try:
        cached_data = await competitive_service.get_cached_benchmark(product_hash)
        
        if cached_data:
            return {"status": "found", "data": cached_data}
        else:
            return {"status": "not_found", "message": "No cached data available"}
            
    except Exception as e:
        print(f"❌ Cache retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Cache retrieval failed: {str(e)}")

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
            "langgraph": "operational",
            "competitive": "operational"
        }
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)