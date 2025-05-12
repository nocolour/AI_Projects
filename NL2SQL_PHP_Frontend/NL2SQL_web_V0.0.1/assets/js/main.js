/**
 * NL2SQL - Natural Language to SQL Query System
 * Main JavaScript for frontend functionality
 */

// API endpoint configuration - adjust this based on your Flask server setup
const API_BASE_URL = 'http://localhost:5000/api';

// Document ready function
$(document).ready(function() {
    // Initialize the application
    initApp();
    
    // Load saved settings on page load
    loadSavedSettings();
    
    // Set up event listeners
    setupEventListeners();
    
    // Error log tab shown event
    $('#error-logs-tab').on('shown.bs.tab', function() {
        fetchLogs();
    });
    
    // Log filter change events
    $('#logLevelFilter, #logSearchFilter').on('change keyup', function() {
        fetchLogs();
    });
    
    // Refresh and clear log buttons
    $('#refreshLogsBtn').on('click', fetchLogs);
    $('#clearLogsBtn').on('click', clearLogs);
    
    // Intercept and log AJAX errors
    $(document).ajaxError(function(event, jqXHR, settings, thrownError) {
        logError('AJAX request failed', {
            url: settings.url,
            status: jqXHR.status,
            statusText: jqXHR.statusText,
            error: thrownError
        });
    });
    
    // Log page initialization
    logInfo('Application initialized', {
        userAgent: navigator.userAgent,
        timestamp: new Date().toISOString()
    });
    
    // Test API Key Button Click
    $('#testApiKeyBtn').on('click', function() {
        const apiKey = $('#apiKey').val().trim();
        const statusEl = $('#apiKeyTestStatus');
        
        if (!apiKey) {
            statusEl.html('<span class="text-danger">Please enter an API key</span>');
            return;
        }
        
        statusEl.html('<span class="text-muted"><i class="fas fa-spinner fa-spin"></i> Testing...</span>');
        
        $.ajax({
            url: 'settings_handler.php',
            type: 'POST',
            data: {
                action: 'test_api_key',
                api_key: apiKey
            },
            dataType: 'json',
            success: function(response) {
                if (response.status === 'success') {
                    statusEl.html('<span class="text-success"><i class="fas fa-check-circle"></i> Success! API key is valid</span>');
                } else {
                    statusEl.html('<span class="text-danger"><i class="fas fa-times-circle"></i> Failed: ' + (response.message || 'Invalid API key') + '</span>');
                }
            },
            error: function() {
                statusEl.html('<span class="text-danger"><i class="fas fa-times-circle"></i> Failed: Server error</span>');
            }
        });
    });
    
    // Save Settings Button Click
    $('#saveSettingsBtn').on('click', function() {
        const btn = $(this);
        const originalText = btn.html();
        
        // Gather all settings
        const settings = {
            database: {
                host: $('#dbHost').val().trim(),
                port: $('#dbPort').val().trim(),
                user: $('#dbUser').val().trim(),
                password: $('#dbPassword').val().trim(),
                name: $('#dbName').val().trim()
            },
            api: {
                key: $('#apiKey').val().trim(),
                model: $('#aiModel').val()
            }
        };
        
        // Disable button and show loading state
        btn.html('<i class="fas fa-spinner fa-spin"></i> Saving...').prop('disabled', true);
        
        $.ajax({
            url: 'settings_handler.php',
            type: 'POST',
            data: {
                action: 'save_settings',
                settings: JSON.stringify(settings)
            },
            dataType: 'json',
            success: function(response) {
                if (response.status === 'success') {
                    // Show success indicator temporarily
                    btn.html('<i class="fas fa-check"></i> Saved!').removeClass('btn-primary').addClass('btn-success');
                    
                    // Close the modal after a brief delay
                    setTimeout(function() {
                        $('#settingsModal').modal('hide');
                        btn.html(originalText).removeClass('btn-success').addClass('btn-primary').prop('disabled', false);
                    }, 1500);
                } else {
                    // Show error and restore button
                    showError('Failed to save settings: ' + (response.message || 'Unknown error'));
                    btn.html(originalText).prop('disabled', false);
                }
            },
            error: function() {
                showError('Server error while saving settings');
                btn.html(originalText).prop('disabled', false);
            }
        });
    });
});

