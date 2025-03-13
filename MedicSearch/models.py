from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from bson.objectid import ObjectId
from flask import current_app

# Initialiser PyMongo avec None - sera configuré dans l'application
mongo = PyMongo()

class User:
    """Modèle pour la collection users dans MongoDB"""
    
    ROLE_VISITOR = 0
    ROLE_PATIENT = 1
    ROLE_PROFESSIONAL = 2
    ROLE_RESEARCHER = 3
    ROLE_ADMIN = 4
    
    ROLE_NAMES = {
        ROLE_VISITOR: "Visiteur",
        ROLE_PATIENT: "Patient",
        ROLE_PROFESSIONAL: "Professionnel de santé",
        ROLE_RESEARCHER: "Chercheur",
        ROLE_ADMIN: "Administrateur"
    }
    
    STATUS_ACTIVE = 'active'
    STATUS_INACTIVE = 'inactive'
    STATUS_VERIFIED = 'verified'
    
    @staticmethod
    def create(email, password, first_name, last_name, role=1):
        """Crée un nouvel utilisateur"""
        # Vérifier que l'email n'est pas déjà utilisé
        if mongo.db.users.find_one({"email": email}):
            return None
            
        user_data = {
            "email": email,
            "password_hash": generate_password_hash(password, method='pbkdf2:sha256', salt_length=10),
            "first_name": first_name,
            "last_name": last_name,
            "role": role,
            "date_created": datetime.utcnow(),
            "account_status": User.STATUS_ACTIVE
        }
        
        result = mongo.db.users.insert_one(user_data)
        return str(result.inserted_id)
    
    @staticmethod
    def get_by_id(user_id):
        """Récupère un utilisateur par son ID"""
        try:
            user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
            return user
        except:
            return None
    
    @staticmethod
    def get_by_email(email):
        """Récupère un utilisateur par son email"""
        return mongo.db.users.find_one({"email": email})
    
    @staticmethod
    def check_password(email, password):
        """Vérifie le mot de passe pour un email donné"""
        user = User.get_by_email(email)
        if not user:
            return None
            
        if check_password_hash(user["password_hash"], password):
            # Mettre à jour la date de dernière connexion
            mongo.db.users.update_one(
                {"_id": user["_id"]}, 
                {"$set": {"last_login": datetime.utcnow()}}
            )
            return user
        
        return None
    
    @staticmethod
    def update(user_id, update_data):
        """Met à jour les données d'un utilisateur"""
        # Ne pas autoriser la mise à jour de certains champs sensibles
        if "password_hash" in update_data or "email" in update_data:
            return False
            
        result = mongo.db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_data}
        )
        return result.modified_count > 0
    
    @staticmethod
    def update_password(user_id, new_password):
        """Met à jour le mot de passe d'un utilisateur"""
        result = mongo.db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"password_hash": generate_password_hash(new_password, method='pbkdf2:sha256', salt_length=10)}}
        )
        return result.modified_count > 0
        
    @staticmethod
    def list(filters=None, limit=20, skip=0):
        """Liste les utilisateurs avec filtres optionnels"""
        query = {}
        if filters:
            if "role" in filters:
                query["role"] = filters["role"]
            if "status" in filters:
                query["account_status"] = filters["status"]
                
        return list(mongo.db.users.find(query).limit(limit).skip(skip))


