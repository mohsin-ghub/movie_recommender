from flask import Flask, render_template, request
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# API Keys
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OMDB_API_KEY = os.getenv("OMDB_API_KEY")

# Get movie poster from OMDb
def get_movie_poster(movie_title):
    url = f"http://www.omdbapi.com/?t={movie_title}&apikey={OMDB_API_KEY}"
    response = requests.get(url)
    data = response.json()
    print(f"📦 OMDb for '{movie_title}':", data)
    if data.get("Poster") and data["Poster"] != "N/A":
        return data["Poster"]
    return "https://via.placeholder.com/200x300?text=No+Image"

# Get GPT movie recommendations
def get_ai_recommendations(movie_title):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "deepseek/deepseek-chat-v3-0324",
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful movie recommender. Reply only with a numbered list of 5 movie titles similar to the input."
            },
            {
                "role": "user",
                "content": f"Recommend 5 movies like '{movie_title}'."
            }
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        data = response.json()
        print("🧠 deepseek Response:", data)
        content = data["choices"][0]["message"]["content"]
        lines = content.strip().split("\n")
        movies = [line.split(". ", 1)[-1].strip() for line in lines if line]
        return movies
    except Exception as e:
        print("❌ deepseek API Error:", e)
        return []

# Home route
@app.route("/", methods=["GET", "POST"])
def home():
    query = ""
    results = []

    if request.method == "POST":
        query = request.form.get("movie")
        recommended = get_ai_recommendations(query)
        results = [(title, get_movie_poster(title)) for title in recommended]

    return render_template("index.html", query=query, results=results)

if __name__ == "__main__":
    app.run(debug=True)
