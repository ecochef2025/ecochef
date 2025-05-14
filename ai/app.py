import ast
import os
import logging
import pandas as pd
from flask import Flask, request, jsonify
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from pymongo import MongoClient
from flask_cors import CORS
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from content_based import recommend_content_based
from collaborative import recommend_collaborative

# Configure logging to reduce noise from PyMongo
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "81eac43cbb8438fb543404c94a4fe2de860b53d22f816256f15ef9949bd194ab")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = 3600
CORS(app, resources={r"/*": {"origins": "https://ecochef.vercel.app"}}, supports_credentials=True)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

# Initialize MongoDB client with connection timeout
mongo_uri = os.getenv("MONGO_URI", "mongodb+srv://ecochef_user:wrJNj3zVI4kWFuPS@ecochefdb.0anvzxc.mongodb.net/?retryWrites=true&w=majority&appName=EcoChefDB")
try:
    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
    client.server_info()
    logger.info("Successfully connected to MongoDB Atlas")
except Exception as e:
    logger.error(f"Failed to connect to MongoDB: {str(e)}")
    raise

db = client["ecochef"]
users_collection = db["users"]
recipes_collection = db["recipes"]
preferences_collection = db["preferences"]
feedback_collection = db["feedback"]

# Load and process dataset with error handling
try:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(base_dir, "cleaned_recipes_with_urls.csv")
    df = pd.read_csv(csv_path)
    logger.info("Successfully loaded dataset")
except Exception as e:
    logger.error(f"Failed to load dataset: {str(e)}")
    raise

# Clean data (moved from content_based.py)
df['Dietary_Tags'] = df['Dietary_Tags'].fillna('[]')
df = df.dropna(subset=['Ingredients'])

# Process ingredients and vectorize (moved from content_based.py)
def safe_eval_ingredients(ingredients):
    try:
        if pd.isna(ingredients) or not isinstance(ingredients, str):
            return ""
        return " ".join(ingredients.split()) if ingredients else ""
    except (SyntaxError, ValueError, TypeError):
        return ""

try:
    ingredients = df['Ingredients'].apply(lambda x: " ".join(ast.literal_eval(x)))
    tfidf = TfidfVectorizer()
    tfidf_matrix = tfidf.fit_transform(ingredients)
    logger.info("Successfully initialized TF-IDF matrix")
except Exception as e:
    logger.error(f"Failed to initialize TF-IDF matrix: {str(e)}")
    raise

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

        # Pass df, vectorizer, and tfidf_matrix to content-based recommendation
        filtered_recipes = recommend_content_based(df, tfidf, tfidf_matrix, ingredients, dietary)

        # Label content-based recommendations
        for recipe in filtered_recipes:
            recipe["Source"] = "Content-Based"

        user_id = get_jwt_identity()
        # Pass MongoDB collections to collaborative recommendation
        collab_recommendations = recommend_collaborative(
            user_id, preferences_collection, feedback_collection, recipes_collection
        )

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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)