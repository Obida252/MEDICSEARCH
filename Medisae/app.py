from flask import Flask, render_template
from pymongo import MongoClient

app = Flask(__name__)

# MongoDB Configuration
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "base_medicaments"
COLLECTION_NAME = "medicaments"

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

@app.route('/')
def index():
    """Displays the list of medications."""
    medicaments = list(collection.find({}, {"_id": 1, "nom": 1}))
    return render_template('medicament.html', medicaments=medicaments)

@app.route('/medicament/<int:specid>')
def medicament_detail(specid):
    """Displays details of a selected medication."""
    medicament = collection.find_one({"_id": specid})
    if not medicament:
        return "Médicament introuvable", 404
    return render_template('detail.html', medicament=medicament)

if __name__ == '__main__':
    app.run(debug=True)