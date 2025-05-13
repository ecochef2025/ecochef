from sklearn.decomposition import TruncatedSVD
import pandas as pd

# Load ratings
ratings = pd.read_csv(r"F:\Documents\Assignment\7\ecochef\ai\user_ratings.csv")
pivot_table = ratings.pivot(index="user_id", columns="recipe_id", values="rating").fillna(0)

# Apply SVD
svd = TruncatedSVD(n_components=10)
matrix = svd.fit_transform(pivot_table)

def recommend_collaborative(user_id, top_n=5):
    user_index = pivot_table.index.get_loc(user_id)
    user_scores = matrix[user_index]
    top_indices = user_scores.argsort()[-top_n:][::-1]
    return pivot_table.columns[top_indices].tolist()

# Test
if __name__ == "__main__":
    print(recommend_collaborative(1))