// Global variables
let workflowSteps = ['step1', 'step2', 'step3', 'step4'];
let currentStep = 0;
let currentAnalysisData = null;

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
    if (event && event.target) {
        event.target.closest('.nav-item').classList.add('active');
    }
    
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

// Workflow Status Functions
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

// Initialize page on load
document.addEventListener('DOMContentLoaded', function() {
    // Show dashboard by default
    switchPage('dashboard');
});