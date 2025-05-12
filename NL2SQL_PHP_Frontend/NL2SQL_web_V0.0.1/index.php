<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NL2SQL - Natural Language to SQL Query System</title>
    
    <!-- Bootstrap 5 CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    
    <!-- Font Awesome for icons -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
    
    <!-- Custom CSS -->
    <link rel="stylesheet" href="assets/css/style.css">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="#">NL2SQL Query System</a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav" aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav ms-auto">
                    <li class="nav-item">
                        <a class="nav-link active" href="index.php">Home</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="#" data-bs-toggle="modal" data-bs-target="#settingsModal">Settings</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="#" data-bs-toggle="modal" data-bs-target="#aboutModal">About</a>
                    </li>
                </ul>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        <!-- Query Input Section -->
        <div class="card mb-4">
            <div class="card-header bg-light">
                <h5>Natural Language Query</h5>
            </div>
            <div class="card-body">
                <div class="mb-3">
                    <textarea class="form-control" id="queryInput" rows="4" placeholder="Enter your question in natural language, e.g., 'Show me the top 5 customers by total amount spent'"></textarea>
                </div>
                
                <!-- Examples dropdown -->
                <div class="row mb-3">
                    <div class="col-md-8">
                        <div class="input-group">
                            <span class="input-group-text">Example queries:</span>
                            <select class="form-select" id="exampleQueries">
                                <option value="" selected>Select an example</option>
                            </select>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="btn-group w-100">
                            <button type="button" id="executeBtn" class="btn btn-primary">
                                <i class="fas fa-play"></i> Execute Query
                            </button>
                            <button type="button" id="clearBtn" class="btn btn-secondary">
                                <i class="fas fa-eraser"></i> Clear
                            </button>
                        </div>
                    </div>
                </div>
                
                <!-- Status indicator -->
                <div id="statusArea" class="alert alert-secondary d-none">
                    <span id="statusText">Processing...</span>
                    <div class="spinner-border spinner-border-sm text-primary ms-2" role="status" id="statusSpinner">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- Generated SQL Section -->
        <div class="card mb-4">
            <div class="card-header bg-light">
                <h5>Generated SQL</h5>
            </div>
            <div class="card-body">
                <pre id="sqlOutput" class="border rounded bg-light p-3">-- SQL query will appear here --</pre>
            </div>
        </div>

        <!-- Results Section -->
        <div class="card mb-4">
            <div class="card-header bg-light">
                <h5>Query Results</h5>
                <span id="rowCount" class="badge bg-secondary ms-2">0 rows</span>
            </div>
            <div class="card-body">
                <!-- Tabs for different views -->
                <ul class="nav nav-tabs" id="resultTabs" role="tablist">
                    <li class="nav-item" role="presentation">
                        <button class="nav-link active" id="table-tab" data-bs-toggle="tab" data-bs-target="#table" type="button" role="tab" aria-controls="table" aria-selected="true">Table View</button>
                    </li>
                    <li class="nav-item" role="presentation">
                        <button class="nav-link" id="chart-tab" data-bs-toggle="tab" data-bs-target="#chart" type="button" role="tab" aria-controls="chart" aria-selected="false">Chart View</button>
                    </li>
                    <li class="nav-item" role="presentation">
                        <button class="nav-link" id="summary-tab" data-bs-toggle="tab" data-bs-target="#summary" type="button" role="tab" aria-controls="summary" aria-selected="false">Summary</button>
                    </li>
                    <li class="nav-item" role="presentation">
                        <button class="nav-link" id="error-logs-tab" data-bs-toggle="tab" data-bs-target="#error-logs" type="button" role="tab" aria-controls="error-logs" aria-selected="false">
                            <i class="fas fa-exclamation-triangle"></i> Error Logs
                        </button>
                    </li>
                </ul>
                
                <!-- Tab content -->
                <div class="tab-content border border-top-0 rounded-bottom p-3" id="resultTabsContent">
                    <!-- Table View -->
                    <div class="tab-pane fade show active" id="table" role="tabpanel" aria-labelledby="table-tab">
                        <div class="table-responsive">
                            <table id="resultsTable" class="table table-striped table-hover">
                                <thead>
                                    <tr id="tableHeader"></tr>
                                </thead>
                                <tbody id="tableBody"></tbody>
                            </table>
                        </div>
                        <div id="noTableResults" class="alert alert-info">No data available</div>
                    </div>
                    
                    <!-- Chart View -->
                    <div class="tab-pane fade" id="chart" role="tabpanel" aria-labelledby="chart-tab">
                        <div id="chartContainer" style="height: 400px; display: none;">
                            <img id="chartImage" class="img-fluid" alt="Data visualization chart" style="max-height: 400px;">
                        </div>
                        <div id="noChartResults" class="alert alert-info">No visualization available for this query</div>
                    </div>
                    
                    <!-- Summary View -->
                    <div class="tab-pane fade" id="summary" role="tabpanel" aria-labelledby="summary-tab">
                        <div id="summaryContent" class="p-3"></div>
                        <div id="noSummaryResults" class="alert alert-info">No summary available</div>
                    </div>

                    <!-- Error Logs View -->
                    <div class="tab-pane fade" id="error-logs" role="tabpanel" aria-labelledby="error-logs-tab">
                        <div class="mb-3">
                            <div class="d-flex justify-content-between align-items-center mb-3">
                                <div class="input-group" style="max-width: 450px;">
                                    <span class="input-group-text">Filter</span>
                                    <select class="form-select" id="logLevelFilter">
                                        <option value="all" selected>All Levels</option>
                                        <option value="error">Errors Only</option>
                                        <option value="warning">Warnings & Errors</option>
                                        <option value="info">Info & Above</option>
                                    </select>
                                    <input type="text" class="form-control" id="logSearchFilter" placeholder="Search in logs...">
                                </div>
                                <div class="btn-group">
                                    <button type="button" id="refreshLogsBtn" class="btn btn-outline-primary">
                                        <i class="fas fa-sync-alt"></i> Refresh
                                    </button>
                                    <button type="button" id="clearLogsBtn" class="btn btn-outline-danger">
                                        <i class="fas fa-trash-alt"></i> Clear Logs
                                    </button>
                                </div>
                            </div>
                            
                            <div class="log-container bg-dark text-light p-3 rounded" style="height: 400px; overflow-y: auto; font-family: monospace;">
                                <pre id="logContent" style="white-space: pre-wrap;"></pre>
                            </div>
                            <div id="noLogsMessage" class="alert alert-info mt-3 d-none">
                                No logs available
                            </div>
                            <div class="text-muted mt-2 small">
                                <span id="logCount">0</span> log entries. Last refreshed: <span id="lastRefreshed">Never</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Settings Modal -->
    <div class="modal fade" id="settingsModal" tabindex="-1" aria-labelledby="settingsModalLabel" aria-hidden="true">
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="settingsModalLabel">Settings</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    <!-- Settings Tabs -->
                    <ul class="nav nav-tabs" id="settingsTabs" role="tablist">
                        <li class="nav-item" role="presentation">
                            <button class="nav-link active" id="database-tab" data-bs-toggle="tab" data-bs-target="#database" type="button" role="tab" aria-controls="database" aria-selected="true">Database</button>
                        </li>
                        <li class="nav-item" role="presentation">
                            <button class="nav-link" id="api-tab" data-bs-toggle="tab" data-bs-target="#api" type="button" role="tab" aria-controls="api" aria-selected="false">API Settings</button>
                        </li>
                    </ul>
                    
                    <div class="tab-content mt-3" id="settingsTabsContent">
                        <!-- Database Settings Tab -->
                        <div class="tab-pane fade show active" id="database" role="tabpanel" aria-labelledby="database-tab">
                            <form id="databaseForm">
                                <div class="mb-3 row">
                                    <label for="dbHost" class="col-sm-3 col-form-label">Host:</label>
                                    <div class="col-sm-9">
                                        <input type="text" class="form-control" id="dbHost" value="localhost">
                                    </div>
                                </div>
                                <div class="mb-3 row">
                                    <label for="dbPort" class="col-sm-3 col-form-label">Port:</label>
                                    <div class="col-sm-9">
                                        <input type="text" class="form-control" id="dbPort" value="3306">
                                    </div>
                                </div>
                                <div class="mb-3 row">
                                    <label for="dbUser" class="col-sm-3 col-form-label">User:</label>
                                    <div class="col-sm-9">
                                        <input type="text" class="form-control" id="dbUser" value="root">
                                    </div>
                                </div>
                                <div class="mb-3 row">
                                    <label for="dbPassword" class="col-sm-3 col-form-label">Password:</label>
                                    <div class="col-sm-9">
                                        <input type="password" class="form-control" id="dbPassword">
                                    </div>
                                </div>
                                <div class="mb-3 row">
                                    <label for="dbName" class="col-sm-3 col-form-label">Database:</label>
                                    <div class="col-sm-9">
                                        <input type="text" class="form-control" id="dbName">
                                    </div>
                                </div>
                                <div class="d-grid">
                                    <button type="button" id="testConnectionBtn" class="btn btn-outline-primary">Test Connection</button>
                                </div>
                            </form>
                        </div>
                        
                        <!-- API Settings Tab -->
                        <div class="tab-pane fade" id="api" role="tabpanel" aria-labelledby="api-tab">
                            <form id="apiForm">
                                <div class="mb-3 row">
                                    <label for="apiKey" class="col-sm-3 col-form-label">OpenAI API Key:</label>
                                    <div class="col-sm-9">
                                        <input type="password" class="form-control" id="apiKey">
                                        <small class="form-text text-muted">Your API key is stored securely and never shared.</small>
                                    </div>
                                </div>
                                <div class="mb-3 row">
                                    <label for="aiModel" class="col-sm-3 col-form-label">AI Model:</label>
                                    <div class="col-sm-9">
                                        <select class="form-select" id="aiModel">
                                            <option value="gpt-4o-mini">gpt-4o-mini</option>
                                            <option value="gpt-4.1-mini">gpt-4.1-mini</option>
                                            <option value="gpt-4o">gpt-4o</option>
                                        </select>
                                    </div>
                                </div>
                                <div class="mb-3 row">
                                    <div class="col-sm-9 offset-sm-3">
                                        <button type="button" id="testApiKeyBtn" class="btn btn-outline-primary">
                                            <i class="fas fa-key"></i> Test OpenAI API Key
                                        </button>
                                        <span id="apiKeyTestStatus" class="ms-3"></span>
                                    </div>
                                </div>
                                <div class="alert alert-info">
                                    <i class="fas fa-lock"></i> Settings are securely encrypted when saved.
                                </div>
                            </form>
                        </div>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                    <button type="button" class="btn btn-primary" id="saveSettingsBtn">Save Settings</button>
                </div>
            </div>
        </div>
    </div>

    <!-- About Modal -->
    <div class="modal fade" id="aboutModal" tabindex="-1" aria-labelledby="aboutModalLabel" aria-hidden="true">
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="aboutModalLabel">About NL2SQL Query System</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    <h4>Natural Language to SQL Query System</h4>
                    <p>This application allows you to query MySQL databases using natural language. It converts your questions into 
                    SQL queries using OpenAI's models.</p>
                    
                    <h5>How it works:</h5>
                    <ol>
                        <li>Enter your question in natural language</li>
                        <li>The system converts it to a valid SQL query</li>
                        <li>The query is executed on your MySQL database</li>
                        <li>Results are displayed in table, chart, and summary formats</li>
                    </ol>
                    
                    <h5>Features:</h5>
                    <ul>
                        <li>Query databases using plain English</li>
                        <li>Visualize results automatically</li>
                        <li>Get AI-generated summaries of results</li>
                        <li>Secure query validation prevents harmful operations</li>
                    </ul>
                    
                    <p class="mt-4">Configure your database connection, API key, and AI model in the settings to get started.</p>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                </div>
            </div>
        </div>
    </div>

    <!-- View Schema Modal -->
    <div class="modal fade" id="schemaModal" tabindex="-1" aria-labelledby="schemaModalLabel" aria-hidden="true">
        <div class="modal-dialog modal-xl">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="schemaModalLabel">Database Schema</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    <div id="schemaContent" class="overflow-auto" style="max-height: 70vh;"></div>
                    <div id="schemaLoading" class="text-center p-3">
                        <div class="spinner-border text-primary" role="status">
                            <span class="visually-hidden">Loading...</span>
                        </div>
                        <p class="mt-2">Loading schema information...</p>
                    </div>
                    <div id="schemaError" class="alert alert-danger d-none"></div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                </div>
            </div>
        </div>
    </div>

    <!-- Error Toast -->
    <div class="position-fixed bottom-0 end-0 p-3" style="z-index: 11">
        <div id="errorToast" class="toast" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-header bg-danger text-white">
                <strong class="me-auto">Error</strong>
                <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
            <div class="toast-body" id="errorToastBody">
                An error occurred. Please try again.
            </div>
        </div>
    </div>
    
    <!-- Bootstrap 5 JS Bundle -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
    
    <!-- jQuery -->
    <script src="https://code.jquery.com/jquery-3.7.1.min.js"></script>
    
    <!-- Chart.js -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.js"></script>
    
    <!-- Custom JS -->
    <script src="assets/js/main.js"></script>
</body>
</html>