from flask import Flask, request, render_template, jsonify, abort, redirect, url_for, stream_with_context, Response, session, g
from pymongo import MongoClient
from bson.objectid import ObjectId
import json
from bson import json_util
import time
import hashlib
from functools import lru_cache
import os
import datetime
from models import init_db, mongo, User
import users  # Importer le module users complet
from users import role_required  # Importer la fonction spécifique role_required
from config import get_config
# Import the AI summary module
from ai_summary import get_or_generate_summary

app = Flask(__name__)
# Charger la configuration
app_config = get_config()
app.config.from_object(app_config)

# Configuration de la connexion à MongoDB
client = MongoClient(app.config['MONGO_URI'])
# Correction de l'erreur: utiliser try-except au lieu de l'opérateur OR
try:
    db = client.get_default_database()
except:
    db = client['medicsearch']
collection = db['medicines']

# Important: Initialiser la base de données avant de définir app.db
init_db(app)

# Définir db comme attribut de l'application pour qu'il soit accessible partout
app.db = db

# Fonction pour convertir les objets BSON en JSON serializable
def bson_to_json(data):
    """Convertit les objets BSON en dictionnaires JSON serialisables"""
    return json.loads(json_util.dumps(data))

# Fonction pour extraire le nom du médicament
def extract_medicine_name(medicine):
    """Extrait le nom du médicament."""
    # Utiliser le titre s'il est disponible (dans la nouvelle structure)
    if 'title' in medicine and medicine['title']:
        return medicine['title']
    
    # Chercher dans la section 1 (DÉNOMINATION DU MÉDICAMENT)
    if 'sections' in medicine and medicine['sections']:
        for section in medicine['sections']:
            if section['title'] == "1. DENOMINATION DU MEDICAMENT" and section.get('content'):
                for content in section['content']:
                    if 'text' in content:
                        return content['text']
    
    # Si aucun nom n'est trouvé, utiliser l'ID comme nom par défaut
    return f"Médicament {medicine['_id']}"

@app.route('/')
def index():
    """Page d'accueil"""
    # Utiliser la connexion MongoDB déjà établie au lieu de models.mongo.db
    
    # Obtenir des statistiques sur la base de données
    total_medicines = collection.count_documents({})
    
    # Récupérer des statistiques de base
    lab_count = len(db.medicines.distinct("medicine_details.laboratoire"))
    substance_count = len(db.medicines.distinct("medicine_details.substances_actives"))
    
    # Récupérer les médicaments les plus récemment mis à jour pour la section "featured"
    featured_medicines = list(db.medicines.find({}, {"title": 1, "update_date": 1})
                           .sort("update_date", -1).limit(3))
    
    return render_template('index.html',
                          total_medicines=total_medicines,
                          lab_count=lab_count,
                          substance_count=substance_count,
                          featured_medicines=featured_medicines)

def extract_filter_options():
    """Extrait les options de filtre disponibles à partir de l'ensemble de la base de données"""
    # Vérifier si nous avons déjà extrait les options de filtrage
    cached_filters = getattr(extract_filter_options, 'cached_filters', None)
    if cached_filters:
        return cached_filters
    
    # Initialiser les ensembles pour stocker les valeurs uniques
    substances_actives = set()
    formes_pharma = set()
    laboratoires = set()
    dosages = set()
    
    # Analyser un échantillon représentatif de la base de données
    try:
        sample_size = 100
        medicines = list(collection.find().limit(sample_size))
        
        for medicine in medicines:
            # Extraction directement depuis medicine_details
            if 'medicine_details' in medicine:
                # Substances actives
                if 'substances_actives' in medicine['medicine_details'] and medicine['medicine_details']['substances_actives']:
                    for substance in medicine['medicine_details']['substances_actives']:
                        if substance and len(substance) > 2:  # Ignorer les valeurs trop courtes
                            substances_actives.add(substance)
                
                # Formes pharmaceutiques
                if 'forme' in medicine['medicine_details'] and medicine['medicine_details']['forme']:
                    forme = medicine['medicine_details']['forme']
                    if forme and len(forme) > 2:  # Ignorer les valeurs trop courtes
                        formes_pharma.add(forme)
                
                # Laboratoires
                if 'laboratoire' in medicine['medicine_details'] and medicine['medicine_details']['laboratoire']:
                    laboratoire = medicine['medicine_details']['laboratoire']
                    if laboratoire and len(laboratoire) > 2:
                        laboratoires.add(laboratoire)
                
                # Dosages
                if 'dosages' in medicine['medicine_details'] and medicine['medicine_details']['dosages']:
                    for dosage in medicine['medicine_details']['dosages']:
                        if dosage and len(str(dosage)) > 1:
                            dosages.add(dosage)
    except Exception as e:
        print(f"Erreur lors de l'extraction des filtres: {e}")
    
    # Convertir en listes triées
    result = {
        'substances': sorted(list(substances_actives)),
        'formes': sorted(list(formes_pharma)),
        'laboratoires': sorted(list(laboratoires)),
        'dosages': sorted(list(dosages))
    }
    
    # Cacher les résultats comme attribut de la fonction pour les prochains appels
    extract_filter_options.cached_filters = result
    return result

