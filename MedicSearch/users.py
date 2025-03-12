from flask import Blueprint, render_template, redirect, url_for, request, flash, session

# Création du Blueprint utilisateur
users_bp = Blueprint('users', __name__, template_folder='templates')

# Routes utilisateur
@users_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Page de connexion utilisateur"""
    # Pour l'instant, juste le rendu du template
    # La logique de connexion sera implémentée ultérieurement
    if request.method == 'POST':
        # Simulation d'un message de notification
        flash("Fonction de connexion pas encore implémentée", "info")
        return redirect(url_for('users.login'))
        
    return render_template('user/login.html')


@users_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Page d'inscription utilisateur"""
    # Pour l'instant, juste le rendu du template
    # La logique d'inscription sera implémentée ultérieurement
    if request.method == 'POST':
        # Simulation d'un message de notification
        flash("Fonction d'inscription pas encore implémentée", "info")
        return redirect(url_for('users.register'))
        
    return render_template('user/register.html')


@users_bp.route('/logout')
def logout():
    """Déconnexion de l'utilisateur"""
    # À implémenter plus tard
    flash("Vous avez été déconnecté", "success")
    return redirect(url_for('main.index'))


@users_bp.route('/profile')
def profile():
    """Profil utilisateur"""
    # À implémenter plus tard
    return render_template('user/profile.html')


# Fonction pour initialiser le blueprint avec l'application Flask
def init_users(app):
    """Enregistre le blueprint utilisateurs dans l'application Flask"""
    app.register_blueprint(users_bp)
