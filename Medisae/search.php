<?php
// Database connection parameters
$dbname = 'medications_db';
$user = 'postgres';
$password = 'root';
$host = 'localhost';
$port = '5432';

// Establish connection
try {
    $db = new PDO("pgsql:host=$host;port=$port;dbname=$dbname", $user, $password);
    $db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
} catch (PDOException $e) {
    die("Error: " . $e->getMessage());
}

// Retrieve form inputs
$search = isset($_GET['search']) ? $_GET['search'] : '';
$condition = isset($_GET['condition']) ? $_GET['condition'] : '';
$manufacturer = isset($_GET['manufacturer']) ? $_GET['manufacturer'] : '';
$dosage = isset($_GET['dosage']) ? $_GET['dosage'] : '';
$form = isset($_GET['form']) ? $_GET['form'] : '';
$activeIngredient = isset($_GET['active_ingredient']) ? $_GET['active_ingredient'] : '';

// Build the base SQL query for results
$query = "SELECT m.med_name, m.dosage, mf.manu_name, pf.form_name, ai.ain_name, c.cond_name,
                 m.condition_id, m.manu_id, pf.form_id, m.ain_id";

if (!empty($search)) {
    $query .= ", similarity(m.med_name, :search) as name_similarity,
               similarity(ai.ain_name, :search) as ingredient_similarity";
}

$query .= " FROM medicaments m
           LEFT JOIN manufacturer mf ON m.manu_id = mf.manu_id
           LEFT JOIN subforms sf ON m.subform_id = sf.subform_id
           LEFT JOIN pharmaceutic_form pf ON sf.form_id = pf.form_id
           LEFT JOIN active_ingredient ai ON m.ain_id = ai.ain_id
           LEFT JOIN conditions c ON m.condition_id = c.cond_id
           WHERE 1=1";

$params = [];

if (!empty($search)) {
    $query .= " AND (similarity(m.med_name, :search) > 0.3 OR similarity(ai.ain_name, :search) > 0.3)";
    $params[':search'] = $search;
}

if (!empty($condition)) {
    $query .= " AND m.condition_id = :condition";
    $params[':condition'] = $condition;
}

if (!empty($manufacturer)) {
    $query .= " AND m.manu_id = :manufacturer";
    $params[':manufacturer'] = $manufacturer;
}

if (!empty($dosage)) {
    $query .= " AND m.dosage = :dosage";
    $params[':dosage'] = $dosage;
}

if (!empty($form)) {
    $query .= " AND pf.form_id = :form";
    $params[':form'] = $form;
}

if (!empty($activeIngredient)) {
    $query .= " AND m.ain_id = :activeIngredient";
    $params[':activeIngredient'] = $activeIngredient;
}

// Execute the query
$stmt = $db->prepare($query);
$stmt->execute($params);
$results = $stmt->fetchAll(PDO::FETCH_ASSOC);

// Extract unique values from results for filters
$availableConditions = array_unique(array_filter(array_column($results, 'condition_id')));
$availableManufacturers = array_unique(array_filter(array_column($results, 'manu_id')));
$availableDosages = array_unique(array_filter(array_column($results, 'dosage')));
$availableForms = array_unique(array_filter(array_column($results, 'form_id')));
$availableActiveIngredients = array_unique(array_filter(array_column($results, 'ain_id')));

// Fetch filter data based on available values
$conditions = $db->query("SELECT cond_id, cond_name FROM conditions" . 
    (!empty($availableConditions) ? " WHERE cond_id IN (" . implode(',', $availableConditions) . ")" : ""))
    ->fetchAll(PDO::FETCH_ASSOC);

$manufacturers = $db->query("SELECT manu_id, manu_name FROM manufacturer" . 
    (!empty($availableManufacturers) ? " WHERE manu_id IN (" . implode(',', $availableManufacturers) . ")" : ""))
    ->fetchAll(PDO::FETCH_ASSOC);

$dosages = $db->query("SELECT DISTINCT dosage FROM medicaments" . 
    (!empty($availableDosages) ? " WHERE dosage IN ('" . implode("','" , $availableDosages) . "')" : "") . " ORDER BY dosage")
    ->fetchAll(PDO::FETCH_ASSOC);

$forms = $db->query("SELECT form_id, form_name FROM pharmaceutic_form" . 
    (!empty($availableForms) ? " WHERE form_id IN (" . implode(',', $availableForms) . ")" : ""))
    ->fetchAll(PDO::FETCH_ASSOC);

