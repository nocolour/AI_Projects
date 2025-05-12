<?php
// Set headers to prevent caching
header('Cache-Control: no-store, no-cache, must-revalidate, max-age=0');
header('Cache-Control: post-check=0, pre-check=0', false);
header('Pragma: no-cache');
header('Content-Type: application/json');

// Define encryption key and method
define('ENCRYPTION_KEY', getEncryptionKey());
define('ENCRYPTION_METHOD', 'AES-256-CBC');

// Get or generate encryption key
function getEncryptionKey() {
    $keyFile = dirname(__FILE__) . '/.key';
    
    if (file_exists($keyFile)) {
        return file_get_contents($keyFile);
    }
    
    // Generate a new key if none exists
    $key = bin2hex(random_bytes(32));
    file_put_contents($keyFile, $key);
    chmod($keyFile, 0600); // Secure the file
    
    return $key;
}

// Encrypt data
function encryptData($data) {
    $ivLen = openssl_cipher_iv_length(ENCRYPTION_METHOD);
    $iv = openssl_random_pseudo_bytes($ivLen);
    $encrypted = openssl_encrypt(
        $data,
        ENCRYPTION_METHOD,
        hex2bin(ENCRYPTION_KEY),
        OPENSSL_RAW_DATA,
        $iv
    );
    
    return base64_encode($iv . $encrypted);
}

// Decrypt data
function decryptData($data) {
    $data = base64_decode($data);
    $ivLen = openssl_cipher_iv_length(ENCRYPTION_METHOD);
    $iv = substr($data, 0, $ivLen);
    $encrypted = substr($data, $ivLen);
    
    return openssl_decrypt(
        $encrypted,
        ENCRYPTION_METHOD,
        hex2bin(ENCRYPTION_KEY),
        OPENSSL_RAW_DATA,
        $iv
    );
}

// Save settings
function saveSettings($data) {
    $settingsFile = dirname(__FILE__) . '/.settings';
    $encrypted = encryptData(json_encode($data));
    
    if (file_put_contents($settingsFile, $encrypted)) {
        chmod($settingsFile, 0600); // Secure the file
        return true;
    }
    
    return false;
}

// Load settings
function loadSettings() {
    $settingsFile = dirname(__FILE__) . '/.settings';
    
    if (file_exists($settingsFile)) {
        $encrypted = file_get_contents($settingsFile);
        return json_decode(decryptData($encrypted), true);
    }
    
    return [];
}

// Handle API requests
$action = isset($_POST['action']) ? $_POST['action'] : '';

switch ($action) {
    case 'test_api_key':
        $apiKey = isset($_POST['api_key']) ? $_POST['api_key'] : '';
        testApiKey($apiKey);
        break;
        
    case 'save_settings':
        $settings = isset($_POST['settings']) ? $_POST['settings'] : '';
        handleSaveSettings($settings);
        break;
        
    case 'load_settings':
        handleLoadSettings();
        break;
        
    default:
        echo json_encode(['status' => 'error', 'message' => 'Unknown action']);
}

// Test OpenAI API key
function testApiKey($apiKey) {
    if (empty($apiKey)) {
        echo json_encode(['status' => 'error', 'message' => 'API key is required']);
        return;
    }
    
    // Create a cURL handle
    $ch = curl_init();
    
    // Set cURL options
    curl_setopt($ch, CURLOPT_URL, 'https://api.openai.com/v1/models');
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_HTTPHEADER, [
        'Authorization: Bearer ' . $apiKey,
        'Content-Type: application/json'
    ]);
    curl_setopt($ch, CURLOPT_TIMEOUT, 10);
    
    // Execute cURL request
    $response = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $error = curl_error($ch);
    
    curl_close($ch);
    
    if ($httpCode === 200) {
        echo json_encode(['status' => 'success', 'message' => 'API key is valid']);
    } else {
        $errorMessage = 'API key validation failed';
        if (!empty($error)) {
            $errorMessage .= ': ' . $error;
        } elseif ($response) {
            $decoded = json_decode($response, true);
            if (isset($decoded['error']['message'])) {
                $errorMessage .= ': ' . $decoded['error']['message'];
            }
        }
        echo json_encode(['status' => 'error', 'message' => $errorMessage]);
    }
}

// Handle settings save
function handleSaveSettings($settingsJson) {
    $settings = json_decode($settingsJson, true);
    
    if (json_last_error() !== JSON_ERROR_NONE) {
        echo json_encode(['status' => 'error', 'message' => 'Invalid settings data']);
        return;
    }
    
    if (saveSettings($settings)) {
        echo json_encode(['status' => 'success', 'message' => 'Settings saved successfully']);
    } else {
        echo json_encode(['status' => 'error', 'message' => 'Failed to save settings']);
    }
}

// Handle settings load
function handleLoadSettings() {
    $settings = loadSettings();
    echo json_encode(['status' => 'success', 'data' => $settings]);
}
?>
