import pandas as pd
from pymongo import MongoClient

# Connect to MongoDB Atlas
client = MongoClient("mongodb+srv://ecochef_user:wrJNj3zVI4kWFuPS@ecochefdb.0anvzxc.mongodb.net/?retryWrites=true&w=majority&appName=EcoChefDB")
db = client["ecochef"]
recipes_collection = db["recipes"]

# Load cleaned dataset
df = pd.read_csv(r"F:\Documents\Assignment\7\ecochef\ai\cleaned_recipes_with_urls.csv")

# Convert to dictionary and insert
recipes = df.to_dict("records")
recipes_collection.drop()  # Clear existing data (optional)
recipes_collection.insert_many(recipes)
print("Updated data imported successfully!")