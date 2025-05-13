import pandas as pd
import ast

# Load dataset
dataset_path = "F:/Documents/Assignment/10/Dataset/Food_Ingredients_and_Recipe_Dataset_with_Image_Name_Mapping.xlsx"
df = pd.read_excel(dataset_path)

# Clean data
# Remove duplicates
df = df.drop_duplicates()

# Convert string lists to actual lists using safe evaluation
df["Ingredients"] = df["Ingredients"].apply(lambda x: ast.literal_eval(x))

# Standardize ingredient names (lowercase, strip whitespace)
df["Ingredients"] = df["Ingredients"].apply(lambda x: [i.lower().strip() for i in x])

# Handle missing values
df = df.dropna()

# Tags recipes as vegan if no animal products are detected
df["Dietary_Tags"] = df["Ingredients"].apply(
    lambda x: ["vegan"] if all(i not in ["meat", "chicken", "fish", "egg", "milk", "cheese", "butter"] for i in x) else []
)

# Save cleaned data for MongoDB import
output_path = "F:/Documents/Assignment/10/ecochef/ai/cleaned_recipes.csv"
df.to_csv(output_path, index=False)
print(f"Dataset cleaned and saved to {output_path}")

# Display sample for verification
print("Sample cleaned data:")
print(df[["Title", "Ingredients", "Dietary_Tags"]].head())