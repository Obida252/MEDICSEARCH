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

if ($_SERVER['REQUEST_METHOD'] == 'POST') {
    $username = $_POST['username'];
    $email = $_POST['email'];
    $age = $_POST['age'];
    $profession = $_POST['profession'];
    $password = $_POST['password'];
    $hashedPassword = password_hash($password, PASSWORD_BCRYPT);

    // Check if email is already registered
    $stmt = $db->prepare("SELECT * FROM Users WHERE Email = :email");
    $stmt->execute([':email' => $email]);

    if ($stmt->rowCount() > 0) {
        $message = "Email is already registered. Try logging in.";
    } else {
        // Insert user into the database
        $stmt = $db->prepare("INSERT INTO Users (Username, Email, Password, Age, Profession, CreationDate) 
                              VALUES (:username, :email, :password, :age, :profession, NOW())");
        $stmt->execute([
            ':username' => $username,
            ':email' => $email,
            ':password' => $hashedPassword,
            ':age' => $age,
            ':profession' => $profession,
        ]);
        $message = "Registration successful! You can now log in.";
    }
}
?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="assets/inpn.css">
    <title>Register</title>
</head>
<body>
<div class="L_container">
    <div class="L_box L_form-box">
        <header>Register</header>
        <?php if (isset($message)) echo "<p class='message'>$message</p>"; ?>
        <form action="" method="POST">
            <div class="L_field L_input">
                <label for="username">Username</label>
                <input type="text" name="username" id="username" required>
            </div>
            <div class="L_field L_input">
                <label for="email">Email</label>
                <input type="email" name="email" id="email" required>
            </div>
            <div class="L_field L_input">
                <label for="age">Age</label>
                <input type="number" name="age" id="age">
            </div>
            <div class="L_field L_input">
                <label for="profession">Profession</label>
                <input type="text" name="profession" id="profession">
            </div>
            <div class="L_field L_input">
                <label for="password">Password</label>
                <input type="password" name="password" id="password" required>
            </div>
            <div class="L_field">
                <input type="submit" class="L_btn" value="Register">
            </div>
            <div class="L_links">
                Already have an account? <a href="login.php">Login here</a>
            </div>
        </form>
    </div>
</div>
</body>
</html>
