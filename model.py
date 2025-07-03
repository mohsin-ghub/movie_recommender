import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


movies = pd.read_csv('movies.csv')


movies['genres'] = movies['genres'].fillna('')

tfidf = TfidfVectorizer(stop_words='english')
tfidf_matrix = tfidf.fit_transform(movies['genres'])

cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)

movies = movies.reset_index()

def find_closest_title(user_input):
    user_input = user_input.lower().replace(" ", "").replace("(", "").replace(")", "")
    for title in movies['title']:
        clean_title = title.lower().replace(" ", "").replace("(", "").replace(")", "")
        if user_input in clean_title:
            return title
    return None

def recommend(title):
    matched_title = find_closest_title(title)
    if matched_title is None:
        return ["Sorry, movie not found."]
    
    idx = movies[movies['title'] == matched_title].index[0]
    sim_scores = list(enumerate(cosine_sim[idx]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    sim_scores = sim_scores[1:6]  # Top 5 recommendations
    movie_indices = [i[0] for i in sim_scores]
    return movies['title'].iloc[movie_indices].tolist()
