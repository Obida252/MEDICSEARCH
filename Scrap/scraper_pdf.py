from pymongo import MongoClient
import requests
import os
import fitz
import pandas as pd
import re
import pdfplumber

def create_collections(database_name, collection_names):
    try:
        # Connect to the MongoDB server
        mongo_client = MongoClient('mongodb://localhost:27017/')
        db = mongo_client[database_name]

        collections = {}
        for name in collection_names:
            # Drop collection if it already exists
            if name in db.list_collection_names():
                db.drop_collection(name)
                print(f"Collection '{name}' dropped.")

            # Create new collection
            collections[name] = db[name]
            print(f"Collection '{name}' created successfully.")

        return collections

    except Exception as e:
        print(f"Error creating collections: {e}")
        return None

def extract_pdf_data(pdf_file):
    try:
        with fitz.open(pdf_file) as doc:
            text = " ".join(page.get_text() for page in doc)

            data = {
                "nom": re.search(r"(?:D[ÉE]NOMINATION DU MÉDICAMENT|Nom du médicament)\s*:?\s*(.*?)(?=\n\d+\.)", text, re.IGNORECASE | re.DOTALL),
                "composition": re.search(r"(?:COMPOSITION QUALITATIVE ET QUANTITATIVE|Composition)\s*:?\s*(.*?)(?=\n\d+\.)", text, re.IGNORECASE | re.DOTALL),
                "indications": re.search(r"(?:Indications thérapeutiques|Indications)\s*:?\s*(.*?)(?=\n\d+\.)", text, re.IGNORECASE | re.DOTALL),
                "contre_indications": re.search(r"(?:Contre-indications|Contre indications)\s*:?\s*(.*?)(?=\n\d+\.)", text, re.IGNORECASE | re.DOTALL),
                "effets_secondaires": re.search(r"(?:Effets secondaires|Effets indésirables)\s*:?\s*(.*?)(?=\n\d+\.)", text, re.IGNORECASE | re.DOTALL),
                "posologie": re.search(r"(?:Posologie et mode d’administration|Posologie)\s*:?\s*(.*?)(?=\n\d+\.)", text, re.IGNORECASE | re.DOTALL)
            }

            # Clean extracted data
            for key in data:
                if data[key]:
                    data[key] = re.sub(r'\n+', ' ', data[key].group(1).strip())
                else:
                    data[key] = "Non spécifié"

            tables = []
            with pdfplumber.open(pdf_file) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    extracted_tables = page.extract_tables()
                    for table_num, table in enumerate(extracted_tables):
                        if table:  # Ensure the table is not empty
                            headers = table[0]
                            # Replace None or empty headers with default names
                            headers = [h if h else f"Column_{i+1}" for i, h in enumerate(headers)]
                            rows = [dict(zip(headers, row)) for row in table[1:] if len(row) == len(headers)]
                            tables.append({
                                "title": f"Table {page_num + 1}-{table_num + 1}",
                                "data": rows[:5]  # Include preview (first 5 rows)
                            })
            data['tables'] = tables

            return data
    except Exception as e:
        print(f"Error extracting data from PDF: {e}")
        return {}

def scrape_pdf_data(xlsx_file, collection):
    try:
        data = pd.read_excel(xlsx_file)
        print("Columns in Excel:", data.columns)

        for index, row in data.iterrows():
            name = row.get('nom_medicament')
            pdf_url = row.get('liens')

            if pd.isna(name) or pd.isna(pdf_url):
                print(f"Skipping row {index} due to missing data.")
                continue

            safe_name = re.sub(r'[\\/:*?"<>|]', '_', name)
            pdf_file = f"{safe_name}.pdf"

            response = requests.get(pdf_url)
            with open(pdf_file, 'wb') as file:
                file.write(response.content)

            extracted_data = extract_pdf_data(pdf_file)
            extracted_data["name"] = name

            collection.insert_one(extracted_data)
            print(f"Inserted data for {name}")

            os.remove(pdf_file)

    except Exception as e:
        print(f"Error scraping PDF data: {e}")

if __name__ == "__main__":
    database_name = "medicament_db"
    collection_names = ["pdf_data", "php_data"]
    collections = create_collections(database_name, collection_names)

    scrape_pdf_data('liens_pdf.xlsx', collections['pdf_data'])
