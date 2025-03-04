import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
import pandas as pd

# Connexion MongoDB avec gestion des bases existantes
client = MongoClient("mongodb://localhost:27017/")
db_name = "medicine_data"
db_list = client.list_database_names()

counter = 1
while db_name in db_list:
    db_name = f"medicine_data{counter}"
    counter += 1

db = client[db_name]
collection = db["medicines"]

# Charger les URLs
excel_file = "liens_R.xlsx"
df = pd.read_excel(excel_file)

if 'liens' not in df.columns:
    raise ValueError("Le fichier Excel ne contient pas de colonne 'liens'.")

urls = df["liens"].tolist()

# Sections cibles
TARGET_SECTIONS = [f"{i}." for i in range(1, 13)] + [f"{i}.{j}" for i in range(1, 13) for j in range(1, 10)]

# Définir des titres standards de sections de RCP
SECTION_TITLES = [
    "1. DÉNOMINATION DU MÉDICAMENT",
    "2. COMPOSITION QUALITATIVE ET QUANTITATIVE",
    "3. FORME PHARMACEUTIQUE",
    "4. DONNÉES CLINIQUES",
    "4.1. Indications thérapeutiques",
    "4.2. Posologie et mode d'administration",
    "4.3. Contre-indications",
    "4.4. Mises en garde spéciales et précautions d'emploi",
    "4.5. Interactions avec d'autres médicaments et autres formes d'interactions",
    "4.6. Fertilité, grossesse et allaitement",
    "4.7. Effets sur l'aptitude à conduire des véhicules et à utiliser des machines",
    "4.8. Effets indésirables",
    "4.9. Surdosage",
    "5. PROPRIÉTÉS PHARMACOLOGIQUES",
    "5.1. Propriétés pharmacodynamiques",
    "5.2. Propriétés pharmacocinétiques",
    "5.3. Données de sécurité préclinique",
    "6. DONNÉES PHARMACEUTIQUES",
    "6.1. Liste des excipients",
    "6.2. Incompatibilités",
    "6.3. Durée de conservation",
    "6.4. Précautions particulières de conservation",
    "6.5. Nature et contenu de l'emballage extérieur",
    "6.6. Précautions particulières d’élimination et de manipulation",
    "7. TITULAIRE DE L'AUTORISATION DE MISE SUR LE MARCHE",
    "8. NUMÉRO(S) D'AUTORISATION DE MISE SUR LE MARCHE",
    "9. DATE DE PREMIÈRE AUTORISATION/DE RENOUVELLEMENT DE L'AUTORISATION",
    "10. DATE DE MISE À JOUR DU TEXTE",
    "11. DOSIMÉTRIE",
    "12. INSTRUCTIONS POUR LA PRÉPARATION DES RADIOPHARMACEUTIQUES"
]

def extract_table(table_element):
    """Extrait un tableau sous forme de liste de listes."""
    rows = table_element.find_all("tr")
    table_data = []

    for row in rows:
        cols = row.find_all(["td", "th"])
        row_data = [col.get_text(strip=True) for col in cols]
        if any(cell.strip() for cell in row_data):  # Évite les lignes vides
            table_data.append(row_data)

    return {"table": table_data} if table_data else {"error": "Table vide"}

def is_inside_table(element):
    """Vérifie si un élément appartient à un tableau."""
    return any(parent.name == "table" for parent in element.parents)

def is_value_in_table(value, tables):
    """Version simplifiée de la détection de doublons maintenant que les sections sont bien identifiées."""
    value = value.lower().strip()
    
    # Cas spécial pour les paragraphes longs (>150 caractères)
    if len(value) > 150:
        # Maintenir la logique des 3+ cellules pour les paragraphes longs
        cell_matches = 0
        all_cells = set()  # Utiliser un set pour éviter les duplications
        
        # Collecter les cellules significatives
        for table in tables:
            for row in table:
                for cell in row:
                    cell_text = cell.lower().strip()
                    if len(cell_text) > 5:  # Ignorer les cellules trop petites
                        all_cells.add(cell_text)
        
        # Compter les correspondances significatives
        for cell in all_cells:
            if cell in value:
                cell_matches += 1
        
        # Un paragraphe n'est un doublon que s'il contient plusieurs cellules du tableau
        return cell_matches >= 3
    
    # Pour les valeurs numériques, normaliser pour la comparaison
    normalized_value = value.replace(',', '.').strip()
    is_num = is_numeric(value)
    if is_num and '(' in normalized_value:
        normalized_value = normalized_value.split('(')[0].strip()
    
    # Règles simplifiées pour les textes courts
    for table in tables:
        for row in table:
            for cell in row:
                cell_text = cell.lower().strip()
                
                # Règle 1: Correspondance exacte
                if value == cell_text:
                    return True
                
                # Règle 2: Pour les nombres, comparer les valeurs normalisées
                if is_num and is_numeric(cell_text):
                    norm_cell = cell_text.replace(',', '.').strip()
                    if '(' in norm_cell:
                        norm_cell = norm_cell.split('(')[0].strip()
                    if normalized_value == norm_cell:
                        return True
                
                # Règle 3: Pour les textes très courts (<20 chars), vérifier l'inclusion dans les deux sens
                if len(value) < 20:
                    if value in cell_text or (len(cell_text) < 20 and cell_text in value):
                        return True
    
    return False

