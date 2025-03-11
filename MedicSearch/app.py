from flask import Flask, request, render_template, jsonify, abort, redirect, url_for
from pymongo import MongoClient
from bson.objectid import ObjectId
import json
from bson import json_util
import re

app = Flask(__name__)

# Configuration de la connexion à MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client['medicine_data43']
collection = db['medicines']

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
    voies_admin = set()
    classes_atc = set()
    
    # Extraire des valeurs prédéfinies communes pour améliorer les résultats même si l'analyse échoue
    common_substances = ["Vitamine A", "Abacavir", "Paracétamol", "Ibuprofène", "Amoxicilline"]
    common_forms = ["Comprimé", "Gélule", "Solution", "Suspension", "Pommade", "Sirop", "Injectable", "Comprimé Pelliculé", "Poudre"]
    common_routes = ["Orale", "Injectable", "Cutanée", "Ophtalmique", "Rectale", "Vaginale", "Inhalation"]
    
    # Classes ATC (Anatomique, Thérapeutique et Chimique)
    atc_classes = {
        'A': 'Système digestif et métabolisme',
        'B': 'Sang et organes hématopoïétiques',
        'C': 'Système cardiovasculaire',
        'D': 'Médicaments dermatologiques',
        'G': 'Système génito-urinaire et hormones sexuelles',
        'H': 'Hormones systémiques',
        'J': 'Anti-infectieux à usage systémique',
        'L': 'Antinéoplasiques et immunomodulateurs',
        'M': 'Système musculo-squelettique',
        'N': 'Système nerveux',
        'P': 'Antiparasitaires',
        'R': 'Système respiratoire',
        'S': 'Organes sensoriels',
        'V': 'Divers'
    }
    
    # Analyser un échantillon représentatif de la base de données
    try:
        sample_size = 50  # Nombre de documents à analyser
        medicines = list(collection.find().limit(sample_size))
        
        for medicine in medicines:
            # Extraction des substances actives depuis medicine_details
            if 'medicine_details' in medicine and 'substances_actives' in medicine['medicine_details']:
                for substance in medicine['medicine_details']['substances_actives']:
                    if substance and len(substance) > 2:  # Ignorer les valeurs trop courtes
                        substances_actives.add(substance)
            
            # Extraction de la forme pharmaceutique depuis medicine_details
            if 'medicine_details' in medicine and 'forme' in medicine['medicine_details']:
                forme = medicine['medicine_details']['forme']
                if forme and len(forme) > 2:  # Ignorer les valeurs trop courtes
                    formes_pharma.add(forme)
            
            # Extraction à partir des sections
            if 'sections' in medicine:
                for section in medicine['sections']:
                    # Extraction des substances actives (section 2)
                    if section['title'] == "2. COMPOSITION QUALITATIVE ET QUANTITATIVE" and section.get('content'):
                        for content_item in section['content']:
                            if 'text' in content_item:
                                text = content_item['text']
                                for common_substance in common_substances:
                                    if common_substance.lower() in text.lower():
                                        substances_actives.add(common_substance)
                                
                                # Chercher des patterns comme "XXX 100 mg" qui sont souvent des substances actives
                                substance_matches = re.findall(r'([A-Za-zÀ-ÿ\s\-]+)\s+\d+(?:[,.]\d+)?\s*(?:mg|g|ml|UI|µg)', text)
                                for match in substance_matches:
                                    clean_match = match.strip()
                                    if len(clean_match) > 3 and len(clean_match) < 30:
                                        substances_actives.add(clean_match.title())
                    
                    # Extraction des formes pharmaceutiques (section 3)
                    if section['title'] == "3. FORME PHARMACEUTIQUE" and section.get('content'):
                        for content_item in section['content']:
                            if 'text' in content_item:
                                text = content_item['text'].lower()
                                for common_form in common_forms:
                                    if common_form.lower() in text:
                                        formes_pharma.add(common_form)
                                
                                # Recherche spécifique pour les comprimés/gélules
                                for terme in ["comprimé", "gélule", "capsule"]:
                                    if terme in text:
                                        if "pelliculé" in text:
                                            formes_pharma.add(f"{terme.title()} Pelliculé")
                                        if "sécable" in text:
                                            formes_pharma.add(f"{terme.title()} Sécable")
                    
                    # Traitement des sous-sections de la section 4
                    if section['title'] == "4. DONNEES CLINIQUES" and section.get('subsections'):
                        for subsection in section['subsections']:
                            # Extraction des voies d'administration (section 4.2)
                            if subsection['title'] == "4.2. Posologie et mode d'administration" and subsection.get('content'):
                                for content_item in subsection['content']:
                                    if 'text' in content_item:
                                        text = content_item['text'].lower()
                                        for common_route in common_routes:
                                            if common_route.lower() in text:
                                                voies_admin.add(common_route)
                    
        print(f"Erreur lors de l'extraction des filtres: {e}")
    except Exception as e:
        print(f"Erreur lors de l'extraction des filtres: {e}")
        # Si une erreur survient, utiliser uniquement les valeurs prédéfinies
    
    # Ajouter les valeurs par défaut si l'extraction n'a pas donné suffisamment de résultats
    if len(substances_actives) < 5:
        substances_actives.update(common_substances)
    
    if len(formes_pharma) < 5:
        formes_pharma.update(common_forms)
        
    if len(voies_admin) < 5:
        voies_admin.update(common_routes)
    
    if len(classes_atc) < 5:
        classes_atc.update(atc_classes.keys())
    
    # Convertir en listes triées
    substances_list = sorted(list(substances_actives))
    formes_list = sorted(list(formes_pharma))
    voies_list = sorted(list(voies_admin))
    
    # Pour les classes ATC, ajouter la description
    classes_list = []
    for code in sorted(list(classes_atc)):
        if code in atc_classes:
            classes_list.append({'code': code, 'name': atc_classes[code]})
    
    # Mettre en cache les résultats pour éviter de recalculer à chaque demande
    result = {
        'substances': substances_list,
        'formes': formes_list,
        'voies_admin': voies_list,
        'classes_atc': classes_list
    }
    
    # Cacher les résultats comme attribut de la fonction pour les prochains appels
    extract_filter_options.cached_filters = result
    return result

