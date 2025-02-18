from pymongo import MongoClient
import pandas as pd


def display_tables_from_mongo(database_name, collection_name):
    try:
        # Connect to MongoDB
        client = MongoClient('mongodb://localhost:27017/')
        db = client[database_name]
        collection = db[collection_name]

        # Retrieve all documents from the collection
        documents = collection.find()

        for doc in documents:
            print(f"Medication Name: {doc.get('name', 'Unknown')}")
            print("=" * 50)  # Separator for readability

            # Check if the document contains tables
            if 'tables' in doc and doc['tables']:
                for table in doc['tables']:
                    print(f"Table Title: {table['title']}")

                    # Convert table data to a Pandas DataFrame
                    df = pd.DataFrame(table['data'])

                    # Print DataFrame as a visual table
                    print(df)
                    print("\n")  # Newline for spacing between tables
            else:
                print("No tables available.")

            print("=" * 50 + "\n")  # End of the document separator

    except Exception as e:
        print(f"Error fetching data from MongoDB: {e}")


# Usage
database_name = "medicament_db"  # Your database name
collection_name = "pdf_data"  # Your collection name
display_tables_from_mongo(database_name, collection_name)