class Comment:
    """Modèle pour la collection comments dans MongoDB"""
    
    STATUS_PUBLISHED = 'published'
    STATUS_MODERATED = 'moderated'
    STATUS_DELETED = 'deleted'
    
    @staticmethod
    def create(user_id, medicine_id, content, visibility=None, rating=None):
        """Crée un nouveau commentaire"""
        # Par défaut, visible par tous les utilisateurs enregistrés
        if visibility is None:
            visibility = [1, 2, 3, 4]  # Tous les rôles sauf visiteur
            
        comment_data = {
            "user_id": ObjectId(user_id),
            "medicine_id": medicine_id,  # medicine_id est déjà une string
            "content": content,
            "visibility": visibility,
            "timestamp": datetime.utcnow(),
            "status": Comment.STATUS_PUBLISHED
        }
        
        if rating is not None:
            comment_data["rating"] = max(1, min(5, rating))  # Limiter entre 1 et 5
            
        result = mongo.db.comments.insert_one(comment_data)
        return str(result.inserted_id)
    
    @staticmethod
    def get_by_id(comment_id):
        """Récupère un commentaire par son ID"""
        try:
            comment = mongo.db.comments.find_one({"_id": ObjectId(comment_id)})
            return comment
        except:
            return None
    
    @staticmethod
    def get_for_medicine(medicine_id, user_role=None):
        """Récupère les commentaires pour un médicament avec filtrage par rôle"""
        query = {
            "medicine_id": medicine_id,
            "status": Comment.STATUS_PUBLISHED
        }
        
        # Filtrer les commentaires par visibilité selon le rôle de l'utilisateur
        if user_role is not None:
            query["visibility"] = user_role
            
        return list(mongo.db.comments.find(query).sort("timestamp", -1))
    
    @staticmethod
    def update(comment_id, user_id, update_data):
        """Met à jour un commentaire (uniquement par l'auteur)"""
        # Vérifier que l'utilisateur est bien l'auteur du commentaire
        comment = Comment.get_by_id(comment_id)
        if not comment or str(comment["user_id"]) != str(user_id):
            return False
            
        # Autoriser uniquement la mise à jour du contenu et du rating
        safe_update = {}
        if "content" in update_data:
            safe_update["content"] = update_data["content"]
        if "rating" in update_data:
            safe_update["rating"] = max(1, min(5, update_data["rating"]))
            
        if safe_update:
            safe_update["last_edited"] = datetime.utcnow()
            result = mongo.db.comments.update_one(
                {"_id": ObjectId(comment_id)},
                {"$set": safe_update}
            )
            return result.modified_count > 0
            
        return False
    
    @staticmethod
    def delete(comment_id, user_id=None, admin=False):
        """Supprime un commentaire (soft delete) par l'auteur ou un admin"""
        if admin:
            # Si c'est un admin, pas besoin de vérifier l'auteur
            query = {"_id": ObjectId(comment_id)}
        else:
            # Sinon vérifier que l'utilisateur est bien l'auteur
            query = {
                "_id": ObjectId(comment_id),
                "user_id": ObjectId(user_id)
            }
            
        result = mongo.db.comments.update_one(
            query,
            {"$set": {"status": Comment.STATUS_DELETED}}
        )
        return result.modified_count > 0


class Interaction:
    """Modèle pour la collection interactions dans MongoDB"""
    
    TYPE_FAVORITE = 'favorite'
    TYPE_VIEW = 'view'
    TYPE_SEARCH = 'search'
    
    @staticmethod
    def create(user_id, medicine_id, interaction_type):
        """Crée ou met à jour une interaction utilisateur-médicament"""
        # Pour les favoris, on vérifie s'il existe déjà et on fait un toggle
        if interaction_type == Interaction.TYPE_FAVORITE:
            existing = mongo.db.interactions.find_one({
                "user_id": ObjectId(user_id),
                "medicine_id": medicine_id,
                "type": Interaction.TYPE_FAVORITE
            })
            
            if existing:
                # Si existe déjà, on supprime (toggle)
                mongo.db.interactions.delete_one({"_id": existing["_id"]})
                return False
                
        # Créer la nouvelle interaction
        interaction_data = {
            "user_id": ObjectId(user_id),
            "medicine_id": medicine_id,
            "type": interaction_type,
            "timestamp": datetime.utcnow()
        }
        
        mongo.db.interactions.insert_one(interaction_data)
        return True
    
    @staticmethod
    def get_favorites(user_id):
        """Récupère les médicaments favoris de l'utilisateur"""
        interactions = mongo.db.interactions.find({
            "user_id": ObjectId(user_id),
            "type": Interaction.TYPE_FAVORITE
        })
        
        return [i["medicine_id"] for i in interactions]
    
    @staticmethod
    def is_favorite(user_id, medicine_id):
        """Vérifie si un médicament est dans les favoris"""
        return mongo.db.interactions.find_one({
            "user_id": ObjectId(user_id),
            "medicine_id": medicine_id,
            "type": Interaction.TYPE_FAVORITE
        }) is not None


class Log:
    """Modèle pour la collection logs dans MongoDB"""
    
    ACTION_LOGIN = 'login'
    ACTION_LOGOUT = 'logout'
    ACTION_REGISTER = 'register'
    ACTION_PASSWORD_CHANGE = 'password_change'
    ACTION_PROFILE_UPDATE = 'profile_update'
    
    @staticmethod
    def create(user_id, action, details=None):
        """Crée une entrée de journal"""
        log_data = {
            "user_id": ObjectId(user_id),
            "action": action,
            "timestamp": datetime.utcnow()
        }
        
        if details:
            log_data["details"] = details
            
        mongo.db.logs.insert_one(log_data)

# Fonction d'initialisation pour configurer les modèles avec l'app Flask
def init_db(app):
    """Initialise la connexion à la base de données"""
    mongo.init_app(app)
    
    # Création des index si nécessaire
    with app.app_context():
        # Index sur l'email des utilisateurs (unique)
        mongo.db.users.create_index("email", unique=True)
        
        # Index sur les commentaires pour recherche efficace
        mongo.db.comments.create_index([
            ("medicine_id", 1),
            ("status", 1),
            ("visibility", 1)
        ])
        
        # Index sur les interactions
        mongo.db.interactions.create_index([
            ("user_id", 1),
            ("medicine_id", 1),
            ("type", 1)
        ], unique=True)