def extract_filter_options_from_results(medicines):
    """Extrait les options de filtre disponibles uniquement à partir des résultats actuels"""
    # Initialiser les ensembles pour stocker les valeurs uniques
    substances_actives = set()
    formes_pharma = set()
    laboratoires = set()
    dosages = set()
    
    # Parcourir les résultats de recherche actuels
    for medicine in medicines:
        # Extraction depuis medicine_details
        if 'medicine_details' in medicine:
            # Substances actives
            if 'substances_actives' in medicine['medicine_details'] and medicine['medicine_details']['substances_actives']:
                for substance in medicine['medicine_details']['substances_actives']:
                    if substance and len(substance) > 2:  # Ignorer les valeurs trop courtes
                        substances_actives.add(substance)
            
            # Formes pharmaceutiques
            if 'forme' in medicine['medicine_details'] and medicine['medicine_details']['forme']:
                forme = medicine['medicine_details']['forme']
                if forme and len(forme) > 2:  # Ignorer les valeurs trop courtes
                    formes_pharma.add(forme)
            
            # Laboratoires
            if 'laboratoire' in medicine['medicine_details'] and medicine['medicine_details']['laboratoire']:
                laboratoire = medicine['medicine_details']['laboratoire']
                if laboratoire and len(laboratoire) > 2:
                    laboratoires.add(laboratoire)
            
            # Dosages
            if 'dosages' in medicine['medicine_details'] and medicine['medicine_details']['dosages']:
                for dosage in medicine['medicine_details']['dosages']:
                    if dosage and len(str(dosage)) > 1:
                        dosages.add(dosage)
    
    # Convertir en listes triées
    result = {
        'substances': sorted(list(substances_actives)),
        'formes': sorted(list(formes_pharma)),
        'laboratoires': sorted(list(laboratoires)),
        'dosages': sorted(list(dosages))
    }
    
    return result

@app.route('/search')
def search():
    # Récupérer les paramètres pour les passer au template
    search_query = request.args.get('search', '')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    substance = request.args.get('substance', '')
    forme = request.args.get('forme', '')
    laboratoire = request.args.get('laboratoire', '')
    dosage = request.args.get('dosage', '')
    sort_option = request.args.get('sort', 'date_desc')
    advanced_search = substance or forme or laboratoire or dosage or sort_option != 'date_desc'
    
    # Get filter options
    available_filters = extract_filter_options()

    # Rendre le template sans les résultats
    return render_template('search.html',
                          search=search_query,
                          substance=substance,
                          forme=forme,
                          laboratoire=laboratoire,
                          dosage=dosage,
                          sort=sort_option,
                          advanced_search=advanced_search,
                          current_page=page,
                          per_page=per_page,
                          available_filters=available_filters)

@lru_cache(maxsize=1024)
def convert_french_date_cached(date_str):
    """Version mise en cache de la conversion de date française"""
    if not date_str or not isinstance(date_str, str):
        return 0
    
    try:
        if '/' in date_str:
            day, month, year = map(int, date_str.split('/'))
            # Retourner une clé de tri au format AAAAMMJJ
            return year * 10000 + month * 100 + day
    except (ValueError, AttributeError):
        return 0
    return 0

def sort_medicines_by_date(medicines, sort_direction):
    """Trie les médicaments par date au format français (JJ/MM/AAAA)"""
    sort_start_time = time.time()
    
    def convert_french_date(medicine):
        # Vérifier si update_date existe dans le document
        if 'update_date' not in medicine:
            return 0
        
        # Utiliser la version mise en cache de la conversion
        return convert_french_date_cached(medicine['update_date'])
    
    # Utiliser la fonction de conversion pour trier
    sorted_medicines = sorted(
        medicines, 
        key=convert_french_date,
        reverse=(sort_direction == -1)  # True si sort_direction est -1 (descendant)
    )
    
    sort_duration = time.time() - sort_start_time
    print(f"TRI PAR DATE: {len(medicines)} documents triés en {sort_duration:.3f} secondes")
    
    return sorted_medicines

