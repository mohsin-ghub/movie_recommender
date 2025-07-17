import os
import requests
from flask import Flask, render_template, request
from dotenv import load_dotenv

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

def get_movie_poster(movie_title):
    if not OMDB_API_KEY:
        return "https://via.placeholder.com/200x300?text=No+Image"
    url = f"http://www.omdbapi.com/?t={movie_title}&apikey={OMDB_API_KEY}"
    response = requests.get(url)
    data = response.json()
    if data.get("Response") == "True" and data.get("Poster") and data["Poster"] != "N/A":
        return data["Poster"]
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
        "model": "google/gemini-2.5-flash-lite-preview-06-17",
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

@app.route("/", methods=["GET"])
def landing():
    return render_template("landing.html")

@app.route("/recommender", methods=["GET", "POST"])
def home():
    query = ""
    results = []
    posters = []
    if request.method == "POST":
        query = request.form.get("movie")
        if query:
            results = get_ai_recommendations(query)
            posters = [get_movie_poster(movie) for movie in results]
    return render_template("index.html", query=query, results=results, posters=posters)

if __name__ == "__main__":
    app.run(debug=True)
    
