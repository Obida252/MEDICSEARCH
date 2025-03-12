from flask import Flask, request, render_template, jsonify, abort, redirect, url_for
from pymongo import MongoClient
from bson.objectid import ObjectId
import json
from bson import json_util
import time
import hashlib
from functools import lru_cache
from users import init_users

app = Flask(__name__)

# Configuration de la connexion à MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client['medicine_data48']
collection = db['medicines']

# Système de cache global pour les requêtes MongoDB
QUERY_CACHE = {}
CACHE_TIMEOUT = 600  # 10 minutes (en secondes)
CACHE_STATS = {
    'hits': 0,
    'misses': 0,
    'total': 0,
    'last_cleanup': time.time()
}

def get_query_cache_key(query=None, sort_option=None, sort_direction=None, skip=0, limit=None, search_query=None):
    """Génère une clé de cache unique pour une requête MongoDB"""
    # Convertir la requête en chaîne JSON triée pour avoir une clé stable
    query_str = json.dumps(query, sort_keys=True) if query else '{}'
    
    # Assembler tous les paramètres qui influencent le résultat
    key_parts = [
        query_str, 
        str(sort_option), 
        str(sort_direction),
        str(skip),
        str(limit)
    ]
    
    # Ajouter le terme de recherche si présent
    if search_query:
        key_parts.append(search_query)
    
    # Créer un hash MD5 comme clé
    cache_key = hashlib.md5('|'.join(key_parts).encode()).hexdigest()
    return cache_key

def get_cached_query_result(query=None, sort_option=None, sort_direction=None, skip=0, limit=None, search_query=None):
    """Récupère un résultat en cache pour une requête MongoDB si disponible"""
    CACHE_STATS['total'] += 1
    
    # Générer la clé de cache
    cache_key = get_query_cache_key(query, sort_option, sort_direction, skip, limit, search_query)
    
    # Vérifier si la clé existe dans le cache et n'a pas expiré
    if cache_key in QUERY_CACHE:
        timestamp, results = QUERY_CACHE[cache_key]
        if time.time() - timestamp < CACHE_TIMEOUT:
            CACHE_STATS['hits'] += 1
            print(f"CACHE HIT: Utilisation des résultats en cache (clé: {cache_key[:8]}...)")
            return results
    
    # Si pas dans le cache ou expiré
    CACHE_STATS['misses'] += 1
    return None

def store_query_result(results, query=None, sort_option=None, sort_direction=None, skip=0, limit=None, search_query=None):
    """Stocke un résultat de requête dans le cache"""
    cache_key = get_query_cache_key(query, sort_option, sort_direction, skip, limit, search_query)
    QUERY_CACHE[cache_key] = (time.time(), results)
    print(f"CACHE STORE: Résultats mis en cache (clé: {cache_key[:8]}...)")
    
    # Nettoyage périodique du cache (toutes les 100 requêtes)
    if CACHE_STATS['total'] % 100 == 0:
        cleanup_cache()

