import os
from typing import Optional, List, Tuple
import requests
import re

def get_movie_poster(movie_title: str, year: Optional[str] = None) -> str:
    """
    Try TMDB for poster first using TMDB_API_KEY from environment. If TMDB fails (timeout, no poster, or error), fallback to OMDB using OMDB_API_KEY from environment. Return placeholder if both fail.
    """
    tmdb_api_key = os.getenv("TMDB_API_KEY")
    omdb_api_key = os.getenv("OMDB_API_KEY")
    # Try TMDB first
    if tmdb_api_key and movie_title:
        try:
            search_url = f"https://api.themoviedb.org/3/search/movie?api_key={tmdb_api_key}&query={requests.utils.quote(movie_title)}"
            # Try with year first
            if year:
                search_url_with_year = search_url + f"&year={year}"
                print(f"[DEBUG] TMDB search_url_with_year: {search_url_with_year}")
                search_resp = requests.get(search_url_with_year, timeout=5)
                if search_resp.status_code == 200:
                    search_data = search_resp.json()
                    results = search_data.get("results", [])
                    if results and results[0].get("poster_path"):
                        poster_url = f"https://image.tmdb.org/t/p/w500{results[0]['poster_path']}"
                        print(f"[DEBUG] Poster URL (TMDB): {poster_url}")
                        return poster_url
            # Try again without year
            print(f"[DEBUG] TMDB search_url (no year): {search_url}")
            search_resp = requests.get(search_url, timeout=5)
            if search_resp.status_code == 200:
                search_data = search_resp.json()
                results = search_data.get("results", [])
                if results and results[0].get("poster_path"):
                    poster_url = f"https://image.tmdb.org/t/p/w500{results[0]['poster_path']}"
                    print(f"[DEBUG] Poster URL (TMDB): {poster_url}")
                    return poster_url
            print("[DEBUG] No poster found on TMDB, will try OMDB.")
        except Exception as e:
            print(f"[DEBUG] Exception in get_movie_poster (TMDB): {e}")
    # Fallback to OMDB
    if omdb_api_key and movie_title:
        try:
            url = f"http://www.omdbapi.com/?t={movie_title}"
            if year:
                url += f"&y={year}"
            url += f"&apikey={omdb_api_key}"
            print(f"[DEBUG] OMDB search_url: {url}")
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("Response") == "True" and data.get("Poster") and data["Poster"] != "N/A":
                    print(f"[DEBUG] Poster URL (OMDB): {data['Poster']}")
                    return data["Poster"]
            print(f"[DEBUG] No poster found on OMDB or OMDB error. OMDB response: {resp.text}")
        except Exception as e:
            print(f"[DEBUG] Exception in get_movie_poster (OMDB): {e}")
    # Fallback to placeholder
    print("[DEBUG] Returning placeholder poster.")
    return "https://via.placeholder.com/200x300?text=No+Image"

def get_ai_recommendations(movie_title: str, openrouter_api_key: Optional[str]) -> List[str]:
    """
    Get movie recommendations from the OpenRouter AI API.
    Returns a list of recommendation strings.
    """
    if not openrouter_api_key:
        return ["API key missing. Please set OPENROUTER_API_KEY in your .env file."]
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {openrouter_api_key}",
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
        if "choices" not in data:
            error_msg = data.get("error", {}).get("message", "Unknown error from API.")
            return [f"API error: {error_msg}"]
        content = data["choices"][0]["message"]["content"]
        lines = content.strip().split("\n")
        movies = [line.split(". ", 1)[-1].strip() for line in lines if line]
        return movies
    except Exception as e:
        return [f"API Exception: {e}"]

def extract_title_and_year(line: str) -> Tuple[str, Optional[str]]:
    """
    Extract the movie title and year from a string line.
    Returns (title, year) or (title, None).
    """
    match = re.match(r"\*\*(.*?)\s*\((\d{4})\)\*\*", line)
    if match:
        return match.group(1).strip(), match.group(2)
    match = re.match(r"\*\*(.*?)\*\*", line)
    if match:
        return match.group(1).strip(), None
    match = re.match(r"(.*?)(?:\s*\((\d{4})\))?$", line)
    if match:
        title = match.group(1).strip()
        year = match.group(2)
        if title and title.lower() not in ['n/a', '[insert title here]']:
            return title, year
    return "", None 