from pymongo import MongoClient
client = MongoClient("mongodb+srv://ecochef_user:wrJNj3zVI4kWFuPS@ecochefdb.0anvzxc.mongodb.net/?retryWrites=true&w=majority&appName=EcoChefDB")
db = client["ecochef"]
print(db.list_collection_names())