/**
 * Initialize the application
 */
function initApp() {
    // Load configuration
    loadConfig();
    
    // Load example queries
    loadExamples();
    
    // Hide result placeholders initially
    $('#noTableResults').hide();
    $('#noChartResults').hide();
    $('#noSummaryResults').hide();
}

/**
 * Set up event listeners for UI elements
 */
function setupEventListeners() {
    // Execute query button
    $('#executeBtn').on('click', executeQuery);
    
    // Clear button
    $('#clearBtn').on('click', function() {
        $('#queryInput').val('');
    });
    
    // Example query selection
    $('#exampleQueries').on('change', function() {
        const selectedExample = $(this).val();
        if (selectedExample) {
            $('#queryInput').val(selectedExample);
        }
    });
    
    // Test connection button
    $('#testConnectionBtn').on('click', testDatabaseConnection);
    
    // Save settings button
    $('#saveSettingsBtn').on('click', saveSettings);
    
    // View schema button (added to navbar)
    $('.navbar').on('click', '.view-schema-btn', function(e) {
        e.preventDefault();
        viewDatabaseSchema();
    });
    
    // Add a "View Schema" button to the navbar if it doesn't exist
    if ($('.view-schema-btn').length === 0) {
        const viewSchemaBtn = $('<li class="nav-item"><a href="#" class="nav-link view-schema-btn">View Schema</a></li>');
        $('#navbarNav .navbar-nav').append(viewSchemaBtn);
    }
}

/**
 * Load configuration from the server
 */
function loadConfig() {
    $.ajax({
        url: `${API_BASE_URL}/config`,
        type: 'GET',
        dataType: 'json',
        success: function(response) {
            if (response) {
                // Database config
                $('#dbHost').val(response.database.host || 'localhost');
                $('#dbPort').val(response.database.port || '3306');
                $('#dbUser').val(response.database.user || 'root');
                $('#dbName').val(response.database.database || '');
                
                // AI model
                if (response.ai_model) {
                    $('#aiModel').val(response.ai_model);
                }
            }
        },
        error: function(xhr, status, error) {
            showError('Could not load configuration. Please configure manually.');
        }
    });
}

/**
 * Load example queries from the server
 */
function loadExamples() {
    $.ajax({
        url: `${API_BASE_URL}/examples`,
        type: 'GET',
        dataType: 'json',
        success: function(response) {
            if (response && response.status === 'success' && Array.isArray(response.examples)) {
                const exampleSelect = $('#exampleQueries');
                exampleSelect.empty();
                exampleSelect.append($('<option>', {
                    value: '',
                    text: 'Select an example'
                }));
                
                response.examples.forEach(example => {
                    exampleSelect.append($('<option>', {
                        value: example,
                        text: example
                    }));
                });
            }
        },
        error: function(xhr, status, error) {
            console.error('Failed to load examples:', error);
        }
    });
}

/**
 * Execute the natural language query
 */
function executeQuery() {
    const query = $('#queryInput').val().trim();
    
    if (!query) {
        showError('Please enter a query.');
        return;
    }
    
    // Show status indicator
    $('#statusArea').removeClass('d-none').addClass('d-flex');
    $('#statusText').text('Processing query...');
    
    // Clear previous results
    clearResults();
    
    // Execute the query via API
    $.ajax({
        url: `${API_BASE_URL}/execute-query`,
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ query: query }),
        dataType: 'json',
        success: function(response) {
            // Hide status indicator
            $('#statusArea').removeClass('d-flex').addClass('d-none');
            
            if (response && response.status === 'success') {
                // Display the SQL
                displaySQL(response.sql_query);
                
                // Display the results
                displayTableResults(response.table_data);
                
                // Display chart if available, or auto-generate from table data
                displayChart(response.chart_data, response.table_data);
                
                // Display summary
                displaySummary(response.summary);
                
                // Update row count
                $('#rowCount').text(`${response.row_count} rows`);
            } else {
                showError(response.message || 'Unknown error occurred');
            }
        },
        error: function(xhr, status, error) {
            // Hide status indicator
            $('#statusArea').removeClass('d-flex').addClass('d-none');
            
            let errorMessage = 'Failed to execute query';
            
            try {
                const response = JSON.parse(xhr.responseText);
                if (response && response.message) {
                    errorMessage = response.message;
                }
            } catch (e) {
                errorMessage += ': ' + error;
            }
            
            showError(errorMessage);
        }
    });
}