def calculate_relevance_score(medicine, search_query):
    """Calcule un score de pertinence pour le classement des résultats."""
    score = 0
    search_terms = search_query.lower().split()
    total_matches = 0  # Compteur pour le nombre total de correspondances
    
    # Si le terme de recherche est dans le titre (très important)
    if 'title' in medicine:
        title = medicine['title'].lower()
        for term in search_terms:
            term_count = title.count(term)
            if term_count > 0:
                score += 10 * term_count
                total_matches += term_count
                # Si c'est un match exact du titre, c'est encore mieux
                if title == term:
                    score += 15
    
    # Si le terme est dans les substances actives (important)
    if 'medicine_details' in medicine and 'substances_actives' in medicine['medicine_details']:
        for substance in medicine['medicine_details']['substances_actives']:
            substance_lower = substance.lower() if substance else ""
            for term in search_terms:
                term_count = substance_lower.count(term)
                if term_count > 0:
                    score += 8 * term_count
                    total_matches += term_count
                    # Match exact de la substance active
                    if substance_lower == term:
                        score += 10
    
    # Si le terme est dans la forme pharmaceutique ou le dosage (moyennement important)
    if 'medicine_details' in medicine:
        if 'forme' in medicine['medicine_details']:
            forme_lower = medicine['medicine_details']['forme'].lower()
            for term in search_terms:
                term_count = forme_lower.count(term)
                if term_count > 0:
                    score += 5 * term_count
                    total_matches += term_count
        
        if 'dosages' in medicine['medicine_details'] and medicine['medicine_details']['dosages']:
            for dosage in medicine['medicine_details']['dosages']:
                dosage_lower = str(dosage).lower() if dosage else ""
                for term in search_terms:
                    term_count = dosage_lower.count(term)
                    if term_count > 0:
                        score += 5 * term_count
                        total_matches += term_count
    
    # Si le terme est dans le contenu (moins important)
    if 'sections' in medicine:
        for section in medicine['sections']:
            section_importance = 0
            # Les sections avec des informations importantes ont un poids plus élevé
            important_sections = ["1. DENOMINATION DU MEDICAMENT", "2. COMPOSITION QUALITATIVE ET QUANTITATIVE"]
            if section['title'] in important_sections:
                section_importance = 3
            
            # Vérifier le titre de la section
            section_title_lower = section['title'].lower()
            for term in search_terms:
                term_count = section_title_lower.count(term)
                if term_count > 0:
                    score += (2 + section_importance) * term_count
                    total_matches += term_count
            
            if 'content' in section and section['content']:
                for content_item in section['content']:
                    if 'text' in content_item:
                        text_lower = content_item['text'].lower()
                        for term in search_terms:
                            term_count = text_lower.count(term)
                            if term_count > 0:
                                score += (1 + section_importance) * term_count
                                total_matches += term_count
            
            # Chercher dans les sous-sections
            if 'subsections' in section:
                for subsection in section['subsections']:
                    # Vérifier le titre de la sous-section
                    subsection_title_lower = subsection['title'].lower()
                    for term in search_terms:
                        term_count = subsection_title_lower.count(term)
                        if term_count > 0:
                            score += 2 * term_count
                            total_matches += term_count
                    
                    if 'content' in subsection and subsection['content']:
                        for content_item in subsection['content']:
                            if 'text' in content_item:
                                text_lower = content_item['text'].lower()
                                for term in search_terms:
                                    term_count = text_lower.count(term)
                                    if term_count > 0:
                                        score += 1 * term_count
                                        total_matches += term_count
    
    # Ajouter le nombre total de correspondances au score pour qu'il compte dans le tri
    score += total_matches
    
    # Stocker le nombre de correspondances dans l'objet médicament pour l'affichage
    medicine['match_count'] = total_matches
    
    return score

