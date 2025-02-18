<?php
require 'vendor/autoload.php'; // For MongoDB client

// Database connections
$pg_params = [
    "dbname" => "medications_db",
    "user" => "postgres",
    "password" => "root",
    "host" => "localhost",
    "port" => "5432"
];

// PostgreSQL connection
$pg_conn = pg_connect(
    "dbname={$pg_params['dbname']} user={$pg_params['user']} password={$pg_params['password']} host={$pg_params['host']} port={$pg_params['port']}"
);

// MongoDB connection
$mongo_client = new MongoDB\Client("mongodb://localhost:27017/");
$mongo_db = $mongo_client->medicaments_db;
$collection = $mongo_db->ingredients;

// Fetch data from MongoDB (Example: for a specific ingredient "fentanyl")
$active_ingredient = "fentanyl";
$mongo_data = $collection->findOne(["Nom" => $active_ingredient]);

// Fetch data from PostgreSQL
$query = "SELECT m.med_name, m.dosage FROM medicaments m JOIN active_ingredient ai ON m.ain_id = ai.ain_id WHERE ai.ain_name = $1";
$result = pg_query_params($pg_conn, $query, [$active_ingredient]);
$medicaments = pg_fetch_all($result);

// Start HTML output
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Medicament Details</title>
    <link rel="stylesheet" href="styles.css"> <!-- Include your CSS file -->
</head>
<body>
    <?php include 'navbar.php'; ?>

    <div class="container">
        <h1>Details for Active Ingredient: <?php echo htmlspecialchars($active_ingredient); ?></h1>

        <?php
        if ($mongo_data) {
            foreach ($mongo_data as $key => $value) {
                if (!empty($value) && $key !== 'Nom') {
                    echo "<h2>" . htmlspecialchars($key) . "</h2>";

                    if (in_array($key, ["Précautions", "Risques liés au traitement"])) {
                        echo "<table class='data-table'>";
                        foreach ($value as $item) {
                            echo "<tr><td>" . htmlspecialchars($item) . "</td></tr>";
                        }
                        echo "</table>";
                    } else {
                        echo "<p>" . implode("</p><p>", array_map('htmlspecialchars', $value)) . "</p>";
                    }
                }
            }
        } else {
            echo "<p>No details found for this active ingredient.</p>";
        }
        ?>

        <h2>Medicaments</h2>
        <table class="data-table">
            <thead>
                <tr>
                    <th>Name</th>
                    <th>Dosage</th>
                </tr>
            </thead>
            <tbody>
                <?php
                if ($medicaments) {
                    foreach ($medicaments as $medicament) {
                        echo "<tr>";
                        echo "<td>" . htmlspecialchars($medicament['med_name']) . "</td>";
                        echo "<td>" . htmlspecialchars($medicament['dosage']) . "</td>";
                        echo "</tr>";
                    }
                } else {
                    echo "<tr><td colspan='2'>No medicaments found for this active ingredient.</td></tr>";
                }
                ?>
            </tbody>
        </table>
    </div>

    <?php include 'footer.php'; ?>
</body>
</html>
