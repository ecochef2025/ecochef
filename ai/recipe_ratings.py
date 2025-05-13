import pandas as pd

# Create the data
data = {
    'user_id': [1, 1, 2, 2],
    'recipe_id': [0, 1, 0, 2],
    'rating': [5, 3, 4, 5]
}

# Create a DataFrame
ratings_df = pd.DataFrame(data)

# Save to CSV
ratings_df.to_csv('recipe_ratings.csv', index=False)

print("CSV file created successfully!")
print(ratings_df)