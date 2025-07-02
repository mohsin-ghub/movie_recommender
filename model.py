import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


df = pd.read_csv("movie.csv")


df['genres'] = df['genres'].fillna('').str.replace('|', ' ', regex=False)


tfidf = TfidfVectorizer(stop_words='english')
tfidf_matrix = tfidf.fit_transform(df['genres'])


cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)


indices = pd.Series(df.index, index=df['title'])


def recommend(title, num_recommendations=5):
    if title not in indices:
        return ["Movie not found in dataset."]
    
    idx = indices[title]
    sim_scores = list(enumerate(cosine_sim[idx]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    sim_scores = sim_scores[1:num_recommendations+1]
    movie_indices = [i[0] for i in sim_scores]
    
    return df['title'].iloc[movie_indices].tolist()