def is_numeric(text):
    """Vérifie si le texte est une valeur numérique, même avec virgule/point."""
    # Supprime les espaces et remplace les virgules par des points
    normalized = text.replace(',', '.').replace(' ', '').strip()
    # Vérifie s'il s'agit d'un nombre décimal
    try:
        float(normalized)
        return True
    except ValueError:
        # Vérifie s'il y a une partie entre parenthèses (ex: "1.07(0,92 - 1,23)")
        if '(' in normalized:
            try:
                main_part = normalized.split('(')[0]
                float(main_part)
                return True
            except ValueError:
                pass
        return False

# Ajoutez une constante pour définir la dernière section à extraire
MAX_SECTION = "6.6"  # Notez que j'ai retiré le point final

# Scraping des pages
for url in urls:
    print(f"Processing URL: {url}")
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Erreur récupération de la page: {response.status_code}")
        continue

    soup = BeautifulSoup(response.content, 'html.parser')

    # Extraction de la date de mise à jour
    update_date = "Date inconnue"
    ansm_date_pattern = soup.find(string=lambda text: text and "ANSM - Mis à jour le :" in text)
    if ansm_date_pattern:
        update_date = ansm_date_pattern.split("ANSM - Mis à jour le :")[1].strip()

    extracted_data = {"url": url, "update_date": update_date, "sections": {}}
    current_section = None
    extracted_tables = []  # Stocker les tableaux pour éviter les doublons

    # Définir une variable pour savoir si on doit continuer le traitement ou non
    should_continue_processing = True

    for element in soup.find_all(["p", "h1", "h2", "h3", "h4", "h5", "h6", "table"]):
        # Si on ne doit plus traiter d'éléments, on sort de la boucle
        if not should_continue_processing:
            break

        text = element.get_text(strip=True) if element.name in ["p", "h1", "h2", "h3", "h4", "h5", "h6"] else ""
        
        # Variable pour suivre si l'élément actuel est un titre de section
        is_section_title = False

        # Détection des sections - CODE MODIFIÉ
        if any(text.startswith(sec) for sec in TARGET_SECTIONS):
            section_number = text.split(" ", 1)[0] if " " in text else text
            
            # Vérifie si c'est une vraie section et pas juste une valeur numérique
            is_valid_section = False
            
            # Si c'est un nombre simple ou avec parenthèses, ce n'est PAS une section
            if is_numeric(text):
                is_valid_section = False
            # Si le texte correspond à un titre de section connu
            elif any(title.lower() in text.lower() for title in SECTION_TITLES):
                is_valid_section = True
            # Si le texte contient un espace après le numéro de section
            elif " " in text:
                is_valid_section = True
            # Si c'est exactement un numéro de section (ex: "1." ou "1.2.")
            elif section_number in TARGET_SECTIONS:
                is_valid_section = True
            
            # Si c'est une section valide, vérifier si on a dépassé la section maximale
            if is_valid_section:
                # Supprimer le point final pour la comparaison
                clean_section_number = section_number.rstrip('.')
                clean_max_section = MAX_SECTION.rstrip('.')
                
                # Vérifier si on a dépassé la section maximale (6.6)
                if clean_section_number.startswith("7"):
                    # Si on est à la section 7 ou plus, on arrête tout traitement
                    should_continue_processing = False
                    break
                
                # Secteur 6.7 ou plus (mais toujours en section 6)
                if clean_section_number.startswith("6.") and len(clean_section_number) > 2:
                    sub_number = int(clean_section_number[2:]) if clean_section_number[2:].isdigit() else 0
                    if sub_number > 6:
                        should_continue_processing = False
                        break
                
                # Sinon c'est une section valide qu'on veut conserver
                current_section = text
                extracted_data["sections"][current_section] = {"content": []}
                extracted_tables = []  # Réinitialiser les tableaux de cette section
                is_section_title = True  # Marquer cet élément comme titre de section

        # Extraction des tableaux et textes uniquement si on est toujours dans les sections à conserver
        if current_section:
            # Extraction des tableaux
            if element.name == "table":
                table_data = extract_table(element)
                if "error" not in table_data:
                    extracted_tables.append(table_data["table"])  # Stocker pour éviter les doublons
                    extracted_data["sections"][current_section]["content"].append(table_data)
                    
            # Extraction des textes (ÉVITER LES DOUBLONS avec les tableaux)
            elif element.name in ["p", "h1", "h2", "h3", "h4", "h5", "h6"]:
                # MODIFICATION : Ne pas ajouter le texte si c'est le titre de la section
                if not is_section_title and not is_inside_table(element) and not is_value_in_table(text, extracted_tables):
                    extracted_data["sections"][current_section]["content"].append({
                        "text": text,
                        "html_content": str(element)
                    })

    # Insérer les données dans MongoDB
    collection.insert_one(extracted_data)
    print(f"Données insérées pour URL: {url}")

print(f"\n=== FIN DU SCRAPING ===")
print("Toutes les données ont été insérées dans MongoDB sans doublons !")