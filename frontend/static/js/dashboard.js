// Global variables
let workflowSteps = ['step1', 'step2', 'step3', 'step4'];
let currentStep = 0;
let currentAnalysisData = null;

// Clear/Refresh Functions
function clearSupplierResults() {
    // Hide results
    document.getElementById('results').style.display = 'none';
    document.getElementById('workflowStatus').style.display = 'none';
    document.getElementById('loading').style.display = 'none';
    
    // Clear form
    document.getElementById('procurementForm').reset();
    
    // Clear results content
    document.getElementById('summary').innerHTML = '';
    document.getElementById('suppliersGrid').innerHTML = '';
    document.getElementById('priceTrend').innerHTML = '';
    document.getElementById('keyFactors').innerHTML = '';
    document.getElementById('recommendations').innerHTML = '';
    
    // Reset workflow steps
    const steps = ['step1', 'step2', 'step3', 'step4'];
    steps.forEach(step => {
        document.getElementById(step).className = 'workflow-step';
    });
    currentStep = 0;
    currentAnalysisData = null;
    
    // Focus on search field
    document.getElementById('query').focus();
}

function clearCompetitiveResults() {
    // Hide results
    document.getElementById('competitive-results').style.display = 'none';
    document.getElementById('competitive-loading').style.display = 'none';
    
    // Clear form
    document.getElementById('competitiveForm').reset();
    
    // Clear results content
    document.getElementById('market-position-content').innerHTML = '';
    document.getElementById('negotiation-strategy-content').innerHTML = '';
    document.getElementById('competitive-landscape-content').innerHTML = '';
    
    // Clear any additional intelligence cards
    const historicalTrendsCard = document.getElementById('historical-trends-card');
    const timingIntelligenceCard = document.getElementById('timing-intelligence-card');
    if (historicalTrendsCard) historicalTrendsCard.remove();
    if (timingIntelligenceCard) timingIntelligenceCard.remove();
    
    // Focus on product field
    document.querySelector('input[name="product"]').focus();
}