def find_search_term_locations(medicine, search_query):
    """Identifie les endroits où les termes de recherche ont été trouvés dans un médicament."""
    if not search_query:
        return []
    
    matches = []
    search_terms = search_query.lower().split()
    
    # Vérifier dans le titre
    if 'title' in medicine:
        title_lower = medicine['title'].lower()
        for term in search_terms:
            if term in title_lower:
                term_count = title_lower.count(term)
                matches.append({
                    'location': 'Titre',
                    'text': medicine['title'],
                    'term': term,
                    'count': term_count,
                    'priority': 1  # Priorité élevée pour le titre
                })
    
    # Vérifier dans les détails du médicament
    if 'medicine_details' in medicine:
        # Chercher dans substances_actives
        if 'substances_actives' in medicine['medicine_details'] and medicine['medicine_details']['substances_actives']:
            for substance in medicine['medicine_details']['substances_actives']:
                substance_lower = substance.lower() if substance else ""
                for term in search_terms:
                    if term in substance_lower:
                        term_count = substance_lower.count(term)
                        matches.append({
                            'location': 'Substance active',
                            'text': substance,
                            'term': term,
                            'count': term_count,
                            'priority': 2  # Priorité haute pour substances actives
                        })
        
        # Chercher dans laboratoire
        if 'laboratoire' in medicine['medicine_details'] and medicine['medicine_details']['laboratoire']:
            lab_lower = medicine['medicine_details']['laboratoire'].lower()
            for term in search_terms:
                if term in lab_lower:
                    term_count = lab_lower.count(term)
                    matches.append({
                        'location': 'Laboratoire',
                        'text': medicine['medicine_details']['laboratoire'],
                        'term': term,
                        'count': term_count,
                        'priority': 3
                    })
        
        # Chercher dans forme
        if 'forme' in medicine['medicine_details'] and medicine['medicine_details']['forme']:
            forme_lower = medicine['medicine_details']['forme'].lower()
            for term in search_terms:
                if term in forme_lower:
                    term_count = forme_lower.count(term)
                    matches.append({
                        'location': 'Forme pharmaceutique',
                        'text': medicine['medicine_details']['forme'],
                        'term': term,
                        'count': term_count,
                        'priority': 3
                    })
        
        # Chercher dans dosages
        if 'dosages' in medicine['medicine_details'] and medicine['medicine_details']['dosages']:
            for dosage in medicine['medicine_details']['dosages']:
                dosage_str = str(dosage).lower() if dosage else ""
                for term in search_terms:
                    if term in dosage_str:
                        term_count = dosage_str.count(term)
                        matches.append({
                            'location': 'Dosage',
                            'text': str(dosage),
                            'term': term,
                            'count': term_count,
                            'priority': 3
                        })
    
    # Chercher dans le contenu des sections
    if 'sections' in medicine:
        for section in medicine['sections']:
            section_title = section.get('title', '')
            
            # Vérifier d'abord dans le titre de la section
            section_title_lower = section_title.lower()
            for term in search_terms:
                if term in section_title_lower:
                    term_count = section_title_lower.count(term)
                    matches.append({
                        'location': f"Section: {section_title}",
                        'text': section_title,
                        'term': term,
                        'count': term_count,
                        'priority': 3
                    })
            
            # Chercher dans le contenu de la section
            if 'content' in section and section['content']:
                for content_item in section['content']:
                    if 'text' in content_item and content_item['text']:
                        text_lower = content_item['text'].lower()
                        for term in search_terms:
                            if term in text_lower:
                                term_count = text_lower.count(term)
                                # Extraire un extrait du texte autour du terme
                                excerpt = extract_excerpt(content_item['text'], term)
                                matches.append({
                                    'location': section_title,
                                    'text': excerpt,
                                    'term': term,
                                    'count': term_count,
                                    'priority': 4
                                })
            
            # Chercher dans le contenu des sous-sections
            if 'subsections' in section and section['subsections']:
                for subsection in section['subsections']:
                    subsection_title = subsection.get('title', '')
                    
                    # Vérifier dans le titre de la sous-section
                    subsection_title_lower = subsection_title.lower()
                    for term in search_terms:
                        if term in subsection_title_lower:
                            term_count = subsection_title_lower.count(term)
                            matches.append({
                                'location': f"{section_title} > {subsection_title}",
                                'text': subsection_title,
                                'term': term,
                                'count': term_count,
                                'priority': 3
                            })
                    
                    if 'content' in subsection and subsection['content']:
                        for content_item in subsection['content']:
                            if 'text' in content_item and content_item['text']:
                                text_lower = content_item['text'].lower()
                                for term in search_terms:
                                    if term in text_lower:
                                        term_count = text_lower.count(term)
                                        # Extraire un extrait du texte autour du terme
                                        excerpt = extract_excerpt(content_item['text'], term)
                                        matches.append({
                                            'location': f"{section_title} > {subsection_title}",
                                            'text': excerpt,
                                            'term': term,
                                            'count': term_count,
                                            'priority': 5
                                        })
                    
                    # Chercher dans les sous-sous-sections si elles existent
                    if 'subsections' in subsection and subsection['subsections']:
                        for sub_subsection in subsection['subsections']:
                            sub_subsection_title = sub_subsection.get('title', '')
                            
                            # Vérifier dans le titre de la sous-sous-section
                            sub_subsection_title_lower = sub_subsection_title.lower()
                            for term in search_terms:
                                if term in sub_subsection_title_lower:
                                    term_count = sub_subsection_title_lower.count(term)
                                    matches.append({
                                        'location': f"{section_title} > {subsection_title} > {sub_subsection_title}",
                                        'text': sub_subsection_title,
                                        'term': term,
                                        'count': term_count,
                                        'priority': 3
                                    })
                            
                            if 'content' in sub_subsection and sub_subsection['content']:
                                for content_item in sub_subsection['content']:
                                    if 'text' in content_item and content_item['text']:
                                        text_lower = content_item['text'].lower()
                                        for term in search_terms:
                                            if term in text_lower:
                                                term_count = text_lower.count(term)
                                                # Extraire un extrait du texte autour du terme
                                                excerpt = extract_excerpt(content_item['text'], term)
                                                matches.append({
                                                    'location': f"{section_title} > {subsection_title} > {sub_subsection_title}",
                                                    'text': excerpt,
                                                    'term': term,
                                                    'count': term_count,
                                                    'priority': 6
                                                })
    
    # Trier les correspondances par priorité puis par nombre d'occurrences
    matches = sorted(matches, key=lambda x: (x.get('priority', 999), -x.get('count', 0)))
    
    # Limiter le nombre de correspondances à afficher
    return matches[:5]  # Retourner au maximum 5 correspondances

