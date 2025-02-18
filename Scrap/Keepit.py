import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient

# MongoDB setup
client = MongoClient("mongodb://localhost:27017/")
db = client["medicine_data"]
collection = db["medicines"]

# URL to scrape
url = "https://base-donnees-publique.medicaments.gouv.fr/affichageDoc.php?specid=68257528&typedoc=R"

# Fetch the page
response = requests.get(url)
if response.status_code != 200:
    print(f"Failed to retrieve the page. Status code: {response.status_code}")
    exit()

# Parse the HTML
soup = BeautifulSoup(response.content, 'html.parser')

# Extract the update date
update_date = soup.find('p', class_='DateNotif').get_text(strip=True)

# Function to extract tables
def extract_table(table):
    rows = []
    for tr in table.find_all('tr'):
        cells = [td.get_text(strip=True) for td in tr.find_all(['td', 'th'])]
        rows.append(cells)
    return rows

# Extract sections
data = {"update_date": update_date, "sections": []}

# Get all section headings
headings = soup.find_all('p', class_=['AmmAnnexeTitre1', 'AmmAnnexeTitre2', 'AmmAnnexeTitre3'])

for i, heading in enumerate(headings):
    section_title = heading.get_text(strip=True)
    content = []

    # Collect content until the next heading
    sibling = heading.find_next_sibling()
    while sibling and sibling not in headings:
        if sibling.name == 'p':
            content.append(sibling.get_text(strip=True))
        elif sibling.name == 'table':
            content.append({"table": extract_table(sibling)})
        sibling = sibling.find_next_sibling()

    # Store the section data
    data["sections"].append({"title": section_title, "content": content})

# Insert data into MongoDB
collection.insert_one(data)

print("Scraping completed and data inserted into MongoDB!")
