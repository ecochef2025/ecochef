import React, { useState } from "react";
import axios from "axios";

function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleLogin = async () => {
    try {
      const response = await axios.post("http://localhost:5000/login", {
        email,
        password,
      });
      localStorage.setItem("token", response.data.token);
      localStorage.setItem("userId", response.data.user_id);
      window.location.href = "/recipe-search"; // Force reload to ensure redirect
    } catch (error) {
      alert("Login failed: " + (error.response?.data?.error || error.message));
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center">
      <div className="bg-white p-8 rounded-lg shadow-lg w-full max-w-md">
        <h1 className="text-3xl font-bold text-center text-gray-800 mb-6">Login to EcoChef</h1>
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
        <button
          onClick={handleLogin}
          className="bg-red-500 text-white p-3 w-full rounded-lg hover:bg-red-600 transition duration-300"
        >
          Login
        </button>
        <p className="text-center text-gray-600 mt-4">
          Don't have an account?{" "}
          <a href="/register" className="text-red-500 hover:underline">
            Register
          </a>
        </p>
      </div>
    </div>
  );
}

export default Login;