/**
 * Display SQL query in the output area
 */
function displaySQL(sql) {
    $('#sqlOutput').text(sql || '-- No SQL query generated --');
}

/**
 * Display table results
 */
function displayTableResults(tableData) {
    if (!tableData || !tableData.columns || !tableData.data || tableData.data.length === 0) {
        $('#resultsTable').hide();
        $('#noTableResults').show();
        return;
    }
    
    // Build table headers
    const tableHeader = $('#tableHeader');
    tableHeader.empty();
    
    tableData.columns.forEach(column => {
        tableHeader.append($('<th>').text(column));
    });
    
    // Build table rows
    const tableBody = $('#tableBody');
    tableBody.empty();
    
    tableData.data.forEach(row => {
        const tr = $('<tr>');
        row.forEach(cell => {
            tr.append($('<td>').text(cell !== null ? cell : 'NULL'));
        });
        tableBody.append(tr);
    });
    
    $('#resultsTable').show();
    $('#noTableResults').hide();
}

/**
 * Display chart for data visualization
 * @param {string|object} chartData - Can be base64 image, URL, or JSON chart config
 * @param {object} tableData - Table data to use for auto-generating chart if chartData not provided
 */
function displayChart(chartData, tableData) {
    // Always hide both first
    $('#chartContainer').hide();
    $('#noChartResults').hide();
    
    // Clear any existing charts
    if (window.currentChart) {
        window.currentChart.destroy();
    }

    // If no chartData but we have tableData, try to auto-generate a chart
    if (!chartData && tableData && tableData.columns && tableData.data && tableData.data.length > 0) {
        const autoGeneratedChart = generateChartFromTableData(tableData);
        if (autoGeneratedChart) {
            renderInteractiveChart(autoGeneratedChart);
            logInfo('Auto-generated chart from query results');
            return;
        }
    }

    if (!chartData) {
        $('#chartImage').attr('src', '');
        $('#noChartResults').text('No visualization available for this data').show();
        logWarning('No chart data available for display');
        return;
    }

    // Check if chartData is JSON object for interactive chart (AI-generated or otherwise)
    if (typeof chartData === 'object') {
        renderInteractiveChart(chartData);
        logInfo('Rendering AI-generated or predefined chart configuration');
        return;
    }
    
    // Handle string-based chart data (base64 or URL)
    if (typeof chartData !== 'string' || chartData.trim() === '') {
        $('#noChartResults').text('Invalid chart data format').show();
        logWarning('Invalid chart data format received');
        return;
    }
    
    // JSON data passed as string
    try {
        const jsonData = JSON.parse(chartData);
        renderInteractiveChart(jsonData);
        return;
    } catch (e) {
        // Not JSON, continue with image processing
        console.log("Not JSON data, attempting to process as image");
    }

    // Process as image data (base64 or URL)
    let formattedChartData = chartData.trim();
    
    // Direct image URL
    if (formattedChartData.match(/^https?:\/\/.+\.(jpg|jpeg|png|gif|svg|webp)(\?.*)?$/i)) {
        displayImageChart(formattedChartData);
        return;
    }
    
    // Base64 image data with prefix
    if (formattedChartData.startsWith('data:image/')) {
        displayImageChart(formattedChartData);
        return;
    }
    
    // Plain base64 data without prefix
    const base64Regex = /^[A-Za-z0-9+/=]+$/;
    if (base64Regex.test(formattedChartData)) {
        formattedChartData = 'data:image/png;base64,' + formattedChartData;
        displayImageChart(formattedChartData);
        return;
    }
    
    // If we reach here, format is unrecognized
    $('#noChartResults').text('Unsupported chart data format').show();
    logError('Unsupported chart data format', { 
        dataType: typeof chartData,
        preview: typeof chartData === 'string' ? chartData.substring(0, 100) + '...' : 'non-string'
    });
}

/**
 * Automatically generate chart configuration from table data
 * @param {object} tableData - The table data with columns and rows
 * @returns {object|null} - Chart.js configuration or null if chart can't be generated
 */
