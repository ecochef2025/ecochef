import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import RecipeSearch from "./components/RecipeSearch";
import Login from "./components/Login";
import Register from "./components/Register";

function App() {
  const isAuthenticated = !!localStorage.getItem("token");

  return (
    <Router>
      <Routes>
        <Route
          path="/"
          element={isAuthenticated ? <Navigate to="/recipe-search" replace /> : <Navigate to="/login" replace />}
        />
        <Route
          path="/login"
          element={isAuthenticated ? <Navigate to="/recipe-search" replace /> : <Login />}
        />
        <Route
          path="/register"
          element={isAuthenticated ? <Navigate to="/recipe-search" replace /> : <Register />}
        />
        <Route
          path="/recipe-search"
          element={isAuthenticated ? <RecipeSearch /> : <Navigate to="/login" replace />}
        />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </Router>
  );
}

export default App;