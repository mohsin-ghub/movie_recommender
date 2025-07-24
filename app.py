import os
import requests
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import re
from utils import get_movie_poster, get_ai_recommendations, extract_title_and_year

load_dotenv()
app = Flask(__name__)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OMDB_API_KEY = os.getenv("OMDB_API_KEY")

# Debug print for keys (do not print actual key for security)
print("OPENROUTER_API_KEY loaded:", bool(OPENROUTER_API_KEY))
print("OMDB_API_KEY loaded:", bool(OMDB_API_KEY))

def get_ai_recommendations(movie_title):
    if not OPENROUTER_API_KEY:
        print("[ERROR] OPENROUTER_API_KEY is missing. Cannot get recommendations.")
        return []
    # Debug print for the API key (masked)
    print("OPENROUTER_API_KEY (masked):", OPENROUTER_API_KEY[:4] + "..." + OPENROUTER_API_KEY[-4:] if OPENROUTER_API_KEY else "None")
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "deepseek/deepseek-chat-v3-0324:free",
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful movie recommendation assistant. Given a movie title, suggest 5 similar movies with a short reason for each."
            },
            {
                "role": "user",
                "content": f"Recommend 5 movies similar to {movie_title}."
            }
        ]
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        data = response.json()
        print("🧠 deepseek Response:", data)
        if "choices" not in data:
            error_msg = data.get("error", {}).get("message", "Unknown error from API.")
            print(f"[ERROR] API response error: {error_msg}")
            return []  # Return empty list on error
        content = data["choices"][0]["message"]["content"]
        lines = content.strip().split("\n")
        movies = [line.split(". ", 1)[-1].strip() for line in lines if line]
        return movies
    except Exception as e:
        print("❌ deepseek API Error:", e)
        return []

# Improved extract_title to handle more edge cases

def extract_title(line):
    # Try to extract from **Title (Year)** or **Title**
    match = re.match(r"\*\*(.*?)\*\*", line)
    if match:
        title = match.group(1).split("&")[0].split(",")[0].strip()
        if title and title.lower() not in ['n/a', '[insert title here]']:
            return title
    # Try to extract up to the first dash, parenthesis, ampersand, or comma
    part = line.split('–')[0].split('-')[0].split('(')[0].split('&')[0].split(',')[0].strip()
    if part and part.lower() not in ['n/a', '[insert title here]']:
        return part
    # Try to extract a capitalized phrase at the start
    match = re.match(r"([A-Z][A-Za-z0-9:,'!\\- ]+)", line)
    if match:
        title = match.group(1).strip()
        if title and title.lower() not in ['n/a', '[insert title here]']:
            return title
    # Fallback: return empty string
    return ""

def extract_title_and_year(line):
    # Try to extract from **Title (Year)**
    match = re.match(r"\*\*(.*?)\s*\((\d{4})\)\*\*", line)
    if match:
        return match.group(1).strip(), match.group(2)
    # Try to extract from **Title**
    match = re.match(r"\*\*(.*?)\*\*", line)
    if match:
        return match.group(1).strip(), None
    # Fallback: extract title and year from e.g. 'Sing (2016)'
    match = re.match(r"(.*?)(?:\s*\((\d{4})\))?$", line)
    if match:
        title = match.group(1).strip()
        year = match.group(2)
        if title and title.lower() not in ['n/a', '[insert title here]']:
            return title, year
    return "", None

def get_movie_details(title, year=None):
    if not OMDB_API_KEY or not title:
        return None
    # Sanitize title: remove asterisks and extra whitespace
    clean_title = title.replace('*', '').strip()
    url = f"http://www.omdbapi.com/?t={clean_title}"
    if year:
        url += f"&y={year}"
    url += f"&apikey={OMDB_API_KEY}"
    print(f"[DEBUG] Requesting OMDB details URL: {url}")
    try:
        response = requests.get(url, timeout=5)
        print(f"[DEBUG] OMDB details status code: {response.status_code}")
        print(f"[DEBUG] OMDB details raw response: {response.text}")
        if response.status_code != 200:
            return None
        data = response.json()
        if data.get("Response") == "True":
            return {
                "Poster": data.get("Poster", "https://via.placeholder.com/200x300?text=No+Image"),
                "Title": data.get("Title", clean_title),
                "Director": data.get("Director", "N/A"),
                "Cast": data.get("Actors", "N/A"),
                "Runtime": data.get("Runtime", "N/A"),
                "Rating": data.get("imdbRating", "N/A"),
                "Year": data.get("Year", year)
            }
        else:
            print(f"[INFO] OMDB details not found for '{clean_title}'. OMDB response: {data}")
            return None
    except Exception as e:
        print(f"[ERROR] Exception fetching movie details for '{title}': {e}")
        return None

@app.route("/movie_details", methods=["POST"])
def movie_details():
    data = request.get_json()
    title = data.get("title")
    year = data.get("year")
    details = get_movie_details(title, year)
    if details:
        return jsonify({"success": True, "details": details})
    else:
        return jsonify({"success": False, "error": "Movie details not found."}), 404

@app.route("/", methods=["GET"])
def landing():
    return render_template("landing.html")

@app.route("/login-signup", methods=["GET"])
def login_signup():
    return render_template("login_signup.html")

@app.route("/recommender", methods=["GET", "POST"])
def home():
    query = ""
    results = []
    error = None
    generic_texts = []
    if request.method == "POST":
        query = request.form.get("movie")
        if query:
            movie_strings = get_ai_recommendations(query)
            if not movie_strings:
                error = "Could not get recommendations. Please check your OpenRouter API key."
                return render_template("index.html", query=query, results=[], error=error, generic_texts=[])
            title_years = [extract_title_and_year(line) for line in movie_strings]
            posters = []
            failed_count = 0
            for title, year in title_years:
                poster = get_movie_poster(title, year)
                if poster.endswith("No+Image"):
                    failed_count += 1
                posters.append(poster)
            def split_title_desc(s):
                parts = re.split(r"\s*[–\-:]\s+", s, maxsplit=1)
                if len(parts) == 2:
                    return parts[0].strip(), parts[1].strip()
                return s.strip(), ""
            results = []
            for movie_str, poster in zip(movie_strings, posters):
                title, desc = split_title_desc(movie_str)
                # Remove asterisks/stars from title
                title = title.replace('*', '').strip()
                # Heuristic: consider as generic text if no description, or if the string is long and not a movie title
                if (not desc and (len(title) > 60 or 'movie' in title.lower() or 'recommend' in title.lower() or 'like' in title.lower())) or (poster.endswith('No+Image') and not desc):
                    generic_texts.append(title)
                else:
                    results.append((title, desc, poster))
            if failed_count == len(title_years):
                error = "No posters found for any recommended movies. Check OMDB API key or title format."
    return render_template("index.html", query=query, results=results, error=error, generic_texts=generic_texts)

if __name__ == "__main__":
    app.run(debug=True)
    
