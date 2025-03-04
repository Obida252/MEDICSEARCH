import os
import requests
import pandas as pd
import pymongo
import fitz  # PyMuPDF pour l'extraction de texte et d'images
import base64
import re
import pdfplumber
import concurrent.futures
from PIL import Image
import io

# Connexion à MongoDB
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["Pharmacie"]
collection = db["Documents"]

# Définition des chemins
PDF_DIR = os.path.abspath(r"C:\Document\IUT\SAE\pdf_files")
EXCEL_PATH = os.path.abspath(r"C:\Document\IUT\SAE\liens_pdf.xlsx")

# Création du dossier PDF s'il n'existe pas
os.makedirs(PDF_DIR, exist_ok=True)

# Charger les liens depuis l'Excel et limiter à 10
df = pd.read_excel(EXCEL_PATH).head(10)

def clean_filename(filename):
    """Supprime les caractères spéciaux du nom du fichier"""
    return re.sub(r'[\\/*?:"<>|,]', "_", filename)

def download_pdf(pdf_url, save_path):
    """Télécharge un PDF depuis une URL"""
    try:
        print(f"Telechargement de : {pdf_url}")
        response = requests.get(pdf_url, timeout=10)
        if response.status_code == 200:
            with open(save_path, "wb") as file:
                file.write(response.content)
            print(f"PDF telecharge : {save_path}")
            return True
        else:
            print(f"Echec ({response.status_code}) : {pdf_url}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"Erreur : {e}")
        return False

def extract_text_tables(pdf_path):
    """Extrait le texte et les tableaux dans l'ordre des pages"""
    doc = fitz.open(pdf_path)
    structured_content = []
    extracted_tables = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, (page_fitz, page_plumber) in enumerate(zip(doc, pdf.pages)):
            elements = []

            # Extraction du texte
            text = page_fitz.get_text("text")
            elements.append({"type": "text", "content": text.strip()})

            # Extraction des tableaux
            tables = page_plumber.extract_tables()
            for table in tables:
                clean_table = [[cell if cell else "" for cell in row] for row in table]
                extracted_tables.append({
                    "page": page_num + 1,
                    "table": clean_table,
                    "context": text.strip()[:200]
                })
                elements.append({"type": "table", "content": clean_table})

            # Stocker dans la structure
            structured_content.append({"page": page_num + 1, "elements": elements})

    return structured_content, extracted_tables

def extract_images(pdf_path):
    """Extrait les images avec leur légende en réduisant leur taille"""
    doc = fitz.open(pdf_path)
    images_data = []

    for page_num, page in enumerate(doc):
        captions = page.get_text("text")
        for img_index, img in enumerate(page.get_images(full=True)):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]

            # Convertir en image PIL et compresser
            image = Image.open(io.BytesIO(image_bytes))
            image = image.convert("RGB")
            image = image.resize((min(image.width, 800), min(image.height, 800)))  # Compression

            # Sauvegarde en base64
            buffered = io.BytesIO()
            image.save(buffered, format="JPEG", optimize=True, quality=70)  # Compression JPEG 70%
            image_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

            # Recherche de la légende
            caption = find_nearest_caption(captions, img_index)

            print(f"Legende trouvee pour l'image {img_index} page {page_num}: {caption}")

            images_data.append({
                "page": page_num + 1,
                "image_data": image_base64,
                "caption": caption if caption else "Legende non disponible"
            })

    return images_data

def find_nearest_caption(text, img_index):
    """Detection amelioree des legendes autour de l'image"""
    possible_captions = re.findall(r'((?:Figure|Schéma|Graphique|Tableau) \d+.*)', text)
    if img_index < len(possible_captions):
        return possible_captions[img_index]
    return None

def process_pdf(index, row):
    """Télécharge, extrait et stocke un PDF"""
    pdf_url = row["liens"]
    pdf_name = clean_filename(f"{row['nom_medicament']}.pdf")
    pdf_path = os.path.join(PDF_DIR, pdf_name)

    print(f"Traitement de : {pdf_name}")

    if not os.path.exists(pdf_path):
        if not download_pdf(pdf_url, pdf_path):
            return

    structured_content, extracted_tables = extract_text_tables(pdf_path)
    extracted_images = extract_images(pdf_path)

    document = {
        "file_name": pdf_name,
        "title": row["nom_medicament"],
        "content": structured_content,
        "tables": extracted_tables,
        "images": extracted_images
    }

    collection.insert_one(document)
    print(f"Donnees inserees pour {pdf_name}")

# Traitement des PDFs en parallele
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
    futures = [executor.submit(process_pdf, index, row) for index, row in df.iterrows()]
    concurrent.futures.wait(futures)

print("Extraction et stockage termines !")