def extract_excerpt(text, term):
    """Extrait un court extrait du texte autour du terme recherché."""
    term_lower = term.lower()
    text_lower = text.lower()
    
    # Trouver la position du terme dans le texte
    pos = text_lower.find(term_lower)
    if pos == -1:
        return text[:100] + "..."  # Retourner le début du texte si terme non trouvé
    
    # Trouver le début and la fin de la phrase contenant le terme
    sentence_start = max(0, text_lower.rfind('.', 0, pos))
    if sentence_start == 0:
        # Si pas de point trouvé, essayer d'autres délimiteurs
        sentence_start = max(0, text_lower.rfind('!', 0, pos))
        sentence_start = max(0, text_lower.rfind('?', 0, pos))
    
    sentence_end = text_lower.find('.', pos)
    if sentence_end == -1:
        # Si pas de point trouvé, chercher d'autres délimiteurs ou prendre la fin du texte
        sentence_end = text_lower.find('!', pos)
        if sentence_end == -1:
            sentence_end = text_lower.find('?', pos)
            if sentence_end == -1:
                sentence_end = len(text)
    else:
        sentence_end += 1  # Inclure le point final
    
    # Si la phrase est trop longue, créer un extrait plus court autour du terme
    if sentence_end - sentence_start > 150:
        # Calculer les positions de début and de fin pour l'extrait
        start_pos = max(0, pos - 60)
        end_pos = min(len(text), pos + len(term) + 60)
    else:
        start_pos = sentence_start
        end_pos = sentence_end
    
    # Créer l'extrait
    excerpt = ""
    if start_pos > 0:
        excerpt += "..."
    excerpt += text[start_pos:end_pos]
    if end_pos < len(text):
        excerpt += "..."
    
    return excerpt

@app.route('/medicine/<id>')
def medicine_details(id):
    """Route pour les détails d'un médicament spécifique"""
    try:
        medicine = collection.find_one({'_id': ObjectId(id)})
        if not medicine:
            abort(404)
        
        # Ajouter le nom extrait comme attribut du médicament
        medicine['name'] = extract_medicine_name(medicine)
        
        # Check if we already have a summary, but don't wait for generation
        # This allows the page to load quickly
        existing_summary = None
        if db is not None:
            try:
                stored_medicine = db.medicines.find_one(
                    {"_id": ObjectId(id)}, 
                    {"ai_summary": 1}
                )
                if stored_medicine and 'ai_summary' in stored_medicine:
                    existing_summary = stored_medicine['ai_summary']
            except Exception as e:
                print(f"Error checking for cached summary: {e}")
        
        # Set the summary if it exists, otherwise it will be loaded via AJAX
        medicine['ai_summary'] = existing_summary
        
        # Vérifier si le médicament est un favori pour l'utilisateur connecté
        is_favorite = False
        comments = []
        user_role = None
        
        # Si l'utilisateur est connecté, récupérer ses interactions
        if 'user_id' in request.cookies:
            from models import Interaction, Comment
            user_id = request.cookies.get('user_id')
            is_favorite = Interaction.is_favorite(user_id, str(medicine['_id']))
            user_role = request.cookies.get('role')
            if user_role:
                user_role = int(user_role)
            
            # Récupérer les commentaires pour ce médicament visibles par l'utilisateur
            comments = Comment.get_for_medicine(str(medicine['_id']), user_role)
        else:
            # Même pour les utilisateurs non connectés, récupérer les commentaires publics
            from models import Comment
            comments = Comment.get_for_medicine(str(medicine['_id']))
        
        # Ajouter les informations utilisateur à chaque commentaire, que l'utilisateur soit connecté ou non
        for comment in comments:
            try:
                comment_user = User.get_by_id(comment['user_id'])
                if comment_user:
                    comment['user'] = {
                        'first_name': comment_user.get('first_name', 'Utilisateur'),
                        'last_name': comment_user.get('last_name', '')
                    }
            except Exception as e:
                print(f"Erreur lors de la récupération des données utilisateur: {e}")
                # Si on ne peut pas récupérer l'utilisateur, on met un placeholder
                comment['user'] = {
                    'first_name': 'Utilisateur',
                    'last_name': ''
                }
        
        # S'assurer que chaque élément de contenu a un champ html_content
        if 'sections' in medicine:
            for section in medicine['sections']:
                if 'content' in section:
                    for content_item in section['content']:
                        # Traiter le texte normal
                        if 'text' in content_item and 'html_content' not in content_item:
                            # Créer un contenu HTML basique si manquant
                            text = content_item['text']
                            # Convertir les sauts de ligne en <br>
                            html_text = text.replace('\n', '<br>')
                            # Garder le texte simple en HTML mais avec les sauts de ligne
                            content_item['html_content'] = f"<p>{html_text}</p>"
                        
                        # S'assurer que les tableaux sont correctement formatés
                        if 'table' in content_item and isinstance(content_item['table'], list):
                            # Le tableau est déjà bien formaté, pas besoin de le modifier
                            pass
                
                # Traiter également les sous-sections
                if 'subsections' in section:
                    for subsection in section['subsections']:
                        if 'content' in subsection:
                            for content_item in subsection['content']:
                                # Traiter le texte normal
                                if 'text' in content_item and 'html_content' not in content_item:
                                    text = content_item['text']
                                    html_text = text.replace('\n', '<br>')
                                    content_item['html_content'] = f"<p>{html_text}</p>"
                                
                                # S'assurer que les tableaux sont correctement formatés
                                if 'table' in content_item and isinstance(content_item['table'], list):
                                    # Le tableau est déjà bien formaté, pas besoin de le modifier
                                    pass
                        
                        # Traiter également les sous-sous-sections si elles existent
                        if 'subsections' in subsection:
                            for sub_subsection in subsection['subsections']:
                                if 'content' in sub_subsection:
                                    for content_item in sub_subsection['content']:
                                        # Traiter le texte normal
                                        if 'text' in content_item and 'html_content' not in content_item:
                                            text = content_item['text']
                                            html_text = text.replace('\n', '<br>')
                                            content_item['html_content'] = f"<p>{html_text}</p>"
                                        
                                        # S'assurer que les tableaux sont correctement formatés
                                        if 'table' in content_item and isinstance(content_item['table'], list):
                                            # Le tableau est déjà bien formaté, pas besoin de le modifier
                                            pass
        
        # Convertir en JSON pour l'affichage brut
        medicine_json = json.dumps(bson_to_json(medicine), indent=2, ensure_ascii=False)
        return render_template('medicine_details.html', 
                               medicine=medicine, 
                               medicine_json=medicine_json,
                               is_favorite=is_favorite,
                               comments=comments)
    
    except Exception as e:
        print(f"Erreur dans medicine_details: {e}")
        abort(404)

