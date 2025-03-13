from flask import Blueprint, render_template, redirect, url_for, request, flash, make_response, g, current_app, abort
from functools import wraps
import models  # Changé de "from . import models" à "import models"
import json
import base64
from werkzeug.security import generate_password_hash, check_password_hash

# Création du Blueprint utilisateur
users_bp = Blueprint('users', __name__, template_folder='templates')

# Décorateur pour vérifier si l'utilisateur est connecté
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in request.cookies:
            flash("Vous devez être connecté pour accéder à cette page.", "warning")
            return redirect(url_for('users.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# Décorateur pour vérifier le rôle de l'utilisateur
def role_required(min_role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in request.cookies:
                flash("Vous devez être connecté pour accéder à cette page.", "warning")
                return redirect(url_for('users.login', next=request.url))
                
            if 'role' not in request.cookies or int(request.cookies.get('role')) < min_role:
                flash("Vous n'avez pas les permissions nécessaires pour accéder à cette page.", "danger")
                return redirect(url_for('main.index'))
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Configuration pour charger l'utilisateur avant chaque requête
@users_bp.before_app_request
def load_logged_in_user():
    """Charge l'utilisateur actuel dans g.user"""
    user_id = request.cookies.get('user_id')
    
    if user_id is None:
        g.user = None
    else:
        g.user = models.User.get_by_id(user_id)

# Routes utilisateur
@users_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Page d'inscription utilisateur"""
    if request.cookies.get('user_id'):
        return redirect(url_for('main.index'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        first_name = request.form.get('first_name', '')
        last_name = request.form.get('last_name', '')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Vérification des données
        if not email or not password or not confirm_password:
            flash("Tous les champs sont obligatoires.", "danger")
            return render_template('user/register.html')
            
        if password != confirm_password:
            flash("Les mots de passe ne correspondent pas.", "danger")
            return render_template('user/register.html')
        
        # Création de l'utilisateur
        user_id = models.User.create(email, password, first_name, last_name)
        if user_id:
            # Journaliser l'inscription
            models.Log.create(user_id, models.Log.ACTION_REGISTER)
            
            flash("Votre compte a été créé avec succès. Vous pouvez maintenant vous connecter.", "success")
            return redirect(url_for('users.login'))
        else:
            flash("Cette adresse email est déjà utilisée. Veuillez en choisir une autre.", "danger")
            
    return render_template('user/register.html')

@users_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Page de connexion utilisateur"""
    if request.cookies.get('user_id'):
        return redirect(url_for('main.index'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = request.form.get('remember') == 'on'
        
        # Vérification des identifiants
        user = models.User.check_password(email, password)
        if user:
            # Créer la réponse
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                response = make_response(redirect(next_page))
            else:
                response = make_response(redirect(url_for('main.index')))
            
            # Définir les cookies
            cookie_options = {
                'httponly': True,
                'secure': request.is_secure,  # Utiliser HTTPS en production
                'samesite': 'Lax'
            }
            
            # Si "se souvenir de moi" est coché, définir max_age à 30 jours
            if remember:
                cookie_options['max_age'] = 30 * 24 * 60 * 60  # 30 jours en secondes
                
            response.set_cookie('user_id', str(user['_id']), **cookie_options)
            response.set_cookie('role', str(user['role']), **cookie_options)
            
            # Journaliser la connexion
            models.Log.create(str(user['_id']), models.Log.ACTION_LOGIN)
            
            flash("Connexion réussie!", "success")
            return response
        else:
            flash("Email ou mot de passe incorrect.", "danger")
            
    return render_template('user/login.html')

@users_bp.route('/logout')
def logout():
    """Déconnexion de l'utilisateur"""
    user_id = request.cookies.get('user_id')
    if user_id:
        # Journaliser la déconnexion
        models.Log.create(user_id, models.Log.ACTION_LOGOUT)
    
    # Créer la réponse et supprimer les cookies
    response = make_response(redirect(url_for('main.index')))
    response.delete_cookie('user_id')
    response.delete_cookie('role')
    
    flash("Vous avez été déconnecté avec succès.", "success")
    return response

@users_bp.route('/profile')
@login_required
def profile():
    """Profil de l'utilisateur connecté"""
    return render_template('user/profile.html', user=g.user)

@users_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Édition du profil utilisateur"""
    if request.method == 'POST':
        # Récupérer les données modifiées
        update_data = {
            'first_name': request.form.get('first_name'),
            'last_name': request.form.get('last_name')
        }
        
        # Ajouter les champs optionnels s'ils sont fournis
        optional_fields = ['age', 'profession', 'company']
        for field in optional_fields:
            if request.form.get(field):
                if field == 'age':
                    # Convertir en nombre
                    try:
                        update_data[field] = int(request.form.get(field))
                    except ValueError:
                        pass
                else:
                    update_data[field] = request.form.get(field)
        
        user_id = request.cookies.get('user_id')
        # Mettre à jour le profil
        if models.User.update(user_id, update_data):
            # Journaliser la mise à jour du profil
            models.Log.create(user_id, models.Log.ACTION_PROFILE_UPDATE)
            
            flash("Votre profil a été mis à jour avec succès.", "success")
        else:
            flash("Une erreur est survenue lors de la mise à jour de votre profil.", "danger")
            
        return redirect(url_for('users.profile'))
        
    return render_template('user/edit_profile.html', user=g.user)

@users_bp.route('/profile/password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Modification du mot de passe"""
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Vérifier que le mot de passe actuel est correct
        user = models.User.check_password(g.user['email'], current_password)
        if not user:
            flash("Mot de passe actuel incorrect.", "danger")
            return render_template('user/change_password.html')
            
        # Vérifier que les nouveaux mots de passe correspondent
        if new_password != confirm_password:
            flash("Les nouveaux mots de passe ne correspondent pas.", "danger")
            return render_template('user/change_password.html')
            
        user_id = request.cookies.get('user_id')
        # Mettre à jour le mot de passe
        if models.User.update_password(user_id, new_password):
            # Journaliser le changement de mot de passe
            models.Log.create(user_id, models.Log.ACTION_PASSWORD_CHANGE)
            
            flash("Votre mot de passe a été modifié avec succès.", "success")
            return redirect(url_for('users.profile'))
        else:
            flash("Une erreur est survenue lors de la modification de votre mot de passe.", "danger")
            
    return render_template('user/change_password.html')

# Routes pour les commentaires
@users_bp.route('/medicines/<medicine_id>/comments', methods=['POST'])
@login_required
def add_comment(medicine_id):
    """Ajouter un commentaire à un médicament"""
    content = request.form.get('content')
    rating = request.form.get('rating')
    
    if not content:
        flash("Le contenu du commentaire est obligatoire.", "danger")
        return redirect(url_for('main.medicine_details', id=medicine_id))
        
    # Convertir rating en nombre si fourni
    rating_val = None
    if rating:
        try:
            rating_val = int(rating)
        except ValueError:
            pass
            
    # Déterminer la visibilité en fonction du rôle de l'utilisateur
    visibility = [1, 2, 3, 4]  # Par défaut, visible par tous les utilisateurs enregistrés
    
    user_id = request.cookies.get('user_id')
    # Créer le commentaire
    comment_id = models.Comment.create(
        user_id,
        medicine_id,
        content,
        visibility,
        rating_val
    )
    
    if comment_id:
        flash("Votre commentaire a été ajouté avec succès.", "success")
    else:
        flash("Une erreur est survenue lors de l'ajout de votre commentaire.", "danger")
        
    return redirect(url_for('main.medicine_details', id=medicine_id))

@users_bp.route('/comments/<comment_id>/edit', methods=['POST'])
@login_required
def edit_comment(comment_id):
    """Modifier un commentaire"""
    content = request.form.get('content')
    rating = request.form.get('rating')
    medicine_id = request.form.get('medicine_id')
    
    if not content or not medicine_id:
        flash("Informations manquantes.", "danger")
        return redirect(url_for('main.medicine_details', id=medicine_id))
        
    # Convertir rating en nombre si fourni
    update_data = {'content': content}
    if rating:
        try:
            update_data['rating'] = int(rating)
        except ValueError:
            pass
            
    user_id = request.cookies.get('user_id')
    # Mettre à jour le commentaire
    if models.Comment.update(comment_id, user_id, update_data):
        flash("Votre commentaire a été modifié avec succès.", "success")
    else:
        flash("Une erreur est survenue lors de la modification de votre commentaire.", "danger")
        
    return redirect(url_for('main.medicine_details', id=medicine_id))

@users_bp.route('/comments/<comment_id>/delete', methods=['POST'])
@login_required
def delete_comment(comment_id):
    """Supprimer un commentaire"""
    medicine_id = request.form.get('medicine_id')
    
    if not medicine_id:
        abort(400)
        
    # Vérifier si l'utilisateur est admin
    is_admin = request.cookies.get('role') and int(request.cookies.get('role')) >= models.User.ROLE_ADMIN
    
    user_id = request.cookies.get('user_id')
    # Supprimer le commentaire
    if models.Comment.delete(comment_id, user_id, is_admin):
        flash("Le commentaire a été supprimé avec succès.", "success")
    else:
        flash("Une erreur est survenue lors de la suppression du commentaire.", "danger")
        
    return redirect(url_for('main.medicine_details', id=medicine_id))

# Routes pour les favoris
@users_bp.route('/medicines/<medicine_id>/favorite', methods=['POST'])
@login_required
def toggle_favorite(medicine_id):
    """Ajouter/Retirer un médicament des favoris"""
    user_id = request.cookies.get('user_id')
    is_favorite = models.Interaction.create(
        user_id,
        medicine_id,
        models.Interaction.TYPE_FAVORITE
    )
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Réponse AJAX
        return {'status': 'success', 'is_favorite': is_favorite}
    
    # Redirection normale
    return redirect(url_for('main.medicine_details', id=medicine_id))

@users_bp.route('/favorites')
@login_required
def favorites():
    """Liste des médicaments favoris de l'utilisateur"""
    user_id = request.cookies.get('user_id')
    favorite_ids = models.Interaction.get_favorites(user_id)
    
    # Récupérer les détails des médicaments favoris
    from .app import collection  # Importer la collection depuis app.py
    from bson.objectid import ObjectId
    favorites = list(collection.find({"_id": {"$in": [ObjectId(id) for id in favorite_ids]}}))
    
    return render_template('user/favorites.html', favorites=favorites)

# Routes administratives
@users_bp.route('/admin/users')
@role_required(models.User.ROLE_ADMIN)
def admin_users():
    """Liste des utilisateurs pour l'administration"""
    page = request.args.get('page', 1, type=int)
    limit = 20
    skip = (page - 1) * limit
    
    filters = {}
    if request.args.get('role'):
        try:
            filters['role'] = int(request.args.get('role'))
        except ValueError:
            pass
            
    if request.args.get('status'):
        filters['status'] = request.args.get('status')
        
    users = models.User.list(filters, limit, skip)
    
    return render_template('admin/users.html', users=users, roles=models.User.ROLE_NAMES)

@users_bp.route('/admin/users/<user_id>', methods=['GET', 'POST'])
@role_required(models.User.ROLE_ADMIN)
def admin_edit_user(user_id):
    """Édition d'un utilisateur par un administrateur"""
    user = models.User.get_by_id(user_id)
    if not user:
        abort(404)
        
    if request.method == 'POST':
        update_data = {}
        
        # Mettre à jour le rôle si fourni
        if request.form.get('role'):
            try:
                update_data['role'] = int(request.form.get('role'))
            except ValueError:
                flash("Rôle invalide.", "danger")
                return render_template('admin/edit_user.html', user=user, roles=models.User.ROLE_NAMES)
                
        # Mettre à jour le statut du compte si fourni
        if request.form.get('account_status'):
            update_data['account_status'] = request.form.get('account_status')
            
        # Appliquer les mises à jour
        if update_data and models.User.update(user_id, update_data):
            flash("L'utilisateur a été mis à jour avec succès.", "success")
        else:
            flash("Aucune modification n'a été appliquée.", "warning")
            
        return redirect(url_for('users.admin_users'))
        
    return render_template('admin/edit_user.html', user=user, roles=models.User.ROLE_NAMES)

# Fonction pour initialiser le blueprint avec l'application Flask
def init_users(app):
    """Enregistre le blueprint utilisateurs dans l'application Flask"""
    app.register_blueprint(users_bp)
