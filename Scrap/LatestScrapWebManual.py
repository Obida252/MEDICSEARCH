import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
import pandas as pd
import re

# Connexion à MongoDB
client = MongoClient("mongodb://localhost:27017/")
db_name = "medicsearch"
db = client[db_name]
collection = db["medicines"]

if collection.count_documents({}) > 0:
    print("La collection existe déjà, pas d'insertion.")
    exit()

# Charger les URLs depuis le fichier Excel
df = pd.read_excel("liens_R.xlsx")
if 'liens' not in df.columns:
    raise ValueError("Le fichier Excel ne contient pas de colonne 'liens'.")
urls = df["liens"].tolist()

def extract_update_date(soup):
    """Extrait la date de mise à jour du document"""
    update_date = "Date not found"
    ansm_date_pattern = soup.find(string=lambda text: text and "ANSM - Mis à jour le :" in text)
    
    if ansm_date_pattern:
        update_date = ansm_date_pattern.split("ANSM - Mis à jour le :")[1].strip()
    else:
        update_date_element = soup.find('div', id='menuhaut')
        if update_date_element:
            update_date = update_date_element.get_text(strip=True)
            if "mise à jour" in update_date:
                update_date = update_date.split("mise à jour")[1].strip()
            elif "mise" in update_date:
                update_date = update_date.split("mise")[1].strip()
    
    return update_date.replace("le ", "").strip()

def extract_text_content(element):
    """Extrait le texte et les attributs de formatage importants"""
    text = re.sub(r'\s+', ' ', element.get_text(strip=False)).strip()
    
    formatting = {
        "bold": False, "italic": False, "underline": False,
        "list_type": None, "alignment": "left"
    }
    
    # Détection de formatage
    if element.name in ['strong', 'b'] or element.find(['strong', 'b']):
        formatting["bold"] = True
    
    if element.name in ['em', 'i'] or element.find(['em', 'i']):
        formatting["italic"] = True
    
    if 'class' in element.attrs:
        classes = ' '.join(element['class'])
        if 'gras' in classes or 'AmmCorpsTexteGras' in classes:
            formatting["bold"] = True
        if 'italique' in classes:
            formatting["italic"] = True
        if 'souligne' in classes:
            formatting["underline"] = True
        if 'AmmListePuces' in classes:
            formatting["list_type"] = "bullet"
        if 'center' in classes or 'text-align:center' in str(element):
            formatting["alignment"] = "center"
    
    if element.name == 'li' or (element.parent and element.parent.name in ['ul', 'ol']):
        formatting["list_type"] = "bullet" if element.parent and element.parent.name == 'ul' else "numbered"
    
    return {"text": text, "formatting": formatting}