@app.route('/raw/<id>')
def raw_medicine(id):
    """Route pour voir les données brutes d'un médicament en JSON"""
    try:
        medicine = collection.find_one({'_id': ObjectId(id)})
        if not medicine:
            abort(404)
        return jsonify(json.loads(json_util.dumps(medicine)))
    except:
        abort(404)

@app.route('/debug')
def debug_info():
    """Page de debug pour afficher la structure de la base de données"""
    collection_stats = db.command("collStats", "medicines")
    sample_doc = collection.find_one()
    sample_json = json_util.dumps(sample_doc, indent=2)
    
    # Liste des champs présents dans les documents
    fields = set()
    for doc in collection.find().limit(100):
        fields.update(doc.keys())
    
    # Get filter options
    available_filters = extract_filter_options()
    
    return render_template('debug.html', 
                          stats=collection_stats,
                          sample=sample_json,
                          fields=sorted(list(fields)),
                          available_filters=available_filters)

@app.route('/api/search-results')
def search_results_api():
    search_query = request.args.get('search', '')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    substance = request.args.get('substance', '')
    forme = request.args.get('forme', '')
    laboratoire = request.args.get('laboratoire', '')
    dosage = request.args.get('dosage', '')
    sort_option = request.args.get('sort', 'date_desc')

    query = {}
    pipeline_filters = []

    # Construction de la requête de recherche
    if search_query:
        search_regex = {'$regex': search_query, '$options': 'i'}
        pipeline_filters.append({'$or': [
            {'title': search_regex},
            {'medicine_details.substances_actives': search_regex},
            {'sections.content.text': search_regex},  # Recherche dans les sections
            {'sections.subsections.content.text': search_regex},
            {'sections.subsections.subsections.content.text': search_regex}
        ]})
    if substance:
        pipeline_filters.append({'medicine_details.substances_actives': {'$regex': substance, '$options': 'i'}})
    if forme:
        pipeline_filters.append({'medicine_details.forme': {'$regex': forme, '$options': 'i'}})
    if laboratoire:
        pipeline_filters.append({'medicine_details.laboratoire': {'$regex': laboratoire, '$options': 'i'}})
    if dosage:
        pipeline_filters.append({'medicine_details.dosages': {'$regex': dosage, '$options': 'i'}})

    # Combiner les filtres avec $and
    if pipeline_filters:
        query['$and'] = pipeline_filters

    # Calculer le nombre de documents correspondant à la requête
    total_results = collection.count_documents(query)

    # Gestion du tri
    if sort_option == 'relevance' and search_query:
        # Calculer le score de pertinence pour chaque médicament
        medicines = list(collection.find(query).skip((page - 1) * per_page).limit(per_page))
        for medicine in medicines:
            medicine['relevance_score'] = calculate_relevance_score(medicine, search_query)
        
        # Trier les médicaments par score de pertinence
        medicines = sorted(medicines, key=lambda x: x['relevance_score'], reverse=True)
    elif sort_option.startswith('name'):
        # Tri par nom
        sort_field = 'title'
        sort_direction = 1 if sort_option == 'name_asc' else -1
        medicines = list(collection.find(query).sort([(sort_field, sort_direction)]).skip((page - 1) * per_page).limit(per_page))
    else:
        # Tri par date (par défaut)
        sort_direction = -1 if sort_option == 'date_desc' else 1
        medicines = list(collection.find(query).skip((page - 1) * per_page).limit(per_page))
        medicines = sort_medicines_by_date(medicines, sort_direction)

    # Préparer les résultats formatés
    formatted_results = []
    for medicine in medicines:
        # Calculer le score de pertinence si la recherche est effectuée
        if search_query:
            relevance_score = calculate_relevance_score(medicine, search_query)
            medicine['search_matches'] = find_search_term_locations(medicine, search_query)
        else:
            relevance_score = 0
            medicine['search_matches'] = []
        
        formatted_results.append({
            'id': str(medicine['_id']),
            'title': medicine['title'],
            'update_date': medicine.get('update_date', 'Non disponible'),
            'medicine_details': medicine.get('medicine_details', {}),
            'relevance_score': relevance_score,  # Inclure le score de pertinence
            'match_count': medicine.get('match_count', 0),
            'search_matches': medicine['search_matches']
        })

    # Calculer s'il y a plus de résultats
    has_more = (page * per_page) < total_results

    return jsonify({
        'results': formatted_results,
        'has_more': has_more,
        'total_results': total_results,
        'total_pages': (total_results + per_page - 1) // per_page
    })

