<?php
// Include Navbar
include 'includes/navbar.php';

// PostgreSQL Connection
$pg_params = [
    "dbname" => "medications_db",
    "user" => "postgres",
    "password" => "root",
    "host" => "localhost",
    "port" => "5432"
];
$pg_conn = pg_connect(
    "dbname={$pg_params['dbname']} user={$pg_params['user']} password={$pg_params['password']} host={$pg_params['host']} port={$pg_params['port']}"
);

// Query for Medicaments with ain_id = 2
$query = "SELECT med_name, dosage FROM medicaments WHERE ain_id = 2";
$result = pg_query($pg_conn, $query);
$medicaments = pg_fetch_all($result);
?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Medication Details</title>
    <link rel="stylesheet" href="assets/style.css"> 
</head>
<body>
    <!-- Main Container -->
    <div class="container">
        <h1 class="hero__heading">Nom: Acarbose</h1>

        <h2>Indications</h2>
        <p class="hero__description">Diabète non insulinodépendant</p>

        <h2>Modalités d'administration</h2>
        <ul class="search__filters">
            <li>Voie orale</li>
            <li>A croquer ou à avaler</li>
            <li>Administrer au début du repas</li>
            <li>Administrer avec un aliment ou une boisson</li>
            <li>Posologie à adapter à la glycémie</li>
            <li>Utiliser le dosage le plus adapté à la posologie</li>
        </ul>

        <h2>Contre-indications</h2>
        <ul class="search__filters">
            <li>Colite ulcéreuse</li>
            <li>Dyspepsie sévère</li>
            <li>Grossesse</li>
            <li>Hernie intestinale majeure</li>
            <li>Hypersensibilité à l'un des composants</li>
            <li>Insuffisance hépatique sévère</li>
            <li>Insuffisance rénale sévère : clairance de la créatinine &lt; 25 ml/min</li>
            <li>Maladie inflammatoire de l'intestin</li>
            <li>Obstruction intestinale</li>
            <li>Patient dont l'état peut être aggravé par l'augmentation de la formation de gaz intestinaux</li>
            <li>Sujet à risque d'occlusion intestinale</li>
        </ul>

        <h2>Mesures à associer au traitement</h2>
        <p>Respecter des mesures hygiéno-diététiques</p>

        <h2>Médicaments contenant le même ingrédient actif</h2>
        <table class="data-table">
            <thead>
                <tr>
                    <th>Nom du médicament</th>
                    <th>Dosage</th>
                </tr>
            </thead>
            <tbody>
                <?php if ($medicaments): ?>
                    <?php foreach ($medicaments as $medicament): ?>
                        <tr class="result__item">
                            <td class="medicine__name"><?php echo htmlspecialchars($medicament['med_name']); ?></td>
                            <td class="medicine__dosage"><?php echo htmlspecialchars($medicament['dosage']); ?></td>
                        </tr>
                    <?php endforeach; ?>
                <?php else: ?>
                    <tr>
                        <td colspan="2">Aucun médicament trouvé pour cet ingrédient actif.</td>
                    </tr>
                <?php endif; ?>
            </tbody>
        </table>
    </div>

    <!-- Include Footer -->
    <?php include 'includes/footer.php'; ?>
</body>
</html>
