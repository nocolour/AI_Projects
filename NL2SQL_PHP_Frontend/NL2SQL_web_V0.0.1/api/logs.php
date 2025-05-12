<?php
header('Content-Type: application/json');

// Configuration
$logDirectory = '../logs/';
$logFile = $logDirectory . 'error_log.txt';

// Create logs directory if it doesn't exist
if (!file_exists($logDirectory)) {
    mkdir($logDirectory, 0755, true);
}

// Ensure the log file exists
if (!file_exists($logFile)) {
    file_put_contents($logFile, "# Error Log Initialized: " . date('Y-m-d H:i:s') . "\n");
    chmod($logFile, 0644);
}

/**
 * Write a message to the error log
 *
 * @param string $level Error level (error, warning, info, debug)
 * @param string $message The log message
 * @param array $context Additional context data (optional)
 * @return bool True on success, false on failure
 */
function writeLog($level, $message, $context = []) {
    global $logFile;
    
    $timestamp = date('Y-m-d H:i:s');
    $contextStr = !empty($context) ? ' ' . json_encode($context) : '';
    $logEntry = "[$timestamp] [$level] $message$contextStr" . PHP_EOL;
    
    return file_put_contents($logFile, $logEntry, FILE_APPEND) !== false;
}

// Handle API requests
$action = isset($_GET['action']) ? $_GET['action'] : '';

switch ($action) {
    case 'add':
        // Add new log entry
        $level = isset($_POST['level']) ? $_POST['level'] : 'info';
        $message = isset($_POST['message']) ? $_POST['message'] : 'No message provided';
        $context = isset($_POST['context']) ? json_decode($_POST['context'], true) : [];
        
        if (writeLog($level, $message, $context)) {
            echo json_encode(['success' => true]);
        } else {
            http_response_code(500);
            echo json_encode(['success' => false, 'error' => 'Failed to write log entry']);
        }
        break;
        
    case 'get':
        // Get log entries
        if (file_exists($logFile)) {
            $filter = isset($_GET['filter']) ? $_GET['filter'] : 'all';
            $search = isset($_GET['search']) ? $_GET['search'] : '';
            $limit = isset($_GET['limit']) ? (int)$_GET['limit'] : 1000;  // Limit number of lines
            
            // Read log file
            $logs = file($logFile, FILE_IGNORE_NEW_LINES);
            $logs = array_reverse($logs);  // Most recent first
            
            // Apply level filter
            if ($filter !== 'all') {
                $logs = array_filter($logs, function($line) use ($filter) {
                    switch($filter) {
                        case 'error':
                            return strpos($line, '[error]') !== false;
                        case 'warning':
                            return strpos($line, '[error]') !== false || strpos($line, '[warning]') !== false;
                        case 'info':
                            return strpos($line, '[error]') !== false || strpos($line, '[warning]') !== false || strpos($line, '[info]') !== false;
                        default:
                            return true;
                    }
                });
            }
            
            // Apply search filter
            if (!empty($search)) {
                $logs = array_filter($logs, function($line) use ($search) {
                    return stripos($line, $search) !== false;
                });
            }
            
            // Apply limit
            $logs = array_slice($logs, 0, $limit);
            
            echo json_encode([
                'success' => true, 
                'logs' => $logs, 
                'count' => count($logs),
                'timestamp' => date('Y-m-d H:i:s')
            ]);
        } else {
            echo json_encode(['success' => false, 'error' => 'Log file not found']);
        }
        break;
        
    case 'clear':
        // Clear log file
        if (file_put_contents($logFile, "# Error Log Cleared: " . date('Y-m-d H:i:s') . "\n") !== false) {
            echo json_encode(['success' => true]);
        } else {
            http_response_code(500);
            echo json_encode(['success' => false, 'error' => 'Failed to clear log file']);
        }
        break;
        
    default:
        http_response_code(400);
        echo json_encode(['success' => false, 'error' => 'Invalid action']);
}
?>