@app.route('/api/search-results-stream')
def search_results_api_stream():
    search_query = request.args.get('search', '')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    substance = request.args.get('substance', '')
    forme = request.args.get('forme', '')
    laboratoire = request.args.get('laboratoire', '')
    dosage = request.args.get('dosage', '')
    sort_option = request.args.get('sort', 'date_desc')

    query = {}
    pipeline_filters = []

    # Construction de la requête de recherche
    if search_query:
        search_regex = {'$regex': search_query, '$options': 'i'}
        pipeline_filters.append({'$or': [
            {'title': search_regex},
            {'medicine_details.substances_actives': search_regex},
            {'sections.content.text': search_regex},  # Recherche dans les sections
            {'sections.subsections.content.text': search_regex},
            {'sections.subsections.subsections.content.text': search_regex}
        ]})
    if substance:
        pipeline_filters.append({'medicine_details.substances_actives': {'$regex': substance, '$options': 'i'}})
    if forme:
        pipeline_filters.append({'medicine_details.forme': {'$regex': forme, '$options': 'i'}})
    if laboratoire:
        pipeline_filters.append({'medicine_details.laboratoire': {'$regex': laboratoire, '$options': 'i'}})
    if dosage:
        pipeline_filters.append({'medicine_details.dosages': {'$regex': dosage, '$options': 'i'}})

    # Combiner les filtres avec $and
    if pipeline_filters:
        query['$and'] = pipeline_filters

    def generate():
        total_results = collection.count_documents(query) # Calculer le nombre total de résultats
        
        # Envoyer le nombre total de résultats
        total_update = json.dumps({'total': total_results})
        yield f"event: total\ndata: {total_update}\n\n"

        medicines = collection.find(query).skip((page - 1) * per_page).limit(per_page) # Charger les résultats par page
        
        result_count = 0
        for medicine in medicines:
            if search_query:
                relevance_score = calculate_relevance_score(medicine, search_query)
                medicine['search_matches'] = find_search_term_locations(medicine, search_query)
            else:
                relevance_score = 0
                medicine['search_matches'] = []
            
            formatted_result = {
                'id': str(medicine['_id']),
                'title': medicine['title'],
                'update_date': medicine.get('update_date', 'Non disponible'),
                'medicine_details': medicine.get('medicine_details', {}),
                'relevance_score': relevance_score,
                'match_count': medicine.get('match_count', 0),
                'search_matches': medicine['search_matches']
            }
            
            # Convertir le résultat en JSON
            json_result = json.dumps(formatted_result, ensure_ascii=False)
            
            # Envoyer le résultat via le flux d'événements
            yield f"data: {json_result}\n\n"
            
            result_count += 1
            
            # Envoyer la mise à jour du compteur
            count_update = json.dumps({'count': result_count})
            yield f"event: count\ndata: {count_update}\n\n"

        # Envoyer un événement de fin de flux
        yield "data: end\n\n"

    return Response(stream_with_context(generate()), mimetype='text/event-stream')