function exportCompetitiveResults() {
    // Get current competitive analysis data
    const productInput = document.querySelector('input[name="product"]').value;
    
    if (!productInput) {
        alert('No analysis to export. Please run a competitive analysis first.');
        return;
    }
    
    // Create a simple text export for now
    const timestamp = new Date().toISOString();
    const filename = `competitive-analysis-${productInput.replace(/\s+/g, '-')}-${timestamp.split('T')[0]}.txt`;
    
    let exportContent = `Competitive Analysis Report\n`;
    exportContent += `Product: ${productInput}\n`;
    exportContent += `Generated: ${new Date().toLocaleString()}\n`;
    exportContent += `\n--- Market Position ---\n`;
    exportContent += document.getElementById('market-position-content').innerText + '\n';
    exportContent += `\n--- Negotiation Strategy ---\n`;
    exportContent += document.getElementById('negotiation-strategy-content').innerText + '\n';
    exportContent += `\n--- Competitive Landscape ---\n`;
    exportContent += document.getElementById('competitive-landscape-content').innerText + '\n';
    
    const blob = new Blob([exportContent], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// Page Navigation
function switchPage(pageId, clickEvent) {
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
    if (clickEvent && clickEvent.target && typeof clickEvent.target.closest === 'function') {
        const navItem = clickEvent.target.closest('.nav-item');
        if (navItem) {
            navItem.classList.add('active');
        }
    }
    
    // Update breadcrumb and page header
    const pageNames = {
        'dashboard': 'Dashboard',
        'supplier-discovery': 'Supplier Discovery',
        'competitive-intelligence': 'Market Intelligence',
        'rfp-generation': 'RFP Generation',
        'analytics': 'Analytics',
        'about': 'About'
    };
    
    const pageTitles = {
        'dashboard': 'Procurement Intelligence Dashboard',
        'supplier-discovery': 'Advanced Supplier Discovery',
        'competitive-intelligence': 'Competitive Market Intelligence',
        'rfp-generation': 'AI-Powered RFP Generation',
        'analytics': 'Analytics & Reporting',
        'about': 'About ProcureAI'
    };
    
    const pageSubtitles = {
        'dashboard': 'AI-powered supplier discovery and competitive analysis',
        'supplier-discovery': 'Find the best suppliers using our AI-powered agent',
        'competitive-intelligence': 'Market positioning and competitive benchmarking',
        'rfp-generation': 'Generate professional RFP, RFI, and RFQ documents using AI',
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
            <h3 style="color: var(--text-primary) !important; margin: 0;">📋 Agent Analysis Summary</h3>
            <button id="exportExcel" class="btn-secondary" onclick="exportToExcel()">
                📊 Export to Excel
            </button>
        </div>
        <p style="color: var(--text-primary) !important; margin-bottom: var(--space-md);">${data.summary}</p>
        <p style="color: var(--text-primary) !important;"><strong>⚡ Processing Time:</strong> ${data.processing_time.toFixed(2)} seconds</p>
        <p style="color: var(--text-primary) !important;"><strong>🏢 Suppliers Found:</strong> ${data.suppliers.length}</p>
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
            
            // Registration status removed (OpenCorporates integration removed)
            
            // Company logo
            const logoHtml = supplier.logo_url ? 
                `<img src="${supplier.logo_url}" alt="${supplier.name} logo" style="width: 32px; height: 32px; border-radius: 4px; object-fit: contain; margin-right: var(--space-sm);" onerror="this.style.display='none'">` : 
                `<div style="width: 32px; height: 32px; background: var(--gradient-primary); border-radius: 4px; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; margin-right: var(--space-sm); font-size: 14px;">${supplier.name.charAt(0)}</div>`;
            
            // Financial health badge
            let financialBadge = '';
            if (supplier.financial_data) {
                const health = supplier.financial_data.financial_health_score || 50;
                const healthColor = health >= 70 ? '#28a745' : health >= 50 ? '#ffc107' : '#dc3545';
                const marketCap = supplier.financial_data.market_cap;
                const sector = supplier.financial_data.sector;
                
                financialBadge = `
                    <div style="margin-top: var(--space-sm); padding: var(--space-xs); background: rgba(40, 167, 69, 0.1); border-radius: var(--radius-sm); border-left: 3px solid ${healthColor};">
                        <div style="font-size: var(--font-size-sm); font-weight: 600; color: ${healthColor};">
                            💰 Public Company (${supplier.financial_data.ticker})
                        </div>
                        <div style="font-size: var(--font-size-xs); color: var(--text-muted); margin-top: 2px;">
                            ${sector || 'Unknown Sector'} • Health: ${health}/100
                            ${marketCap ? ` • $${(marketCap / 1000000000).toFixed(1)}B` : ''}
                        </div>
                    </div>
                `;
            }
            
            // Risk assessment badge
            let riskBadge = '';
            if (supplier.risk_assessment) {
                const risk = supplier.risk_assessment.risk_score || 50;
                const riskColor = risk <= 30 ? '#28a745' : risk <= 60 ? '#ffc107' : '#dc3545';
                const riskLabel = risk <= 30 ? 'Low Risk' : risk <= 60 ? 'Medium Risk' : 'High Risk';
                const domainAge = supplier.risk_assessment.domain_age_years;
                
                riskBadge = `
                    <div style="margin-top: var(--space-sm); padding: var(--space-xs); background: rgba(40, 167, 69, 0.1); border-radius: var(--radius-sm); border-left: 3px solid ${riskColor};">
                        <div style="font-size: var(--font-size-sm); font-weight: 600; color: ${riskColor};">
                            ⚠️ ${riskLabel} (${risk}/100)
                        </div>
                        ${domainAge ? `<div style="font-size: var(--font-size-xs); color: var(--text-muted); margin-top: 2px;">Domain: ${domainAge} years old</div>` : ''}
                    </div>
                `;
            }
            
            // Web intelligence badges
            let webIntelBadges = '';
            if (supplier.web_intelligence) {
                const intel = supplier.web_intelligence;
                let badges = [];
                
                if (intel.founded_year) {
                    const yearsActive = 2025 - intel.founded_year;
                    badges.push(`<span class="intel-badge" style="background: #e3f2fd; color: #1976d2;">📅 Est. ${intel.founded_year} (${yearsActive}y)</span>`);
                }
                
                if (intel.team_size_indicators && intel.team_size_indicators.length > 0) {
                    const maxSize = Math.max(...intel.team_size_indicators);
                    badges.push(`<span class="intel-badge" style="background: #f3e5f5; color: #7b1fa2;">👥 ${maxSize}+ employees</span>`);
                }
                
                if (intel.social_media && Object.keys(intel.social_media).length > 0) {
                    const socialCount = Object.keys(intel.social_media).length;
                    badges.push(`<span class="intel-badge" style="background: #e8f5e8; color: #388e3c;">📱 ${socialCount} social media</span>`);
                }
                
                if (intel.technology_stack && intel.technology_stack.length > 0) {
                    badges.push(`<span class="intel-badge" style="background: #fff3e0; color: #f57c00;">⚙️ ${intel.technology_stack.length} tech stack</span>`);
                }
                
                if (badges.length > 0) {
                    webIntelBadges = `<div style="margin-top: var(--space-sm); display: flex; flex-wrap: wrap; gap: var(--space-xs);">${badges.join('')}</div>`;
                }
            }
            
            const supplierCard = `
                <div class="supplier-card" style="position: relative; overflow: visible;">
                    <div style="display: flex; align-items: center; margin-bottom: var(--space-sm);">
                        ${logoHtml}
                        <div>
                            <div class="supplier-name">${supplier.name}</div>
                            <div class="supplier-location">📍 ${supplier.location}</div>
                        </div>
                    </div>
                    
                    <div class="supplier-description">${supplier.description.substring(0, 150)}...</div>
                    
                    <div class="confidence-score ${confidenceClass}" style="margin-top: var(--space-sm);">
                        Confidence: ${(supplier.confidence_score * 100).toFixed(0)}% 
                        ${supplier.confidence_score >= 0.8 ? '🟢' : supplier.confidence_score >= 0.6 ? '🟡' : '🔴'}
                    </div>
                    
                    ${supplier.rating ? `<div style="margin-top: var(--space-sm); color: var(--text-secondary);">⭐ Rating: ${supplier.rating.toFixed(1)}</div>` : ''}
                    ${certifications ? `<div class="certifications" style="margin-top: var(--space-sm);">${certifications}</div>` : ''}
                    ${webIntelBadges}
                    ${financialBadge}
                    ${riskBadge}
                    
                    ${supplier.website ? `<div style="margin-top: var(--space-sm);"><a href="${supplier.website}" target="_blank" style="color: var(--primary-blue); text-decoration: none;">🔗 Visit Website</a></div>` : ''}
                </div>
            `;
            suppliersGrid.innerHTML += supplierCard;
        });
    }
    
    // Show market insights
    document.getElementById('priceTrend').innerHTML = `<strong style="color: var(--text-primary) !important;">📈 ${data.market_insights.price_trend.toUpperCase()}</strong>`;
    
    const keyFactors = document.getElementById('keyFactors');
    keyFactors.innerHTML = '';
    data.market_insights.key_factors.forEach(factor => {
        keyFactors.innerHTML += `<li style="color: var(--text-primary) !important;">• ${factor}</li>`;
    });
    
    const recommendations = document.getElementById('recommendations');
    recommendations.innerHTML = '';
    data.market_insights.recommendations.forEach(rec => {
        recommendations.innerHTML += `<li style="color: var(--text-primary) !important;">💡 ${rec}</li>`;
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
    
    // Historical Trends Intelligence (New)
    if (data.historical_trends) {
        renderHistoricalTrends(data.historical_trends);
    }
    
    // Market Timing Intelligence (New)
    if (data.timing_intelligence) {
        renderTimingIntelligence(data.timing_intelligence);
    }
    
    // Show results
    document.getElementById('competitive-results').style.display = 'block';
    document.getElementById('competitive-results').scrollIntoView({ behavior: 'smooth' });
}

// Historical Trends Intelligence Rendering
function renderHistoricalTrends(trendsData) {
    // Create or find historical trends container
    let trendsContainer = document.getElementById('historical-trends-container');
    if (!trendsContainer) {
        // Create new container after competitive results
        trendsContainer = document.createElement('div');
        trendsContainer.id = 'historical-trends-container';
        trendsContainer.style.marginTop = 'var(--space-xl)';
        
        const competitiveResults = document.getElementById('competitive-results');
        competitiveResults.appendChild(trendsContainer);
    }
    
    let trendsHtml = `
        <div class="card">
            <div class="card-header">
                <h3 class="card-title">📈 Historical Trend Intelligence</h3>
            </div>
            <div style="padding: var(--space-lg);">
                <!-- Price History Chart -->
                <div style="margin-bottom: var(--space-xl);">
                    <h4 style="font-weight: 600; color: var(--text-primary); margin-bottom: var(--space-md);">📊 6-Month Price History</h4>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: var(--space-md); margin-bottom: var(--space-lg);">
    `;
    
    // Render price history points
    trendsData.price_history.forEach(point => {
        const hasEvents = point.market_events && point.market_events.length > 0;
        trendsHtml += `
            <div style="text-align: center; padding: var(--space-md); border-radius: var(--radius-lg); background: var(--bg-tertiary);">
                <div style="font-size: var(--font-size-xs); color: var(--text-muted); margin-bottom: var(--space-xs);">${point.month}</div>
                <div style="font-size: var(--font-size-lg); font-weight: 600; color: var(--text-primary);">$${point.price.toLocaleString()}</div>
                ${hasEvents ? `<div style="font-size: var(--font-size-xs); color: var(--warning-yellow); margin-top: var(--space-xs);">📌 Event</div>` : ''}
            </div>
        `;
    });
    
    trendsHtml += `
                    </div>
                </div>
                
                <!-- Trend Analysis -->
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: var(--space-lg); margin-bottom: var(--space-lg);">
                    <div style="padding: var(--space-md); border-radius: var(--radius-lg); background: var(--bg-tertiary);">
                        <div style="font-size: var(--font-size-sm); color: var(--text-muted); margin-bottom: var(--space-xs);">Price Direction</div>
                        <div style="font-size: var(--font-size-lg); font-weight: 600; color: var(--text-primary); text-transform: capitalize;">${getTrendIcon(trendsData.trend_analysis.direction)} ${trendsData.trend_analysis.direction}</div>
                    </div>
                    <div style="padding: var(--space-md); border-radius: var(--radius-lg); background: var(--bg-tertiary);">
                        <div style="font-size: var(--font-size-sm); color: var(--text-muted); margin-bottom: var(--space-xs);">Volatility</div>
                        <div style="font-size: var(--font-size-lg); font-weight: 600; color: ${getVolatilityColor(trendsData.trend_analysis.volatility)}; text-transform: capitalize;">${trendsData.trend_analysis.volatility}</div>
                    </div>
                    <div style="padding: var(--space-md); border-radius: var(--radius-lg); background: var(--bg-tertiary);">
                        <div style="font-size: var(--font-size-sm); color: var(--text-muted); margin-bottom: var(--space-xs);">Current Position</div>
                        <div style="font-size: var(--font-size-base); font-weight: 600; color: var(--text-primary);">${trendsData.trend_analysis.current_position}</div>
                    </div>
                </div>
                
                <!-- Seasonal Pattern -->
                <div style="margin-bottom: var(--space-lg);">
                    <h4 style="font-weight: 600; color: var(--text-primary); margin-bottom: var(--space-md);">🗓️ Seasonal Pattern</h4>
                    <p style="color: var(--text-secondary); padding: var(--space-md); border-radius: var(--radius-lg); background: var(--bg-tertiary);">${trendsData.trend_analysis.seasonal_pattern}</p>
                </div>
                
                <!-- Key Insights -->
                <div>
                    <h4 style="font-weight: 600; color: var(--text-primary); margin-bottom: var(--space-md);">💡 Historical Insights</h4>
                    <ul style="list-style: none; padding: 0; margin: 0;">
    `;
    
    trendsData.insights.forEach(insight => {
        trendsHtml += `
            <li style="display: flex; align-items: flex-start; gap: var(--space-sm); margin-bottom: var(--space-sm); padding: var(--space-sm); border-radius: var(--radius-md); background: var(--bg-tertiary);">
                <span style="color: var(--primary-blue); font-weight: 600;">📊</span>
                <span style="color: var(--text-secondary);">${insight}</span>
            </li>
        `;
    });
    
    trendsHtml += `
                    </ul>
                </div>
            </div>
        </div>
    `;
    
    trendsContainer.innerHTML = trendsHtml;
}

// Market Timing Intelligence Rendering
function renderTimingIntelligence(timingData) {
    // Create or find timing intelligence container
    let timingContainer = document.getElementById('timing-intelligence-container');
    if (!timingContainer) {
        // Create new container after historical trends
        timingContainer = document.createElement('div');
        timingContainer.id = 'timing-intelligence-container';
        timingContainer.style.marginTop = 'var(--space-xl)';
        
        const competitiveResults = document.getElementById('competitive-results');
        competitiveResults.appendChild(timingContainer);
    }
    
    const urgencyColor = getUrgencyColor(timingData.urgency_level);
    const recommendationIcon = getRecommendationIcon(timingData.recommendation);
    
    let timingHtml = `
        <div class="card">
            <div class="card-header">
                <h3 class="card-title">⏰ Market Timing Intelligence</h3>
            </div>
            <div style="padding: var(--space-lg);">
                <!-- Primary Recommendation -->
                <div style="padding: var(--space-xl); border-radius: var(--radius-xl); background: ${urgencyColor}; margin-bottom: var(--space-xl); text-align: center;">
                    <div style="font-size: var(--font-size-3xl); margin-bottom: var(--space-md);">${recommendationIcon}</div>
                    <h3 style="font-weight: 700; color: white; margin-bottom: var(--space-sm); font-size: var(--font-size-2xl);">${formatRecommendation(timingData.recommendation)}</h3>
                    <p style="color: rgba(255,255,255,0.9); font-size: var(--font-size-lg);">Urgency Level: ${timingData.urgency_level}</p>
                </div>
                
                <!-- Price Forecasts -->
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: var(--space-lg); margin-bottom: var(--space-xl);">
                    <div style="padding: var(--space-lg); border-radius: var(--radius-lg); background: var(--bg-tertiary);">
                        <h4 style="font-weight: 600; color: var(--text-primary); margin-bottom: var(--space-md);">📅 30-Day Forecast</h4>
                        <div style="display: flex; align-items: center; gap: var(--space-md);">
                            <span style="font-size: var(--font-size-2xl);">${getDirectionIcon(timingData.price_forecast['30_days'].direction)}</span>
                            <div>
                                <div style="font-size: var(--font-size-lg); font-weight: 600; color: var(--text-primary); text-transform: capitalize;">${timingData.price_forecast['30_days'].direction}</div>
                                <div style="font-size: var(--font-size-sm); color: var(--text-muted);">${timingData.price_forecast['30_days'].range}</div>
                            </div>
                        </div>
                    </div>
                    
                    <div style="padding: var(--space-lg); border-radius: var(--radius-lg); background: var(--bg-tertiary);">
                        <h4 style="font-weight: 600; color: var(--text-primary); margin-bottom: var(--space-md);">📅 60-Day Forecast</h4>
                        <div style="display: flex; align-items: center; gap: var(--space-md);">
                            <span style="font-size: var(--font-size-2xl);">${getDirectionIcon(timingData.price_forecast['60_days'].direction)}</span>
                            <div>
                                <div style="font-size: var(--font-size-lg); font-weight: 600; color: var(--text-primary); text-transform: capitalize;">${timingData.price_forecast['60_days'].direction}</div>
                                <div style="font-size: var(--font-size-sm); color: var(--text-muted);">${timingData.price_forecast['60_days'].range}</div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Optimal Window -->
                <div style="margin-bottom: var(--space-xl);">
                    <h4 style="font-weight: 600; color: var(--text-primary); margin-bottom: var(--space-md);">🎯 Optimal Purchase Window</h4>
                    <div style="padding: var(--space-lg); border-radius: var(--radius-lg); background: var(--bg-tertiary);">
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: var(--space-md); margin-bottom: var(--space-md);">
                            <div>
                                <div style="font-size: var(--font-size-sm); color: var(--text-muted);">Start Date</div>
                                <div style="font-size: var(--font-size-base); font-weight: 600; color: var(--text-primary);">${timingData.optimal_window.start_date}</div>
                            </div>
                            <div>
                                <div style="font-size: var(--font-size-sm); color: var(--text-muted);">End Date</div>
                                <div style="font-size: var(--font-size-base); font-weight: 600; color: var(--text-primary);">${timingData.optimal_window.end_date}</div>
                            </div>
                        </div>
                        <p style="color: var(--text-secondary); font-style: italic;">${timingData.optimal_window.reasoning}</p>
                    </div>
                </div>
                
                <!-- Savings Opportunity -->
                <div>
                    <h4 style="font-weight: 600; color: var(--text-primary); margin-bottom: var(--space-md);">💰 Savings Opportunity</h4>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: var(--space-md);">
                        <div style="padding: var(--space-md); border-radius: var(--radius-lg); background: var(--gradient-success); text-align: center;">
                            <div style="color: white; font-size: var(--font-size-sm); margin-bottom: var(--space-xs);">Per Unit Savings</div>
                            <div style="color: white; font-size: var(--font-size-xl); font-weight: 700;">${timingData.savings_opportunity.amount_per_unit}</div>
                        </div>
                        <div style="padding: var(--space-md); border-radius: var(--radius-lg); background: var(--gradient-success); text-align: center;">
                            <div style="color: white; font-size: var(--font-size-sm); margin-bottom: var(--space-xs);">Total Potential</div>
                            <div style="color: white; font-size: var(--font-size-xl); font-weight: 700;">${timingData.savings_opportunity.total_potential}</div>
                        </div>
                    </div>
                    <div style="margin-top: var(--space-md); padding: var(--space-md); border-radius: var(--radius-lg); background: var(--bg-tertiary);">
                        <div style="font-size: var(--font-size-sm); color: var(--text-muted); margin-bottom: var(--space-xs);">Risk of Waiting</div>
                        <p style="color: var(--text-secondary);">${timingData.savings_opportunity.risk_of_waiting}</p>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    timingContainer.innerHTML = timingHtml;
}

// Helper functions for styling and icons
function getTrendIcon(direction) {
    switch(direction) {
        case 'upward': return '📈';
        case 'downward': return '📉';
        case 'stable': return '➡️';
        default: return '📊';
    }
}

function getVolatilityColor(volatility) {
    switch(volatility) {
        case 'high': return 'var(--danger-red)';
        case 'medium': return 'var(--warning-yellow)';
        case 'low': return 'var(--success-green)';
        default: return 'var(--text-primary)';
    }
}

function getUrgencyColor(urgency) {
    switch(urgency) {
        case 'HIGH': return 'var(--gradient-primary)';
        case 'MEDIUM': return 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)';
        case 'LOW': return 'var(--gradient-success)';
        default: return 'var(--bg-tertiary)';
    }
}

function getRecommendationIcon(recommendation) {
    switch(recommendation) {
        case 'BUY_NOW': return '🚀';
        case 'WAIT': return '⏳';
        case 'MONITOR': return '👀';
        default: return '📊';
    }
}

function formatRecommendation(recommendation) {
    return recommendation.replace('_', ' ');
}

function getDirectionIcon(direction) {
    switch(direction) {
        case 'up': return '📈';
        case 'down': return '📉';
        case 'stable': return '➡️';
        default: return '📊';
    }
}

// RFP Generation Functions
let currentRFPData = null;

// Initialize RFP page event listeners
function initializeRFPGeneration() {
    // Add requirement management
    const addReqBtn = document.getElementById('add-requirement');
    if (addReqBtn) {
        addReqBtn.addEventListener('click', addRequirement);
    }
    
    // Form submission
    const rfpForm = document.getElementById('rfpGenerationForm');
    if (rfpForm) {
        rfpForm.addEventListener('submit', handleRFPSubmission);
    }
    
    // Remove requirement handlers (delegated)
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('remove-requirement')) {
            removeRequirement(e.target);
        }
    });
}

function addRequirement() {
    const container = document.getElementById('requirements-container');
    const newReq = document.createElement('div');
    newReq.className = 'requirement-item';
    newReq.style.display = 'flex';
    newReq.style.gap = 'var(--space-sm)';
    newReq.style.marginBottom = 'var(--space-sm)';
    
    newReq.innerHTML = `
        <input 
            type="text" 
            class="form-input requirement-input" 
            placeholder="Enter a requirement..."
            style="flex: 1;"
        >
        <button type="button" class="btn-outline remove-requirement" style="width: 40px;">×</button>
    `;
    
    container.appendChild(newReq);
    newReq.querySelector('.requirement-input').focus();
}

function removeRequirement(button) {
    const container = document.getElementById('requirements-container');
    if (container.children.length > 1) {
        button.parentNode.remove();
    }
}

async function handleRFPSubmission(event) {
    event.preventDefault();
    
    // Collect form data
    const formData = new FormData(event.target);
    const requirements = [];
    
    document.querySelectorAll('.requirement-input').forEach(input => {
        if (input.value.trim()) {
            requirements.push(input.value.trim());
        }
    });
    
    if (requirements.length === 0) {
        Swal.fire({
            icon: 'warning',
            title: 'Missing Requirements',
            text: 'Please add at least one requirement to generate the document.',
            confirmButtonColor: '#007bff'
        });
        return;
    }
    
    const requestData = {
        document_type: formData.get('document_type'),
        project_title: formData.get('project_title'),
        description: formData.get('description'),
        requirements: requirements,
        budget_range: formData.get('budget_range') || null,
        timeline: formData.get('timeline') || null,
        industry: formData.get('industry') || null
    };
    
    // Switch to generation step and ensure it's visible
    switchRFPStep(2);
    
    try {
        await generateRFPDocument(requestData);
    } catch (error) {
        console.error('RFP Generation failed:', error);
        alert('RFP generation failed. Please try again.');
        switchRFPStep(1);
    }
}

function switchRFPStep(stepNumber) {
    console.log('🔄 Switching to RFP step:', stepNumber);
    
    try {
        // Update step navigation (only in RFP page)
        const rfpSteps = document.querySelectorAll('#rfp-generation-page .step');
        console.log(`📊 Found ${rfpSteps.length} step navigation elements`);
        
        rfpSteps.forEach(step => {
            step.classList.remove('active');
            const stepNum = parseInt(step.dataset.step);
            if (stepNum === stepNumber) {
                step.classList.add('active');
                console.log('✅ Activated step navigation:', stepNumber);
            }
        });
        
        // Update step content (only in RFP page)
        const rfpStepContents = document.querySelectorAll('#rfp-generation-page .step-content');
        console.log(`📊 Found ${rfpStepContents.length} step content elements`);
        
        rfpStepContents.forEach((content, index) => {
            content.classList.remove('active');
            content.style.display = 'none';
            console.log(`❌ Hidden step content ${index + 1}`);
        });
        
        const activeStep = document.getElementById(`rfp-step${stepNumber}`);
        if (activeStep) {
            activeStep.classList.add('active');
            activeStep.style.display = 'block';
            activeStep.style.visibility = 'visible';
            console.log('✅ Displayed step content:', stepNumber);
            
            // Ensure the step is fully visible
            setTimeout(() => {
                activeStep.scrollIntoView({ 
                    behavior: 'smooth', 
                    block: 'start',
                    inline: 'nearest' 
                });
                console.log('✅ Scrolled to step:', stepNumber);
            }, 100);
            
            // Special handling for step 2 (progress)
            if (stepNumber === 2) {
                console.log('🎯 Step 2 activated - ensuring progress is visible');
                const loadingSection = activeStep.querySelector('#rfp-loading');
                if (loadingSection) {
                    loadingSection.style.display = 'block';
                    loadingSection.style.visibility = 'visible';
                    console.log('✅ Made loading section visible');
                }
                
                // Force a visual indicator that step 2 is active
                activeStep.style.backgroundColor = '#f8f9fa';
                activeStep.style.border = '2px solid #007bff';
                activeStep.style.borderRadius = '8px';
                activeStep.style.padding = '20px';
                
                console.log('✅ Applied visual styling to step 2');
            }
            
            // Special handling for step 3 (results)
            if (stepNumber === 3) {
                console.log('🎯 Step 3 activated - ensuring results are visible');
                const resultsSection = activeStep.querySelector('#rfp-results');
                if (resultsSection) {
                    resultsSection.style.display = 'block';
                    resultsSection.style.visibility = 'visible';
                    console.log('✅ Made results section visible');
                }
                
                // Force a visual indicator that step 3 is active
                activeStep.style.backgroundColor = '#f8f9fa';
                activeStep.style.border = '2px solid #007bff';
                activeStep.style.borderRadius = '8px';
                activeStep.style.padding = '20px';
                
                console.log('✅ Applied visual styling to step 3');
            }
            
        } else {
            console.error('❌ Could not find step element:', `rfp-step${stepNumber}`);
            
            // Fallback: try to find any element that might be the step
            const allSteps = document.querySelectorAll('[id*="rfp-step"]');
            console.log('🔍 Available step elements:', Array.from(allSteps).map(el => el.id));
        }
        
        console.log('🎯 Step switching completed for:', stepNumber);
        
    } catch (error) {
        console.error('❌ Error in switchRFPStep:', error);
        alert('Error switching steps: ' + error.message);
    }
}

async function generateRFPDocument(requestData) {
    console.log('🚀 Starting RFP generation with data:', requestData);
    
    try {
        // Start progress updates
        updateGenerationProgress('Initializing AI generation...', 10);
        
        // Start the API call with progress simulation
        const progressInterval = startProgressSimulation();
        
        console.log('📡 Making API call to:', '/api/v1/rfp/generate');
        const response = await fetch('/api/v1/rfp/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestData)
        });
        
        clearInterval(progressInterval);
        
        console.log('📡 API Response status:', response.status);
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error('❌ API Error:', errorText);
            throw new Error(`HTTP error! status: ${response.status} - ${errorText}`);
        }
        
        updateGenerationProgress('Processing API response...', 90);
        
        const result = await response.json();
        console.log('✅ API Response received:', result);
        
        currentRFPData = result;
        
        updateGenerationProgress('Document generation complete!', 100);
        await new Promise(resolve => setTimeout(resolve, 500));
        
        // Display results and switch to preview
        console.log('📄 Displaying results and switching to step 3...');
        displayRFPResults(result);
        switchRFPStep(3);
        
        console.log('🎉 RFP generation completed successfully');
        
        // Force scroll to top of results
        const step3Element = document.getElementById('rfp-step3');
        if (step3Element) {
            step3Element.scrollIntoView({ behavior: 'smooth' });
            console.log('✅ Scrolled to step 3 element');
        }
        
        // Auto-trigger download after successful generation
        setTimeout(() => {
            Swal.fire({
                icon: 'success',
                title: '🎉 RFP Generation Complete!',
                html: `
                    <div style="text-align: left; margin: 15px 0;">
                        <p><strong>📄 Project:</strong> ${result.project_title}</p>
                        <p><strong>⏱️ Generated in:</strong> ${result.processing_time.toFixed(1)}s</p>
                        <p><strong>📊 Sections:</strong> ${result.generation_metadata.sections_count} professional sections</p>
                        <p><strong>💬 Words:</strong> ${result.final_document.split(' ').length}</p>
                    </div>
                    <p style="margin-top: 15px;">Would you like to download the PDF now?</p>
                `,
                showCancelButton: true,
                confirmButtonColor: '#007bff',
                cancelButtonColor: '#6c757d',
                confirmButtonText: '📄 Download PDF',
                cancelButtonText: 'View First'
            }).then((result) => {
                if (result.isConfirmed) {
                    downloadRFPDocument();
                }
            });
        }, 1000);
        
    } catch (error) {
        console.error('❌ RFP Generation failed:', error);
        updateGenerationProgress('Generation failed: ' + error.message, 0);
        
        // Show error message to user
        Swal.fire({
            icon: 'error',
            title: 'Generation Failed',
            text: 'RFP generation failed: ' + error.message,
            confirmButtonColor: '#007bff'
        });
        throw error;
    }
}

function startProgressSimulation() {
    let progress = 10;
    const messages = [
        'Analyzing project requirements...',
        'Researching industry standards...',
        'Generating document sections...',
        'Finalizing RFP structure...'
    ];
    let messageIndex = 0;
    
    return setInterval(() => {
        if (progress < 85) {
            progress += Math.random() * 15 + 5;
            if (messageIndex < messages.length) {
                updateGenerationProgress(messages[messageIndex], Math.min(progress, 85));
                messageIndex++;
            }
        }
    }, 1000);
}

function updateGenerationProgress(message, percentage) {
    console.log(`📊 Progress: ${percentage}% - ${message}`);
    
    const progressMessage = document.getElementById('progress-message');
    const progressFill = document.getElementById('rfp-progress-fill');
    const progressPercentage = document.getElementById('progress-percentage');
    
    if (progressMessage) {
        progressMessage.textContent = message;
        console.log('✅ Updated progress message');
    } else {
        console.error('❌ Progress message element not found');
    }
    
    if (progressFill) {
        progressFill.style.width = `${Math.round(percentage)}%`;
        console.log(`✅ Updated progress bar to ${percentage}%`);
    } else {
        console.error('❌ Progress fill element not found');
    }
    
    if (progressPercentage) {
        progressPercentage.textContent = `${Math.round(percentage)}%`;
        console.log(`✅ Updated progress percentage display`);
    }
    
    // Update step indicators
    const steps = ['step-analyze', 'step-research', 'step-generate', 'step-finalize'];
    steps.forEach((stepId, index) => {
        const step = document.getElementById(stepId);
        if (step) {
            if (percentage >= (index + 1) * 20) {
                if (!step.innerHTML.includes('✅')) {
                    step.style.color = '#28a745';
                    step.style.fontWeight = 'bold';
                    step.innerHTML = step.innerHTML + ' ✅';
                    console.log(`✅ Updated step indicator: ${stepId}`);
                }
            }
        }
    });
}

function displayRFPResults(data) {
    console.log('🎨 Starting to display RFP results:', data);
    
    try {
        // Update document title
        const docTitle = document.getElementById('generated-document-title');
        if (docTitle) {
            docTitle.textContent = `Generated ${data.document_type}: ${data.project_title}`;
            console.log('✅ Updated document title');
        } else {
            console.error('❌ Document title element not found');
        }
        
        // Update generation info  
        const genTime = document.getElementById('generation-time');
        const docLength = document.getElementById('document-length');
        const sectionsCount = document.getElementById('sections-count');
        
        if (genTime) {
            genTime.textContent = `Generated in ${data.processing_time.toFixed(1)}s`;
            console.log('✅ Updated generation time');
        }
        if (docLength) {
            docLength.textContent = `${data.final_document.split(' ').length} words`;
            console.log('✅ Updated document length');
        }
        if (sectionsCount) {
            sectionsCount.textContent = `${data.generation_metadata.sections_count} sections`;
            console.log('✅ Updated sections count');
        }
        
        // Display document preview
        const preview = document.getElementById('document-preview');
        if (preview) {
            console.log('✅ Found document preview element');
            
            // Build a cleaner document structure with FORCED BLACK TEXT
            let htmlContent = `
                <div style="max-width: 800px; margin: 0 auto; font-family: Georgia, serif; color: #000000 !important; line-height: 1.6; background: #ffffff;">
                    <h1 style="color: #007bff !important; border-bottom: 2px solid #007bff; padding-bottom: 10px;">
                        ${data.document_type}: ${data.project_title}
                    </h1>
                    
                    <div style="background: #ffffff !important; padding: 20px; border-radius: 8px; margin: 20px 0; border: 2px solid #007bff; color: #000000 !important;">
                        <strong style="color: #000000 !important;">Document Type:</strong> <span style="color: #000000 !important;">${data.document_type} - ${getDocumentTypeName(data.document_type)}</span><br>
                        <strong style="color: #000000 !important;">Generated:</strong> <span style="color: #000000 !important;">${new Date().toLocaleDateString()}</span><br>
                        <strong style="color: #000000 !important;">Processing Time:</strong> <span style="color: #000000 !important;">${data.processing_time.toFixed(1)} seconds</span><br>
                        <strong style="color: #000000 !important;">Sections:</strong> <span style="color: #000000 !important;">${data.generation_metadata.sections_count} professional sections</span><br>
                        <strong style="color: #000000 !important;">Word Count:</strong> <span style="color: #000000 !important;">${data.final_document.split(' ').length} words</span>
                    </div>

                    <h2 style="color: #007bff !important; margin-top: 30px;">📋 Executive Summary</h2>
                    <div style="background: #ffffff !important; padding: 15px; border-radius: 6px; border: 1px solid #007bff; color: #000000 !important;">
                        <p style="color: #000000 !important;">This ${data.document_type} has been professionally generated with comprehensive requirements analysis, industry benchmarks, and detailed specifications for <strong style="color: #000000 !important;">${data.project_title}</strong>.</p>
                    </div>

                    <h2 style="color: #007bff !important; margin-top: 30px;">📊 Project Analysis</h2>
                    <div style="background: #ffffff !important; padding: 15px; border-radius: 6px; border: 1px solid #007bff; color: #000000 !important;">
                        <p style="color: #000000 !important;"><strong style="color: #000000 !important;">Project Category:</strong> <span style="color: #000000 !important;">${data.requirements_analysis.project_category}</span></p>
                        <p style="color: #000000 !important;"><strong style="color: #000000 !important;">Complexity Level:</strong> <span style="color: #000000 !important;">${data.requirements_analysis.complexity_level}</span></p>
                        <p style="color: #000000 !important;"><strong style="color: #000000 !important;">Key Challenges:</strong></p>
                        <ul style="margin: 10px 0; padding-left: 20px; color: #000000 !important;">
                            ${data.requirements_analysis.key_challenges.map(challenge => `<li style="margin: 5px 0; color: #000000 !important;">${challenge}</li>`).join('')}
                        </ul>
                    </div>

                    <h2 style="color: #007bff !important; margin-top: 30px;">🏆 Evaluation Framework</h2>
                    <div style="background: #ffffff !important; padding: 15px; border-radius: 6px; border: 1px solid #007bff; color: #000000 !important;">
                        ${data.requirements_analysis.evaluation_factors.map(factor => 
                            `<div style="display: flex; justify-content: space-between; margin: 8px 0; padding: 8px; background: #f8f9fa !important; border-radius: 4px; color: #000000 !important;">
                                <strong style="color: #000000 !important;">${factor.factor}:</strong> 
                                <span style="color: #007bff !important; font-weight: bold;">${factor.weight}</span>
                            </div>`
                        ).join('')}
                    </div>

                    <h2 style="color: #007bff !important; margin-top: 30px;">📈 Market Intelligence</h2>
                    <div style="background: #ffffff !important; padding: 15px; border-radius: 6px; border: 1px solid #007bff; color: #000000 !important;">
                        <p style="color: #000000 !important;"><strong style="color: #000000 !important;">Industry Timeline:</strong> <span style="color: #000000 !important;">${data.industry_benchmarks.typical_timeline}</span></p>
                        <p style="color: #000000 !important;"><strong style="color: #000000 !important;">Budget Guidelines:</strong> <span style="color: #000000 !important;">${data.industry_benchmarks.budget_benchmarks}</span></p>
                        <p style="color: #000000 !important;"><strong style="color: #000000 !important;">Current Market Trends:</strong></p>
                        <ul style="margin: 10px 0; padding-left: 20px; color: #000000 !important;">
                            ${data.industry_benchmarks.market_trends.map(trend => `<li style="margin: 5px 0; color: #000000 !important;">${trend}</li>`).join('')}
                        </ul>
                    </div>

                    <div style="margin-top: 40px; padding: 25px; background: linear-gradient(135deg, #007bff 0%, #6610f2 100%); color: white; border-radius: 12px; text-align: center; box-shadow: 0 4px 15px rgba(0,123,255,0.3);">
                        <h3 style="margin: 0 0 10px 0; color: white; font-size: 24px;">🎉 Document Generation Complete!</h3>
                        <p style="margin: 0; opacity: 0.95; font-size: 16px;">Professional ${data.document_type} ready for vendor distribution • ${data.generation_metadata.sections_count} sections • Industry-standard format</p>
                    </div>
                </div>
            `;
            
            preview.innerHTML = htmlContent;
            console.log('✅ Updated document preview with enhanced content');
            
            // Force visibility
            preview.style.display = 'block';
            preview.style.visibility = 'visible';
            
        } else {
            console.error('❌ Document preview element not found');
        }
        
        console.log('🎨 RFP results display completed successfully');
        
    } catch (error) {
        console.error('❌ Error displaying RFP results:', error);
        Swal.fire({
            icon: 'error',
            title: 'Display Error',
            text: 'Error displaying results: ' + error.message,
            confirmButtonColor: '#007bff'
        });
    }
}

function getDocumentTypeName(type) {
    const names = {
        'RFP': 'Request for Proposal',
        'RFI': 'Request for Information', 
        'RFQ': 'Request for Quote'
    };
    return names[type] || type;
}

function downloadRFPDocument() {
    console.log('📄 Download button clicked');
    
    if (!currentRFPData) {
        console.error('❌ No RFP data available for download');
        Swal.fire({
            icon: 'error',
            title: 'No Document Found',
            text: 'Please generate an RFP document first.',
            confirmButtonColor: '#007bff'
        });
        return;
    }
    
    console.log('📄 Starting PDF download for:', currentRFPData.project_title);
    
    try {
        const docType = currentRFPData.document_type;
        const projectTitle = currentRFPData.project_title.replace(/[^a-z0-9\s]/gi, '_').toLowerCase().replace(/\s+/g, '_');
        const timestamp = new Date().toISOString().split('T')[0];
        const filename = `${docType}_${projectTitle}_${timestamp}.pdf`;
        
        console.log('📄 Creating PDF:', filename);
        
        // Create PDF using jsPDF
        const { jsPDF } = window.jspdf;
        const pdf = new jsPDF();
        
        // Set up PDF formatting
        pdf.setFontSize(20);
        pdf.setTextColor(0, 123, 255);
        pdf.text(`${currentRFPData.document_type}: ${currentRFPData.project_title}`, 20, 30);
        
        // Document info
        pdf.setFontSize(12);
        pdf.setTextColor(0, 0, 0);
        let yPosition = 50;
        
        pdf.text(`Document Type: ${currentRFPData.document_type} - ${getDocumentTypeName(currentRFPData.document_type)}`, 20, yPosition);
        yPosition += 10;
        pdf.text(`Generated: ${new Date().toLocaleDateString()}`, 20, yPosition);
        yPosition += 10;
        pdf.text(`Processing Time: ${currentRFPData.processing_time.toFixed(1)} seconds`, 20, yPosition);
        yPosition += 10;
        pdf.text(`Sections: ${currentRFPData.generation_metadata.sections_count} professional sections`, 20, yPosition);
        yPosition += 10;
        pdf.text(`Word Count: ${currentRFPData.final_document.split(' ').length} words`, 20, yPosition);
        yPosition += 20;
        
        // Executive Summary
        pdf.setFontSize(16);
        pdf.setTextColor(0, 123, 255);
        pdf.text('Executive Summary', 20, yPosition);
        yPosition += 15;
        
        pdf.setFontSize(10);
        pdf.setTextColor(0, 0, 0);
        const summaryText = `This ${currentRFPData.document_type} has been professionally generated with comprehensive requirements analysis, industry benchmarks, and detailed specifications for ${currentRFPData.project_title}.`;
        const splitSummary = pdf.splitTextToSize(summaryText, 170);
        pdf.text(splitSummary, 20, yPosition);
        yPosition += splitSummary.length * 5 + 10;
        
        // Project Analysis
        pdf.setFontSize(16);
        pdf.setTextColor(0, 123, 255);
        pdf.text('Project Analysis', 20, yPosition);
        yPosition += 15;
        
        pdf.setFontSize(10);
        pdf.setTextColor(0, 0, 0);
        pdf.text(`Project Category: ${currentRFPData.requirements_analysis.project_category}`, 20, yPosition);
        yPosition += 8;
        pdf.text(`Complexity Level: ${currentRFPData.requirements_analysis.complexity_level}`, 20, yPosition);
        yPosition += 12;
        
        pdf.text('Key Challenges:', 20, yPosition);
        yPosition += 8;
        currentRFPData.requirements_analysis.key_challenges.forEach(challenge => {
            const challengeText = pdf.splitTextToSize(`• ${challenge}`, 160);
            pdf.text(challengeText, 25, yPosition);
            yPosition += challengeText.length * 5 + 2;
        });
        yPosition += 10;
        
        // Evaluation Framework
        if (yPosition > 250) {
            pdf.addPage();
            yPosition = 30;
        }
        
        pdf.setFontSize(16);
        pdf.setTextColor(0, 123, 255);
        pdf.text('Evaluation Framework', 20, yPosition);
        yPosition += 15;
        
        pdf.setFontSize(10);
        pdf.setTextColor(0, 0, 0);
        currentRFPData.requirements_analysis.evaluation_factors.forEach(factor => {
            pdf.text(`${factor.factor}: ${factor.weight}`, 20, yPosition);
            yPosition += 8;
        });
        yPosition += 10;
        
        // Market Intelligence
        if (yPosition > 230) {
            pdf.addPage();
            yPosition = 30;
        }
        
        pdf.setFontSize(16);
        pdf.setTextColor(0, 123, 255);
        pdf.text('Market Intelligence', 20, yPosition);
        yPosition += 15;
        
        pdf.setFontSize(10);
        pdf.setTextColor(0, 0, 0);
        pdf.text(`Industry Timeline: ${currentRFPData.industry_benchmarks.typical_timeline}`, 20, yPosition);
        yPosition += 8;
        pdf.text(`Budget Guidelines: ${currentRFPData.industry_benchmarks.budget_benchmarks}`, 20, yPosition);
        yPosition += 12;
        
        pdf.text('Current Market Trends:', 20, yPosition);
        yPosition += 8;
        currentRFPData.industry_benchmarks.market_trends.forEach(trend => {
            const trendText = pdf.splitTextToSize(`• ${trend}`, 160);
            pdf.text(trendText, 25, yPosition);
            yPosition += trendText.length * 5 + 2;
        });
        
        // Footer
        const pageCount = pdf.internal.getNumberOfPages();
        for (let i = 1; i <= pageCount; i++) {
            pdf.setPage(i);
            pdf.setFontSize(8);
            pdf.setTextColor(128, 128, 128);
            pdf.text('Generated by ProcureAI - AI-Powered Procurement Intelligence', 20, 285);
            pdf.text(`Page ${i} of ${pageCount}`, 170, 285);
        }
        
        // Save PDF
        pdf.save(filename);
        console.log('✅ PDF download initiated:', filename);
        
        // Show success message with SweetAlert2
        Swal.fire({
            icon: 'success',
            title: 'Document Downloaded!',
            html: `
                <div style="text-align: left; margin: 15px 0;">
                    <p><strong>File:</strong> ${filename}</p>
                    <p><strong>Format:</strong> Professional PDF</p>
                    <p><strong>Sections:</strong> ${currentRFPData.generation_metadata.sections_count}</p>
                    <p><strong>Location:</strong> Downloads folder</p>
                </div>
            `,
            confirmButtonColor: '#007bff',
            confirmButtonText: 'Great!'
        });
        
        // Visual feedback
        const downloadBtn = event?.target;
        if (downloadBtn) {
            const originalText = downloadBtn.innerHTML;
            downloadBtn.innerHTML = '✅ Downloaded!';
            downloadBtn.style.background = '#28a745';
            setTimeout(() => {
                downloadBtn.innerHTML = originalText;
                downloadBtn.style.background = '';
            }, 2000);
        }
        
    } catch (error) {
        console.error('❌ PDF download failed:', error);
        Swal.fire({
            icon: 'error',
            title: 'Download Failed',
            text: 'Failed to generate PDF. Please try again.',
            confirmButtonColor: '#007bff'
        });
    }
}

function regenerateRFP() {
    if (!currentRFPData) {
        switchRFPStep(1);
        return;
    }
    
    Swal.fire({
        title: 'Regenerate Document?',
        text: 'Generate a new document with the same requirements?',
        icon: 'question',
        showCancelButton: true,
        confirmButtonColor: '#007bff',
        cancelButtonColor: '#6c757d',
        confirmButtonText: 'Yes, Generate New',
        cancelButtonText: 'Cancel'
    }).then((result) => {
        if (result.isConfirmed) {
        // Extract original request data and regenerate
        const requestData = {
            document_type: currentRFPData.document_type,
            project_title: currentRFPData.project_title,
            description: document.getElementById('rfp-description').value,
            requirements: Array.from(document.querySelectorAll('.requirement-input'))
                .map(input => input.value.trim()).filter(val => val),
            budget_range: document.getElementById('rfp-budget-range').value || null,
            timeline: document.getElementById('rfp-timeline').value || null,
            industry: document.getElementById('rfp-industry').value || null
        };
        
            switchRFPStep(2);
            generateRFPDocument(requestData).catch(error => {
                console.error('Regeneration failed:', error);
                Swal.fire({
                    icon: 'error',
                    title: 'Regeneration Failed',
                    text: 'Document regeneration failed. Please try again.',
                    confirmButtonColor: '#007bff'
                });
                switchRFPStep(3);
            });
        }
    });
}

function editRFPRequirements() {
    switchRFPStep(1);
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

// Initialize page on load
document.addEventListener('DOMContentLoaded', function() {
    // Show dashboard by default
    switchPage('dashboard');
    
    // Initialize RFP functionality
    initializeRFPGeneration();
});