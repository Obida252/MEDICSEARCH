import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient

# MongoDB Configuration
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "pharmascan"
COLLECTION_NAME = "medicaments"

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

# List of medications to scrape
medicament_specids = [
    62170486,  # Example: ABACAVIR/LAMIVUDINE MYLAN
    67767535,  # Example: PLAQUENIL 200 mg
    60234100  # Example: DOLIPRANE 1000 mg
]

# Define section range
start_section = "RcpDenomination"
end_section = "RcpTitulaireAmm"


def extract_table(table):
    """Extracts table data into a structured format."""
    rows = table.find_all('tr')
    if not rows:
        return None  # No rows found

    headers = [header.get_text(strip=True) for header in rows[0].find_all(['th', 'td'])]
    if not headers:
        headers = [f"Column {i + 1}" for i in range(len(rows[1].find_all(['td', 'th'])))]

    table_data = []
    for row in rows[1:]:  # Skip header row if present
        cells = row.find_all(['td', 'th'])
        row_data = {}

        for i, cell in enumerate(cells):
            column_name = headers[i] if i < len(headers) else f"Column {i + 1}"
            row_data[column_name] = cell.get_text(strip=True)

        table_data.append(row_data)

    return table_data if table_data else None  # Return None if empty


def scrape_medicament(specid):
    """Scrapes structured medication data while maintaining section order properly."""
    url = f"https://base-donnees-publique.medicaments.gouv.fr/affichageDoc.php?specid={specid}&typedoc=R"
    res = requests.get(url)
    res.encoding = res.apparent_encoding or 'utf-8'
    soup = BeautifulSoup(res.text, 'html.parser')

    # Locate start and end sections
    start_tag = soup.find("a", {"name": start_section})
    end_tag = soup.find("a", {"name": end_section})

    if not start_tag or not end_tag:
        print(f"Skipping {specid}: Required sections not found.")
        return None

    med_data = {}
    current_section = None
    current_content = []
    tables = []
    section_started = False

    # Iterate through elements within the defined range
    for elem in start_tag.find_all_next():
        if elem == end_tag:
            break  # Stop at the last section

        # Detect new section headers
        if elem.name == "a" and elem.has_attr("name"):
            # **Finalizing previous section** before moving to a new one
            if section_started and current_section:
                med_data[current_section] = {
                    "text": "\n".join(current_content) if current_content else None,
                    "tables": tables if tables else None
                }
            section_started = True
            current_section = elem.get_text(strip=True)  # Store new section title
            current_content = []
            tables = []
            continue  # Move to next element

        if section_started:
            # Extract paragraph text
            if elem.name in ["p", "span", "div"]:
                text = elem.get_text(strip=True)
                if text:
                    current_content.append(text)

            # Extract tables
            if elem.name == "table":
                extracted_table = extract_table(elem)
                if extracted_table:
                    tables.append(extracted_table)

    # Save last section
    if current_section:
        med_data[current_section] = {
            "text": "\n".join(current_content) if current_content else None,
            "tables": tables if tables else None
        }

    return med_data


# Insert data into MongoDB
for specid in medicament_specids:
    try:
        data = scrape_medicament(specid)
        if not data:
            continue

        # Extract and clean denomination
        denomination = data.get("1. DENOMINATION DU MÉDICAMENT", {}).get("text", "").replace("\n",
                                                                                             " ") if "1. DENOMINATION DU MÉDICAMENT" in data else "Unknown"
        document = {"_id": specid, "nom": denomination, "sections": data}

        collection.replace_one({"_id": specid}, document, upsert=True)
        print(f"> Inserted medication {specid}: {denomination}")
    except Exception as e:
        print(f"Error scraping medication {specid}: {e}")

print("Scraping complete. Data stored in MongoDB.")
