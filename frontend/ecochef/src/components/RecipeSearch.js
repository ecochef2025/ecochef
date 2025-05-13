import React, { useState } from "react";
import axios from "axios";

function RecipeSearch() {
  const [ingredients, setIngredients] = useState("");
  const [dietary, setDietary] = useState("");
  const [recipes, setRecipes] = useState([]);

  const handleSearch = async () => {
    const token = localStorage.getItem("token");
    if (!token) {
      alert("Please login to search for recipes.");
      return;
    }
    try {
      const response = await axios.post(
        "http://localhost:5000/recommend",
        { ingredients, dietary },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setRecipes(response.data);
    } catch (error) {
      alert("Error fetching recommendations: " + (error.response?.data?.msg || error.message));
    }
  };

  const handleLike = async (recipeTitle, liked) => {
    const token = localStorage.getItem("token");
    try {
      await axios.post(
        "http://localhost:5000/like",
        { recipe_title: recipeTitle, liked },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      alert(`Recipe ${liked ? "liked" : "disliked"}!`);
    } catch (error) {
      alert("Error submitting preference: " + (error.response?.data?.error || error.message));
    }
  };

  const handleFeedback = async (recipeTitle, rating) => {
    const token = localStorage.getItem("token");
    try {
      await axios.post(
        "http://localhost:5000/feedback",
        { recipe_title: recipeTitle, rating },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      alert("Feedback submitted!");
    } catch (error) {
      alert("Error submitting feedback: " + (error.response?.data?.error || error.message));
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("userId");
    window.location.href = "/login";
  };

  return (
    <div className="min-h-screen bg-gray-100 py-6">
      <div className="max-w-4xl mx-auto px-4">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-4xl font-bold text-center text-gray-800">EcoChef Recipe Search</h1>
          <button
            onClick={handleLogout}
            className="bg-red-500 text-white px-4 py-2 rounded-lg hover:bg-red-600 transition duration-300"
          >
            Logout
          </button>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-lg">
          <input
            type="text"
            value={ingredients}
            onChange={(e) => setIngredients(e.target.value)}
            placeholder="Enter ingredients (e.g., tomato, onion)"
            className="border p-3 w-full mb-4 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500"
          />
          <input
            type="text"
            value={dietary}
            onChange={(e) => setDietary(e.target.value)}
            placeholder="Dietary preferences (e.g., vegan, gluten-free)"
            className="border p-3 w-full mb-4 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500"
          />
          <button
            onClick={handleSearch}
            className="bg-red-500 text-white p-3 w-full rounded-lg hover:bg-red-600 transition duration-300"
          >
            Search Recipes
          </button>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-6">
          {recipes.map((recipe) => {
            const dietaryTags = typeof recipe.Dietary_Tags === "string" ? JSON.parse(recipe.Dietary_Tags.replace(/'/g, '"')) : recipe.Dietary_Tags;
            const recipeIngredients = typeof recipe.Ingredients === "string" ? JSON.parse(recipe.Ingredients.replace(/'/g, '"')) : recipe.Ingredients;
            return (
              <div key={recipe.Title} className="bg-white p-4 rounded-lg shadow-md hover:shadow-lg transition duration-300">
                <img src={recipe.Image_URL} alt={recipe.Title} className="w-full h-48 object-cover rounded-t-lg mb-4" />
                <h3 className="text-xl font-semibold text-gray-800">{recipe.Title}</h3>
                <p className="text-gray-600 text-sm mb-2"><strong>Ingredients:</strong> {recipeIngredients.join(", ")}</p>
                <p className="text-gray-600 text-sm mb-2"><strong>Instructions:</strong> {recipe.Instructions}</p>
                <p className="text-gray-500 text-xs mb-2"><strong>Dietary:</strong> {dietaryTags.join(", ")}</p>
                <p className="text-gray-500 text-xs mb-4"><strong>Source:</strong> {recipe.Source}</p>
                <div className="flex space-x-2 mb-2">
                  <button
                    onClick={() => handleLike(recipe.Title, true)}
                    className="bg-green-500 text-white px-2 py-1 rounded hover:bg-green-600"
                  >
                    Like
                  </button>
                  <button
                    onClick={() => handleLike(recipe.Title, false)}
                    className="bg-red-500 text-white px-2 py-1 rounded hover:bg-red-600"
                  >
                    Dislike
                  </button>
                </div>
                <div>
                  <label className="text-gray-700">Rate (1-5): </label>
                  <select
                    onChange={(e) => handleFeedback(recipe.Title, parseInt(e.target.value))}
                    className="border p-1 rounded"
                  >
                    <option value="">Select</option>
                    {[1, 2, 3, 4, 5].map((num) => (
                      <option key={num} value={num}>{num}</option>
                    ))}
                  </select>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

export default RecipeSearch;