$activeIngredients = $db->query("SELECT ain_id, ain_name FROM active_ingredient" . 
    (!empty($availableActiveIngredients) ? " WHERE ain_id IN (" . implode(',', $availableActiveIngredients) . ")" : ""))
    ->fetchAll(PDO::FETCH_ASSOC);
?>

<?php include("includes/navbar.php"); ?>

<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Pharma - Search</title>
  <link rel="stylesheet" href="assets/styles.css">
</head>
<body>

<div class="search__form">
  <form method="GET" action="">
    <input type="text" name="search" class="search__bar" placeholder="Search by name or active ingredient..." value="<?= htmlspecialchars($search ?? '') ?>">

    <div class="search__filters">
      <!-- Conditions Filter -->
      <select name="condition" class="search__filter">
        <option value="">Condition</option>
        <?php foreach ($conditions as $cond): ?>
          <option value="<?= $cond['cond_id'] ?>" <?= $cond['cond_id'] == $condition ? 'selected' : '' ?>><?= htmlspecialchars($cond['cond_name'] ?? '') ?></option>
        <?php endforeach; ?>
      </select>

      <!-- Manufacturer Filter -->
      <select name="manufacturer" class="search__filter">
        <option value="">Manufacturer</option>
        <?php foreach ($manufacturers as $manufacturer_option): ?>
          <option value="<?= $manufacturer_option['manu_id'] ?>" <?= $manufacturer_option['manu_id'] == $manufacturer ? 'selected' : '' ?>><?= htmlspecialchars($manufacturer_option['manu_name'] ?? '') ?></option>
        <?php endforeach; ?>
      </select>

      <!-- Dosage Filter -->
      <select name="dosage" class="search__filter">
        <option value="">Dosage</option>
        <?php foreach ($dosages as $dosage_option): ?>
          <option value="<?= $dosage_option['dosage'] ?>" <?= $dosage_option['dosage'] == $dosage ? 'selected' : '' ?>><?= htmlspecialchars($dosage_option['dosage'] ?? '') ?></option>
        <?php endforeach; ?>
      </select>

      <!-- Form Filter -->
      <select name="form" class="search__filter">
        <option value="">Pharmaceutical Form</option>
        <?php foreach ($forms as $form_option): ?>
          <option value="<?= $form_option['form_id'] ?>" <?= $form_option['form_id'] == $form ? 'selected' : '' ?>><?= htmlspecialchars($form_option['form_name'] ?? '') ?></option>
        <?php endforeach; ?>
      </select>

      <!-- Active Ingredient Filter -->
      <select name="active_ingredient" class="search__filter">
        <option value="">Active Ingredient</option>
        <?php foreach ($activeIngredients as $ingredient): ?>
          <option value="<?= $ingredient['ain_id'] ?>" <?= $ingredient['ain_id'] == $activeIngredient ? 'selected' : '' ?>><?= htmlspecialchars($ingredient['ain_name'] ?? '') ?></option>
        <?php endforeach; ?>
      </select>
    </div>

    <button type="submit" class="main__btn">Search</button>
  </form>
</div>

<div class="search__results">
    <h2 class="results__heading">Your Medicine Matches</h2>
    <?php if (count($results) > 0): ?>
        <div class="results__grid">
            <?php foreach ($results as $result): ?>
                <div class="result__item">
                    <h3 class="active__ingredient"><?= htmlspecialchars($result['ain_name'] ?? 'Unknown Ingredient') ?></h3>
                    <p><strong>Manufacturer:</strong> <?= htmlspecialchars($result['manu_name'] ?? 'N/A') ?></p>
                    <p><strong>Condition:</strong> <?= htmlspecialchars($result['cond_name'] ?? 'N/A') ?></p>
                    <p><strong>Dosage:</strong> <?= htmlspecialchars($result['dosage'] ?? 'N/A') ?></p>
                    <p><strong>Form:</strong> <?= htmlspecialchars($result['form_name'] ?? 'N/A') ?></p>
                    <a href="medi.php" class="savoir__plus">Savoir Plus</a>

                </div>
            <?php endforeach; ?>
        </div>
    <?php else: ?>
        <p class="no__results">No matches found. Try adjusting your filters.</p>
    <?php endif; ?>
    
</div>


<?php include("includes/footer.php"); ?>

</body>
</html>
