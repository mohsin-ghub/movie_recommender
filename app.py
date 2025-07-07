from flask import Flask, render_template, request
import requests

app = Flask(__name__)

OMDB_API_KEY = "ae9b968"  # Replace with your real OMDb API key

def get_movie_poster(movie_title):
    url = f"http://www.omdbapi.com/?t={movie_title}&apikey={OMDB_API_KEY}"
    response = requests.get(url)
    data = response.json()
    if data.get("Poster") and data["Poster"] != "N/A":
        return data["Poster"]
    return None

@app.route('/', methods=['GET', 'POST'])
def home():
    poster = None
    movie = None
    if request.method == 'POST':
        movie = request.form['movie']
        poster = get_movie_poster(movie)
    return render_template('index.html', movie=movie, poster=poster)

if __name__ == '__main__':
    app.run(debug=True)
