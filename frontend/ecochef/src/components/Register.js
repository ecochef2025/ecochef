import React, { useState } from "react";
import axios from "axios";
import { useNavigate, Link } from "react-router-dom";

function Register() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [dietary, setDietary] = useState("");
  const navigate = useNavigate();

  const handleRegister = async () => {
    try {
      await axios.post("https://ecochef-backend.onrender.com/register", {
        email,
        password,
        name,
        dietary_preferences: dietary.split(",").map((d) => d.trim()),
      });
      alert("Registration successful!");
      navigate("/login");
    } catch (error) {
      alert("Registration failed: " + (error.response?.data?.error || error.message));
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center">
      <div className="bg-white p-6 rounded-lg shadow-lg w-full max-w-md">
        <h1 className="text-3xl font-bold text-center text-gray-800 mb-6">Register</h1>
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Name"
          className="border p-3 w-full mb-4 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500"
        />
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="Email"
          className="border p-3 w-full mb-4 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500"
        />
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Password"
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
          onClick={handleRegister}
          className="bg-red-500 text-white p-3 w-full rounded-lg hover:bg-red-600 transition duration-300"
        >
          Register
        </button>
        <p className="mt-4 text-center text-gray-600">
          Already have an account?{" "}
          <Link to="/login" className="text-red-500 underline">
            Login here
          </Link>
        </p>
      </div>
    </div>
  );
}

export default Register;