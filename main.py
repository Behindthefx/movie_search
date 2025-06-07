from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import json
import os
import requests

app = FastAPI()

# Enable CORS for GPT to access the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can tighten this later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load NGSS data at startup
with open("ngss.json") as f:
    ngss_data = json.load(f)

@app.get("/")
def read_root():
    return {"message": "API is live on Render"}

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

# TMDb Movie Search (replace with your TMDb API key)
TMDB_API_KEY = os.environ.get("TMDB_API_KEY", "YOUR_API_KEY_HERE")

@app.get("/movies")
def search_movies(query: str):
    if not TMDB_API_KEY or TMDB_API_KEY == "YOUR_API_KEY_HERE":
        return JSONResponse({"error": "Missing TMDb API key"}, status_code=500)

    # First step: search for movies by keyword
    search_url = "https://api.themoviedb.org/3/search/movie"
    params = {"api_key": TMDB_API_KEY, "query": query}
    response = requests.get(search_url, params=params)

    if response.status_code != 200:
        return JSONResponse({"error": "TMDb search failed"}, status_code=500)

    results = []
    for movie in response.json().get("results", []):
        movie_id = movie.get("id")
        title = movie.get("title")
        overview = movie.get("overview", "")
        release_year = movie.get("release_date", "")[:4]

        # Step 2: Get MPAA rating
        cert_url = f"https://api.themoviedb.org/3/movie/{movie_id}/release_dates"
        cert_resp = requests.get(cert_url, params={"api_key": TMDB_API_KEY})
        rating = "NR"

        if cert_resp.status_code == 200:
            for entry in cert_resp.json().get("results", []):
                if entry["iso_3166_1"] == "US":
                    for rel in entry["release_dates"]:
                        rating = rel.get("certification", "NR")
                        if rating:
                            break

        results.append({
            "title": title,
            "release_year": release_year,
            "overview": overview,
            "rating": rating or "NR"
        })

    return {"results": results}
