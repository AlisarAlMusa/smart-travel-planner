// Protects authenticated app routes and renders the shared navbar layout.

import { Navigate, Outlet } from "react-router-dom";

import { Navbar } from "../components/Navbar";
import { useAuth } from "../context/AuthContext";

export function ProtectedRoute() {
  const { isAuthenticated } = useAuth();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div className="app-shell">
      <Navbar />
      <Outlet />
    </div>
  );
}