function generateChartFromTableData(tableData) {
    try {
        if (!tableData || !tableData.columns || !tableData.data || tableData.data.length < 1) {
            return null;
        }
        
        const columns = tableData.columns;
        const data = tableData.data;
        
        // Analyze what kind of data we have to determine the best chart type
        const colCount = columns.length;
        const rowCount = data.length;
        
        // Too many columns or rows might not make a good chart
        if (colCount < 2 || rowCount < 1 || rowCount > 100) {
            return null;
        }
        
        // Determine data types for each column
        const columnTypes = columns.map((col, index) => {
            // Sample first few values to determine type
            const samples = data.slice(0, Math.min(5, data.length)).map(row => row[index]);
            
            // Check if numeric
            const isNumeric = samples.every(value => 
                value === null || value === '' || !isNaN(parseFloat(value))
            );
            
            // Check if date
            const isDate = samples.every(value => 
                value === null || value === '' || !isNaN(Date.parse(String(value)))
            );
            
            return {
                name: col,
                isNumeric: isNumeric,
                isDate: isDate
            };
        });
        
        // Find numeric columns (potential values for y-axis)
        const numericColumns = columnTypes.filter(col => col.isNumeric);
        
        // Find potential label columns (non-numeric or date columns are good candidates)
        const labelColumns = columnTypes.filter((col, idx) => 
            !col.isNumeric || idx === 0 || col.isDate
        );
        
        if (numericColumns.length === 0) {
            // No numeric columns, can't create a meaningful chart
            return null;
        }
        
        // Decide on chart type and axes
        let chartType = 'bar'; // Default
        let xAxisIndex = 0;
        let yAxisIndices = [];
        
        // If we have a date column, it's likely a good x-axis for a line chart
        const dateColumnIndex = columnTypes.findIndex(col => col.isDate);
        if (dateColumnIndex >= 0) {
            xAxisIndex = dateColumnIndex;
            chartType = 'line';
        } else {
            // Otherwise, use first column as labels
            xAxisIndex = 0;
        }
        
        // Use up to 3 numeric columns as data series
        columnTypes.forEach((col, idx) => {
            if (col.isNumeric && idx !== xAxisIndex && yAxisIndices.length < 3) {
                yAxisIndices.push(idx);
            }
        });
        
        // If no numeric columns found except the xAxis, and xAxis is numeric, 
        // use it as both label and data
        if (yAxisIndices.length === 0 && columnTypes[xAxisIndex].isNumeric) {
            yAxisIndices.push(xAxisIndex);
            // In this case, use row numbers as labels
            xAxisIndex = -1;
        }
        
        // If still no data series found, we can't create a chart
        if (yAxisIndices.length === 0) {
            return null;
        }
        
        // Create chart configuration
        const chartData = {
            labels: xAxisIndex >= 0 ? data.map(row => row[xAxisIndex]) : data.map((_, i) => `Row ${i+1}`),
            datasets: yAxisIndices.map((colIdx, i) => {
                const colors = getChartColors(i, yAxisIndices.length);
                return {
                    label: columns[colIdx],
                    data: data.map(row => {
                        const val = row[colIdx];
                        return val === null || val === '' ? null : parseFloat(val);
                    }),
                    backgroundColor: chartType === 'line' ? colors.background + '80' : colors.background,
                    borderColor: colors.border,
                    borderWidth: 1
                };
            })
        };
        
        // Special case for pie chart - if single data series with few categories
        if (yAxisIndices.length === 1 && data.length <= 10) {
            chartType = 'pie';
        }
        
        return {
            type: chartType,
            data: chartData,
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Auto-generated Chart'
                    },
                    legend: {
                        position: 'top'
                    }
                }
            }
        };
        
    } catch (error) {
        logError('Error generating chart from table data', { error: error.message });
        return null;
    }
}

/**
 * Display chart as image
 * @param {string} imageUrl - Image URL or data URL
 */
function displayImageChart(imageUrl) {
    // Create image with appropriate styling
    $('#chartContainer').addClass('text-center').show();
    $('#chartImage')
        .off('error')
        .on('error', function() {
            $('#chartContainer').hide();
            $('#noChartResults').text('Failed to load chart image').show();
            logError('Chart image failed to load');
        })
        .on('load', function() {
            $('#chartContainer').show();
            $('#chartImage').addClass('img-fluid mx-auto d-block');
            logInfo('Chart image displayed successfully');
        })
        .attr('src', imageUrl);
}

