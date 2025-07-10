<?php
// SECURITY TEST FILE - MEDIUM-RISK VIOLATIONS
// This file contains intentional security violations for testing Security Agent detection

// Medium-risk violations - missing input validation and sanitization

// Insecure file upload handling
function handle_file_upload() {
    // No file type validation
    // No file size validation
    // No file name sanitization
    
    if (isset($_FILES['upload'])) {
        $file = $_FILES['upload'];
        
        // Insecure: using original filename without validation
        $filename = $file['name'];
        $upload_path = '/var/www/uploads/' . $filename;
        
        // Insecure: no content validation
        move_uploaded_file($file['tmp_name'], $upload_path);
        
        echo "File uploaded: " . $filename;
    }
}

// Insecure form processing
function process_user_form() {
    // No CSRF token validation
    // No input sanitization
    // No input validation
    
    $username = $_POST['username'] ?? '';
    $email = $_POST['email'] ?? '';
    $age = $_POST['age'] ?? '';
    $website = $_POST['website'] ?? '';
    $bio = $_POST['bio'] ?? '';
    
    // Insecure: direct database insertion without validation
    $sql = "INSERT INTO users (username, email, age, website, bio) VALUES (?, ?, ?, ?, ?)";
    $stmt = $pdo->prepare($sql);
    $stmt->execute([$username, $email, $age, $website, $bio]);
    
    echo "User created successfully";
}

// Insecure search functionality
function search_users() {
    $search_term = $_GET['q'] ?? '';
    
    // Insecure: no input sanitization
    // Insecure: no SQL injection protection
    $sql = "SELECT * FROM users WHERE username LIKE '%" . $search_term . "%'";
    $result = $pdo->query($sql);
    
    // Insecure: no output sanitization
    while ($row = $result->fetch()) {
        echo "<div>" . $row['username'] . "</div>";
    }
}

// Insecure URL parameter handling
function get_user_profile() {
    $user_id = $_GET['id'] ?? '';
    
    // Insecure: no input validation
    // Insecure: no authorization check
    $sql = "SELECT * FROM users WHERE id = " . $user_id;
    $result = $pdo->query($sql);
    
    if ($row = $result->fetch()) {
        // Insecure: exposing sensitive information
        echo json_encode($row);
    }
}

// Insecure email validation
function validate_email($email) {
    // Insecure: weak email validation
    return strpos($email, '@') !== false;
}

// Insecure password validation
function validate_password($password) {
    // Insecure: no password complexity requirements
    return strlen($password) >= 4;
}

// Insecure URL validation
function validate_url($url) {
    // Insecure: no proper URL validation
    return filter_var($url, FILTER_VALIDATE_URL);
}

// Insecure file path validation
function validate_file_path($path) {
    // Insecure: no path traversal protection
    return file_exists($path);
}

// Insecure HTML sanitization
function sanitize_html($html) {
    // Insecure: weak HTML sanitization
    return htmlspecialchars($html, ENT_QUOTES);
}

// Insecure user input processing
function process_comment() {
    $comment = $_POST['comment'] ?? '';
    $user_id = $_SESSION['user_id'] ?? '';
    
    // Insecure: no input length validation
    // Insecure: no profanity filter
    // Insecure: no spam protection
    
    $sql = "INSERT INTO comments (user_id, comment) VALUES (?, ?)";
    $stmt = $pdo->prepare($sql);
    $stmt->execute([$user_id, $comment]);
    
    echo "Comment posted successfully";
}

// Insecure file download
function download_file() {
    $filename = $_GET['file'] ?? '';
    
    // Insecure: no path validation
    // Insecure: no authorization check
    $file_path = '/var/www/files/' . $filename;
    
    if (file_exists($file_path)) {
        // Insecure: no content-type validation
        header('Content-Type: application/octet-stream');
        header('Content-Disposition: attachment; filename="' . $filename . '"');
        readfile($file_path);
    }
}

