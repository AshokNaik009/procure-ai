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
                /* Modern B2B SaaS Color Palette */
                --primary-blue: #3b82f6;
                --primary-blue-light: #60a5fa;
                --primary-blue-dark: #1d4ed8;
                --accent-purple: #8b5cf6;
                --accent-purple-light: #a78bfa;
                --success-green: #10b981;
                --warning-yellow: #f59e0b;
                --danger-red: #ef4444;
                
                /* Background Colors */
                --bg-primary: #0f172a;
                --bg-secondary: #1e293b;
                --bg-tertiary: #334155;
                --bg-card: #1e293b;
                --bg-sidebar: #0f172a;
                --bg-hover: #334155;
                
                /* Text Colors */
                --text-primary: #f8fafc;
                --text-secondary: #cbd5e1;
                --text-muted: #64748b;
                --text-accent: #3b82f6;
                
                /* Border Colors */
                --border-primary: #334155;
                --border-secondary: #475569;
                --border-accent: #3b82f6;
                
                /* Gradients */
                --gradient-primary: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
                --gradient-card: linear-gradient(135deg, #1e293b 0%, #334155 100%);
                --gradient-success: linear-gradient(135deg, #10b981 0%, #059669 100%);
                
                /* Shadows */
                --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
                --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
                --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
                
                /* Spacing */
                --space-xs: 0.25rem;
                --space-sm: 0.5rem;
                --space-md: 1rem;
                --space-lg: 1.5rem;
                --space-xl: 2rem;
                --space-2xl: 3rem;
                
                /* Border Radius */
                --radius-sm: 0.25rem;
                --radius-md: 0.5rem;
                --radius-lg: 0.75rem;
                --radius-xl: 1rem;
                
                /* Typography */
                --font-size-xs: 0.75rem;
                --font-size-sm: 0.875rem;
                --font-size-base: 1rem;
                --font-size-lg: 1.125rem;
                --font-size-xl: 1.25rem;
                --font-size-2xl: 1.5rem;
                --font-size-3xl: 1.875rem;
                --font-size-4xl: 2.25rem;
                
                /* Transitions */
                --transition-fast: 150ms cubic-bezier(0.4, 0, 0.2, 1);
                --transition-normal: 300ms cubic-bezier(0.4, 0, 0.2, 1);
                --transition-slow: 500ms cubic-bezier(0.4, 0, 0.2, 1);
            }
            
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Inter', sans-serif;
                background: var(--bg-primary);
                color: var(--text-primary);
                min-height: 100vh;
                margin: 0;
                overflow-x: hidden;
            }
            
            .dashboard-layout {
                display: flex;
                min-height: 100vh;
            }
            
            /* Sidebar Navigation */
            .sidebar {
                width: 280px;
                background: var(--bg-sidebar);
                border-right: 1px solid var(--border-primary);
                padding: var(--space-lg);
                display: flex;
                flex-direction: column;
                position: fixed;
                height: 100vh;
                left: 0;
                top: 0;
                z-index: 100;
                transition: transform var(--transition-normal);
            }
            
            .sidebar.collapsed {
                width: 70px;
                padding: var(--space-md);
            }
            
            .sidebar.collapsed .sidebar-title,
            .sidebar.collapsed .nav-item span,
            .sidebar.collapsed .user-info {
                display: none;
            }
            
            .sidebar.collapsed .nav-item {
                justify-content: center;
                padding: var(--space-md);
            }
            
            .sidebar-toggle {
                position: absolute;
                top: var(--space-lg);
                right: -15px;
                width: 30px;
                height: 30px;
                background: var(--bg-card);
                border: 1px solid var(--border-primary);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                color: var(--text-primary);
                font-size: 14px;
                transition: all var(--transition-fast);
            }
            
            .sidebar-toggle:hover {
                background: var(--bg-hover);
                border-color: var(--border-accent);
            }
            
            .mobile-menu-btn {
                display: none;
                position: fixed;
                top: 20px;
                left: 20px;
                z-index: 101;
                background: var(--bg-card);
                border: 1px solid var(--border-primary);
                border-radius: var(--radius-lg);
                padding: var(--space-md);
                color: var(--text-primary);
                cursor: pointer;
                font-size: 18px;
            }
            
            .sidebar-header {
                display: flex;
                align-items: center;
                gap: var(--space-md);
                margin-bottom: var(--space-2xl);
                padding-bottom: var(--space-lg);
                border-bottom: 1px solid var(--border-primary);
            }
            
            .sidebar-logo {
                width: 40px;
                height: 40px;
                background: var(--gradient-primary);
                border-radius: var(--radius-lg);
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: var(--font-size-xl);
                font-weight: 600;
            }
            
            .sidebar-title {
                font-size: var(--font-size-lg);
                font-weight: 600;
                color: var(--text-primary);
            }
            
            .sidebar-nav {
                flex: 1;
                display: flex;
                flex-direction: column;
                gap: var(--space-xs);
            }
            
            .nav-item {
                display: flex;
                align-items: center;
                gap: var(--space-md);
                padding: var(--space-md);
                border-radius: var(--radius-lg);
                color: var(--text-secondary);
                text-decoration: none;
                transition: all var(--transition-fast);
                font-weight: 500;
                cursor: pointer;
            }
            
            .nav-item:hover {
                background: var(--bg-hover);
                color: var(--text-primary);
            }
            
            .nav-item.active {
                background: var(--primary-blue);
                color: white;
            }
            
            .nav-icon {
                width: 20px;
                height: 20px;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
            /* Main Content Area */
            .main-content {
                flex: 1;
                margin-left: 280px;
                background: var(--bg-primary);
                min-height: 100vh;
                transition: margin-left var(--transition-normal);
            }
            
            .main-content.sidebar-collapsed {
                margin-left: 70px;
            }
            
            .content-header {
                background: var(--bg-secondary);
                border-bottom: 1px solid var(--border-primary);
                padding: var(--space-lg) var(--space-xl);
                position: sticky;
                top: 0;
                z-index: 50;
            }
            
            .breadcrumb {
                display: flex;
                align-items: center;
                gap: var(--space-sm);
                margin-bottom: var(--space-md);
                font-size: var(--font-size-sm);
                color: var(--text-muted);
            }
            
            .breadcrumb-item {
                color: var(--text-muted);
            }
            
            .breadcrumb-item.active {
                color: var(--text-accent);
            }
            
            .page-title {
                font-size: var(--font-size-3xl);
                font-weight: 700;
                color: var(--text-primary);
                margin-bottom: var(--space-sm);
            }
            
            .page-subtitle {
                color: var(--text-secondary);
                font-size: var(--font-size-lg);
            }
            
            .content-body {
                padding: var(--space-xl);
            }
            
            /* Modern Card Styles */
            .card {
                background: var(--bg-card);
                border: 1px solid var(--border-primary);
                border-radius: var(--radius-xl);
                padding: var(--space-xl);
                box-shadow: var(--shadow-lg);
                transition: all var(--transition-fast);
            }
            
            .card:hover {
                border-color: var(--border-accent);
                box-shadow: var(--shadow-xl);
                transform: translateY(-2px);
            }
            
            .card-header {
                display: flex;
                align-items: center;
                justify-content: between;
                margin-bottom: var(--space-lg);
            }
            
            .card-title {
                font-size: var(--font-size-xl);
                font-weight: 600;
                color: var(--text-primary);
                margin: 0;
            }
            
            .card-subtitle {
                color: var(--text-secondary);
                font-size: var(--font-size-sm);
                margin: var(--space-xs) 0 0 0;
            }
            
            /* Popular Categories */
            .popular-categories {
                margin-bottom: var(--space-2xl);
            }
            
            .categories-header {
                display: flex;
                align-items: center;
                justify-content: space-between;
                margin-bottom: var(--space-lg);
            }
            
            .categories-title {
                font-size: var(--font-size-2xl);
                font-weight: 600;
                color: var(--text-primary);
            }
            
            .categories-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: var(--space-lg);
                margin-bottom: var(--space-xl);
            }
            
            .category-card {
                background: var(--bg-card);
                border: 1px solid var(--border-primary);
                border-radius: var(--radius-xl);
                padding: var(--space-xl);
                cursor: pointer;
                transition: all var(--transition-fast);
                position: relative;
                overflow: hidden;
            }
            
            .category-card:hover {
                border-color: var(--primary-blue);
                box-shadow: var(--shadow-xl);
                transform: translateY(-4px);
            }
            
            .category-card::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 3px;
                background: var(--gradient-primary);
                opacity: 0;
                transition: opacity var(--transition-fast);
            }
            
            .category-card:hover::before {
                opacity: 1;
            }
            
            .category-icon {
                width: 48px;
                height: 48px;
                background: var(--gradient-primary);
                border-radius: var(--radius-lg);
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: var(--font-size-2xl);
                margin-bottom: var(--space-md);
            }
            
            .category-name {
                font-size: var(--font-size-lg);
                font-weight: 600;
                color: var(--text-primary);
                margin-bottom: var(--space-sm);
            }
            
            .category-description {
                color: var(--text-secondary);
                font-size: var(--font-size-sm);
                line-height: 1.5;
                margin-bottom: var(--space-md);
            }
            
            .category-examples {
                display: flex;
                flex-wrap: wrap;
                gap: var(--space-xs);
            }
            
            .category-tag {
                background: var(--bg-tertiary);
                color: var(--text-secondary);
                padding: var(--space-xs) var(--space-sm);
                border-radius: var(--radius-md);
                font-size: var(--font-size-xs);
                font-weight: 500;
            }
            
            /* Search Section */
            .search-section {
                background: var(--bg-card);
                border: 1px solid var(--border-primary);
                border-radius: var(--radius-xl);
                padding: var(--space-2xl);
                margin-bottom: var(--space-xl);
            }
            
            .search-header {
                text-align: center;
                margin-bottom: var(--space-xl);
            }
            
            .search-title {
                font-size: var(--font-size-3xl);
                font-weight: 700;
                color: var(--text-primary);
                margin-bottom: var(--space-sm);
            }
            
            .search-subtitle {
                color: var(--text-secondary);
                font-size: var(--font-size-lg);
            }
            
            .search-form {
                max-width: 600px;
                margin: 0 auto;
            }
            
            .form-group {
                margin-bottom: var(--space-lg);
            }
            
            .form-label {
                display: block;
                margin-bottom: var(--space-sm);
                font-weight: 600;
                color: var(--text-primary);
                font-size: var(--font-size-sm);
            }
            
            .form-input {
                width: 100%;
                padding: var(--space-md);
                border: 1px solid var(--border-primary);
                border-radius: var(--radius-lg);
                font-size: var(--font-size-base);
                background: var(--bg-primary);
                color: var(--text-primary);
                transition: all var(--transition-fast);
            }
            
            .form-input:focus {
                outline: none;
                border-color: var(--primary-blue);
                box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
            }
            
            .form-input::placeholder {
                color: var(--text-muted);
            }
            
            .btn-primary {
                background: var(--gradient-primary);
                color: white;
                padding: var(--space-md) var(--space-xl);
                border: none;
                border-radius: var(--radius-lg);
                font-size: var(--font-size-base);
                font-weight: 600;
                cursor: pointer;
                transition: all var(--transition-fast);
                display: inline-flex;
                align-items: center;
                gap: var(--space-sm);
            }
            
            .btn-primary:hover {
                transform: translateY(-2px);
                box-shadow: var(--shadow-xl);
            }
            
            .btn-primary:active {
                transform: translateY(0);
            }
            
            .btn-secondary {
                background: var(--bg-tertiary);
                color: var(--text-primary);
                padding: var(--space-md) var(--space-xl);
                border: 1px solid var(--border-primary);
                border-radius: var(--radius-lg);
                font-size: var(--font-size-base);
                font-weight: 600;
                cursor: pointer;
                transition: all var(--transition-fast);
            }
            
            .btn-secondary:hover {
                background: var(--bg-hover);
                border-color: var(--border-accent);
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
        <div class="dashboard-layout">
            <!-- Sidebar Navigation -->
            <nav class="sidebar">
                <div class="sidebar-header">
                    <div class="sidebar-logo">🤖</div>
                    <div>
                        <div class="sidebar-title">ProcureAI</div>
                        <div style="font-size: 12px; color: var(--text-muted);">v2.0</div>
                    </div>
                </div>
                
                <div class="sidebar-nav">
                    <div class="nav-item active" onclick="switchPage('dashboard')">
                        <div class="nav-icon">📊</div>
                        <span>Dashboard</span>
                    </div>
                    <div class="nav-item" onclick="switchPage('supplier-discovery')">
                        <div class="nav-icon">🔍</div>
                        <span>Supplier Discovery</span>
                    </div>
                    <div class="nav-item" onclick="switchPage('competitive-intelligence')">
                        <div class="nav-icon">📈</div>
                        <span>Market Intelligence</span>
                    </div>
                    <div class="nav-item" onclick="switchPage('analytics')">
                        <div class="nav-icon">📋</div>
                        <span>Analytics</span>
                    </div>
                    <div class="nav-item" onclick="switchPage('about')">
                        <div class="nav-icon">ℹ️</div>
                        <span>About</span>
                    </div>
                </div>
                
                <div class="user-info" style="padding: var(--space-md); border-top: 1px solid var(--border-primary); margin-top: auto;">
                    <div style="display: flex; align-items: center; gap: var(--space-sm);">
                        <div style="width: 32px; height: 32px; background: var(--gradient-primary); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 14px;">🤖</div>
                        <div>
                            <div style="font-size: 14px; font-weight: 600; color: var(--text-primary);">ProcureAI</div>
                            <div style="font-size: 12px; color: var(--text-muted);">Smart Procurement</div>
                        </div>
                    </div>
                </div>
                
                <div class="sidebar-toggle" onclick="toggleSidebar()">
                    <span id="sidebar-toggle-icon">←</span>
                </div>
            </nav>
            
            <div class="mobile-menu-btn" onclick="toggleMobileSidebar()">
                ☰
            </div>
            
            <!-- Main Content -->
            <main class="main-content">
                <div class="content-header">
                    <nav class="breadcrumb">
                        <span class="breadcrumb-item">Home</span>
                        <span>/</span>
                        <span class="breadcrumb-item active" id="current-page">Dashboard</span>
                    </nav>
                    <h1 class="page-title" id="page-title">Procurement Intelligence Dashboard</h1>
                    <p class="page-subtitle" id="page-subtitle">AI-powered supplier discovery and competitive analysis</p>
                </div>
                
                <div class="content-body">
                    <!-- Dashboard Page -->
                    <div id="dashboard-page" class="page-content active">
                        <!-- Popular Categories Section -->
                        <section class="popular-categories">
                            <div class="categories-header">
                                <h2 class="categories-title">Popular Procurement Categories</h2>
                                <button class="btn-secondary" onclick="switchPage('supplier-discovery')">
                                    Start Custom Search →
                                </button>
                            </div>
                            
                            <div class="categories-grid">
                                <div class="category-card" onclick="searchCategory('Raw Materials')">
                                    <div class="category-icon">🏗️</div>
                                    <div class="category-name">Raw Materials</div>
                                    <div class="category-description">Essential materials for manufacturing and production processes</div>
                                    <div class="category-examples">
                                        <span class="category-tag">Steel</span>
                                        <span class="category-tag">Aluminum</span>
                                        <span class="category-tag">Plastics</span>
                                        <span class="category-tag">Chemicals</span>
                                    </div>
                                </div>
                                
                                <div class="category-card" onclick="searchCategory('Industrial Equipment')">
                                    <div class="category-icon">⚙️</div>
                                    <div class="category-name">Industrial Equipment</div>
                                    <div class="category-description">Machinery and equipment for manufacturing operations</div>
                                    <div class="category-examples">
                                        <span class="category-tag">CNC Machines</span>
                                        <span class="category-tag">Conveyor Systems</span>
                                        <span class="category-tag">Pumps</span>
                                        <span class="category-tag">Generators</span>
                                    </div>
                                </div>
                                
                                <div class="category-card" onclick="searchCategory('IT Services')">
                                    <div class="category-icon">💻</div>
                                    <div class="category-name">IT Services</div>
                                    <div class="category-description">Technology solutions and digital transformation services</div>
                                    <div class="category-examples">
                                        <span class="category-tag">Cloud Services</span>
                                        <span class="category-tag">Software Development</span>
                                        <span class="category-tag">IT Support</span>
                                        <span class="category-tag">Cybersecurity</span>
                                    </div>
                                </div>
                                
                                <div class="category-card" onclick="searchCategory('Construction Materials')">
                                    <div class="category-icon">🏢</div>
                                    <div class="category-name">Construction Materials</div>
                                    <div class="category-description">Building materials and construction supplies</div>
                                    <div class="category-examples">
                                        <span class="category-tag">Concrete</span>
                                        <span class="category-tag">Lumber</span>
                                        <span class="category-tag">Insulation</span>
                                        <span class="category-tag">Roofing</span>
                                    </div>
                                </div>
                                
                                <div class="category-card" onclick="searchCategory('Office Supplies')">
                                    <div class="category-icon">📝</div>
                                    <div class="category-name">Office Supplies</div>
                                    <div class="category-description">Administrative and operational office requirements</div>
                                    <div class="category-examples">
                                        <span class="category-tag">Furniture</span>
                                        <span class="category-tag">Stationery</span>
                                        <span class="category-tag">Electronics</span>
                                        <span class="category-tag">Printing</span>
                                    </div>
                                </div>
                                
                                <div class="category-card" onclick="searchCategory('Transportation & Logistics')">
                                    <div class="category-icon">🚚</div>
                                    <div class="category-name">Transportation & Logistics</div>
                                    <div class="category-description">Shipping, freight, and logistics services</div>
                                    <div class="category-examples">
                                        <span class="category-tag">Freight</span>
                                        <span class="category-tag">Warehousing</span>
                                        <span class="category-tag">Fleet Management</span>
                                        <span class="category-tag">Packaging</span>
                                    </div>
                                </div>
                            </div>
                        </section>
                        
                        <!-- Quick Search Section -->
                        <section class="search-section">
                            <div class="search-header">
                                <h2 class="search-title">Quick Supplier Search</h2>
                                <p class="search-subtitle">Get instant insights on suppliers for any product or service</p>
                            </div>
                            
                            <form class="search-form" id="quickSearchForm">
                                <div class="form-group">
                                    <label class="form-label" for="quick-search">What are you looking to procure?</label>
                                    <input type="text" id="quick-search" class="form-input" placeholder="e.g., Industrial steel, IT services, Office furniture..." required>
                                </div>
                                <div style="text-align: center;">
                                    <button type="submit" class="btn-primary">
                                        🔍 Search
                                    </button>
                                </div>
                            </form>
                        </section>
                    </div>
                    
                    <!-- Supplier Discovery Page -->
                    <div id="supplier-discovery-page" class="page-content" style="display: none;">
                        <div class="search-section">
                            <div class="search-header">
                                <h2 class="search-title">Advanced Supplier Discovery</h2>
                                <p class="search-subtitle">Use our AI-powered agent to find the best suppliers for your needs</p>
                            </div>
                            
                            <form class="search-form" id="procurementForm">
                                <div class="form-group">
                                    <label class="form-label" for="query">Product/Service *</label>
                                    <input type="text" id="query" name="query" class="form-input" required 
                                           placeholder="e.g., industrial steel, IT services, manufacturing equipment">
                                </div>
                                
                                <div class="form-group">
                                    <label class="form-label" for="location">Location (Optional)</label>
                                    <input type="text" id="location" name="location" class="form-input"
                                           placeholder="e.g., Texas, California, New York">
                                </div>
                                
                                <div class="form-group">
                                    <label class="form-label" for="category">Category</label>
                                    <select id="category" name="category" class="form-input">
                                        <option value="">Select category...</option>
                                        <option value="materials">Materials</option>
                                        <option value="equipment">Equipment</option>
                                        <option value="services">Services</option>
                                        <option value="software">Software</option>
                                        <option value="construction">Construction</option>
                                        <option value="manufacturing">Manufacturing</option>
                                    </select>
                                </div>
                                
                                <div style="text-align: center;">
                                    <button type="submit" class="btn-primary">
                                        🔍 Search
                                    </button>
                                </div>
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
            
                        
                        <!-- Workflow Status -->
                        <div class="workflow-status" id="workflowStatus" style="display: none;">
                            <div class="card" style="background: #3f433f !important;">
                                <h3 style="color: white !important; margin-bottom: var(--space-lg);">🔄 Agent Workflow Status</h3>
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
                        </div>
                        
                        <!-- Loading State -->
                        <div class="loading" id="loading" style="display: none;">
                            <div class="card" style="text-align: center;">
                                <div class="spinner"></div>
                                <p style="color: var(--text-secondary); margin-top: var(--space-md);">LangGraph agent is processing your request...</p>
                            </div>
                        </div>
                        
                        <!-- Results Section -->
                        <div class="results" id="results" style="display: none;">
                            <div class="card" id="summary" style="margin-bottom: var(--space-xl);">
                                <div style="display: flex; justify-content: between; align-items: center; margin-bottom: var(--space-md);">
                                    <div></div>
                                    <button id="exportExcel" class="btn-secondary" style="display: none;" onclick="exportToExcel()">
                                        📊 Export to Excel
                                    </button>
                                </div>
                            </div>
                            
                            <div class="card">
                                <h2 style="color: var(--text-primary); margin-bottom: var(--space-lg);">📊 Suppliers Found</h2>
                                <div class="suppliers-grid" id="suppliersGrid"></div>
                            </div>
                            
                            <div class="card market-insights">
                                <h3 style="color: #1a202c !important; margin-bottom: var(--space-lg);">📈 Market Insights</h3>
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
                    
                    <!-- Competitive Intelligence Page -->
                    <div id="competitive-intelligence-page" class="page-content" style="display: none;">
                        <div class="search-section">
                            <div class="search-header">
                                <h2 class="search-title">🎯 Competitive Analysis</h2>
                                <p class="search-subtitle">Get market intelligence and competitive positioning insights</p>
                            </div>
                            
                            <form class="search-form" id="competitiveForm">
                                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: var(--space-lg);">
                                    <div class="form-group">
                                        <label class="form-label" for="comp-product">Product/Service *</label>
                                        <input type="text" id="comp-product" name="product" class="form-input" required 
                                               placeholder="e.g., Steel pipes, CRM Software, Office chairs">
                                    </div>
                                    
                                    <div class="form-group">
                                        <label class="form-label" for="comp-quote">Your Quote (Optional)</label>
                                        <input type="number" id="comp-quote" name="supplier_quote" step="0.01" class="form-input"
                                               placeholder="500.00">
                                    </div>
                                    
                                    <div class="form-group">
                                        <label class="form-label" for="comp-quantity">Quantity</label>
                                        <input type="number" id="comp-quantity" name="quantity" class="form-input"
                                               placeholder="100">
                                    </div>
                                    
                                    <div class="form-group">
                                        <label class="form-label" for="comp-location">Location</label>
                                        <input type="text" id="comp-location" name="location" class="form-input"
                                               placeholder="e.g., Texas, Dubai, Global">
                                    </div>
                                    
                                    <div class="form-group">
                                        <label class="form-label" for="comp-size">Company Size</label>
                                        <select id="comp-size" name="company_size" class="form-input">
                                            <option value="">Select size</option>
                                            <option value="startup">Startup (1-50 employees)</option>
                                            <option value="sme">SME (51-500 employees)</option>
                                            <option value="enterprise">Enterprise (500+ employees)</option>
                                        </select>
                                    </div>
                                    
                                    <div class="form-group">
                                        <label class="form-label" for="comp-currency">Currency</label>
                                        <select id="comp-currency" name="currency" class="form-input">
                                            <option value="USD">USD</option>
                                            <option value="EUR">EUR</option>
                                            <option value="GBP">GBP</option>
                                            <option value="AED">AED</option>
                                        </select>
                                    </div>
                                </div>
                                
                                <div style="text-align: center; margin-top: var(--space-xl);">
                                    <button type="submit" class="btn-primary">
                                        📊 Analyze
                                    </button>
                                </div>
                            </form>
                        </div>
                        
                        <!-- Competitive Loading State -->
                        <div id="competitive-loading" class="card" style="display: none; text-align: center;">
                            <div class="spinner"></div>
                            <p style="color: var(--text-primary); margin-top: var(--space-md);">Analyzing market position...</p>
                            <p style="color: var(--text-secondary); font-size: var(--font-size-sm);">Searching industry benchmarks</p>
                        </div>
                        
                        <!-- Competitive Results -->
                        <div id="competitive-results" style="display: none;">
                            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: var(--space-lg); margin-top: var(--space-xl);">
                                <!-- Market Position Card -->
                                <div class="card">
                                    <h3 class="card-title">📈 Market Position</h3>
                                    <div id="market-position-content"></div>
                                </div>
                                
                                <!-- Negotiation Strategy Card -->
                                <div class="card">
                                    <h3 class="card-title">🎯 Negotiation Strategy</h3>
                                    <div id="negotiation-strategy-content"></div>
                                </div>
                                
                                <!-- Competitive Landscape Card -->
                                <div class="card">
                                    <h3 class="card-title">🏆 Competitive Landscape</h3>
                                    <div id="competitive-landscape-content"></div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Analytics Page -->
                    <div id="analytics-page" class="page-content" style="display: none;">
                        <div class="card">
                            <h2 class="card-title">📊 Analytics Dashboard</h2>
                            <p class="card-subtitle">Coming soon - Advanced analytics and reporting features</p>
                        </div>
                    </div>
                    
                    <!-- About Page -->
                    <div id="about-page" class="page-content" style="display: none;">
                        <div class="card">
                            <h2 class="card-title">🚀 Why ProcureAI?</h2>
                            <p class="card-subtitle">Transform your procurement process with AI-powered intelligence</p>
                            
                            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: var(--space-lg); margin-top: var(--space-xl);">
                                <div style="background: var(--bg-tertiary); padding: var(--space-lg); border-radius: var(--radius-lg);">
                                    <h3 style="color: var(--text-primary); margin-bottom: var(--space-md); display: flex; align-items: center; gap: var(--space-sm);">⚡ Save Time</h3>
                                    <p style="color: var(--text-secondary); line-height: 1.6;">What takes hours of manual Google searches now takes minutes. Our AI agent automatically finds suppliers, analyzes market data, and provides insights.</p>
                                    <p style="color: var(--text-accent); font-weight: 600; margin-top: var(--space-sm);">From 4+ hours to 2 minutes</p>
                                </div>
                                
                                <div style="background: var(--bg-tertiary); padding: var(--space-lg); border-radius: var(--radius-lg);">
                                    <h3 style="color: var(--text-primary); margin-bottom: var(--space-md); display: flex; align-items: center; gap: var(--space-sm);">🎯 Better Results</h3>
                                    <p style="color: var(--text-secondary); line-height: 1.6;">Get structured supplier data with confidence scores, certifications, and market insights instead of random search results.</p>
                                    <p style="color: var(--text-accent); font-weight: 600; margin-top: var(--space-sm);">Structured data vs scattered results</p>
                                </div>
                                
                                <div style="background: var(--bg-tertiary); padding: var(--space-lg); border-radius: var(--radius-lg);">
                                    <h3 style="color: var(--text-primary); margin-bottom: var(--space-md); display: flex; align-items: center; gap: var(--space-sm);">💡 Smart Insights</h3>
                                    <p style="color: var(--text-secondary); line-height: 1.6;">Get market trends, price analysis, and negotiation strategies automatically generated from real-time data.</p>
                                    <p style="color: var(--text-accent); font-weight: 600; margin-top: var(--space-sm);">AI-powered market intelligence</p>
                                </div>
                                
                                <div style="background: var(--bg-tertiary); padding: var(--space-lg); border-radius: var(--radius-lg);">
                                    <h3 style="color: var(--text-primary); margin-bottom: var(--space-md); display: flex; align-items: center; gap: var(--space-sm);">🔄 Competitive Edge</h3>
                                    <p style="color: var(--text-secondary); line-height: 1.6;">Analyze competitor pricing, benchmark your quotes, and get negotiation strategies to secure better deals.</p>
                                    <p style="color: var(--text-accent); font-weight: 600; margin-top: var(--space-sm);">Data-driven procurement decisions</p>
                                </div>
                            </div>
                            
                            <div class="card" style="margin-top: var(--space-xl); background: var(--gradient-primary); color: white;">
                                <h3 style="color: white; margin-bottom: var(--space-md);">📝 Example Use Cases</h3>
                                <div style="display: grid; gap: var(--space-md);">
                                    <div style="background: rgba(255,255,255,0.1); padding: var(--space-md); border-radius: var(--radius-md);">
                                        <strong>"Industrial Steel Suppliers"</strong> → Get 10+ verified suppliers with pricing, certifications, and market trend analysis
                                    </div>
                                    <div style="background: rgba(255,255,255,0.1); padding: var(--space-md); border-radius: var(--radius-md);">
                                        <strong>"Office Furniture Quote Analysis"</strong> → Compare your $5,000 quote against market rates and get negotiation tips
                                    </div>
                                    <div style="background: rgba(255,255,255,0.1); padding: var(--space-md); border-radius: var(--radius-md);">
                                        <strong>"IT Services Procurement"</strong> → Find specialized vendors with confidence scores and detailed capability analysis
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </main>
        </div>
            
        
        <script>
            // Page Navigation
            function switchPage(pageId) {
                // Hide all pages
                const pages = document.querySelectorAll('.page-content');
                pages.forEach(page => {
                    page.style.display = 'none';
                });
                
                // Remove active class from all nav items
                const navItems = document.querySelectorAll('.nav-item');
                navItems.forEach(item => {
                    item.classList.remove('active');
                });
                
                // Show selected page
                const targetPage = document.getElementById(pageId + '-page');
                if (targetPage) {
                    targetPage.style.display = 'block';
                }
                
                // Add active class to clicked nav item
                event.target.closest('.nav-item').classList.add('active');
                
                // Update breadcrumb and page header
                const pageNames = {
                    'dashboard': 'Dashboard',
                    'supplier-discovery': 'Supplier Discovery',
                    'competitive-intelligence': 'Market Intelligence',
                    'analytics': 'Analytics',
                    'about': 'About'
                };
                
                const pageTitles = {
                    'dashboard': 'Procurement Intelligence Dashboard',
                    'supplier-discovery': 'Advanced Supplier Discovery',
                    'competitive-intelligence': 'Competitive Market Intelligence',
                    'analytics': 'Analytics & Reporting',
                    'about': 'About ProcureAI'
                };
                
                const pageSubtitles = {
                    'dashboard': 'AI-powered supplier discovery and competitive analysis',
                    'supplier-discovery': 'Find the best suppliers using our AI-powered agent',
                    'competitive-intelligence': 'Market positioning and competitive benchmarking',
                    'analytics': 'Advanced analytics and procurement insights',
                    'about': 'Learn why ProcureAI is better than manual Google searches'
                };
                
                document.getElementById('current-page').textContent = pageNames[pageId] || 'Dashboard';
                document.getElementById('page-title').textContent = pageTitles[pageId] || 'Procurement Intelligence Dashboard';
                document.getElementById('page-subtitle').textContent = pageSubtitles[pageId] || 'AI-powered supplier discovery and competitive analysis';
            }
            
            // Category Search with Dubai as default location
            function searchCategory(category) {
                switchPage('supplier-discovery');
                setTimeout(() => {
                    document.getElementById('query').value = category;
                    document.getElementById('location').value = 'Dubai';
                    document.getElementById('query').focus();
                }, 100);
            }
            
            // Quick Search Form
            document.getElementById('quickSearchForm').addEventListener('submit', function(e) {
                e.preventDefault();
                const query = document.getElementById('quick-search').value;
                if (query.trim()) {
                    switchPage('supplier-discovery');
                    setTimeout(() => {
                        document.getElementById('query').value = query;
                        document.getElementById('location').value = 'Dubai';
                        document.getElementById('procurementForm').dispatchEvent(new Event('submit'));
                    }, 100);
                }
            });
            
            // Add spinner styles
            const spinnerStyle = document.createElement('style');
            spinnerStyle.textContent = `
                .spinner {
                    width: 40px;
                    height: 40px;
                    border: 4px solid var(--border-primary);
                    border-top: 4px solid var(--primary-blue);
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                    margin: 0 auto;
                }
                
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
                
                .workflow-step {
                    padding: var(--space-md);
                    margin-bottom: var(--space-sm);
                    border-radius: var(--radius-lg);
                    background: #3f433f !important;
                    border-left: 4px solid var(--border-primary);
                    color: white !important;
                    transition: all var(--transition-fast);
                }
                
                .workflow-step.active {
                    background: #3f433f !important;
                    border-left-color: var(--warning-yellow);
                    color: white !important;
                }
                
                .workflow-step.completed {
                    background: #3f433f !important;
                    border-left-color: var(--success-green);
                    color: white !important;
                }
                
                .insight-title {
                    font-weight: 600;
                    color: #1a202c !important;
                    margin-bottom: var(--space-sm);
                }
                
                .insight-list {
                    list-style: none;
                    padding: 0;
                    color: #2d3748 !important;
                }
                
                .insight-list li {
                    padding: var(--space-xs) 0;
                    border-bottom: 1px solid var(--border-primary);
                    color: #2d3748 !important;
                }
                
                .insight-list li:last-child {
                    border-bottom: none;
                }
                
                .supplier-card {
                    background: var(--bg-card);
                    border: 1px solid var(--border-primary);
                    border-radius: var(--radius-lg);
                    padding: var(--space-lg);
                    margin-bottom: var(--space-md);
                    transition: all var(--transition-fast);
                }
                
                .supplier-card:hover {
                    border-color: var(--border-accent);
                    transform: translateY(-2px);
                }
                
                .supplier-name {
                    font-weight: 600;
                    color: var(--text-primary);
                    margin-bottom: var(--space-xs);
                    font-size: var(--font-size-lg);
                }
                
                .supplier-location {
                    color: var(--text-muted);
                    margin-bottom: var(--space-sm);
                }
                
                .supplier-description {
                    color: var(--text-secondary);
                    line-height: 1.5;
                    margin-bottom: var(--space-md);
                }
                
                .confidence-score {
                    display: inline-block;
                    padding: var(--space-xs) var(--space-sm);
                    border-radius: var(--radius-md);
                    font-size: var(--font-size-sm);
                    font-weight: 600;
                }
                
                .confidence-high {
                    background: var(--success-green);
                    color: white;
                }
                
                .confidence-medium {
                    background: var(--warning-yellow);
                    color: white;
                }
                
                .confidence-low {
                    background: var(--danger-red);
                    color: white;
                }
                
                .cert-badge {
                    display: inline-block;
                    background: var(--primary-blue);
                    color: white;
                    padding: var(--space-xs) var(--space-sm);
                    border-radius: var(--radius-sm);
                    font-size: var(--font-size-xs);
                    margin-right: var(--space-xs);
                    margin-bottom: var(--space-xs);
                }
            `;
            document.head.appendChild(spinnerStyle);
            
            // Add responsive styles
            const responsiveStyle = document.createElement('style');
            responsiveStyle.textContent = `
                @media (max-width: 768px) {
                    .sidebar {
                        transform: translateX(-100%);
                        width: 280px;
                    }
                    
                    .sidebar.mobile-open {
                        transform: translateX(0);
                    }
                    
                    .main-content {
                        margin-left: 0;
                    }
                    
                    .main-content.sidebar-collapsed {
                        margin-left: 0;
                    }
                    
                    .categories-grid {
                        grid-template-columns: 1fr;
                    }
                    
                    .suppliers-grid {
                        grid-template-columns: 1fr;
                    }
                    
                    .mobile-menu-btn {
                        display: block;
                    }
                    
                    .sidebar-toggle {
                        display: none;
                    }
                    
                    .content-header {
                        padding-left: 60px;
                    }
                    
                    .search-form {
                        padding: var(--space-md);
                    }
                    
                    .form-group {
                        margin-bottom: var(--space-md);
                    }
                    
                    .category-card {
                        padding: var(--space-md);
                    }
                }
            `;
            document.head.appendChild(responsiveStyle);
            
            // Sidebar functionality
            function toggleSidebar() {
                const sidebar = document.querySelector('.sidebar');
                const mainContent = document.querySelector('.main-content');
                const toggleIcon = document.getElementById('sidebar-toggle-icon');
                
                sidebar.classList.toggle('collapsed');
                mainContent.classList.toggle('sidebar-collapsed');
                
                if (sidebar.classList.contains('collapsed')) {
                    toggleIcon.textContent = '→';
                } else {
                    toggleIcon.textContent = '←';
                }
            }
            
            function toggleMobileSidebar() {
                const sidebar = document.querySelector('.sidebar');
                sidebar.classList.toggle('mobile-open');
            }
            
            // Close mobile sidebar when clicking outside
            document.addEventListener('click', function(e) {
                const sidebar = document.querySelector('.sidebar');
                const menuBtn = document.querySelector('.mobile-menu-btn');
                
                if (window.innerWidth <= 768 && 
                    !sidebar.contains(e.target) && 
                    !menuBtn.contains(e.target) && 
                    sidebar.classList.contains('mobile-open')) {
                    sidebar.classList.remove('mobile-open');
                }
            });
            
            // Handle window resize
            window.addEventListener('resize', function() {
                const sidebar = document.querySelector('.sidebar');
                if (window.innerWidth > 768) {
                    sidebar.classList.remove('mobile-open');
                }
            });
            
            // Global variable to store current results for export
            let currentAnalysisData = null;
            
            // Excel Export Functionality
            function exportToExcel() {
                if (!currentAnalysisData) {
                    alert('No data to export. Please run an analysis first.');
                    return;
                }
                
                try {
                    // Create workbook and worksheet
                    const wb = XLSX.utils.book_new();
                    
                    // Summary sheet
                    const summaryData = [
                        ['Procurement Intelligence Report'],
                        ['Generated on:', new Date().toLocaleString()],
                        ['Query:', currentAnalysisData.query || 'N/A'],
                        ['Location:', currentAnalysisData.location || 'Global'],
                        ['Processing Time:', currentAnalysisData.processing_time.toFixed(2) + ' seconds'],
                        ['Suppliers Found:', currentAnalysisData.suppliers.length],
                        [''],
                        ['Analysis Summary:'],
                        [currentAnalysisData.summary]
                    ];
                    
                    const summaryWs = XLSX.utils.aoa_to_sheet(summaryData);
                    XLSX.utils.book_append_sheet(wb, summaryWs, 'Summary');
                    
                    // Suppliers sheet
                    const suppliersData = [
                        ['Supplier Name', 'Location', 'Description', 'Confidence Score', 'Rating', 'Certifications', 'Website']
                    ];
                    
                    currentAnalysisData.suppliers.forEach(supplier => {
                        suppliersData.push([
                            supplier.name || 'N/A',
                            supplier.location || 'N/A',
                            supplier.description || 'N/A',
                            (supplier.confidence_score * 100).toFixed(0) + '%',
                            supplier.rating ? supplier.rating.toFixed(1) : 'N/A',
                            supplier.certifications.join(', ') || 'None',
                            supplier.website || 'N/A'
                        ]);
                    });
                    
                    const suppliersWs = XLSX.utils.aoa_to_sheet(suppliersData);
                    XLSX.utils.book_append_sheet(wb, suppliersWs, 'Suppliers');
                    
                    // Market Insights sheet
                    const marketData = [
                        ['Market Insights'],
                        [''],
                        ['Price Trend:', currentAnalysisData.market_insights.price_trend.toUpperCase()],
                        [''],
                        ['Key Factors:']
                    ];
                    
                    currentAnalysisData.market_insights.key_factors.forEach(factor => {
                        marketData.push(['• ' + factor]);
                    });
                    
                    marketData.push([''], ['Recommendations:']);
                    
                    currentAnalysisData.market_insights.recommendations.forEach(rec => {
                        marketData.push(['• ' + rec]);
                    });
                    
                    const marketWs = XLSX.utils.aoa_to_sheet(marketData);
                    XLSX.utils.book_append_sheet(wb, marketWs, 'Market Insights');
                    
                    // Export file
                    const filename = `ProcureAI_Analysis_${new Date().toISOString().split('T')[0]}.xlsx`;
                    XLSX.writeFile(wb, filename);
                    
                    // Show success message
                    alert('✅ Excel report exported successfully!');
                    
                } catch (error) {
                    console.error('Export error:', error);
                    alert('❌ Export failed. Please try again.');
                }
            }
            
            // Add SheetJS library for Excel export
            const sheetJSScript = document.createElement('script');
            sheetJSScript.src = 'https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js';
            document.head.appendChild(sheetJSScript);
            
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
            
            // Procurement Form Event Listener
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
                
                const submitButton = document.querySelector('#procurementForm button[type="submit"]');
                submitButton.disabled = true;
                
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
                    submitButton.disabled = false;
                }
            });
            
            function displayResults(data) {
                // Store data for export
                currentAnalysisData = {
                    ...data,
                    query: document.getElementById('query').value,
                    location: document.getElementById('location').value
                };
                
                // Hide loading and workflow status
                document.getElementById('workflowStatus').style.display = 'none';
                document.getElementById('loading').style.display = 'none';
                
                // Show summary
                document.getElementById('summary').innerHTML = `
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--space-md);">
                        <h3 style="color: #1a202c !important; margin: 0;">📋 Agent Analysis Summary</h3>
                        <button id="exportExcel" class="btn-secondary" onclick="exportToExcel()">
                            📊 Export to Excel
                        </button>
                    </div>
                    <p style="color: #2d3748 !important; margin-bottom: var(--space-md);">${data.summary}</p>
                    <p style="color: #2d3748 !important;"><strong>⚡ Processing Time:</strong> ${data.processing_time.toFixed(2)} seconds</p>
                    <p style="color: #2d3748 !important;"><strong>🏢 Suppliers Found:</strong> ${data.suppliers.length}</p>
                `;
                
                // Show suppliers
                const suppliersGrid = document.getElementById('suppliersGrid');
                suppliersGrid.innerHTML = '';
                
                if (data.suppliers.length === 0) {
                    suppliersGrid.innerHTML = '<p style="color: var(--text-muted);">No suppliers found. Try a different search term.</p>';
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
                                ${supplier.rating ? `<div style="margin-top: var(--space-sm); color: var(--text-secondary);">⭐ Rating: ${supplier.rating.toFixed(1)}</div>` : ''}
                                ${certifications ? `<div class="certifications" style="margin-top: var(--space-sm);">${certifications}</div>` : ''}
                                ${supplier.website ? `<div style="margin-top: var(--space-sm);"><a href="${supplier.website}" target="_blank" style="color: var(--primary-blue); text-decoration: none;">🔗 Visit Website</a></div>` : ''}
                            </div>
                        `;
                        suppliersGrid.innerHTML += supplierCard;
                    });
                }
                
                // Show market insights
                document.getElementById('priceTrend').innerHTML = `<strong style="color: #1a202c !important;">📈 ${data.market_insights.price_trend.toUpperCase()}</strong>`;
                
                const keyFactors = document.getElementById('keyFactors');
                keyFactors.innerHTML = '';
                data.market_insights.key_factors.forEach(factor => {
                    keyFactors.innerHTML += `<li style="color: #2d3748 !important;">• ${factor}</li>`;
                });
                
                const recommendations = document.getElementById('recommendations');
                recommendations.innerHTML = '';
                data.market_insights.recommendations.forEach(rec => {
                    recommendations.innerHTML += `<li style="color: #2d3748 !important;">💡 ${rec}</li>`;
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
                        <div style="margin-bottom: var(--space-lg);">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--space-md);">
                                <span style="color: var(--text-secondary);">Market Average:</span>
                                <span style="color: var(--text-primary); font-size: var(--font-size-xl); font-weight: 600;">$${data.market_average_price}</span>
                            </div>
                    `;
                    
                    if (data.price_variance) {
                        const varianceColor = data.price_variance > 0 ? 'var(--danger-red)' : 'var(--success-green)';
                        positionHtml += `
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <span style="color: var(--text-secondary);">Variance:</span>
                                <span style="color: ${varianceColor}; font-size: var(--font-size-lg); font-weight: 600;">${data.price_variance > 0 ? '+' : ''}${data.price_variance.toFixed(1)}%</span>
                            </div>
                        `;
                    }
                    positionHtml += '</div>';
                }
                
                if (data.percentile_ranking) {
                    positionHtml += `
                        <div style="margin-bottom: var(--space-lg);">
                            <div style="display: flex; justify-content: space-between; margin-bottom: var(--space-sm); font-size: var(--font-size-sm); color: var(--text-muted);">
                                <span>25th</span><span>50th</span><span>75th</span><span>90th</span>
                            </div>
                            <div style="height: 12px; background: var(--bg-tertiary); border-radius: var(--radius-md); position: relative; overflow: hidden;">
                                <div style="height: 100%; background: var(--gradient-primary); border-radius: var(--radius-md); width: ${data.percentile_ranking}%;"></div>
                            </div>
                            <p style="text-align: center; margin-top: var(--space-sm); font-size: var(--font-size-sm); color: var(--text-muted);">${data.percentile_ranking}th percentile</p>
                        </div>
                    `;
                }
                
                marketPositionContent.innerHTML = positionHtml || '<p style="color: var(--text-muted);">Limited market data available</p>';
                
                // Negotiation Strategy
                const negotiationContent = document.getElementById('negotiation-strategy-content');
                let negotiationHtml = '';
                
                if (data.negotiation_strategy.suggested_counter_offer) {
                    negotiationHtml += `
                        <div style="padding: var(--space-lg); border-radius: var(--radius-lg); background: var(--gradient-primary); margin-bottom: var(--space-lg);">
                            <h4 style="font-weight: 600; color: white; margin-bottom: var(--space-sm);">💬 Suggested Counter-offer</h4>
                            <p style="color: white; font-size: var(--font-size-xl); font-weight: 700;">$${data.negotiation_strategy.suggested_counter_offer}</p>
                        </div>
                    `;
                }
                
                if (data.negotiation_strategy.leverage_points.length > 0) {
                    negotiationHtml += `
                        <div style="margin-bottom: var(--space-lg);">
                            <h4 style="font-weight: 600; color: var(--text-primary); margin-bottom: var(--space-md);">📋 Leverage Points:</h4>
                            <ul style="list-style: none; padding: 0; margin: 0;">
                    `;
                    
                    data.negotiation_strategy.leverage_points.forEach(point => {
                        negotiationHtml += `
                            <li style="display: flex; align-items: flex-start; gap: var(--space-sm); margin-bottom: var(--space-sm);">
                                <span style="color: var(--success-green); font-weight: 600;">✓</span>
                                <span style="color: var(--text-secondary);">${point}</span>
                            </li>
                        `;
                    });
                    
                    negotiationHtml += '</ul></div>';
                }
                
                negotiationContent.innerHTML = negotiationHtml || '<p style="color: var(--text-muted);">Negotiation strategy analysis in progress</p>';
                
                // Competitive Landscape
                const competitiveContent = document.getElementById('competitive-landscape-content');
                let competitiveHtml = '';
                
                if (data.key_competitors.length > 0) {
                    data.key_competitors.forEach(competitor => {
                        competitiveHtml += `
                            <div style="display: flex; justify-content: space-between; align-items: center; padding: var(--space-md); border-radius: var(--radius-lg); background: var(--bg-tertiary); margin-bottom: var(--space-md);">
                                <div>
                                    <p style="font-weight: 600; color: var(--text-primary); margin-bottom: var(--space-xs);">${competitor.name}</p>
                                    <p style="font-size: var(--font-size-sm); color: var(--text-muted); text-transform: capitalize;">${competitor.market_position}</p>
                                </div>
                                ${competitor.price ? `<span style="color: var(--primary-blue); font-weight: 600;">$${competitor.price}</span>` : ''}
                            </div>
                        `;
                    });
                } else {
                    competitiveHtml = '<p style="color: var(--text-muted);">Competitive landscape analysis in progress</p>';
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