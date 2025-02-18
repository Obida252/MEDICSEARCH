<?php
// Start the session
session_start();
?>

<nav class="navbar">
  <div class="navbar__container">
    <a href="index.php" id="navbar__logo">MEDICSEARCH</a>
    <div class="navbar__toggle" id="mobile-menu">
      <span class="bar"></span>
      <span class="bar"></span>
      <span class="bar"></span>
    </div>
    <ul class="navbar__menu">
      <li class="navbar__item">
        <a href="index.php" class="navbar__links">Home</a>
      </li>
      <li class="navbar__item">
        <a href="about.php" class="navbar__links">About</a>
      </li>
      <li class="navbar__item">
        <a href="search.php" class="navbar__links">Search</a>
      </li>
      <?php if (isset($_SESSION['logged_in']) && $_SESSION['logged_in'] === true): ?>
        <li class="navbar__item navbar__user-dropdown">
          <div class="navbar__user-square">
            <span><?php echo htmlspecialchars($_SESSION['username']); ?></span>
          </div>
          <div class="dropdown__menu">
            <a href="logout.php" class="dropdown__link" onclick="return confirm('Are you sure you want to log out?')">Logout</a>
          </div>
        </li>
      <?php else: ?>
        <li class="navbar__btn">
          <a href="login.php" class="button">Sign In</a>
        </li>
      <?php endif; ?>
    </ul>
  </div>
</nav>

