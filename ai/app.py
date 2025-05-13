from flask import Flask, request, jsonify
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from pymongo import MongoClient
from flask_cors import CORS
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import logging

# Configure logging to reduce noise from PyMongo
logging.basicConfig(level=logging.INFO)  # Changed from DEBUG to INFO
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = "81eac43cbb8438fb543404c94a4fe2de860b53d22f816256f15ef9949bd194ab"
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = 3600
CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}}, supports_credentials=True)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

# Initialize MongoDB client with connection timeout
try:
    client = MongoClient(
        "mongodb+srv://ecochef_user:wrJNj3zVI4kWFuPS@ecochefdb.0anvzxc.mongodb.net/?retryWrites=true&w=majority&appName=EcoChefDB",
        serverSelectionTimeoutMS=5000  # 5-second timeout
    )
    client.server_info()  # Test the connection
    logger.info("Successfully connected to MongoDB Atlas")
except Exception as e:
    logger.error(f"Failed to connect to MongoDB: {str(e)}")
    raise  # Raise the exception to stop the app if connection fails

db = client["ecochef"]
users_collection = db["users"]
recipes_collection = db["recipes"]
preferences_collection = db["preferences"]
feedback_collection = db["feedback"]

# Load and process dataset with error handling
try:
    df = pd.read_csv(r"F:\Documents\Assignment\7\ecochef\ai\cleaned_recipes_with_urls.csv")
    logger.info("Successfully loaded dataset")
except Exception as e:
    logger.error(f"Failed to load dataset: {str(e)}")
    raise  # Raise the exception to stop the app if dataset fails

def safe_eval_ingredients(ingredients):
    try:
        if pd.isna(ingredients) or not isinstance(ingredients, str):
            return ""
        return " ".join(ingredients.split()) if ingredients else ""
    except (SyntaxError, ValueError, TypeError):
        return ""

try:
    tfidf = TfidfVectorizer()
    tfidf_matrix = tfidf.fit_transform(df["Ingredients"].apply(safe_eval_ingredients))
    logger.info("Successfully initialized TF-IDF matrix")
except Exception as e:
    logger.error(f"Failed to initialize TF-IDF matrix: {str(e)}")
    raise  # Raise the exception to stop the app if TF-IDF fails

@app.route("/register", methods=["POST"])
def register():
    try:
        data = request.get_json()
        email = data.get("email")
        password = data.get("password")
        name = data.get("name")
        dietary_preferences = data.get("dietary_preferences", [])

        if users_collection.find_one({"email": email}):
            return jsonify({"error": "User already exists"}), 400

        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
        user = {
            "email": email,
            "password": hashed_password,
            "name": name,
            "dietary_preferences": dietary_preferences
        }
        user_id = users_collection.insert_one(user).inserted_id
        logger.info(f"User registered: {email}")
        return jsonify({"message": "User registered"}), 201
    except Exception as e:
        logger.error(f"Error in /register: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json()
        email = data.get("email")
        password = data.get("password")

        user = users_collection.find_one({"email": email})
        if not user or not bcrypt.check_password_hash(user["password"], password):
            return jsonify({"error": "Invalid credentials"}), 401

        access_token = create_access_token(identity=str(user["_id"]))
        logger.info(f"User logged in: {email}")
        return jsonify({"token": access_token, "user_id": str(user["_id"])}), 200
    except Exception as e:
        logger.error(f"Error in /login: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/recommend", methods=["POST"])
@jwt_required()
def recommend():
    try:
        data = request.get_json()
        ingredients = data.get("ingredients", "")
        dietary = data.get("dietary", "").lower()

        user_vector = tfidf.transform([safe_eval_ingredients(ingredients)])
        cosine_similarities = cosine_similarity(user_vector, tfidf_matrix).flatten()
        similar_indices = cosine_similarities.argsort()[-10:][::-1]
        recommended_recipes = df.iloc[similar_indices].to_dict("records")

        filtered_recipes = [
            recipe for recipe in recommended_recipes
            if dietary in [tag.lower() for tag in eval(recipe["Dietary_Tags"])]
        ]

        # Label content-based recommendations
        for recipe in filtered_recipes:
            recipe["Source"] = "Content-Based"

        user_id = get_jwt_identity()
        collab_recommendations = get_collaborative_recommendations(user_id)

        # Label collaborative recommendations
        for recipe in collab_recommendations:
            recipe["Source"] = "Collaborative"

        combined_recommendations = filtered_recipes[:3] + collab_recommendations[:2]
        logger.info(f"Recommendations generated for user {user_id}")
        return jsonify(combined_recommendations[:5]), 200
    except Exception as e:
        logger.error(f"Error in /recommend: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/like", methods=["POST"])
@jwt_required()
def like_recipe():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        recipe_title = data.get("recipe_title")
        liked = data.get("liked", True)

        recipe = recipes_collection.find_one({"Title": recipe_title})
        if not recipe:
            return jsonify({"error": "Recipe not found"}), 404

        preferences_collection.update_one(
            {"user_id": user_id, "recipe_title": recipe_title},
            {"$set": {"liked": liked}},
            upsert=True
        )
        logger.info(f"Preference updated for user {user_id}: {recipe_title}")
        return jsonify({"message": "Preference updated"}), 200
    except Exception as e:
        logger.error(f"Error in /like: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/feedback", methods=["POST"])
@jwt_required()
def submit_feedback():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        recipe_title = data.get("recipe_title")
        rating = data.get("rating")

        if not (1 <= rating <= 5):
            return jsonify({"error": "Rating must be between 1 and 5"}), 400

        recipe = recipes_collection.find_one({"Title": recipe_title})
        if not recipe:
            return jsonify({"error": "Recipe not found"}), 404

        feedback_collection.update_one(
            {"user_id": user_id, "recipe_title": recipe_title},
            {"$set": {"rating": rating}},
            upsert=True
        )
        logger.info(f"Feedback submitted for user {user_id}: {recipe_title}")
        return jsonify({"message": "Feedback submitted"}), 200
    except Exception as e:
        logger.error(f"Error in /feedback: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

def get_collaborative_recommendations(user_id):
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

        return recommendations
    except Exception as e:
        logger.error(f"Error in get_collaborative_recommendations: {str(e)}")
        return []

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)