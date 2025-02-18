from pymongo import MongoClient
import pprint  # For pretty printing

# Connect to MongoDB
mongo_client = MongoClient('mongodb://localhost:27017/')
db = mongo_client['medicament_db']  # Database name
collection = db['pdf_data']         # Collection name

# Fetch all documents
documents = collection.find()

# Loop through documents and print tables
for doc in documents:
    print(f"Name: {doc['name']}")
    if 'tables' in doc and doc['tables']:
        print("Tables:")
        for i, table in enumerate(doc['tables']):
            print(f"Table {i + 1}:")
            pprint.pprint(table)
    else:
        print("No tables found.")
    print("-" * 50)