// Insecure image processing
function process_image() {
    $image_data = $_POST['image'] ?? '';
    
    // Insecure: no image validation
    // Insecure: no size limits
    // Insecure: no format validation
    
    $decoded_image = base64_decode($image_data);
    $filename = 'image_' . time() . '.jpg';
    
    file_put_contents('/var/www/uploads/' . $filename, $decoded_image);
    
    echo "Image uploaded: " . $filename;
}

// Insecure JSON processing
function process_json() {
    $json_data = file_get_contents('php://input');
    
    // Insecure: no JSON validation
    // Insecure: no size limits
    $data = json_decode($json_data, true);
    
    // Insecure: no schema validation
    foreach ($data as $key => $value) {
        echo $key . ": " . $value . "<br>";
    }
}

// Insecure XML processing
function process_xml() {
    $xml_data = $_POST['xml'] ?? '';
    
    // Insecure: XXE vulnerability
    libxml_disable_entity_loader(false);
    $xml = simplexml_load_string($xml_data);
    
    // Insecure: no XML validation
    foreach ($xml as $element) {
        echo $element . "<br>";
    }
}

// Insecure CSV processing
function process_csv() {
    $csv_data = $_POST['csv'] ?? '';
    
    // Insecure: no CSV validation
    // Insecure: no injection protection
    $lines = explode("\n", $csv_data);
    
    foreach ($lines as $line) {
        $fields = explode(",", $line);
        // Insecure: no field validation
        $sql = "INSERT INTO data (field1, field2, field3) VALUES (?, ?, ?)";
        $stmt = $pdo->prepare($sql);
        $stmt->execute($fields);
    }
}

// Insecure redirect handling
function redirect_user() {
    $url = $_GET['redirect'] ?? '';
    
    // Insecure: no URL validation
    // Insecure: open redirect vulnerability
    if ($url) {
        header('Location: ' . $url);
        exit;
    }
}

// Insecure session handling
function handle_session() {
    // Insecure: no session validation
    // Insecure: no CSRF protection
    
    if (isset($_POST['action'])) {
        $action = $_POST['action'];
        
        // Insecure: no action validation
        switch ($action) {
            case 'login':
                $_SESSION['user_id'] = $_POST['user_id'];
                break;
            case 'logout':
                session_destroy();
                break;
            case 'admin':
                $_SESSION['is_admin'] = true;
                break;
        }
    }
}

// Insecure cookie handling
function set_user_cookie() {
    $user_data = $_POST['user_data'] ?? '';
    
    // Insecure: no cookie validation
    // Insecure: no encryption
    // Insecure: no secure flag
    setcookie('user_data', $user_data, time() + 3600, '/', '', false, false);
}

// Insecure header injection
function send_email() {
    $to = $_POST['to'] ?? '';
    $subject = $_POST['subject'] ?? '';
    $message = $_POST['message'] ?? '';
    
    // Insecure: no header injection protection
    $headers = "From: noreply@example.com\r\n";
    $headers .= "Reply-To: " . $_POST['reply_to'] . "\r\n";
    $headers .= "X-Mailer: PHP/" . phpversion();
    
    mail($to, $subject, $message, $headers);
}

// Insecure command execution
function execute_command() {
    $command = $_POST['command'] ?? '';
    
    // Insecure: no command validation
    // Insecure: command injection vulnerability
    $output = shell_exec($command);
    
    echo "<pre>" . $output . "</pre>";
}

// Insecure regular expression
function validate_input($input) {
    // Insecure: ReDoS vulnerability
    $pattern = '/^(a+)+b$/';
    return preg_match($pattern, $input);
}

// Insecure deserialization
function process_serialized_data() {
    $data = $_POST['data'] ?? '';
    
    // Insecure: unsafe deserialization
    $object = unserialize($data);
    
    // Insecure: no object validation
    if (is_object($object)) {
        echo "Object processed: " . get_class($object);
    }
}

// Export insecure functions
$insecure_functions = [
    'handle_file_upload',
    'process_user_form',
    'search_users',
    'get_user_profile',
    'validate_email',
    'validate_password',
    'process_comment',
    'download_file',
    'process_json',
    'process_xml',
    'redirect_user',
    'execute_command',
    'process_serialized_data'
];

?>