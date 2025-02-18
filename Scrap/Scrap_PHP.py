import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
import pandas as pd

client = MongoClient("mongodb://localhost:27017/")
db = client["medicine_data"]
collection = db["medicines"]

excel_file = "liens_R.xlsx"
df = pd.read_excel(excel_file)

if 'liens' not in df.columns:
    raise ValueError("The Excel file does not contain a 'liens' column.")

urls = df["liens"].tolist()

TARGET_SECTIONS = {
    "Nom de médicament": ("RcpDenomination", None),
    "Effets indésirables": ("RcpEffetsIndesirables", "RcpSurdosage"),
    "Grossesse et allaitement": ("RcpFertGrossAllait", "RcpConduite"),
    "Contre-indications": ("RcpContreindications", "RcpMisesEnGarde"),
    "Liste des excipients": ("RcpListeExcipients", "RcpIncompatibilites")
}

def extract_section_content(soup, start_anchor, stop_anchor=None, single_line=False):
    heading = soup.find('a', {'name': start_anchor})
    if not heading:
        print(f"Start anchor '{start_anchor}' not found.")
        return None

    if single_line:
        line = heading.find_parent().find_next_sibling()
        if line and line.name == 'p':
            return [line.get_text(strip=True)]
        return []

    content = []
    sibling = heading.find_parent().find_next_sibling()

    while sibling:
        if stop_anchor:
            stop_heading = sibling.find('a', {'name': stop_anchor}) if sibling.find('a') else None
            if stop_heading:
                break

        if sibling.name == 'p':
            content.append(sibling.get_text(strip=True))
        elif sibling.name == 'table':
            rows = []
            for tr in sibling.find_all('tr'):
                cells = [td.get_text(strip=True) for td in tr.find_all(['td', 'th'])]
                rows.append(cells)
            content.append({"table": rows})

        sibling = sibling.find_next_sibling()

    return content

for url in urls:
    print(f"Processing URL: {url}")
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to retrieve the page. Status code: {response.status_code}")
        continue

    soup = BeautifulSoup(response.content, 'html.parser')

    update_date = soup.find('p', class_='DateNotif').get_text(strip=True)

    extracted_data = {"url": url, "update_date": update_date}

    for section_name, (start_anchor, stop_anchor) in TARGET_SECTIONS.items():
        print(f"Extracting section: {section_name}")
        single_line = section_name == "Nom de médicament"
        section_content = extract_section_content(soup, start_anchor, stop_anchor, single_line=single_line)
        if section_content:
            extracted_data[section_name] = section_content
            print(f"Extracted content for '{section_name}': {len(section_content)} items.")
        else:
            print(f"No content found for section '{section_name}'.")

    collection.insert_one(extracted_data)

print("Scraping completed for all URLs and data inserted into MongoDB!")