def extract_sections(soup):
    """
    Construit une hiérarchie des sections à partir de <a name="RcpDenomination">.
    Si non trouvé, commence après <p class="DateNotif">.
    L'extraction s'arrête à <a name="RcpInstPrepRadioph">.
    """
    root_sections = []    # Liste des sections principales
    stack = []            # Pile pour gérer la hiérarchie
    processed_elements = set()  # Pour suivre les éléments déjà traités
    
    body = soup.find('body')
    if not body:
        return root_sections

    # Trouver le point de départ
    start_found = False
    elements = body.find_all(['a', 'p', 'div', 'table'], recursive=True)
    
    for i, element in enumerate(elements):
        # Point de départ principal : RcpDenomination
        if element.name == 'a' and element.get('name') == 'RcpDenomination':
            start_found = True
            continue
        # Point de départ alternatif : après DateNotif
        elif not start_found and element.name == 'p' and element.has_attr('class') and 'DateNotif' in element['class']:
            start_found = True
            continue
        
        # Ne rien traiter avant le point de départ
        if not start_found:
            continue
            
        # Arrêter à l'ancre de fin
        if element.name == 'a' and element.get('name') == 'RcpInstPrepRadioph':
            break

        # Ne pas traiter les éléments déjà traités
        if element in processed_elements:
            continue

        # Détecter un titre de section
        if element.name == 'p' and element.has_attr('class'):
            section_class = next((cls for cls in element['class'] if cls.startswith("AmmAnnexeTitre")), None)
            if section_class:
                match = re.search(r"AmmAnnexeTitre(\d+)(Bis)?", section_class)
                if match:
                    level = int(match.group(1))
                    a_tag = element.find('a')
                    title = a_tag.get_text(strip=True) if a_tag else element.get_text(strip=True)
                    
                    # Créer la nouvelle section sans le champ "level"
                    new_section = {"title": title, "content": [], "subsections": []}
                    
                    # Gérer la hiérarchie
                    while stack and stack[-1].get("level", 0) >= level:
                        stack.pop()
                    if stack:
                        stack[-1]["subsections"].append(new_section)
                    else:
                        root_sections.append(new_section)
                    # Garder le level temporairement dans la stack pour la comparaison
                    new_section["level"] = level
                    stack.append(new_section)
                    continue

        # Traiter le contenu
        if element.name == 'table':
            # Extraction du contenu de tableau intégrée directement
            try:
                rows = element.find_all("tr")
                
                # Marquer tous les éléments du tableau comme traités
                for row in rows:
                    for cell in row.find_all(['td', 'th']):
                        processed_elements.add(cell)
                        # Marquer également tous les éléments enfants
                        for child in cell.find_all(True):
                            processed_elements.add(child)
                
                headers = []
                header_row = element.find("thead")
                if header_row and header_row.find_all("th"):
                    headers = [th.get_text(strip=True) for th in header_row.find_all("th")]
                
                table_data = []
                for row in rows:
                    cols = row.find_all(["td", "th"])
                    row_data = [col.get_text(strip=True) for col in cols]
                    if any(cell.strip() for cell in row_data):
                        table_data.append(row_data)
                
                content_data = {"table": table_data}
                
                if headers:
                    content_data["headers"] = headers
                
                caption = element.find("caption")
                if caption:
                    content_data["caption"] = caption.get_text(strip=True)
                    processed_elements.add(caption)
            except Exception as e:
                content_data = {"error": f"Erreur d'extraction de tableau: {str(e)}"}
        elif element.name in ['p', 'div']:
            if element.has_attr('class') and any(cls.startswith("AmmAnnexeTitre") for cls in element['class']):
                continue
            content_data = extract_text_content(element)
        else:
            continue
        
        # Ajouter le contenu à la dernière section
        if stack:
            stack[-1]["content"].append(content_data)
        elif root_sections:
            root_sections[-1]["content"].append(content_data)
        else:
            root_sections.append({
                "title": "Contenu non sectionné",
                "content": [content_data],
                "subsections": []
            })
    
    # Nettoyer les sections en supprimant le champ level
    def clean_sections(sections):
        for section in sections:
            if "level" in section:
                del section["level"]
            clean_sections(section["subsections"])
    
    clean_sections(root_sections)
    return root_sections

def extract_medicine_title(soup):
    """Extrait directement le titre du médicament"""
    denomination_section = soup.find('a', {'name': 'RcpDenomination'})
    if denomination_section:
        title_element = denomination_section.find_next('p', class_=lambda c: c and ('AmmCorpsTexteGras' in c or 'AmmDenomination' in c))
        if title_element:
            return re.sub(r'\s+', ' ', title_element.get_text(strip=True)).strip()
    
    # Méthodes alternatives
    title_h1 = soup.find('h1', class_='textedeno')
    if title_h1:
        title_text = title_h1.get_text(strip=True)
        if " - " in title_text:
            title_text = title_text.split(" - ")[0].strip()
        return title_text
    
    # Dernière tentative
    for class_name in ['AmmDenomination', 'AmmCorpsTexteGras']:
        title_elements = soup.find_all('p', class_=class_name, limit=3)
        for element in title_elements:
            text = element.get_text(strip=True)
            if text and len(text) > 5:
                return re.sub(r'\s+', ' ', text).strip()
    
    return "Document sans titre"

def extract_laboratory(soup):
    """Extrait directement le laboratoire"""
    titulaire_section = soup.find('a', {'name': 'RcpTitulaireAmm'})
    if titulaire_section:
        # Récupérer précisément le paragraphe qui contient le nom du laboratoire (généralement le premier ou deuxième paragraphe après l'ancre)
        paragraphs = []
        current_elem = titulaire_section.parent
        # Obtenir les 3 paragraphes après la section de titre
        for _ in range(5):  # Cherche dans les 5 éléments suivants maximum
            current_elem = current_elem.find_next(['p', 'div'])
            if not current_elem:
                break
            paragraphs.append(current_elem)
        
        # Stratégie 1: Chercher spécifiquement un élément avec span class="gras"
        for paragraph in paragraphs:
            spans = paragraph.find_all('span', class_='gras')
            for span in spans:
                text = span.get_text(strip=True)
                # Vérifier que ce n'est pas une adresse (ne contient pas de code postal)
                if text and not re.match(r'^\d{5}', text) and not re.search(r'\d{5}\s', text):
                    return text
        
        # Stratégie 2: Chercher le premier paragraphe qui contient du texte en gras
        for paragraph in paragraphs:
            # Vérifier si le paragraphe a la classe AmmCorpsTexteGras ou contient un span gras
            if (paragraph.has_attr('class') and 'AmmCorpsTexteGras' in paragraph['class']) or paragraph.find('span', class_='gras'):
                text = paragraph.get_text(strip=True)
                # Vérifier que ce n'est pas un titre, une date ou une adresse
                if not text.startswith(('7.', '8.', 'TITULAIRE', 'DATE')) and not re.match(r'^\d{5}', text):
                    return text
        
        # Stratégie 3: Prendre le premier paragraphe non vide qui n'est pas un titre
        for paragraph in paragraphs:
            text = paragraph.get_text(strip=True)
            # Exclure les titres et les adresses
            if (text and 
                not text.startswith(('7.', '8.', 'TITULAIRE', 'DATE')) and 
                not re.match(r'^\d{5}', text) and 
                not re.search(r'\b\d{5}\b', text) and  # Pas de code postal
                not any(word.lower() in text.lower() for word in ['rue', 'avenue', 'boulevard', 'cedex'])):  # Pas d'adresse
                return text.replace('LABORATOIRES', 'LABORATOIRES ').strip()  # Fix for cases where LABORATOIRES is stuck to the name
    
    return ""

