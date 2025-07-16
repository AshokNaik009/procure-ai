// Dashboard-specific JavaScript for Procurement Intelligence System

class DashboardManager {
    constructor() {
        this.api = new ProcurementAPI();
        this.lastAnalysisResults = null;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.animateStats();
        this.updateStats();
    }

    setupEventListeners() {
        // Form submission
        const form = document.getElementById('procurementForm');
        if (form) {
            form.addEventListener('submit', (e) => this.handleFormSubmission(e));
        }

        // Real-time search suggestions
        const productQuery = document.getElementById('productQuery');
        if (productQuery) {
            productQuery.addEventListener('input', debounce((e) => this.handleSearchInput(e), 300));
        }

        // Category change handler
        const category = document.getElementById('category');
        if (category) {
            category.addEventListener('change', (e) => this.handleCategoryChange(e));
        }
    }

    async handleFormSubmission(event) {
        event.preventDefault();
        
        const formData = this.getFormData();
        
        if (!this.validateForm(formData)) {
            return;
        }

        try {
            // Show loading with progress updates
            this.showProgressiveLoading();
            
            // Perform analysis
            const results = await this.api.analyzeMarket(formData);
            
            // Store results
            this.lastAnalysisResults = results;
            
            // Display results
            this.displayResults(results);
            
            // Save to history
            this.saveToHistory(formData, results);
            
            ToastManager.showSuccess('Analysis completed successfully!');
            
        } catch (error) {
            console.error('Analysis failed:', error);
            ToastManager.showError('Analysis failed. Please try again.');
            this.hideResults();
        }
    }

    getFormData() {
        return {
            query: document.getElementById('productQuery').value.trim(),
            category: document.getElementById('category').value,
            location: document.getElementById('location').value.trim(),
            timeline: document.getElementById('timeline').value.trim(),
            budget_range: this.parseBudgetRange(),
            requirements: this.parseRequirements()
        };
    }

    parseBudgetRange() {
        // In a real implementation, you might have budget input fields
        return null;
    }

    parseRequirements() {
        const requirements = document.getElementById('requirements').value.trim();
        if (!requirements) return [];
        
        // Split by comma, semicolon, or newline
        return requirements.split(/[,;\n]/).map(req => req.trim()).filter(req => req);
    }

    validateForm(formData) {
        if (!formData.query) {
            ToastManager.showError('Please enter a product or service description.');
            document.getElementById('productQuery').focus();
            return false;
        }

        if (!formData.category) {
            ToastManager.showError('Please select a category.');
            document.getElementById('category').focus();
            return false;
        }

        if (formData.query.length < 3) {
            ToastManager.showError('Product description must be at least 3 characters long.');
            document.getElementById('productQuery').focus();
            return false;
        }

        return true;
    }

    showProgressiveLoading() {
        this.api.showLoading();
        
        // Simulate progressive loading
        const steps = [
            { percent: 10, message: 'Initializing search...' },
            { percent: 30, message: 'Searching for suppliers...' },
            { percent: 50, message: 'Analyzing market data...' },
            { percent: 70, message: 'Processing with AI...' },
            { percent: 90, message: 'Finalizing results...' }
        ];

        let currentStep = 0;
        const progressInterval = setInterval(() => {
            if (currentStep < steps.length) {
                const step = steps[currentStep];
                this.api.updateProgress(step.percent);
                this.updateLoadingMessage(step.message);
                currentStep++;
            } else {
                clearInterval(progressInterval);
            }
        }, 800);

        // Store interval for cleanup
        this.progressInterval = progressInterval;
    }

    updateLoadingMessage(message) {
        const loadingOverlay = document.getElementById('loadingOverlay');
        if (loadingOverlay) {
            const messageElement = loadingOverlay.querySelector('p');
            if (messageElement) {
                messageElement.textContent = message;
            }
        }
    }

    displayResults(results) {
        // Clear any existing progress interval
        if (this.progressInterval) {
            clearInterval(this.progressInterval);
        }

        // Show results section
        const resultsSection = document.getElementById('resultsSection');
        if (resultsSection) {
            resultsSection.style.display = 'block';
            resultsSection.scrollIntoView({ behavior: 'smooth' });
        }

        // Update executive summary
        this.updateExecutiveSummary(results);
        
        // Update suppliers
        this.updateSuppliers(results.suppliers);
        
        // Update market intelligence
        this.updateMarketIntelligence(results.market_intelligence);
        
        // Update recommendations
        this.updateRecommendations(results);
        
        // Add fade-in animation
        resultsSection.classList.add('fade-in');
    }

