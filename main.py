# main.py
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse
import json
import os

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "API is live"}

# Load NGSS data on startup
with open("ngss.json") as f:
    ngss_data = json.load(f)

@app.get("/api/hello")
def hello_api():
    return {"message": "Hello from your FastAPI!"}

@app.get("/ngss")
def search_ngss(grade: str = "", topic: str = ""):
    grade = grade.lower()
    topic = topic.lower()

    if not grade or not topic:
        return JSONResponse({"error": "Missing grade or topic"}, status_code=400)

    results = []

    for uri, standard in ngss_data.items():
        desc_entries = standard.get("http://purl.org/dc/terms/description", [])
        description_text = " ".join([d.get("value", "").lower() for d in desc_entries])

        grade_entries = standard.get("http://purl.org/dc/terms/educationLevel", [])
        grade_values = [g.get("value", "").split("/")[-1].lower() for g in grade_entries]

        if topic in description_text and grade in grade_values:
            notation = standard.get("http://purl.org/ASN/schema/core/statementNotation", [{}])[0].get("value", "")
            results.append({
                "id": notation,
                "description": desc_entries[0].get("value", "") if desc_entries else "",
                "grade": grade_values,
                "uri": uri
            })

    return {"standards": results}
