// Renders the authenticated navigation bar and logout action.

import { LogOut, MessageSquareText, Plane, ScrollText } from "lucide-react";
import { NavLink, useNavigate } from "react-router-dom";

import { useAuth } from "../context/AuthContext";

export function Navbar() {
  const navigate = useNavigate();
  const { logout, user } = useAuth();

  function handleLogout() {
    logout();
    navigate("/login", { replace: true });
  }

  return (
    <header className="navbar">
      <NavLink to="/chat" className="brand" aria-label="Smart Travel Planner home">
        <Plane size={22} />
        <span>Smart Travel Planner</span>
      </NavLink>

      <nav className="nav-links" aria-label="Main navigation">
        <NavLink to="/chat">
          <MessageSquareText size={18} />
          <span>Planner</span>
        </NavLink>
        <NavLink to="/history">
          <ScrollText size={18} />
          <span>History</span>
        </NavLink>
      </nav>

      <div className="nav-user">
        <span title={user?.email}>{user?.email ?? "Signed in"}</span>
        <button className="icon-button" type="button" onClick={handleLogout} title="Log out">
          <LogOut size={18} />
        </button>
      </div>
    </header>
  );
}
