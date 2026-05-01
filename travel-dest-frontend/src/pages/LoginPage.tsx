// Login page for existing users.

import { LogIn, Plane } from "lucide-react";
import { useState, type FormEvent } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";

import { getApiErrorMessage } from "../api/client";
import { useAuth } from "../context/AuthContext";

export function LoginPage() {
  const navigate = useNavigate();
  const { isAuthenticated, login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");

    if (!email.trim() || !password.trim()) {
      setError("Please enter both email and password.");
      return;
    }

    try {
      setIsLoading(true);
      await login({ email: email.trim(), password });
      navigate("/chat", { replace: true });
    } catch (apiError) {
      setError(getApiErrorMessage(apiError));
      setPassword("");
    } finally {
      setIsLoading(false);
    }
  }

  if (isAuthenticated) {
    return <Navigate to="/chat" replace />;
  }

  return (
    <main className="auth-page">
      <section className="auth-card">
        <div className="auth-icon">
          <Plane size={26} />
        </div>
        <h1>Welcome Back</h1>
        <p>Log in to plan trips and review your agent traces.</p>

        <form onSubmit={handleSubmit}>
          <label>
            Email
            <input
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="testuser@example.com"
              autoComplete="email"
            />
          </label>

          <label>
            Password
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="password123"
              autoComplete="current-password"
            />
          </label>

          {error ? (
            <p className="form-error" role="alert">
              {error}
            </p>
          ) : null}

          <button className="primary-button" type="submit" disabled={isLoading}>
            <LogIn size={18} />
            {isLoading ? "Logging in..." : "Log in"}
          </button>
        </form>

        <p className="auth-switch">
          Need an account? <Link to="/signup">Create one</Link>
        </p>
      </section>
    </main>
  );
}
