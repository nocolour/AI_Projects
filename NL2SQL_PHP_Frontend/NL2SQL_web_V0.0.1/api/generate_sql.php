<?php
// Set headers for JSON response
header('Content-Type: application/json');

// Get the POST data
$postData = json_decode(file_get_contents('php://input'), true);

if (!$postData) {
    http_response_code(400);
    echo json_encode(['error' => 'Invalid request data']);
    exit;
}

// Extract parameters
$naturalLanguageQuery = $postData['query'] ?? '';
$apiKey = $postData['apiKey'] ?? '';
$model = $postData['model'] ?? 'gpt-4o-mini';
$database = $postData['database'] ?? [];

// Validate input
if (empty($naturalLanguageQuery)) {
    http_response_code(400);
    echo json_encode(['error' => 'Query cannot be empty']);
    exit;
}

if (empty($apiKey)) {
    http_response_code(400);
    echo json_encode(['error' => 'API key is required']);
    exit;
}

try {
    // Call OpenAI API to generate SQL
    $sql = callOpenAI($naturalLanguageQuery, $apiKey, $model, $database);
    
    // Return the generated SQL
    echo json_encode([
        'success' => true,
        'sql' => $sql
    ]);
    
} catch (Exception $e) {
    http_response_code(500);
    echo json_encode([
        'error' => $e->getMessage()
    ]);
}

/**
 * Calls the OpenAI API to generate an SQL query
 * 
 * @param string $query The natural language query
 * @param string $apiKey OpenAI API key
 * @param string $model AI model to use
 * @param array $database Database information
 * @return string Generated SQL query
 */
function callOpenAI($query, $apiKey, $model, $database) {
    $url = 'https://api.openai.com/v1/chat/completions';
    
    // Create a context for the AI to understand the database structure
    $systemPrompt = "You are an SQL expert. Convert the natural language query to a valid MySQL SQL query for the database '{$database['database']}'. Respond only with the SQL query, no explanations. Ensure the SQL is secure and properly formatted.";
    
    $data = [
        'model' => $model,
        'messages' => [
            ['role' => 'system', 'content' => $systemPrompt],
            ['role' => 'user', 'content' => $query]
        ],
        'temperature' => 0.3,
        'max_tokens' => 500
    ];
    
    $headers = [
        'Content-Type: application/json',
        'Authorization: Bearer ' . $apiKey
    ];
    
    $curl = curl_init($url);
    curl_setopt($curl, CURLOPT_POST, true);
    curl_setopt($curl, CURLOPT_POSTFIELDS, json_encode($data));
    curl_setopt($curl, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($curl, CURLOPT_HTTPHEADER, $headers);
    
    $response = curl_exec($curl);
    
    if (curl_errno($curl)) {
        throw new Exception('API request error: ' . curl_error($curl));
    }
    
    curl_close($curl);
    
    $responseData = json_decode($response, true);
    
    if (isset($responseData['error'])) {
        throw new Exception('OpenAI API error: ' . $responseData['error']['message']);
    }
    
    if (!isset($responseData['choices'][0]['message']['content'])) {
        throw new Exception('Unexpected API response format');
    }
    
    return $responseData['choices'][0]['message']['content'];
}
?>
