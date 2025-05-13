from sklearn.metrics.pairwise import cosine_similarity

def recommend_collaborative(user_id, preferences_collection, feedback_collection, recipes_collection, top_n=5):
    try:
        all_preferences = list(preferences_collection.find())
        all_feedback = list(feedback_collection.find())
        if not (all_preferences or all_feedback):
            return []

        users = list(set(pref["user_id"] for pref in all_preferences).union(fb["user_id"] for fb in all_feedback))
        recipes = list(set(pref["recipe_title"] for pref in all_preferences).union(fb["recipe_title"] for fb in all_feedback))
        user_index = {user: idx for idx, user in enumerate(users)}
        recipe_index = {recipe: idx for idx, recipe in enumerate(recipes)}

        matrix = [[0] * len(recipes) for _ in range(len(users))]
        for pref in all_preferences:
            u_idx = user_index[pref["user_id"]]
            r_idx = recipe_index[pref["recipe_title"]]
            matrix[u_idx][r_idx] = 1 if pref["liked"] else -1
        for fb in all_feedback:
            u_idx = user_index[fb["user_id"]]
            r_idx = recipe_index[fb["recipe_title"]]
            matrix[u_idx][r_idx] = fb["rating"]

        current_user_idx = user_index.get(user_id, -1)
        if current_user_idx == -1:
            return []

        current_user_vector = matrix[current_user_idx]
        similarities = []
        for idx, user_vector in enumerate(matrix):
            if idx == current_user_idx:
                continue
            sim = cosine_similarity([current_user_vector], [user_vector])[0][0]
            similarities.append((idx, sim))

        similarities.sort(key=lambda x: x[1], reverse=True)
        similar_users = [idx for idx, sim in similarities[:2]]

        recommended_titles = set()
        for idx in similar_users:
            for r_idx, value in enumerate(matrix[idx]):
                if value >= 4 and matrix[current_user_idx][r_idx] == 0:
                    recommended_titles.add(recipes[r_idx])

        recommendations = []
        for title in recommended_titles:
            recipe = recipes_collection.find_one({"Title": title})
            if recipe:
                recommendations.append({
                    "Title": recipe["Title"],
                    "Ingredients": recipe["Ingredients"],
                    "Instructions": recipe["Instructions"],
                    "Dietary_Tags": recipe["Dietary_Tags"],
                    "Image_URL": recipe["Image_URL"]
                })

        return recommendations[:top_n]
    except Exception as e:
        print(f"Error in recommend_collaborative: {str(e)}")
        return []

# Test (only runs locally)
if __name__ == "__main__":
    from pymongo import MongoClient
    client = MongoClient("mongodb+srv://ecochef_user:wrJNj3zVI4kWFuPS@ecochefdb.0anvzxc.mongodb.net/?retryWrites=true&w=majority&appName=EcoChefDB")
    db = client["ecochef"]
    print(recommend_collaborative("user_id_example", db["preferences"], db["feedback"], db["recipes"]))