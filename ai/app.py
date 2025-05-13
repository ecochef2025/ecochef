import os
import logging
import pandas as pd
from flask import Flask, request, jsonify
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_cors import CORS
from pymongo import MongoClient
from content_based import recommend_recipes_content_based
from collaborative import recommend_recipes_collaborative

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB connection
mongo_uri = os.getenv("MONGO_URI", "mongodb+srv://ecochef_user:wrJNj3zVI4kWFuPS@ecochefdb.0anvzxc.mongodb.net/?retryWrites=true&w=majority&appName=EcoChefDB")
client = MongoClient(mongo_uri)
try:
    client.server_info()
    logger.info("Successfully connected to MongoDB Atlas")
except Exception as e:
    logger.error(f"Failed to connect to MongoDB Atlas: {e}")
    raise

db = client['ecochef']
users_collection = db['users']
ratings_collection = db['ratings']

# Flask app configuration
app.config['JWT_SECRET_KEY'] = os.getenv("JWT_SECRET_KEY", "81eac43cbb8438fb543404c94a4fe2de860b53d22f816256f15ef9949bd194ab")
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

# Load the dataset using a relative path
try:
    # Get the directory of the current script (app.py)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    # Construct the path to the CSV file relative to app.py
    csv_path = os.path.join(base_dir, "cleaned_recipes_with_urls.csv")
    df = pd.read_csv(csv_path)
    logger.info("Dataset loaded successfully")
except Exception as e:
    logger.error(f"Failed to load dataset: {e}")
    raise

# Routes...

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400

    if users_collection.find_one({'email': email}):
        return jsonify({'error': 'Email already exists'}), 400

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    user = {'email': email, 'password': hashed_password}
    user_id = users_collection.insert_one(user).inserted_id
    return jsonify({'msg': 'User registered successfully', 'user_id': str(user_id)}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    user = users_collection.find_one({'email': email})
    if not user or not bcrypt.check_password_hash(user['password'], password):
        return jsonify({'error': 'Invalid email or password'}), 401

    access_token = create_access_token(identity=str(user['_id']))
    return jsonify({'token': access_token, 'user_id': str(user['_id'])}), 200

@app.route('/recommend', methods=['POST'])
@jwt_required()
def recommend():
    user_id = get_jwt_identity()
    data = request.get_json()
    ingredients = data.get('ingredients', '').split(',')
    dietary = data.get('dietary', '').split(',')

    try:
        content_recommendations = recommend_recipes_content_based(df, ingredients, dietary)
        collaborative_recommendations = recommend_recipes_collaborative(user_id, ratings_collection, df)

        content_recommendations['Source'] = 'Content-Based'
        collaborative_recommendations['Source'] = 'Collaborative'

        combined_recommendations = pd.concat([content_recommendations, collaborative_recommendations])
        recommendations_json = combined_recommendations.to_dict('records')

        return jsonify(recommendations_json), 200
    except Exception as e:
        logger.error(f"Error in recommendation: {e}")
        return jsonify({'msg': 'Error generating recommendations'}), 500

@app.route('/like', methods=['POST'])
@jwt_required()
def like_recipe():
    user_id = get_jwt_identity()
    data = request.get_json()
    recipe_title = data.get('recipe_title')
    liked = data.get('liked')

    ratings_collection.update_one(
        {'user_id': user_id, 'recipe_title': recipe_title},
        {'$set': {'liked': liked}},
        upsert=True
    )
    return jsonify({'msg': 'Preference saved'}), 200

@app.route('/feedback', methods=['POST'])
@jwt_required()
def feedback():
    user_id = get_jwt_identity()
    data = request.get_json()
    recipe_title = data.get('recipe_title')
    rating = data.get('rating')

    if not isinstance(rating, int) or rating < 1 or rating > 5:
        return jsonify({'error': 'Rating must be an integer between 1 and 5'}), 400

    ratings_collection.update_one(
        {'user_id': user_id, 'recipe_title': recipe_title},
        {'$set': {'rating': rating}},
        upsert=True
    )
    return jsonify({'msg': 'Feedback saved'}), 200

if __name__ == '__main__':
    app.run(debug=True)