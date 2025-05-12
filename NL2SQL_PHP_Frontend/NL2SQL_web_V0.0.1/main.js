// Ensure Chart.js v4 is properly included
import Chart from 'chart.js/auto';

// Replace or add this function to handle chart rendering
function renderChart(chartData) {
    const chartContainer = document.getElementById('chart-container');
    chartContainer.innerHTML = ''; // Clear previous chart
    
    if (!chartData) {
        chartContainer.innerHTML = '<div class="alert alert-info">No visualization available for this query.</div>';
        return;
    }
    
    try {
        // Check if chartData is a base64 image or a Chart.js configuration
        if (typeof chartData === 'string' && chartData.startsWith('data:image/png;base64,')) {
            // Handle base64 image from fallback chart generation
            const img = document.createElement('img');
            img.src = chartData;
            img.className = 'img-fluid chart-image';
            img.alt = 'Query result chart';
            chartContainer.appendChild(img);
        } else if (typeof chartData === 'object') {
            // Handle Chart.js configuration object
            const canvas = document.createElement('canvas');
            canvas.id = 'query-result-chart';
            chartContainer.appendChild(canvas);
            
            // Get the canvas context and create the chart
            const ctx = canvas.getContext('2d');
            
            // Destroy existing chart if any
            if (window.resultChart) {
                window.resultChart.destroy();
            }
            
            // Create new chart with the configuration
            window.resultChart = new Chart(ctx, chartData);
        }
    } catch (error) {
        console.error('Failed to render chart:', error);
        chartContainer.innerHTML = `<div class="alert alert-danger">Failed to render chart: ${error.message}</div>`;
    }
}

// Update the executeQuery function to properly handle the chart data
function executeQuery() {
    const query = document.getElementById('query-input').value.trim();
    if (!query) {
        alert('Please enter a query.');
        return;
    }

    fetch('/api/execute-query', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ query: query })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            // Render table data
            const tableContainer = document.getElementById('table-container');
            tableContainer.innerHTML = ''; // Clear previous table
            const table = document.createElement('table');
            table.className = 'table table-striped';
            const thead = document.createElement('thead');
            const tbody = document.createElement('tbody');
            
            // Add table headers
            const headerRow = document.createElement('tr');
            data.table_data.columns.forEach(column => {
                const th = document.createElement('th');
                th.textContent = column;
                headerRow.appendChild(th);
            });
            thead.appendChild(headerRow);
            
            // Add table rows
            data.table_data.data.forEach(row => {
                const tr = document.createElement('tr');
                row.forEach(cell => {
                    const td = document.createElement('td');
                    td.textContent = cell;
                    tr.appendChild(td);
                });
                tbody.appendChild(tr);
            });
            
            table.appendChild(thead);
            table.appendChild(tbody);
            tableContainer.appendChild(table);
            
            // Render chart with the chart data
            renderChart(data.chart_data);
            
            // Show the summary if available
            const summaryContainer = document.getElementById('summary-container');
            if (data.summary) {
                summaryContainer.innerHTML = `<div class="alert alert-info">${data.summary.replace(/\n/g, '<br>')}</div>`;
                summaryContainer.classList.remove('d-none');
            } else {
                summaryContainer.classList.add('d-none');
            }
        } else {
            alert(`Error: ${data.message}`);
        }
    })
    .catch(error => {
        console.error('Failed to execute query:', error);
        alert('Failed to execute query. Please try again.');
    });
}

// Attach event listener to the query execution button
document.getElementById('execute-query-btn').addEventListener('click', executeQuery);