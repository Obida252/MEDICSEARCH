import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient

# MongoDB Configuration
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "base_medicaments"
COLLECTION_NAME = "medicaments"

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

# List of medications to scrape (specid values)
medicament_specids = [
    62170486,  # Example: ABACAVIR ARROW 300 mg
    67767535,  # Example: PLAQUENIL 200 mg
    60234100   # Example: DOLIPRANE 1000 mg
]

# Section identifiers (anchors) to extract from the HTML
section_anchors = [
    "RcpDenomination", "RcpCompoQualiQuanti", "RcpFormePharm",
    "RcpIndicTherap", "RcpPosoAdmin", "RcpContreindications",
    "RcpMisesEnGarde", "RcpInteractionsMed", "RcpFertGrossAllait",
    "RcpConduite", "RcpEffetsIndesirables", "RcpSurdosage",
    "RcpPropPharmacodynamiques", "RcpPropPharmacocinetiques", "RcpSecuritePreclinique",
    "RcpListeExcipients", "RcpIncompatibilites", "RcpDureeConservation",
    "RcpPrecConservation", "RcpEmballage", "RcpPrecEmpl"
]

def scrape_medicament(specid):
    """Scrapes medication data from the website and returns it as a structured JSON."""
    url = f"https://base-donnees-publique.medicaments.gouv.fr/affichageDoc.php?specid={specid}&typedoc=R"
    res = requests.get(url)
    res.encoding = res.apparent_encoding or 'utf-8'
    html = res.text
    soup = BeautifulSoup(html, 'lxml')

    med_data = {}  # Stores extracted data

    for anchor in section_anchors:
        tag = soup.find('a', {"name": anchor})
        if not tag:
            continue

        section_title = tag.get_text(strip=True)
        content_lines = []

        parent_p = tag.find_parent('p')
        sibling = parent_p.find_next_sibling()
        while sibling:
            if sibling.name == 'p' and any(cls in ["AmmAnnexeTitre1", "AmmAnnexeTitre2"] for cls in sibling.get("class", [])):
                break
            if sibling.name == 'table':
                table_lines = []
                for row in sibling.find_all('tr'):
                    cells = [cell.get_text(" ", strip=True) for cell in row.find_all(['th', 'td'])]
                    if cells:
                        table_lines.append(" | ".join(cells))
                if table_lines:
                    content_lines.append(f"Table: {section_title}\n" + "\n".join(table_lines))
            else:
                text = sibling.get_text(" ", strip=True)
                if text:
                    content_lines.append(text)
            sibling = sibling.find_next_sibling()

        med_data[section_title] = "\n".join(content_lines)

    return med_data

# Insert data into MongoDB
for specid in medicament_specids:
    try:
        data = scrape_medicament(specid)
    except Exception as e:
        print(f"Error scraping medication {specid}: {e}")
        continue
    if not data:
        continue

    denomination = data.get("1. DÉNOMINATION DU MÉDICAMENT", "").replace("\n", " ")
    data["_id"] = specid
    data["nom"] = denomination
    collection.replace_one({"_id": specid}, data, upsert=True)
    print(f"> Inserted medication {specid}: {denomination}")

print("Scraping complete. Data stored in MongoDB.")