/**
 * Render interactive chart using Chart.js
 * @param {object} chartConfig - Chart configuration data
 */
function renderInteractiveChart(chartConfig) {
    // Hide image element and show canvas
    $('#chartImage').hide();
    
    // Make sure we have a canvas element
    let chartCanvas = $('#chartCanvas');
    if (chartCanvas.length === 0) {
        $('#chartContainer').append('<canvas id="chartCanvas"></canvas>');
        chartCanvas = $('#chartCanvas');
    } else {
        chartCanvas.show();
    }
    
    try {
        // Prepare config for Chart.js
        const config = prepareChartConfig(chartConfig);
        
        // Create chart
        const ctx = document.getElementById('chartCanvas').getContext('2d');
        window.currentChart = new Chart(ctx, config);
        
        // Show container
        $('#chartContainer').show();
        
        // Check if this was likely AI-generated
        if (chartConfig.type && chartConfig.data && chartConfig.options && 
            chartConfig.options.plugins && chartConfig.options.plugins.title) {
            logInfo('AI-recommended chart rendered successfully');
        } else {
            logInfo('Interactive chart rendered successfully');
        }
    } catch (error) {
        $('#chartCanvas').hide();
        $('#noChartResults').text('Failed to render interactive chart: ' + error.message).show();
        logError('Failed to render interactive chart', { error: error.message });
    }
}

/**
 * Prepare chart configuration based on data
 * @param {object} data - Raw chart data
 * @returns {object} - Chart.js configuration
 */
function prepareChartConfig(data) {
    // If data is already in Chart.js format, return as is
    if (data.type && data.data) {
        return data;
    }
    
    // Otherwise, intelligently determine chart type based on data
    let chartType = 'bar'; // Default
    let chartData = {
        labels: [],
        datasets: []
    };
    
    // Analyze data structure to determine appropriate chart type
    if (data.categories && data.series) {
        // Looks like a categorical dataset
        chartData.labels = data.categories;
        
        // Check if time series for line chart
        const hasTimeData = data.categories.every(cat => 
            !isNaN(Date.parse(cat)) || (typeof cat === 'string' && cat.match(/^\d{4}(-\d{2})?(-\d{2})?$/))
        );
        
        if (hasTimeData) {
            chartType = 'line';
        }
        
        // Check if pie chart might be appropriate (single series, <10 categories)
        if (data.series.length === 1 && data.categories.length <= 10) {
            chartType = 'pie';
        }
        
        // Create datasets
        data.series.forEach((series, index) => {
            const colors = getChartColors(index, data.series.length);
            chartData.datasets.push({
                label: series.name || `Series ${index + 1}`,
                data: series.data,
                backgroundColor: chartType === 'line' ? colors.background + '80' : colors.background,
                borderColor: colors.border,
                borderWidth: 1
            });
        });
    } else if (Array.isArray(data)) {
        // Simple array of values
        chartType = 'bar';
        const labels = data.map((_, index) => `Item ${index + 1}`);
        chartData.labels = labels;
        chartData.datasets.push({
            label: 'Value',
            data: data,
            backgroundColor: getChartColors(0, 1).background,
            borderColor: getChartColors(0, 1).border,
            borderWidth: 1
        });
    }
    
    return {
        type: chartType,
        data: chartData,
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                title: {
                    display: data.title ? true : false,
                    text: data.title || ''
                },
                legend: {
                    position: 'top',
                }
            }
        }
    };
}

/**
 * Generate colors for charts
 * @param {number} index - Dataset index
 * @param {number} count - Total datasets
 * @returns {object} - Background and border colors
 */