    updateExecutiveSummary(results) {
        const summaryElement = document.getElementById('executiveSummary');
        if (summaryElement) {
            summaryElement.innerHTML = `
                <div class="d-flex justify-content-between align-items-start mb-3">
                    <div>
                        <h6><i class="fas fa-clock me-2"></i>Processing Time</h6>
                        <span class="badge bg-primary">${formatTime(results.processing_time)}</span>
                    </div>
                    <div>
                        <h6><i class="fas fa-gauge-high me-2"></i>Confidence Score</h6>
                        <span class="badge ${this.getConfidenceBadgeClass(results.confidence_score)}">
                            ${(results.confidence_score * 100).toFixed(1)}%
                        </span>
                    </div>
                </div>
                <p class="mb-0">${results.summary}</p>
            `;
        }
    }

    updateSuppliers(suppliers) {
        const suppliersList = document.getElementById('suppliersList');
        const supplierCount = document.getElementById('supplierCount2');
        
        if (supplierCount) {
            supplierCount.textContent = suppliers.length;
        }

        if (suppliersList) {
            if (suppliers.length === 0) {
                suppliersList.innerHTML = `
                    <div class="col-12">
                        <div class="alert alert-warning">
                            <i class="fas fa-exclamation-triangle me-2"></i>
                            No suppliers found for your criteria. Try broadening your search.
                        </div>
                    </div>
                `;
                return;
            }

            suppliersList.innerHTML = suppliers.map(supplier => this.createSupplierCard(supplier)).join('');
        }
    }

