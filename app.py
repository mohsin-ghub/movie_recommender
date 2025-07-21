import os
import requests
from flask import Flask, render_template, request
from dotenv import load_dotenv
import re

load_dotenv()
app = Flask(__name__)

def get_env_key(key_name):
    value = os.getenv(key_name)
    if not value:
        print(f"[ERROR] Environment variable '{key_name}' is missing or empty.")
    return value

OPENROUTER_API_KEY = get_env_key("OPENROUTER_API_KEY")
OMDB_API_KEY = get_env_key("OMDB_API_KEY")

# Debug print for keys (do not print actual key for security)
print("OPENROUTER_API_KEY loaded:", bool(OPENROUTER_API_KEY))
print("OMDB_API_KEY loaded:", bool(OMDB_API_KEY))

def get_movie_poster(movie_title, year=None):
    if not OMDB_API_KEY or not movie_title:
        print(f"[DEBUG] OMDB_API_KEY present: {bool(OMDB_API_KEY)}; movie_title: '{movie_title}'")
        return "https://via.placeholder.com/200x300?text=No+Image"
    url = f"http://www.omdbapi.com/?t={movie_title}"
    if year:
        url += f"&y={year}"
    url += f"&apikey={OMDB_API_KEY}"
    masked_key = OMDB_API_KEY[:4] + "..." + OMDB_API_KEY[-4:] if len(OMDB_API_KEY) > 8 else OMDB_API_KEY
    print(f"[DEBUG] Requesting OMDB URL: {url.replace(OMDB_API_KEY, masked_key)}")
    try:
        response = requests.get(url, timeout=5)
        print(f"[DEBUG] OMDB status code: {response.status_code}")
        if response.status_code != 200:
            print(f"[ERROR] OMDB API returned status code {response.status_code} for title '{movie_title}'")
            return "https://via.placeholder.com/200x300?text=No+Image"
        try:
            data = response.json()
        except Exception as e:
            print(f"[ERROR] Could not decode JSON for '{movie_title}': {e}")
            print(f"[DEBUG] Raw response text: {response.text}")
            return "https://via.placeholder.com/200x300?text=No+Image"
        if data.get("Response") == "True" and data.get("Poster") and data["Poster"] != "N/A":
            return data["Poster"]
        else:
            print(f"[INFO] No poster found for '{movie_title}'. OMDB response: {data}")
            return "https://via.placeholder.com/200x300?text=No+Image"
    except Exception as e:
        print(f"[ERROR] Exception fetching poster for '{movie_title}': {e}")
        return "https://via.placeholder.com/200x300?text=No+Image"

def get_ai_recommendations(movie_title):
    if not OPENROUTER_API_KEY:
        print("[ERROR] OPENROUTER_API_KEY is missing. Cannot get recommendations.")
        return ["API key missing. Please set OPENROUTER_API_KEY in your .env file."]
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
            return [f"API error: {error_msg}"]
        content = data["choices"][0]["message"]["content"]
        lines = content.strip().split("\n")
        movies = [line.split(". ", 1)[-1].strip() for line in lines if line]
        return movies
    except Exception as e:
        print("❌ deepseek API Error:", e)
        return [f"API Exception: {e}"]

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

# Extract both title and year for OMDB

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
    