def cleanup_cache():
    """Nettoie le cache en supprimant les entrées expirées"""
    current_time = time.time()
    # Ne nettoyer que si le dernier nettoyage date d'au moins 1 minute
    if current_time - CACHE_STATS.get('last_cleanup', 0) > 60:
        expired_count = 0
        expired_keys = []
        
        for k, (timestamp, _) in QUERY_CACHE.items():
            if current_time - timestamp > CACHE_TIMEOUT:
                expired_keys.append(k)
                expired_count += 1
        
        # Supprimer les entrées expirées
        for k in expired_keys:
            del QUERY_CACHE[k]
        
        CACHE_STATS['last_cleanup'] = current_time
        print(f"CACHE CLEANUP: {expired_count} entrées expirées supprimées. {len(QUERY_CACHE)} entrées restantes.")

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
    """Route principale - page d'accueil"""
    return render_template('index.html')

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
    """Route de recherche de médicaments avec filtres avancés"""
    search_start_time = time.time()
    
    # Paramètres de recherche and de filtrage
    search_query = request.args.get('search', '')
    
    # Pagination
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))  # Par défaut 10 résultats par page
    # S'assurer que per_page est une valeur valide
    valid_per_page_values = [10, 25, 50, 100, 200, 500, 1000]
    if per_page not in valid_per_page_values:
        per_page = 10
    
    # Filtres basés uniquement sur medicine_details
    substance = request.args.get('substance', '')
    forme = request.args.get('forme', '')
    laboratoire = request.args.get('laboratoire', '')
    dosage = request.args.get('dosage', '')
    
    # Par défaut, utiliser le tri par date décroissante si aucun tri spécifié
    sort_option = request.args.get('sort', 'date_desc')
    
    # Détecter si nous avons une recherche avancée
    advanced_search = substance or forme or laboratoire or dosage or sort_option != 'date_desc'
    
    # Construction de la requête principale avec opérateur $and pour combiner tous les filtres
    pipeline_filters = []
    
    # Recherche générale (dans toutes les sections)
    if search_query:
        # Utilisation de l'opérateur $text pour une recherche en texte intégral si disponible
        if collection.index_information().get('text_index'):
            search_condition = {'$text': {'$search': search_query}}
        else:
            # Sinon, recherche dans tous les champs possibles
            search_condition = {
                '$or': [
                    {'title': {'$regex': search_query, '$options': 'i'}},
                    {'medicine_details.substances_actives': {'$regex': search_query, '$options': 'i'}},
                    {'medicine_details.laboratoire': {'$regex': search_query, '$options': 'i'}},
                    {'medicine_details.forme': {'$regex': search_query, '$options': 'i'}},
                    {'medicine_details.dosages': {'$regex': search_query, '$options': 'i'}},
                    {'sections.title': {'$regex': search_query, '$options': 'i'}},
                    {'sections.content.text': {'$regex': search_query, '$options': 'i'}},
                    {'sections.subsections.title': {'$regex': search_query, '$options': 'i'}},
                    {'sections.subsections.content.text': {'$regex': search_query, '$options': 'i'}},
                    {'sections.subsections.subsections.title': {'$regex': search_query, '$options': 'i'}},
                    {'sections.subsections.subsections.content.text': {'$regex': search_query, '$options': 'i'}}
                ]
            }
            
            # Essayer d'ajouter la recherche par ID si la requête est un ObjectId valide
            try:
                oid = ObjectId(search_query)
                search_condition['$or'].append({'_id': oid})
            except:
                pass
                
        pipeline_filters.append(search_condition)
    
    # Filtres basés uniquement sur medicine_details
    if substance:
        pipeline_filters.append({'medicine_details.substances_actives': {'$regex': substance, '$options': 'i'}})
    
    if forme:
        pipeline_filters.append({'medicine_details.forme': {'$regex': forme, '$options': 'i'}})
    
    if laboratoire:
        pipeline_filters.append({'medicine_details.laboratoire': {'$regex': laboratoire, '$options': 'i'}})
    
    if dosage:
        pipeline_filters.append({'medicine_details.dosages': {'$regex': dosage, '$options': 'i'}})
    
    # Construire la requête finale
    query = {}
    if pipeline_filters:
        query['$and'] = pipeline_filters
    
    # Calculer le nombre total de résultats
    # Cette opération peut également être mise en cache
    total_results_cache_key = get_query_cache_key(query, "count", None)
    cached_total = get_cached_query_result(query, "count")
    if cached_total is not None:
        total_results = cached_total
    else:
        total_results = collection.count_documents(query) if query else collection.count_documents({})
        store_query_result(total_results, query, "count")
    
    # Calculer le nombre total de pages
    total_pages = (total_results + per_page - 1) // per_page  # Arrondir au supérieur
    
    # Appliquer la pagination
    skip_count = (page - 1) * per_page
    
    # Déterminer l'ordre du tri
    sort_direction = -1  # Par défaut, du plus récent au plus ancien
    sort_field = None
    sort_by_date = False  # Indicateur pour savoir si on trie par date
    
    if sort_option == 'name_asc':
        sort_field = 'title'
        sort_direction = 1
    elif sort_option == 'name_desc':
        sort_field = 'title'
        sort_direction = -1
    elif sort_option == 'date_asc':
        sort_by_date = True
        sort_direction = 1
    elif sort_option == 'date_desc':
        sort_by_date = True
        sort_direction = -1
    
    # Exécution de la requête paginée avec cache
    medicines = None
    all_medicines = None
    
    if query:
        if sort_option == 'relevance' and search_query:
            # Vérifier le cache pour les résultats triés par pertinence
            cached_results = get_cached_query_result(query, sort_option, sort_direction, skip=0, limit=None, search_query=search_query)
            
            if cached_results:
                # Utiliser les résultats depuis le cache
                all_medicines = cached_results
                medicines = all_medicines[skip_count:skip_count + per_page]
            else:
                print(f"CACHE MISS: Exécution du tri par pertinence pour '{search_query}'")
                # Récupérer tous les résultats pour le tri
                query_start = time.time()
                all_medicines = list(collection.find(query))
                print(f"Requête MongoDB complète: {time.time() - query_start:.3f}s - {len(all_medicines)} résultats")
                
                # Calculer des scores de pertinence
                scoring_start = time.time()
                for medicine in all_medicines:
                    medicine['relevance_score'] = calculate_relevance_score(medicine, search_query)
                print(f"Calcul des scores: {time.time() - scoring_start:.3f}s")
                
                # Trier par score
                sort_start = time.time()
                all_medicines = sorted(all_medicines, key=lambda x: (x.get('relevance_score', 0), x.get('match_count', 0)), reverse=True)
                print(f"Tri par pertinence: {time.time() - sort_start:.3f}s")
                
                # Mettre en cache les résultats triés
                store_query_result(all_medicines, query, sort_option, sort_direction, skip=0, limit=None, search_query=search_query)
                
                # Obtenir la page actuelle
                medicines = all_medicines[skip_count:skip_count + per_page]
        
        elif sort_by_date:
            # Vérifier le cache pour les résultats triés par date
            cached_results = get_cached_query_result(query, sort_option, sort_direction)
            
            if cached_results:
                # Utiliser les résultats depuis le cache
                all_medicines = cached_results
                medicines = all_medicines[skip_count:skip_count + per_page]
            else:
                print(f"CACHE MISS: Exécution du tri par date ({sort_option})")
                # Récupérer tous les résultats pour le tri
                query_start = time.time()
                all_medicines = list(collection.find(query))
                print(f"Requête MongoDB complète: {time.time() - query_start:.3f}s - {len(all_medicines)} résultats")
                
                # Tri manuel par date
                all_medicines = sort_medicines_by_date(all_medicines, sort_direction)
                
                # Mettre en cache les résultats triés
                store_query_result(all_medicines, query, sort_option, sort_direction)
                
                # Obtenir la page actuelle
                medicines = all_medicines[skip_count:skip_count + per_page]
        else:
            # Pour les autres types de tri, utiliser MongoDB
            # Vérifier d'abord le cache
            cached_results = get_cached_query_result(query, sort_option, sort_direction, skip=skip_count, limit=per_page)
            
            if cached_results:
                medicines = cached_results
            else:
                print(f"CACHE MISS: Tri standard par MongoDB ({sort_option})")
                medicines = list(collection.find(query).sort(sort_field, sort_direction).skip(skip_count).limit(per_page))
                
                # Mettre en cache
                store_query_result(medicines, query, sort_option, sort_direction, skip=skip_count, limit=per_page)
    else:
        # Si aucun filtre
        if sort_by_date:
            # Vérifier le cache
            cached_results = get_cached_query_result({}, sort_option, sort_direction)
            
            if cached_results:
                all_medicines = cached_results
                medicines = all_medicines[skip_count:skip_count + per_page]
            else:
                print(f"CACHE MISS: Récupération et tri de tous les documents par date")
                # Récupérer tous les documents
                query_start = time.time()
                all_medicines = list(collection.find())
                print(f"Récupération de tous les documents: {time.time() - query_start:.3f}s - {len(all_medicines)} résultats")
                
                # Tri manuel par date
                all_medicines = sort_medicines_by_date(all_medicines, sort_direction)
                
                # Mettre en cache
                store_query_result(all_medicines, {}, sort_option, sort_direction)
                
                # Obtenir la page actuelle
                medicines = all_medicines[skip_count:skip_count + per_page]
        else:
            # Tri standard par MongoDB
            cached_results = get_cached_query_result({}, sort_option, sort_direction, skip=skip_count, limit=per_page)
            
            if cached_results:
                medicines = cached_results
            else:
                sort_field = sort_field or '_id'
                medicines = list(collection.find().sort(sort_field, sort_direction).skip(skip_count).limit(per_page))
                
                # Mettre en cache
                store_query_result(medicines, {}, sort_option, sort_direction, skip=skip_count, limit=per_page)
    
    # Pour chaque médicament affiché, ajouter les détails de recherche si nécessaire
    if search_query:
        for medicine in medicines:
            if 'search_matches' not in medicine:
                medicine['search_matches'] = find_search_term_locations(medicine, search_query)
                # Calculer le score de pertinence s'il n'est pas déjà calculé
                if 'relevance_score' not in medicine:
                    calculate_relevance_score(medicine, search_query)
    
    # Récupérer les options de filtre
    filter_cache_key = get_query_cache_key(query, "filters")
    cached_filters = get_cached_query_result(query, "filters")
    
    if cached_filters:
        available_filters = cached_filters
    else:
        # Limiter à 1000 pour la performance
        matching_meds_for_filters = all_medicines if all_medicines else list(collection.find(query).limit(1000))
        available_filters = extract_filter_options_from_results(matching_meds_for_filters)
        store_query_result(available_filters, query, "filters")
    
    # Ajouter le nom des médicaments
    for medicine in medicines:
        medicine['name'] = extract_medicine_name(medicine)
    
    # Calculer le temps d'exécution total
    total_duration = time.time() - search_start_time
    print(f"TEMPS TOTAL DE RECHERCHE: {total_duration:.3f}s")
    print(f"STATS CACHE: {CACHE_STATS['hits']} hits, {CACHE_STATS['misses']} misses ({len(QUERY_CACHE)} entrées en cache)")
    
    return render_template('search.html',
                          medicines=medicines, 
                          search=search_query,
                          substance=substance,
                          forme=forme,
                          laboratoire=laboratoire,
                          dosage=dosage,
                          sort=sort_option,
                          advanced_search=advanced_search,
                          available_filters=available_filters,
                          current_page=page,
                          total_pages=total_pages,
                          total_results=total_results,
                          per_page=per_page,
                          execution_time=total_duration)

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
        return render_template('medicine_details.html', medicine=medicine, medicine_json=medicine_json)
    
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
    
    return render_template('debug.html', 
                          stats=collection_stats,
                          sample=sample_json,
                          fields=sorted(list(fields)))