function getChartColors(index, count) {
    const colorSets = [
        { background: 'rgba(75, 192, 192, 0.7)', border: 'rgba(75, 192, 192, 1)' },
        { background: 'rgba(54, 162, 235, 0.7)', border: 'rgba(54, 162, 235, 1)' },
        { background: 'rgba(255, 206, 86, 0.7)', border: 'rgba(255, 206, 86, 1)' },
        { background: 'rgba(255, 99, 132, 0.7)', border: 'rgba(255, 99, 132, 1)' },
        { background: 'rgba(153, 102, 255, 0.7)', border: 'rgba(153, 102, 255, 1)' },
        { background: 'rgba(255, 159, 64, 0.7)', border: 'rgba(255, 159, 64, 1)' }
    ];
    
    if (count <= colorSets.length) {
        return colorSets[index % colorSets.length];
    } else {
        // Generate color algorithmically if we need more colors
        const hue = (index * (360 / count)) % 360;
        return {
            background: `hsla(${hue}, 70%, 60%, 0.7)`,
            border: `hsla(${hue}, 70%, 50%, 1)`
        };
    }
}

/**
 * Display summary text
 */
function displaySummary(summary) {
    if (!summary) {
        $('#summaryContent').empty();
        $('#noSummaryResults').show();
        return;
    }
    
    $('#summaryContent').html(summary);
    $('#noSummaryResults').hide();
}

/**
 * Display query results including chart
 */
function displayQueryResults(response) {
    // Assuming other result processing code is here
    
    // Use the dedicated displayChart function for consistency
    displayChart(response.chart_data, response.table_data);
    
    // Rest of your result processing code
}

/**
 * Clear all results
 */
function clearResults() {
    // Clear SQL
    $('#sqlOutput').text('-- SQL query will appear here --');
    
    // Clear table
    $('#tableHeader').empty();
    $('#tableBody').empty();
    $('#resultsTable').hide();
    $('#noTableResults').show();
    
    // Clear chart - Hide container and clear image source
    $('#chartContainer').hide();
    $('#chartImage').attr('src', ''); // Clear the image source
    $('#noChartResults').show();
    
    // Clear summary
    $('#summaryContent').empty();
    $('#noSummaryResults').show();
    
    // Reset row count
    $('#rowCount').text('0 rows');
}

/**
 * Test the database connection
 */
function testDatabaseConnection() {
    const connectionData = {
        host: $('#dbHost').val(),
        port: $('#dbPort').val(),
        user: $('#dbUser').val(),
        password: $('#dbPassword').val(),
        database: $('#dbName').val()
    };
    
    // Show testing indicator
    const testBtn = $('#testConnectionBtn');
    const originalText = testBtn.html();
    testBtn.html('<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Testing...');
    testBtn.prop('disabled', true);
    
    $.ajax({
        url: `${API_BASE_URL}/test-connection`,
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify(connectionData),
        dataType: 'json',
        success: function(response) {
            testBtn.html(originalText);
            testBtn.prop('disabled', false);
            
            if (response && response.status === 'success') {
                alert('Database connection successful!');
            } else {
                showError(response.message || 'Connection test failed');
            }
        },
        error: function(xhr, status, error) {
            testBtn.html(originalText);
            testBtn.prop('disabled', false);
            
            let errorMessage = 'Connection test failed';
            
            try {
                const response = JSON.parse(xhr.responseText);
                if (response && response.message) {
                    errorMessage = response.message;
                }
            } catch (e) {
                errorMessage += ': ' + error;
            }
            
            showError(errorMessage);
        }
    });
}

/**
 * Save configuration settings
 */
function saveSettings() {
    const configData = {
        database: {
            host: $('#dbHost').val(),
            port: parseInt($('#dbPort').val(), 10),
            user: $('#dbUser').val(),
            password: $('#dbPassword').val(),
            database: $('#dbName').val()
        },
        openai_api_key: $('#apiKey').val(),
        ai_model: $('#aiModel').val()
    };
    
    // Show saving indicator
    const saveBtn = $('#saveSettingsBtn');
    const originalText = saveBtn.html();
    saveBtn.html('<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Saving...');
    saveBtn.prop('disabled', true);
    
    $.ajax({
        url: `${API_BASE_URL}/config`,
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify(configData),
        dataType: 'json',
        success: function(response) {
            saveBtn.html(originalText);
            saveBtn.prop('disabled', false);
            
            if (response && response.status === 'success') {
                alert('Settings saved successfully!');
                $('#settingsModal').modal('hide');
            } else {
                showError(response.message || 'Failed to save settings');
            }
        },
        error: function(xhr, status, error) {
            saveBtn.html(originalText);
            saveBtn.prop('disabled', false);
            
            let errorMessage = 'Failed to save settings';
            
            try {
                const response = JSON.parse(xhr.responseText);
                if (response && response.message) {
                    errorMessage = response.message;
                }
            } catch (e) {
                errorMessage += ': ' + error;
            }
            
            showError(errorMessage);
        }
    });
}