    createSupplierCard(supplier) {
        const confidenceClass = getConfidenceClass(supplier.confidence_score);
        const confidenceText = getConfidenceText(supplier.confidence_score);
        
        return `
            <div class="col-lg-4 col-md-6 mb-4">
                <div class="supplier-card">
                    <div class="d-flex justify-content-between align-items-start mb-3">
                        <div>
                            <h5 class="supplier-name">${supplier.name}</h5>
                            <div class="supplier-location">
                                <i class="fas fa-map-marker-alt me-1"></i>
                                ${supplier.location}
                            </div>
                        </div>
                        <div class="verification-badge">
                            ${this.getVerificationBadge(supplier.verification_status)}
                        </div>
                    </div>
                    
                    <div class="confidence-score ${confidenceClass}">
                        ${confidenceText}
                    </div>
                    
                    ${supplier.rating ? `
                        <div class="rating-section mb-3">
                            ${generateStars(supplier.rating)}
                            <span class="ms-2 text-muted">(${supplier.rating.toFixed(1)})</span>
                        </div>
                    ` : ''}
                    
                    ${supplier.description ? `
                        <p class="supplier-description text-muted mb-3">
                            ${supplier.description.substring(0, 150)}${supplier.description.length > 150 ? '...' : ''}
                        </p>
                    ` : ''}
                    
                    <div class="supplier-badges mb-3">
                        ${supplier.certifications.map(cert => 
                            `<span class="badge bg-success">${cert}</span>`
                        ).join('')}
                        ${supplier.specialties.map(specialty => 
                            `<span class="badge bg-info">${specialty}</span>`
                        ).join('')}
                        ${supplier.company_size ? 
                            `<span class="badge bg-secondary">${supplier.company_size}</span>` : ''
                        }
                    </div>
                    
                    <div class="supplier-actions">
                        ${supplier.website ? `
                            <a href="${supplier.website}" target="_blank" class="btn btn-sm btn-outline-primary me-2">
                                <i class="fas fa-external-link-alt me-1"></i>
                                Visit Website
                            </a>
                        ` : ''}
                        <button class="btn btn-sm btn-primary" onclick="showSupplierDetails('${supplier.name}')">
                            <i class="fas fa-info-circle me-1"></i>
                            Details
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    getVerificationBadge(status) {
        const badges = {
            'verified': '<span class="badge bg-success"><i class="fas fa-check-circle me-1"></i>Verified</span>',
            'pending': '<span class="badge bg-warning"><i class="fas fa-clock me-1"></i>Pending</span>',
            'unverified': '<span class="badge bg-secondary"><i class="fas fa-question-circle me-1"></i>Unverified</span>',
            'failed': '<span class="badge bg-danger"><i class="fas fa-times-circle me-1"></i>Failed</span>'
        };
        return badges[status] || badges['unverified'];
    }

    updateMarketIntelligence(marketIntel) {
        this.updatePriceInsights(marketIntel.price_insights);
        this.updateMarketTrends(marketIntel.market_trends);
    }

    updatePriceInsights(priceInsights) {
        const priceInsightsElement = document.getElementById('priceInsights');
        if (priceInsightsElement) {
            const { price_range, currency, trend, factors } = priceInsights;
            
            priceInsightsElement.innerHTML = `
                <div class="row mb-3">
                    <div class="col-4">
                        <div class="text-center">
                            <div class="h5 text-success">${formatCurrency(price_range.min, currency)}</div>
                            <small class="text-muted">Minimum</small>
                        </div>
                    </div>
                    <div class="col-4">
                        <div class="text-center">
                            <div class="h5 text-primary">${formatCurrency(price_range.avg, currency)}</div>
                            <small class="text-muted">Average</small>
                        </div>
                    </div>
                    <div class="col-4">
                        <div class="text-center">
                            <div class="h5 text-warning">${formatCurrency(price_range.max, currency)}</div>
                            <small class="text-muted">Maximum</small>
                        </div>
                    </div>
                </div>
                
                <div class="mb-3">
                    <h6><i class="fas fa-trending-${trend === 'increasing' ? 'up' : trend === 'decreasing' ? 'down' : 'right'} me-2"></i>Price Trend</h6>
                    <span class="badge ${this.getTrendBadgeClass(trend)}">${trend.toUpperCase()}</span>
                </div>
                
                ${factors.length > 0 ? `
                    <div>
                        <h6><i class="fas fa-list me-2"></i>Price Factors</h6>
                        <ul class="list-unstyled">
                            ${factors.map(factor => `<li><i class="fas fa-arrow-right me-2 text-muted"></i>${factor}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}
            `;
        }
    }

    updateMarketTrends(trends) {
        const trendsElement = document.getElementById('marketTrends');
        if (trendsElement) {
            if (trends.length === 0) {
                trendsElement.innerHTML = '<p class="text-muted">No market trends available.</p>';
                return;
            }

            trendsElement.innerHTML = trends.map(trend => `
                <div class="trend-item mb-3 p-3 border rounded">
                    <div class="d-flex justify-content-between align-items-start mb-2">
                        <h6 class="mb-0">${trend.trend_type.replace('_', ' ').toUpperCase()}</h6>
                        <span class="badge ${this.getImpactBadgeClass(trend.impact)}">${trend.impact.toUpperCase()}</span>
                    </div>
                    <p class="mb-2">${trend.description}</p>
                    <div class="progress" style="height: 8px;">
                        <div class="progress-bar" style="width: ${trend.confidence * 100}%"></div>
                    </div>
                    <small class="text-muted">Confidence: ${(trend.confidence * 100).toFixed(1)}%</small>
                </div>
            `).join('');
        }
    }

    updateRecommendations(results) {
        const nextSteps = document.getElementById('nextSteps');
        const recommendationsList = document.getElementById('recommendationsList');

        if (nextSteps && results.next_steps) {
            nextSteps.innerHTML = results.next_steps.map(step => `
                <li class="list-group-item">
                    <i class="fas fa-check-circle me-2 text-success"></i>
                    ${step}
                </li>
            `).join('');
        }

        if (recommendationsList && results.recommendations) {
            recommendationsList.innerHTML = results.recommendations.map(rec => `
                <li class="list-group-item">
                    <i class="fas fa-lightbulb me-2 text-warning"></i>
                    ${rec}
                </li>
            `).join('');
        }
    }

    getTrendBadgeClass(trend) {
        const classes = {
            'increasing': 'bg-danger',
            'decreasing': 'bg-success',
            'stable': 'bg-info'
        };
        return classes[trend] || 'bg-secondary';
    }

    getImpactBadgeClass(impact) {
        const classes = {
            'high': 'bg-danger',
            'medium': 'bg-warning',
            'low': 'bg-success'
        };
        return classes[impact] || 'bg-secondary';
    }

    getConfidenceBadgeClass(score) {
        if (score >= 0.8) return 'bg-success';
        if (score >= 0.6) return 'bg-warning';
        return 'bg-danger';
    }

    hideResults() {
        const resultsSection = document.getElementById('resultsSection');
        if (resultsSection) {
            resultsSection.style.display = 'none';
        }
    }

    saveToHistory(formData, results) {
        const historyItem = {
            id: Date.now(),
            timestamp: new Date().toISOString(),
            query: formData,
            results: results,
            processingTime: results.processing_time
        };

        let history = JSON.parse(localStorage.getItem('procurementHistory') || '[]');
        history.unshift(historyItem);
        
        // Keep only last 50 items
        history = history.slice(0, 50);
        
        localStorage.setItem('procurementHistory', JSON.stringify(history));
    }

    async handleSearchInput(event) {
        const query = event.target.value.trim();
        if (query.length < 3) return;

        try {
            // Get search suggestions (if API supports it)
            const suggestions = await this.getSuggestions(query);
            this.showSuggestions(suggestions);
        } catch (error) {
            console.error('Failed to get suggestions:', error);
        }
    }

    async getSuggestions(query) {
        try {
            const response = await fetch(`/api/v1/suppliers/suggestions?query=${encodeURIComponent(query)}`);
            if (response.ok) {
                return await response.json();
            }
        } catch (error) {
            console.error('Suggestions API error:', error);
        }
        return [];
    }

    showSuggestions(suggestions) {
        // Implementation for search suggestions dropdown
        // This would create a dropdown with suggestions
        console.log('Suggestions:', suggestions);
    }

    handleCategoryChange(event) {
        const category = event.target.value;
        // Update form based on category selection
        this.updateFormForCategory(category);
    }

    updateFormForCategory(category) {
        // Category-specific form updates
        const requirementsField = document.getElementById('requirements');
        
        const categoryPlaceholders = {
            'materials': 'e.g., Grade specifications, quantity requirements, delivery schedule',
            'equipment': 'e.g., Technical specifications, warranty requirements, service support',
            'services': 'e.g., Service level agreements, expertise requirements, location preferences',
            'software': 'e.g., License type, integration requirements, support level',
            'construction': 'e.g., Project specifications, compliance requirements, timeline',
            'manufacturing': 'e.g., Production capacity, quality standards, delivery schedule'
        };

        if (requirementsField && categoryPlaceholders[category]) {
            requirementsField.placeholder = categoryPlaceholders[category];
        }
    }

    animateStats() {
        // Animate statistics on page load
        const animateValue = (element, start, end, duration) => {
            const startTime = performance.now();
            
            const animate = (currentTime) => {
                const elapsed = currentTime - startTime;
                const progress = Math.min(elapsed / duration, 1);
                
                const value = start + (end - start) * progress;
                element.textContent = Math.floor(value).toLocaleString();
                
                if (progress < 1) {
                    requestAnimationFrame(animate);
                }
            };
            
            requestAnimationFrame(animate);
        };

        // Animate stats with realistic numbers
        setTimeout(() => {
            const supplierCount = document.getElementById('supplierCount');
            const analysisCount = document.getElementById('analysisCount');
            
            if (supplierCount) animateValue(supplierCount, 0, 12547, 2000);
            if (analysisCount) animateValue(analysisCount, 0, 892, 1500);
        }, 500);
    }

    updateStats() {
        // Update dynamic statistics
        const avgResponseTime = document.getElementById('avgResponseTime');
        const accuracyRate = document.getElementById('accuracyRate');
        
        if (avgResponseTime) {
            // Simulate real-time response time
            const times = ['2.8s', '3.2s', '2.9s', '3.5s', '2.7s'];
            let index = 0;
            
            setInterval(() => {
                avgResponseTime.textContent = times[index];
                index = (index + 1) % times.length;
            }, 10000);
        }

        if (accuracyRate) {
            // Simulate accuracy rate updates
            const rates = ['94%', '95%', '93%', '96%', '94%'];
            let index = 0;
            
            setInterval(() => {
                accuracyRate.textContent = rates[index];
                index = (index + 1) % rates.length;
            }, 15000);
        }
    }
}

// Global functions for supplier interactions
function showSupplierDetails(supplierName) {
    // In a real implementation, this would open a modal or navigate to details page
    console.log('Showing details for:', supplierName);
    ToastManager.showSuccess(`Supplier details for ${supplierName} - Feature coming soon!`);
}

// Initialize dashboard when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    new DashboardManager();
});

// Utility function for debouncing
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}