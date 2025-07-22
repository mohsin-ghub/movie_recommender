import os
import requests
import re
from typing import Optional, Tuple, List


def get_env_key(key_name: str) -> Optional[str]:
    """
    Retrieve an environment variable by name.
    Returns None if the variable is not set.
    """
    value = os.getenv(key_name)
    if not value:
        # Log error elsewhere, do not print sensitive info
        pass
    return value


def get_movie_poster(movie_title: str, year: Optional[str] = None, omdb_api_key: Optional[str] = None) -> str:
    """
    Fetch the movie poster URL from OMDB API. Returns a placeholder if not found or on error.
    """
    if not omdb_api_key or not movie_title:
        return "https://via.placeholder.com/200x300?text=No+Image"
    url = f"http://www.omdbapi.com/?t={movie_title}"
    if year:
        url += f"&y={year}"
    url += f"&apikey={omdb_api_key}"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code != 200:
            return "https://via.placeholder.com/200x300?text=No+Image"
        data = response.json()
        if data.get("Response") == "True" and data.get("Poster") and data["Poster"] != "N/A":
            return data["Poster"]
        else:
            return "https://via.placeholder.com/200x300?text=No+Image"
    except Exception:
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


def extract_title(line: str) -> str:
    """
    Extract the movie title from a string line.
    """
    match = re.match(r"\*\*(.*?)\*\*", line)
    if match:
        title = match.group(1).split("&")[0].split(",")[0].strip()
        if title and title.lower() not in ['n/a', '[insert title here]']:
            return title
    part = line.split('\u2013')[0].split('-')[0].split('(')[0].split('&')[0].split(',')[0].strip()
    if part and part.lower() not in ['n/a', '[insert title here]']:
        return part
    match = re.match(r"([A-Z][A-Za-z0-9:,'!\\- ]+)", line)
    if match:
        title = match.group(1).strip()
        if title and title.lower() not in ['n/a', '[insert title here]']:
            return title
    return ""


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