@app.route('/cache-stats')
def cache_stats():
    """Affiche les statistiques du cache et permet de le vider"""
    hit_rate = 0
    if CACHE_STATS['total'] > 0:
        hit_rate = (CACHE_STATS['hits'] / CACHE_STATS['total']) * 100
        
    return jsonify({
        'stats': {
            'hits': CACHE_STATS['hits'],
            'misses': CACHE_STATS['misses'],
            'total': CACHE_STATS['total'],
            'hit_rate': f"{hit_rate:.2f}%",
            'entries': len(QUERY_CACHE),
            'last_cleanup': CACHE_STATS['last_cleanup']
        },
        'cache_info': {
            'timeout': CACHE_TIMEOUT,
            'date_converter_cache_info': convert_french_date_cached.cache_info()._asdict()
        }
    })

@app.route('/clear-cache')
def clear_cache():
    """Vide le cache de requêtes"""
    global QUERY_CACHE
    cache_size = len(QUERY_CACHE)
    QUERY_CACHE = {}
    
    # Réinitialiser les statistiques
    CACHE_STATS['hits'] = 0
    CACHE_STATS['misses'] = 0
    CACHE_STATS['total'] = 0
    CACHE_STATS['last_cleanup'] = time.time()
    
    # Vider également le cache LRU des dates
    convert_french_date_cached.cache_clear()
    
    return jsonify({
        'status': 'success',
        'message': f'Cache vidé ({cache_size} entrées supprimées)',
        'timestamp': time.time()
    })

if __name__ == '__main__':
    init_users(app)
    app.run(debug=True)
