// Statistics tracking
let testStatistics = {
    totalTests: 0,
    passedTests: 0,
    failedTests: 0
};

// API Base URL
const API_BASE = '/api';

// DOM Functions
function showLoading() {
    document.getElementById('loadingOverlay').style.display = 'flex';
}

function hideLoading() {
    document.getElementById('loadingOverlay').style.display = 'none';
}

function showResults() {
    document.getElementById('results').style.display = 'block';
}

function updateStatistics(decision) {
    testStatistics.totalTests++;
    if (decision === 'FAIL TO REJECT') {
        testStatistics.passedTests++;
    } else {
        testStatistics.failedTests++;
    }
    
    const successRate = ((testStatistics.passedTests / testStatistics.totalTests) * 100).toFixed(1);
    
    document.getElementById('totalTests').textContent = testStatistics.totalTests;
    document.getElementById('passedTests').textContent = testStatistics.passedTests;
    document.getElementById('failedTests').textContent = testStatistics.failedTests;
    document.getElementById('successRate').textContent = `${successRate}%`;
}

// API Functions
async function runTest() {
    showLoading();
    
    const config = {
        n_numbers: parseInt(document.getElementById('sampleSize').value),
        n_intervals: parseInt(document.getElementById('numIntervals').value),
        alpha: parseFloat(document.getElementById('alphaLevel').value),
        random_seed: parseInt(document.getElementById('randomSeed').value)
    };
    
    try {
        const response = await fetch(`${API_BASE}/chi-square-test`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(config)
        });
        
        const data = await response.json();
        
        if (data.success) {
            displayResults(data.data);
            updateStatistics(data.data.test_results.decision);
        } else {
            alert('Error: ' + data.error);
        }
    } catch (error) {
        alert('Network error: ' + error.message);
    } finally {
        hideLoading();
        showResults();
    }
}

async function runMultipleAlphaTest() {
    showLoading();
    
    const config = {
        n_numbers: parseInt(document.getElementById('sampleSize').value),
        n_intervals: parseInt(document.getElementById('numIntervals').value),
        random_seed: parseInt(document.getElementById('randomSeed').value)
    };
    
    try {
        const response = await fetch(`${API_BASE}/multiple-alpha-test`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(config)
        });
        
        const data = await response.json();
        
        if (data.success) {
            displayAlphaComparison(data.data);
        } else {
            alert('Error: ' + data.error);
        }
    } catch (error) {
        alert('Network error: ' + error.message);
    } finally {
        hideLoading();
    }
}

async function exportResults() {
    // This would export the current results as CSV
    alert('Export feature would be implemented here');
}

// Display Functions
function displayResults(data) {
    // Display test summary
    const testSummary = `
        <div class="row">
            <div class="col-6">
                <strong><i class="fas fa-hashtag me-2"></i>Sample Size:</strong> ${data.test_parameters.n_numbers}<br>
                <strong><i class="fas fa-calculator me-2"></i>Sample Mean:</strong> ${data.sample_statistics.sample_mean}<br>
                <strong><i class="fas fa-chart-line me-2"></i>Sample Variance:</strong> ${data.sample_statistics.sample_variance}
            </div>
            <div class="col-6">
                <strong><i class="fas fa-chart-bar me-2"></i>Intervals:</strong> ${data.test_parameters.n_intervals}<br>
                <strong><i class="fas fa-project-diagram me-2"></i>Degrees of Freedom:</strong> ${data.test_parameters.df}<br>
                <strong><i class="fas fa-square-root-alt me-2"></i>Test Statistic (χ²):</strong> ${data.test_results.chi_square}
            </div>
        </div>
        <div class="mt-3">
            <strong><i class="fas fa-list me-2"></i>First 10 Numbers:</strong><br>
            <code>[${data.sample_statistics.first_10_numbers.join(', ')}]</code>
        </div>
    `;
    document.getElementById('testSummary').innerHTML = testSummary;

    // Display statistical decision
    const decisionColor = data.test_results.decision === "REJECT" ? "danger" : "success";
    const icon = data.test_results.decision === "REJECT" ? "fa-times-circle" : "fa-check-circle";
    
    const statisticalDecision = `
        <div class="text-center">
            <span class="badge bg-${decisionColor} result-badge mb-3">
                <i class="fas ${icon} me-2"></i>${data.test_results.decision} H₀
            </span>
            <p><strong><i class="fas fa-comment me-2"></i>Conclusion:</strong> ${data.test_results.conclusion}</p>
            <p><strong><i class="fas fa-bullseye me-2"></i>Critical Value:</strong> ${data.test_results.critical_value}</p>
            <p><strong><i class="fas fa-percentage me-2"></i>P-value:</strong> ${data.test_results.p_value}</p>
            <p><strong><i class="fas fa-filter me-2"></i>Significance Level:</strong> α = ${data.test_parameters.alpha}</p>
        </div>
    `;
    document.getElementById('statisticalDecision').innerHTML = statisticalDecision;

    // Display frequency table
    const tableBody = document.getElementById('tableBody');
    tableBody.innerHTML = '';
    
    data.frequency_table.forEach(row => {
        const tr = document.createElement('tr');
        tr.className = 'fade-in';
        tr.innerHTML = `
            <td>${row.interval}</td>
            <td>${row.range}</td>
            <td>${row.observed}</td>
            <td>${row.expected}</td>
            <td>${row.O_minus_E}</td>
            <td>${row.O_minus_E_squared}</td>
            <td>${row.chi_component}</td>
        `;
        tableBody.appendChild(tr);
    });

    // Display table footer
    const totalObserved = data.frequency_table.reduce((sum, row) => sum + row.observed, 0);
    const totalExpected = data.frequency_table.reduce((sum, row) => sum + row.expected, 0);
    
    const tableFooter = document.getElementById('tableFooter');
    tableFooter.innerHTML = `
        <td colspan="2"><strong>Total</strong></td>
        <td><strong>${totalObserved}</strong></td>
        <td><strong>${totalExpected.toFixed(1)}</strong></td>
        <td><strong>-</strong></td>
        <td><strong>-</strong></td>
        <td><strong>${data.test_results.chi_square}</strong></td>
    `;

    // Create charts
    createCharts(data);
}

