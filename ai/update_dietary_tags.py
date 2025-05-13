import pandas as pd
import ast

# Load dataset
df = pd.read_csv(r"F:\Documents\Assignment\7\ecochef\ai\cleaned_recipes_with_urls.csv")

# Function to assign dietary tags
def assign_dietary_tags(ingredients):
    try:
        ingredients = ast.literal_eval(ingredients)
        tags = []
        # Define exclusion terms
        meat_terms = ["meat", "chicken", "beef", "pork", "fish", "turkey", "sausage", "bacon"]
        dairy_terms = ["milk", "cheese", "butter", "cream", "parmesan", "yogurt", "parmigiano", "cheddar", "mozzarella", "feta"]
        gluten_terms = ["flour", "wheat", "bread", "pasta", "ciabatta", "spaghetti"]
        high_carb_terms = ["pasta", "spaghetti", "bread", "rice", "potato", "sugar", "honey", "flour", "ciabatta"]

        # Case-insensitive check
        has_meat = any(any(term in i.lower() for term in meat_terms) for i in ingredients)
        has_dairy = any(any(term in i.lower() for term in dairy_terms) for i in ingredients)
        has_gluten = any(any(term in i.lower() for term in gluten_terms) for i in ingredients)
        has_high_carb = any(any(term in i.lower() for term in high_carb_terms) for i in ingredients)

        # Vegan: No meat or dairy
        if not (has_meat or has_dairy):
            tags.append("vegan")
        # Vegetarian: No meat
        if not has_meat:
            tags.append("vegetarian")
        # Gluten-free: No gluten
        if not has_gluten:
            tags.append("gluten-free")
        # Dairy-free: No dairy
        if not has_dairy:
            tags.append("dairy-free")
        # Low-carb: No high-carb ingredients
        if not has_high_carb:
            tags.append("low-carb")
        # Keto: No high-carb, must have dairy or meat (keto allows dairy and meat)
        if not has_high_carb and (has_meat or has_dairy):
            tags.append("keto")

        return tags
    except:
        return []

# Apply tags
df["Dietary_Tags"] = df["Ingredients"].apply(assign_dietary_tags)

# Save updated dataset
df.to_csv(r"F:\Documents\Assignment\7\ecochef\ai\cleaned_recipes_with_urls.csv", index=False)
print("Dietary tags updated and saved!")