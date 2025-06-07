# main.py
from fastapi import FastAPI
import json
import os

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "API is live"}
    
# Load NGSS data on startup
with open("ngss.json") as f:
    ngss_data = json.load(f)

@app.route('/')
def home():
    return "Hello from Flask on Replit!"

@app.route('/api/hello', methods=['GET'])
def hello_api():
    return jsonify({"message": "Hello from your Flask API!"})

@app.route("/ngss", methods=["GET"])
def search_ngss():
    grade = request.args.get("grade", "").lower()
    topic = request.args.get("topic", "").lower()

    if not grade or not topic:
        return jsonify({"error": "Missing grade or topic"}), 400

    results = []

    for uri, standard in ngss_data.items():
        # Safely get description field
        desc_entries = standard.get("http://purl.org/dc/terms/description", [])
        description_text = " ".join([d.get("value", "").lower() for d in desc_entries])

        # Safely get education level and extract grade codes (e.g., "K", "1")
        grade_entries = standard.get("http://purl.org/dc/terms/educationLevel", [])
        grade_values = [g.get("value", "").split("/")[-1].lower() for g in grade_entries]

        # Check if topic and grade match
        if topic in description_text and grade in grade_values:
            notation = standard.get("http://purl.org/ASN/schema/core/statementNotation", [{}])[0].get("value", "")
            results.append({
                "id": notation,
                "description": desc_entries[0].get("value", "") if desc_entries else "",
                "grade": grade_values,
                "uri": uri
            })

    return jsonify({"standards": results})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port)