@app.route('/search')
def search():
    """Route de recherche de médicaments avec filtres avancés"""
    # Paramètres de recherche et de filtrage
    search_query = request.args.get('search', '')
    
    # Nouveaux filtres simplifiés
    substance = request.args.get('substance', '')
    forme = request.args.get('forme', '')
    voie_admin = request.args.get('voie_admin', '')
    classe_atc = request.args.get('classe_atc', '')
    sort = request.args.get('sort', 'relevance')
    
    # Détecter si nous avons une recherche avancée
    advanced_search = substance or forme or voie_admin or classe_atc or (sort != 'relevance')
    
    # Charger les options de filtrage disponibles (indépendamment des résultats de recherche)
    available_filters = extract_filter_options()
    
    # Construction de la requête principale avec opérateur $and pour combiner tous les filtres
    pipeline_filters = []
    
    # Recherche générale (dans toutes les sections)
    if search_query:
        search_condition = {
            '$or': [
                {'sections.$**.content.text': {'$regex': search_query, '$options': 'i'}}
            ]
        }
        
        # Essayer d'ajouter la recherche par ID si la requête est un ObjectId valide
        try:
            oid = ObjectId(search_query)
            search_condition['$or'].append({'_id': oid})
        except:
            pass
            
        pipeline_filters.append(search_condition)
    
    # Filtrage par substance active - SIMPLIFIÉ et PLUS LARGE
    if substance:
        # Chercher la substance active partout dans le document
        substance_filter = {
            '$or': [
                {'sections.$**.content.text': {'$regex': substance, '$options': 'i'}},
                {'sections.$**.content.html_content': {'$regex': substance, '$options': 'i'}}
            ]
        }
        pipeline_filters.append(substance_filter)
    
    # Filtrage par forme pharmaceutique - SIMPLIFIÉ
    if forme:
        # Recherche plus large de la forme dans tout le document
        forme_filter = {
            '$or': [
                {'sections.$**.content.text': {'$regex': forme, '$options': 'i'}},
                {'sections.$**.content.html_content': {'$regex': forme, '$options': 'i'}}
            ]
        }
        pipeline_filters.append(forme_filter)
    
    # Filtrage par voie d'administration - SIMPLIFIÉ
    if voie_admin:
        voie_filter = {
            '$or': [
                {'sections.$**.content.text': {'$regex': voie_admin, '$options': 'i'}},
                {'sections.$**.content.html_content': {'$regex': voie_admin, '$options': 'i'}}
            ]
        }
        pipeline_filters.append(voie_filter)
    
    # Filtrage par classe ATC - SIMPLIFIÉ 
    if classe_atc:
        atc_pattern = f"ATC.*\\b{classe_atc}\\b|\\bcode ATC.*\\b{classe_atc}\\b"
        atc_filter = {
            '$or': [
                {'sections.$**.content.text': {'$regex': atc_pattern, '$options': 'i'}},
                {'sections.$**.content.html_content': {'$regex': atc_pattern, '$options': 'i'}}
            ]
        }
        pipeline_filters.append(atc_filter)
    
    # Construire la requête finale
    query = {}
    if pipeline_filters:
        query['$and'] = pipeline_filters
    
    # Exécution de la requête
    limit = 100  # Limiter le nombre de résultats pour des raisons de performance
    
    if query:
        medicines = list(collection.find(query).limit(limit))
    else:
        # Si aucun filtre, afficher les 50 médicaments les plus récents
        medicines = list(collection.find().sort('_id', -1).limit(50))
    
    # Ajouter le nom des médicaments et l'information sur les filtres appliqués
    for medicine in medicines:
        medicine['name'] = extract_medicine_name(medicine)
        medicine['filter_info'] = {
            'search': bool(search_query),
            'substance': bool(substance),
            'forme': bool(forme),
            'voie_admin': bool(voie_admin),
            'classe_atc': bool(classe_atc)
        }
    
    # Ajout des informations de recherche
    if search_query:
        for medicine in medicines:
            search_match = None
            if 'sections' in medicine:
                for section_key, section_data in medicine['sections'].items():
                    if 'content' in section_data:
                        for content_item in section_data['content']:
                            if 'text' in content_item and search_query.lower() in content_item['text'].lower():
                                search_match = f"Section {section_key.split('.')[0]}"
                                break
                    if search_match:
                        break
            medicine['search_match'] = search_match
    
    # Trier les résultats
    if sort == 'name_asc':
        medicines = sorted(medicines, key=lambda x: x.get('name', '').lower())
    elif sort == 'name_desc':
        medicines = sorted(medicines, key=lambda x: x.get('name', '').lower(), reverse=True)
    elif sort == 'date_desc':
        try:
            medicines = sorted(medicines, key=lambda x: x.get('update_date', '') or '', reverse=True)
        except:
            pass
    elif sort == 'date_asc':
        try:
            medicines = sorted(medicines, key=lambda x: x.get('update_date', '') or '')
        except:
            pass
    
    # Afficher des informations de diagnostic
    print(f"Requête: {json.dumps(query, indent=2)}")
    print(f"Nombre de résultats: {len(medicines)}")
    
    # Passer tous les paramètres de filtrage au template
    return render_template('search.html',
                          medicines=medicines, 
                          search=search_query,
                          substance=substance,
                          forme=forme,
                          voie_admin=voie_admin,
                          classe_atc=classe_atc,
                          sort=sort,
                          advanced_search=advanced_search,
                          available_filters=available_filters)

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

if __name__ == '__main__':
    app.run(debug=True)