# Ajout de la page d'erreur 404
@app.errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404

# Ajout de la page d'erreur 500
@app.errorhandler(500)
def internal_server_error(e):
    return render_template('errors/500.html'), 500

# Fonction pour créer un context processor qui sera disponible dans tous les templates
@app.context_processor
def inject_user_and_date():
    return {
        'user': g.get('user', None),
        'now': datetime.datetime.now()
    }

@app.route('/api/toggle-favorite/<medicine_id>', methods=['POST'])
def toggle_favorite(medicine_id):
    """Ajoute ou supprime un médicament des favoris de l'utilisateur connecté"""
    # Vérifier si l'utilisateur est connecté
    if 'user_id' not in request.cookies:
        return jsonify({"success": False, "message": "Utilisateur non connecté"}), 401
    
    user_id = request.cookies.get('user_id')
    
    try:
        # Vérifier si le médicament existe
        medicine = collection.find_one({'_id': ObjectId(medicine_id)})
        if not medicine:
            return jsonify({"success": False, "message": "Médicament non trouvé"}), 404
        
        from models import Interaction
        
        # Vérifier si le médicament est déjà un favori
        if Interaction.is_favorite(user_id, medicine_id):
            # Supprimer des favoris
            if Interaction.remove_favorite(user_id, medicine_id):
                return jsonify({"success": True, "is_favorite": False})
            else:
                return jsonify({"success": False, "message": "Erreur lors de la suppression des favoris"}), 500
        else:
            # Ajouter aux favoris
            if Interaction.add_favorite(user_id, medicine_id):
                return jsonify({"success": True, "is_favorite": True})
            else:
                return jsonify({"success": False, "message": "Erreur lors de l'ajout aux favoris"}), 500
    except Exception as e:
        print(f"Erreur lors de la gestion des favoris: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/medicine-summary/<id>')
def get_medicine_summary(id):
    """API endpoint to get the AI summary of a medicine"""
    try:
        # First check if we already have the summary in the database
        stored_medicine = db.medicines.find_one(
            {'_id': ObjectId(id)},
            {'ai_summary': 1}
        )
        
        if stored_medicine and 'ai_summary' in stored_medicine and stored_medicine['ai_summary']:
            return jsonify({
                "success": True,
                "summary": stored_medicine['ai_summary']
            })
        
        # If not, generate a new summary
        medicine = collection.find_one({'_id': ObjectId(id)})
        if not medicine:
            return jsonify({"success": False, "message": "Médicament non trouvé"}), 404
        
        # Generate summary but don't wait for it in the page load
        summary = get_or_generate_summary(medicine, db=db)
        
        # Return the generated summary
        return jsonify({
            "success": True,
            "summary": summary
        })
    except Exception as e:
        print(f"Error retrieving medicine summary: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

if __name__ == '__main__':
    # Initialiser la base de données
    init_db(app)
    
    # Initialiser le système d'utilisateurs
    users.init_users(app)  # Maintenant users est correctement défini
    
    app.run(debug=app.config['DEBUG'])

@users_bp.route('/admin/database')
@role_required(models.User.ROLE_ADMIN)
def admin_database():
    """Page d'administration de la base de données"""
    # Utiliser la connexion MongoDB à travers mongo.db au lieu de current_app.db
    db = models.mongo.db
    
    # Récupérer les métadonnées de scraping
    metadata = db.metadata.find_one({"_id": "scraping_metadata"})
    
    # Obtenir des statistiques sur la base de données
    total_medicines = db.medicines.count_documents({})
    
    # Récupérer les dates des 5 dernières mises à jour de médicaments
    # Modifier pour utiliser uniquement update_date au lieu de last_scraped
    latest_updates = list(db.medicines.find({}, {"title": 1, "update_date": 1})
                         .sort("_id", -1).limit(5))  # Tri par ID au lieu de last_scraped
    
    # Récupérer des statistiques de base
    lab_count = len(db.medicines.distinct("medicine_details.laboratoire"))
    substance_count = len(db.medicines.distinct("medicine_details.substances_actives"))
    
    # Import datetime pour le contexte du template
    import datetime
    
    return render_template('user/admin_database.html', 
                          metadata=metadata,
                          total_medicines=total_medicines,
                          latest_updates=latest_updates,
                          lab_count=lab_count,
                          substance_count=substance_count,
                          now=datetime.datetime.now(),
                          datetime=datetime)  # Passer le module datetime au contexte
