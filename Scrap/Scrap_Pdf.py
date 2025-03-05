import requests
import fitz  # PyMuPDF pour l'extraction des PDFs
import pytesseract  # OCR pour les PDF scannés
from pdf2image import convert_from_bytes
import pandas as pd
import base64
from io import BytesIO
from pymongo import MongoClient
from PIL import Image

# Configurer le chemin de Tesseract si nécessaire
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Connexion MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["Pharmacie"]
collection = db["PDF"]

# Charger les URLs des PDFs depuis l'Excel (sélection des 10 premiers)
excel_file = r"C:\Document\IUT\SAE\liens_pdf.xlsx"
df = pd.read_excel(excel_file)

if 'liens' not in df.columns:
    raise ValueError("Le fichier Excel ne contient pas de colonne 'liens'.")

urls = df["liens"].head(10).tolist()

# User-Agent pour éviter le blocage
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
}

# Sections cibles pour structurer les médicaments
TARGET_SECTIONS = [
    "1. DÉNOMINATION DU MÉDICAMENT", "2. COMPOSITION QUALITATIVE ET QUANTITATIVE",
    "3. FORME PHARMACEUTIQUE", "4. DONNÉES CLINIQUES", "5. PROPRIÉTÉS PHARMACOLOGIQUES",
    "6. DONNÉES PHARMACEUTIQUES", "7. TITULAIRE DE L'AUTORISATION DE MISE SUR LE MARCHE",
    "8. NUMÉRO(S) D'AUTORISATION DE MISE SUR LE MARCHE", "9. DATE DE PREMIÈRE AUTORISATION",
    "10. DATE DE MISE À JOUR DU TEXTE", "11. DOSIMÉTRIE", "12. INSTRUCTIONS POUR LA PRÉPARATION"
]

def resize_image(image, base_width=1000):
    """ Réduit la taille de l’image pour accélérer l’OCR """
    w_percent = base_width / float(image.size[0])
    h_size = int(float(image.size[1]) * w_percent)
    return image.resize((base_width, h_size), Image.Resampling.LANCZOS)

def extract_text_by_sections(doc):
    """Extrait et structure le texte du PDF en sections bien définies"""
    extracted_medicines = []
    current_medicine = None
    current_section = None

    for page in doc:
        text_blocks = page.get_text("blocks")

        for block in text_blocks:
            line = block[4].strip()

            if line.startswith("1.") and "DÉNOMINATION DU MÉDICAMENT" in line.upper():
                if current_medicine:
                    extracted_medicines.append(current_medicine)

                current_medicine = {"sections": {}, "tables": [], "images": []}
                current_section = line
                current_medicine["sections"][current_section] = {"content": []}
                print(f"Nouveau médicament détecté : {line}")

            elif any(line.startswith(sec) for sec in TARGET_SECTIONS):
                current_section = line
                if current_medicine is None:
                    continue
                current_medicine["sections"][current_section] = {"content": []}
                print(f"Section détectée : {line}")

            elif current_section and current_medicine:
                current_medicine["sections"][current_section]["content"].append({"text": line})

    if current_medicine:
        extracted_medicines.append(current_medicine)

    return extracted_medicines

def extract_text_from_images(pdf_bytes):
    """Utilise OCR pour extraire du texte si le PDF est scanné"""
    try:
        images = convert_from_bytes(pdf_bytes.read())
        text = "\n".join(pytesseract.image_to_string(resize_image(img), lang="fra", timeout=15) for img in images)
        return text
    except Exception as e:
        print(f"Erreur OCR : {e}")
        return ""

def extract_images_from_pdf(doc):
    """Extrait les images du PDF et les encode en base64"""
    images = []
    for page_index in range(len(doc)):
        for img_index, img in enumerate(doc[page_index].get_images(full=True)):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            encoded_image = base64.b64encode(image_bytes).decode("utf-8")
            images.append({"page": page_index + 1, "image": encoded_image})
    return images

def extract_tables_from_pdf(doc):
    """Extraction améliorée des tableaux à partir des blocs de texte tabulaires"""
    tables = []
    for page in doc:
        text_blocks = page.get_text("blocks")
        table = []
        for block in text_blocks:
            line = block[4].strip()
            if "|" in line or "\t" in line or "  " in line:  # Détection des structures tabulaires
                table.append(line.split("|") if "|" in line else line.split())
        if table:
            tables.append({"table": table})
    return tables

# Vérifier si l'URL a déjà été traitée
existing_urls = {doc["url"] for doc in collection.find({}, {"url": 1})}

# Scraping des PDFs
for url in urls:
    if url in existing_urls:
        print(f"URL déjà traitée, passage au suivant : {url}")
        continue

    print(f"Téléchargement et traitement du PDF : {url}")

    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors du téléchargement : {e}")
        continue

    # Chargement du PDF
    pdf_bytes = BytesIO(response.content)
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    # Essayer d'extraire le texte
    medicines = extract_text_by_sections(doc)
    if not medicines:
        print(f"Aucune donnée trouvée, tentative OCR sur {url}")
        ocr_text = extract_text_from_images(pdf_bytes)
        if ocr_text.strip():
            medicines = [{"sections": {"OCR": {"content": [{"text": ocr_text}]}}}]
        else:
            print(f"OCR a échoué, PDF peut être illisible : {url}")
            continue

    images = extract_images_from_pdf(doc)
    tables = extract_tables_from_pdf(doc)

    # Insérer chaque médicament individuellement
    for medicine in medicines:
        medicine["url"] = url
        medicine["images"] = images
        medicine["tables"] = tables

        # Vérification insertion MongoDB
        result = collection.insert_one(medicine)
        if result.inserted_id:
            print(f"Médicament inséré avec ID {result.inserted_id}")
        else:
            print("Échec de l'insertion dans MongoDB !")

print("\n=== FIN DU SCRAPING PDF ===")
print("Toutes les données ont été extraites et insérées dans MongoDB !")
