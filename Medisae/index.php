<?php
// Include the Navbar
include("includes/navbar.php");
?>
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Pharma - Home</title>
  <link rel="stylesheet" href="assets/styles.css">
</head>
<body>
  <!-- Hero Section -->
  <div class="hero" id="home">
    <div class="hero__container">
      <h1 class="hero__heading">Makes Your Health <span>Better</span></h1>
      <p class="hero__description">
        Access reliable medicines anytime, anywhere.
      </p>
      <button class="main__btn"><a href="search.php">Get Started</a></button>
    </div>
  </div>

  <?php
// Include the Footer
include("includes/footer.php");
?>

  <script src="app.js"></script>
</body>
</html>
