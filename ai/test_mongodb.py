from pymongo import MongoClient
client = MongoClient("mongodb+srv://ecochef6:<BBkL5PRtcMSXwlB7>@ecochefdb.k5pczsf.mongodb.net/?retryWrites=true&w=majority&appName=EcoChefDB")
db = client["ecochef6"]
print(db.list_collection_names())