def extract_substances_and_dosages(soup):
    """
    Extrait la première substance active et son dosage à partir du premier élément avec la classe 'AmmComposition'.
    """
    dosages = []
    substances = []

    # Récupère directement le premier paragraphe avec la classe 'AmmComposition'
    paragraph = soup.find('p', class_='AmmComposition')
    
    if paragraph:
        text = paragraph.get_text(strip=True)
        print(f"🔎 Paragraphe trouvé: {text}")

        # Regex pour extraire substance et dosage
        match = re.search(
            r"^(.*?)\.{3,}\s*([\d\s,]+(?:[.,]\d+)?\s*(?:mg|g|ml|µg|UI|U\.I\.|microgrammes|unités|%))\s*$",
            text, re.UNICODE | re.IGNORECASE
        )
        if match:
            substance = match.group(1).strip()
            dosage = match.group(2).strip()

            # Nettoyage du nom de la substance : supprime les contenus entre parenthèses
            substance = re.sub(r'\s*\([^)]*\)', '', substance).strip()

            print(f"✅ Extraction réussie : Substance '{substance}' - Dosage '{dosage}'")
            substances.append(substance)
            dosages.append(dosage)
        else:
            print("⚠️ Aucun dosage détecté dans ce texte.")
    else:
        print("⚠️ Aucune balise <p class='AmmComposition'> trouvée.")

    return {
        "substances_actives": substances,
        "dosages": dosages
    }



def extract_pharmaceutical_form(soup):
    """Extrait la forme pharmaceutique"""
    form_section = soup.find('a', {'name': 'RcpFormePharm'})
    if form_section:
        # Recherche plus générique pour trouver le premier paragraphe après la section
        form_paragraph = form_section.find_next('p')
        if form_paragraph:
            return form_paragraph.get_text(strip=True).rstrip('.')
    
    # Alternative via le titre
    title = extract_medicine_title(soup)
    if title and ',' in title:
        return title.split(',', 1)[1].strip()
    
    return ""

# Traitement des URLs
total_urls = len(urls)
processed = 0

for url in urls:
    processed += 1
    print(f"Progression: {(processed / total_urls) * 100:.1f}% - URL {processed}/{total_urls}")
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        # Gestion des encodages
        try:
            soup = BeautifulSoup(response.content, 'html.parser')
        except:
            for encoding in ['utf-8', 'latin-1', 'windows-1252', 'iso-8859-1']:
                try:
                    soup = BeautifulSoup(response.content.decode(encoding), 'html.parser')
                    break
                except:
                    continue
        
        # Extractions
        main_title = extract_medicine_title(soup)
        substance_dosage_data = extract_substances_and_dosages(soup)
        document = {
            "url": url,
            "title": main_title,
            "medicine_details": {
                "substances_actives": substance_dosage_data["substances_actives"],
                "laboratoire": extract_laboratory(soup),
                "dosages": substance_dosage_data["dosages"],
                "forme": extract_pharmaceutical_form(soup)
            },
            "update_date": extract_update_date(soup),
            "sections": {}
        }
        
        try:
            document["sections"] = extract_sections(soup)
        except Exception as e:
            print(f"Erreur lors de l'extraction des sections pour {url}: {str(e)}")
        
        # Insertion dans MongoDB
        collection.insert_one(document)
        print(f"Données insérées pour: {main_title}")
    
    except Exception as e:
        print(f"Erreur lors du traitement de {url}: {str(e)}")
    
    print("-" * 50)

print(f"Scraping terminé! Données stockées dans la base '{db_name}'")
