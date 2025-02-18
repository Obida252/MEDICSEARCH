<?php

// Database credentials
$dbHost = 'localhost';
$dbName = 'medications_db';
$dbUser = 'postgres';
$dbPass = 'root';

// Directory containing SQL files
$sqlDirectory = __DIR__ . '/exported_tables';

try {
    // Connect to PostgreSQL database
    $pdo = new PDO("pgsql:host=$dbHost;port=5432;dbname=$dbName", $dbUser, $dbPass);
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

    // Define the execution order based on dependencies
    $executionOrder = [
        'active_ingredient.sql',
        'conditions.sql',
        'cyptochrome.sql',
        'manufacturer.sql',
        'pharmaceutic_form.sql',
        'subforms.sql',
        'effets_indesirables.sql',
        'medicaments.sql'
    ];

    foreach ($executionOrder as $fileName) {
        $filePath = $sqlDirectory . '/' . $fileName;

        if (!file_exists($filePath)) {
            echo "File not found: $fileName" . PHP_EOL;
            continue;
        }

        // Read the SQL file content
        $sql = file_get_contents($filePath);
        
        if ($sql === false) {
            echo "Failed to read file: $fileName" . PHP_EOL;
            continue;
        }

        // Execute the SQL commands
        $pdo->exec($sql);
        echo "Successfully executed: $fileName" . PHP_EOL;
    }

    echo "All SQL files have been loaded successfully." . PHP_EOL;

} catch (PDOException $e) {
    echo "Database error: " . $e->getMessage() . PHP_EOL;
} catch (Exception $e) {
    echo "Error: " . $e->getMessage() . PHP_EOL;
}