function displayAlphaComparison(data) {
    const alphaComparisonBody = document.getElementById('alphaComparisonBody');
    alphaComparisonBody.innerHTML = '';
    
    data.forEach(result => {
        const decisionColor = result.decision === "REJECT" ? "table-danger" : "table-success";
        const icon = result.decision === "REJECT" ? "fa-times-circle" : "fa-check-circle";
        
        const tr = document.createElement('tr');
        tr.className = decisionColor;
        tr.innerHTML = `
            <td>${result.alpha}</td>
            <td>${result.test_statistic.toFixed(4)}</td>
            <td>${result.critical_value.toFixed(4)}</td>
            <td>${result.p_value.toFixed(4)}</td>
            <td><strong><i class="fas ${icon} me-2"></i>${result.decision}</strong></td>
        `;
        alphaComparisonBody.appendChild(tr);
    });
}

function createCharts(data) {
    const intervals = data.chart_data.intervals;
    const observed = data.chart_data.observed;
    const expected = data.chart_data.expected;
    const components = data.chart_data.components;

    // Destroy existing charts
    const chartIds = ['histogramChart', 'comparisonChart', 'componentChart', 'distributionChart'];
    chartIds.forEach(chartId => {
        const chart = Chart.getChart(chartId);
        if (chart) chart.destroy();
    });

    // Histogram Chart
    new Chart(document.getElementById('histogramChart'), {
        type: 'bar',
        data: {
            labels: intervals,
            datasets: [{
                label: 'Observed Frequency',
                data: observed,
                backgroundColor: 'rgba(54, 162, 235, 0.6)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 1
            }, {
                label: 'Expected Frequency',
                data: expected,
                type: 'line',
                borderColor: 'rgba(255, 99, 132, 1)',
                borderWidth: 2,
                fill: false,
                pointRadius: 3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Frequency'
                    }
                }
            }
        }
    });

    // Comparison Chart
    new Chart(document.getElementById('comparisonChart'), {
        type: 'bar',
        data: {
            labels: intervals,
            datasets: [{
                label: 'Observed',
                data: observed,
                backgroundColor: 'rgba(54, 162, 235, 0.6)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 1
            }, {
                label: 'Expected',
                data: expected,
                backgroundColor: 'rgba(255, 99, 132, 0.6)',
                borderColor: 'rgba(255, 99, 132, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Frequency'
                    }
                }
            }
        }
    });

    // Component Analysis Chart
    new Chart(document.getElementById('componentChart'), {
        type: 'bar',
        data: {
            labels: intervals,
            datasets: [{
                label: '(O-E)²/E Contribution',
                data: components,
                backgroundColor: components.map(val => 
                    val > 2 ? 'rgba(255, 99, 132, 0.6)' : 'rgba(255, 159, 64, 0.6)'
                ),
                borderColor: components.map(val => 
                    val > 2 ? 'rgba(255, 99, 132, 1)' : 'rgba(255, 159, 64, 1)'
                ),
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Chi-Square Component'
                    }
                }
            }
        }
    });

    // Distribution Comparison Chart
    new Chart(document.getElementById('distributionChart'), {
        type: 'pie',
        data: {
            labels: ['Within Expected Range', 'Outside Expected Range'],
            datasets: [{
                data: [
                    observed.filter((val, idx) => Math.abs(val - expected[idx]) <= 2).length,
                    observed.filter((val, idx) => Math.abs(val - expected[idx]) > 2).length
                ],
                backgroundColor: [
                    'rgba(75, 192, 192, 0.6)',
                    'rgba(255, 99, 132, 0.6)'
                ],
                borderColor: [
                    'rgba(75, 192, 192, 1)',
                    'rgba(255, 99, 132, 1)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false
        }
    });
}

function resetTest() {
    document.getElementById('sampleSize').value = 100;
    document.getElementById('numIntervals').value = 10;
    document.getElementById('alphaLevel').value = 0.05;
    document.getElementById('randomSeed').value = 42;
    document.getElementById('results').style.display = 'none';
}

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    console.log('Chi-Square Uniformity Test Application Initialized');
    
    // Add event listeners for Enter key
    const inputs = ['sampleSize', 'numIntervals', 'randomSeed'];
    inputs.forEach(id => {
        document.getElementById(id).addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                runTest();
            }
        });
    });
});
