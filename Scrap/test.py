import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient

MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "base_medicaments"
COLLECTION_NAME = "medicaments"

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

medicament_specids = [
    62170486,  # ABACAVIR ARROW 300 mg
    67767535,  # PLAQUENIL 200 mg
    60234100  # DOLIPRANE 1000 mg
]

section_names = {
    "RcpDenomination": "1. DENOMINATION DU MEDICAMENT",
    "RcpCompoQualiQuanti": "2. COMPOSITION QUALITATIVE ET QUANTITATIVE",
    "RcpFormePharm": "3. FORME PHARMACEUTIQUE",
    "RcpDonneesCliniques": "4. DONNEES CLINIQUES",
    "RcpIndicTherap": "4.1. Indications thérapeutiques",
    "RcpPosoAdmin": "4.2. Posologie et mode d'administration",
    "RcpContreindications": "4.3. Contre-indications",
    "RcpMisesEnGarde": "4.4. Mises en garde spéciales et précautions d'emploi",
    "RcpInteractionsMed": "4.5. Interactions avec d'autres médicaments et autres formes d'interactions",
    "RcpFertGrossAllait": "4.6. Fertilité, grossesse et allaitement",
    "RcpConduite": "4.7. Effets sur l'aptitude à conduire des véhicules et à utiliser des machines",
    "RcpEffetsIndesirables": "4.8. Effets indésirables",
    "RcpSurdosage": "4.9. Surdosage",
    "RcpPropPharmacologiques": "5. PROPRIETES PHARMACOLOGIQUES",
    "RcpPropPharmacodynamiques": "5.1. Propriétés pharmacodynamiques",
    "RcpPropPharmacocinetiques": "5.2. Propriétés pharmacocinétiques",
    "RcpDonneesPharmaceutiques": "6. DONNEES PHARMACEUTIQUES",
    "RcpListeExcipients": "6.1. Liste des excipients",
    "RcpIncompatibilites": "6.2. Incompatibilités",
    "RcpDureeConservation": "6.3. Durée de conservation",
    "RcpPrecConservation": "6.4. Précautions particulières de conservation",
    "RcpEmballage": "6.5. Nature et contenu de l'emballage extérieur",
    "RcpPrecEmpl": "6.6. Précautions particulières d’élimination et de manipulation"
}


def extract_table(table):
    rows = table.find_all('tr')
    if not rows or len(rows) < 2:
        return None

    headers = [header.get_text(strip=True) for header in rows[0].find_all(['th', 'td'])]
    if not headers:
        headers = [f"Column {i + 1}" for i in range(len(rows[1].find_all(['td', 'th'])))]

    table_data = []
    for row in rows[1:]:
        cells = row.find_all(['td', 'th'])
        if len(cells) != len(headers):
            continue
        row_data = {headers[i]: cell.get_text(strip=True) for i, cell in enumerate(cells)}
        table_data.append(row_data)

    return table_data if table_data else None


def scrape_medicament(specid):
    url = f"https://base-donnees-publique.medicaments.gouv.fr/affichageDoc.php?specid={specid}&typedoc=R"
    res = requests.get(url)
    res.encoding = res.apparent_encoding or 'utf-8'
    soup = BeautifulSoup(res.text, 'html.parser')

    med_data = {}
    current_section = None
    content = []
    tables = []

    for element in soup.find_all(['a', 'p', 'table']):
        if element.name == 'a' and 'name' in element.attrs:
            section_key = element['name']
            if section_key in section_names:
                if current_section:
                    if content:
                        content.pop()
                    section_data = {"text": "\n".join(content).strip()} if content else {}
                    if tables:
                        section_data["tables"] = tables
                    med_data[current_section] = section_data

                current_section = section_names[section_key]
                content = []
                tables = []

        elif element.name == 'p':
            content.append(element.get_text(strip=True))

        elif element.name == 'table':
            extracted_table = extract_table(element)
            if extracted_table:
                tables.append(extracted_table)

    if current_section and content:
        content.pop()
        section_data = {"text": "\n".join(content).strip()} if content else {}
        if tables:
            section_data["tables"] = tables
        med_data[current_section] = section_data

    return med_data


for specid in medicament_specids:
    try:
        data = scrape_medicament(specid)
    except Exception as e:
        print(f"Error scraping medication {specid}: {e}")
        continue
    if not data:
        continue

    denomination = data.get("1. DENOMINATION DU MEDICAMENT", {}).get("text", "").replace("\n", " ")
    data["_id"] = specid
    data["nom"] = denomination
    collection.replace_one({"_id": specid}, data, upsert=True)
    print(f"> Inserted medication {specid}: {denomination}")

print("Scraping complete. Data stored in MongoDB.")