/**
 * View database schema
 */
function viewDatabaseSchema() {
    // Show the schema modal
    $('#schemaModal').modal('show');
    
    // Show loading state
    $('#schemaContent').empty();
    $('#schemaLoading').show();
    $('#schemaError').hide();
    
    // Fetch schema from API
    $.ajax({
        url: `${API_BASE_URL}/schema`,
        type: 'GET',
        dataType: 'json',
        success: function(response) {
            $('#schemaLoading').hide();
            
            if (response && response.status === 'success' && Array.isArray(response.schema)) {
                displaySchema(response.schema);
            } else {
                $('#schemaError').text(response.message || 'Failed to load schema').removeClass('d-none');
            }
        },
        error: function(xhr, status, error) {
            $('#schemaLoading').hide();
            
            let errorMessage = 'Failed to load schema';
            
            try {
                const response = JSON.parse(xhr.responseText);
                if (response && response.message) {
                    errorMessage = response.message;
                }
            } catch (e) {
                errorMessage += ': ' + error;
            }
            
            $('#schemaError').text(errorMessage).removeClass('d-none');
        }
    });
}

/**
 * Display schema information
 */
function displaySchema(schemaData) {
    const schemaContent = $('#schemaContent');
    schemaContent.empty();
    
    if (!schemaData || schemaData.length === 0) {
        schemaContent.html('<div class="alert alert-info">No schema information available</div>');
        return;
    }
    
    // Create tables for each schema item
    schemaData.forEach(item => {
        const tableDiv = $('<div>').addClass('mb-4');
        
        // Table title
        const title = $('<h5>').text(item.table);
        tableDiv.append(title);
        
        // Table for columns
        const table = $('<table>').addClass('table table-bordered schema-table');
        
        // Header row
        const thead = $('<thead>');
        const headerRow = $('<tr>');
        headerRow.append($('<th>').text('Column'));
        headerRow.append($('<th>').text('Type'));
        thead.append(headerRow);
        table.append(thead);
        
        // Body rows
        const tbody = $('<tbody>');
        
        item.columns.forEach(column => {
            const parts = column.split(' (');
            const columnName = parts[0];
            const columnType = parts.length > 1 ? parts[1].replace(')', '') : '';
            
            const row = $('<tr>');
            row.append($('<td>').text(columnName));
            row.append($('<td>').text(columnType));
            tbody.append(row);
        });
        
        table.append(tbody);
        tableDiv.append(table);
        schemaContent.append(tableDiv);
    });
}

/**
 * Generates SQL from natural language using the configured AI model
 * @param {string} naturalLanguageQuery - The user's query in plain language
 * @returns {Promise<string>} - The generated SQL query
 */
async function generate_sql(naturalLanguageQuery) {
    try {
        // Show the status indicator
        $('#statusArea').removeClass('d-none');
        $('#statusText').text('Generating SQL...');
        
        // Get API settings from storage
        const apiKey = localStorage.getItem('apiKey');
        const aiModel = localStorage.getItem('aiModel') || 'gpt-4o-mini';
        
        if (!apiKey) {
            // Add a 5-second timeout before showing the error
            await new Promise(resolve => setTimeout(resolve, 5000));
            throw new Error('API key not configured. Please set it in Settings.');
        }
        
        // Get database settings
        const dbSettings = {
            host: localStorage.getItem('dbHost') || 'localhost',
            database: localStorage.getItem('dbName'),
            // We don't need to send other db credentials to generate SQL
        };
        
        if (!dbSettings.database) {
            throw new Error('Database not selected. Please configure database settings.');
        }
        
        // Make API request to backend endpoint
        const response = await fetch('/api/generate_sql.php', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                query: naturalLanguageQuery,
                apiKey: apiKey,
                model: aiModel,
                database: dbSettings
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to generate SQL query');
        }
        
        const data = await response.json();
        return data.sql;
    } catch (error) {
        console.error('Error generating SQL:', error);
        showError('SQL generation failed: ' + error.message);
        throw error;
    } finally {
        // Hide the status indicator in all cases
        $('#statusArea').addClass('d-none');
    }
}

