<?php
// MongoDB connection without Composer
try {
    $manager = new MongoDB\Driver\Manager("mongodb://localhost:27017");

    // Query to fetch data
    $filter = ['Nom' => 'fentanyl']; // Replace 'fentanyl' with your desired active ingredient
    $query = new MongoDB\Driver\Query($filter);
    $cursor = $manager->executeQuery("medicaments_db.ingredients", $query);

    // Convert data to an array
    $mongo_data = [];
    foreach ($cursor as $document) {
        $mongo_data = (array) $document; // Convert BSON to array
    }
} catch (MongoDB\Driver\Exception\Exception $e) {
    die("Error connecting to MongoDB: " . $e->getMessage());
}

// Example: Print fetched data
echo "<pre>";
print_r($mongo_data);
echo "</pre>";
?>
