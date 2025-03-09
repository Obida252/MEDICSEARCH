import requests
import fitz
import pytesseract
from pdf2image import convert_from_bytes
import pandas as pd
import base64
from io import BytesIO
from pymongo import MongoClient
from PIL import Image
import re
import pdfplumber
import logging

logging.basicConfig(level=logging.INFO)

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

client = MongoClient("mongodb://localhost:27017/")
db = client["Pharmacie"]
collection = db["PDF"]

excel_file = r"C:\Document\IUT\SAE\liens_pdf.xlsx"
df = pd.read_excel(excel_file)

if 'liens' not in df.columns:
    raise ValueError("Le fichier Excel doit contenir une colonne 'liens'.")

urls = df["liens"].head(10).tolist()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/114.0.0.0 Safari/537.36"
}

ANNEXE_REGEX = re.compile(r"^(ANNEXE\s+[IVX]+)", re.I)
SECTION_REGEX = re.compile(
    r"^(\d{1,2}\.|[A-D]\.)\s+[A-ZÉÈÀÇ'’\-\(\)\s]+",
    re.I
)

def resize_image(image, base_width=1000):
    w_percent = base_width / float(image.size[0])
    h_size = int((float(image.size[1]) * w_percent))
    try:
        return image.resize((base_width, h_size), Image.Resampling.LANCZOS)
    except AttributeError:
        return image.resize((base_width, h_size), Image.ANTIALIAS)

def extract_sections(doc):
    structured_data = {}
    current_annexe = None
    current_section = None

    ANNEXE_REGEX = re.compile(r"^(ANNEXE\s+[IVX]+)", re.I)
    
    # Cette regex est plus souple et détectera correctement tes sections
    SECTION_REGEX = re.compile(
        r"^(\d{1,2}\.\s*[A-ZÉÈÀÇ'’\-\(\)\s]+|[A-D]\.\s*[A-ZÉÈÀÇ'’\-\(\)\s]+)", re.I)

    # Sauvegarde la dernière ligne pour gérer les titres en plusieurs lignes
    previous_line = ""

    for page in doc:
        blocks = page.get_text("blocks")
        blocks_sorted = sorted(blocks, key=lambda b: (b[1], b[0]))

        for block in blocks_sorted:
            line = block[4].strip()

            annexe_match = ANNEXE_REGEX.match(line)
            section_match = SECTION_REGEX.match(line)

            if annexe_match:
                current_annexe = annexe_match.group(1).strip()
                structured_data[current_annexe] = {}
                current_section = None
                previous_line = ""
                logging.info(f"Annexe détectée : {current_annexe}")
                continue

            if section_match and current_annexe:
                current_section = section_match.group(1).strip()
                structured_data[current_annexe][current_section] = []
                previous_line = ""
                logging.info(f"Section détectée : {current_section}")
                continue

            # Gestion des titres potentiellement en plusieurs lignes
            if current_annexe and not current_section and previous_line:
                combined_line = previous_line + " " + line
                combined_match = SECTION_REGEX.match(combined_line)
                if combined_match:
                    current_section = combined_match.group(1).strip()
                    structured_data[current_annexe][current_section] = []
                    previous_line = ""
                    logging.info(f"Section combinée détectée : {current_section}")
                    continue

            if current_annexe and current_section:
                structured_data[current_annexe][current_section].append(line)

            previous_line = line

    # Nettoyage final du contenu
    for annexe in structured_data:
        for sec in structured_data[annexe]:
            structured_data[annexe][sec] = re.sub(r'\s+', ' ', " ".join(structured_data[annexe][sec])).strip()

    return structured_data


def extract_images_from_pdf(doc):
    images = []
    for page_index in range(len(doc)):
        for img in doc[page_index].get_images(full=True):
            base_image = doc.extract_image(img[0])
            image_bytes = base_image["image"]
            encoded_image = base64.b64encode(image_bytes).decode("utf-8")
            images.append({"page": page_index + 1, "image": encoded_image})
    return images

def extract_tables_from_pdf(pdf_bytes):
    tables = []
    pdf_bytes.seek(0)
    with pdfplumber.open(pdf_bytes) as pdf:
        for page in pdf.pages:
            page_tables = page.extract_tables()
            if page_tables:
                tables.extend(page_tables)
    return tables

existing_urls = set(doc["url"] for doc in collection.find({}, {"url": 1}))

for url in urls:
    if url in existing_urls:
        logging.info(f"URL déjà traitée : {url}")
        continue

    logging.info(f"Traitement de l'URL : {url}")

    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        pdf_bytes = BytesIO(response.content)
    except Exception as e:
        logging.error(f"Erreur téléchargement : {e}")
        continue

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    structured_data = extract_sections(doc)

    if not structured_data:
        logging.warning("Aucune donnée textuelle trouvée, tentative OCR.")
        structured_data = {"OCR": pytesseract.image_to_string(resize_image(img), lang="fra") for img in convert_from_bytes(pdf_bytes.getvalue(), dpi=200)}

    images = extract_images_from_pdf(doc)
    tables = extract_tables_from_pdf(pdf_bytes)

    document = {
        "url": url,
        "sections": structured_data,
        "images": images,
        "tables": tables
    }

    result = collection.insert_one(document)
    if result.inserted_id:
        logging.info(f"Document inséré avec ID {result.inserted_id}")
    else:
        logging.error("Échec de l'insertion dans MongoDB !")

logging.info("=== FIN DU SCRAPING PDF ===")
logging.info("Toutes les données ont été extraites et insérées dans MongoDB !")