/**
 * Show error message using toast
 */
function showError(message) {
    $('#errorToastBody').text(message);
    const toast = new bootstrap.Toast($('#errorToast'));
    toast.show();
}

/**
 * Error logging functionality
 */
function logError(message, context = {}) {
    $.post('api/logs.php?action=add', {
        level: 'error',
        message: message,
        context: JSON.stringify(context)
    });
}

function logWarning(message, context = {}) {
    $.post('api/logs.php?action=add', {
        level: 'warning',
        message: message,
        context: JSON.stringify(context)
    });
}

function logInfo(message, context = {}) {
    $.post('api/logs.php?action=add', {
        level: 'info',
        message: message,
        context: JSON.stringify(context)
    });
}

function fetchLogs() {
    const filter = $('#logLevelFilter').val();
    const search = $('#logSearchFilter').val();
    
    $('#logContent').html('<div class="text-center"><div class="spinner-border text-light" role="status"></div><div>Loading logs...</div></div>');
    
    $.getJSON('api/logs.php?action=get', {
        filter: filter,
        search: search,
        limit: 1000
    })
    .done(function(data) {
        if (data.success) {
            if (data.logs.length > 0) {
                const logLines = data.logs.map(line => {
                    // Colorize log entries based on level
                    if (line.includes('[error]')) {
                        return `<span class="text-danger">${escapeHtml(line)}</span>`;
                    } else if (line.includes('[warning]')) {
                        return `<span class="text-warning">${escapeHtml(line)}</span>`;
                    } else if (line.includes('[info]')) {
                        return `<span class="text-info">${escapeHtml(line)}</span>`;
                    } else {
                        return escapeHtml(line);
                    }
                });
                
                $('#logContent').html(logLines.join('\n'));
                $('#logCount').text(data.count);
                $('#lastRefreshed').text(data.timestamp);
                $('#noLogsMessage').addClass('d-none');
            } else {
                $('#logContent').html('');
                $('#noLogsMessage').removeClass('d-none');
                $('#logCount').text(0);
                $('#lastRefreshed').text(data.timestamp);
            }
        } else {
            $('#logContent').html(`<div class="text-danger">Error loading logs: ${data.error || 'Unknown error'}</div>`);
        }
    })
    .fail(function(jqXHR, textStatus, errorThrown) {
        $('#logContent').html(`<div class="text-danger">Failed to fetch logs: ${errorThrown}</div>`);
    });
}

function clearLogs() {
    if (confirm('Are you sure you want to clear all logs? This cannot be undone.')) {
        $.post('api/logs.php?action=clear')
            .done(function(data) {
                if (data.success) {
                    fetchLogs();
                    showToast('success', 'Logs cleared successfully');
                } else {
                    showToast('error', `Failed to clear logs: ${data.error || 'Unknown error'}`);
                }
            })
            .fail(function(jqXHR, textStatus, errorThrown) {
                showToast('error', `Failed to clear logs: ${errorThrown}`);
            });
    }
}

// Helper to show toast messages
function showToast(type, message) {
    const toast = new bootstrap.Toast(document.getElementById('errorToast'));
    $('#errorToastBody').text(message);
    toast.show();
}

// Helper to escape HTML in log entries
function escapeHtml(text) {
    return text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// Helper function to load saved settings
function loadSavedSettings() {
    $.ajax({
        url: 'settings_handler.php',
        type: 'POST',
        data: {
            action: 'load_settings'
        },
        dataType: 'json',
        success: function(response) {
            if (response.status === 'success' && response.data) {
                const settings = response.data;
                
                // Populate database settings
                if (settings.database) {
                    $('#dbHost').val(settings.database.host || '');
                    $('#dbPort').val(settings.database.port || '');
                    $('#dbUser').val(settings.database.user || '');
                    $('#dbPassword').val(settings.database.password || '');
                    $('#dbName').val(settings.database.name || '');
                }
                
                // Populate API settings
                if (settings.api) {
                    $('#apiKey').val(settings.api.key || '');
                    $('#aiModel').val(settings.api.model || 'gpt-4o-mini');
                }
            }
        },
        error: function() {
            logWarning('Failed to load saved settings');
        }
    });
}