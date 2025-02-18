<?php
// Database connection parameters
$dbHost = 'localhost';
$dbName = 'medications_db';
$dbUser = 'postgres';
$dbPass = 'root';

try {
    $db = new PDO("pgsql:host=$dbHost;dbname=$dbName", $dbUser, $dbPass);
    $db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
} catch (PDOException $e) {
    die("Database connection failed: " . $e->getMessage());
}

$message = ""; // Initialize $message to display feedback

if ($_SERVER['REQUEST_METHOD'] == 'POST') {
    $email = trim($_POST['email']);
    $password = trim($_POST['password']);

    // Check if user exists
    $stmt = $db->prepare("SELECT * FROM Users WHERE LOWER(Email) = LOWER(:email)");
    $stmt->execute([':email' => $email]);
    $user = $stmt->fetch(PDO::FETCH_ASSOC);

    if ($user) {
        if (isset($user['password']) && password_verify($password, $user['password'])) {
            session_start();
            $_SESSION['user_id'] = $user['userid'];
            $_SESSION['username'] = $user['username'];
            $_SESSION['logged_in'] = true; // Mark the user as logged in
            header("Location: index.php");
            exit;
        } else {
            $message = "The password you entered is incorrect."; // Incorrect password message
        }
    } else {
        $message = "No account found with that email address."; // No user found message
    }
}
?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="assets/inpn.css">
    <title>Login</title>
    <style>
        .message {
            color: red;
            font-size: 0.9em;
            margin-bottom: 10px;
        }
    </style>
</head>
<body>
<div class="L_container">
    <div class="L_box L_form-box">
        <header>Login</header>
        <!-- Display the message if it exists -->
        <?php if (!empty($message)) echo "<p class='message'>$message</p>"; ?>
        <form action="" method="POST">
            <div class="L_field L_input">
                <label for="email">Email</label>
                <input type="email" name="email" id="email" required>
            </div>
            <div class="L_field L_input">
                <label for="password">Password</label>
                <input type="password" name="password" id="password" required>
            </div>
            <div class="L_field">
                <input type="submit" class="L_btn" value="Login">
            </div>
            <div class="L_links">
                Don't have an account? <a href="register.php">Register here</a>
            </div>
        </form>
    </div>
</div>
</body>
</html>
