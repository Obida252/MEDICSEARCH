import requests
from bs4 import BeautifulSoup
import pandas as pd
import re

# Sample URLs for testing
urls = [
    "https://base-donnees-publique.medicaments.gouv.fr/affichageDoc.php?specid=61266250&typedoc=R",
    "https://base-donnees-publique.medicaments.gouv.fr/affichageDoc.php?specid=61876780&typedoc=R",
    "https://base-donnees-publique.medicaments.gouv.fr/affichageDoc.php?specid=63797011&typedoc=R",
]

# Function to extract data from a single URL
def extract_data_from_url(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    data = {"url": url}

    # Extract "ANSM - Mis à jour" date
    date_element = soup.find('p', class_='DateNotif')
    if date_element:
        match = re.search(r": (\d{2}/\d{2}/\d{4})", date_element.text)
        if match:
            data["date_mise_a_jour"] = match.group(1)

    # Extract "Nom du médicament"
    nom_medicament_element = soup.find('a', name=re.compile(r'_Hlk\d+'))
    if nom_medicament_element:
        data["nom_medicament"] = nom_medicament_element.text.strip()

    # Additional extraction logic can go here for other sections

    return data

# Process all URLs
data_list = []
for url in urls:
    try:
        extracted_data = extract_data_from_url(url)
        data_list.append(extracted_data)
    except Exception as e:
        print(f"Error processing {url}: {e}")

# Convert to DataFrame and export to CSV
final_data = pd.DataFrame(data_list)
final_data.to_csv('medicines_data.csv', index=False, encoding='utf-8')

print("Data extraction complete. Output saved to 'medicines_data.csv'")
