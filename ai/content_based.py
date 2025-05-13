from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
import ast

# Load dataset
df = pd.read_csv(r"F:\Documents\Assignment\7\ecochef\ai\cleaned_recipes_with_urls.csv")

# Clean data
df['Dietary_Tags'] = df['Dietary_Tags'].fillna('[]')
df = df.dropna(subset=['Ingredients'])

# Process ingredients
ingredients = df['Ingredients'].apply(lambda x: " ".join(ast.literal_eval(x)))

# Vectorize ingredients
vectorizer = TfidfVectorizer()
tfidf_matrix = vectorizer.fit_transform(ingredients)

def recommend_content_based(user_ingredients, dietary=None, top_n=5):
    user_vector = vectorizer.transform([user_ingredients.lower()])
    similarities = cosine_similarity(user_vector, tfidf_matrix)
    top_indices = similarities.argsort()[0][-top_n:][::-1]
    recommendations = df.iloc[top_indices][['Title', 'Ingredients', 'Instructions', 'Dietary_Tags', 'Image_URL']].to_dict('records')
    
    if dietary:
        dietary = dietary.lower()
        recommendations = [
            r for r in recommendations
            if any(dietary in tag.lower() for tag in ast.literal_eval(r['Dietary_Tags']))
        ]
    return recommendations[:top_n]

# Test
if __name__ == "__main__":
    print(recommend_content_based("tomato onion garlic", dietary="vegan"))
    print(recommend_content_based("potatoes", dietary="gluten-free"))