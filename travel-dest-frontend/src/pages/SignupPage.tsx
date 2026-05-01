// Signup page for creating a new planner account.

import { Plane, UserPlus } from "lucide-react";
import { useState, type FormEvent } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";

import { getApiErrorMessage } from "../api/client";
import { useAuth } from "../context/AuthContext";

export function SignupPage() {
  const navigate = useNavigate();
  const { isAuthenticated, signup } = useAuth();
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

    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }

    try {
      setIsLoading(true);
      await signup({ email: email.trim(), password });
      navigate("/chat", { replace: true });
    } catch (apiError) {
      setError(getApiErrorMessage(apiError));
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
        <h1>Create Account</h1>
        <p>Save your trip requests and see what the agent did each time.</p>

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
              placeholder="At least 8 characters"
              autoComplete="new-password"
            />
          </label>

          {error ? <p className="form-error">{error}</p> : null}

          <button className="primary-button" type="submit" disabled={isLoading}>
            <UserPlus size={18} />
            {isLoading ? "Creating account..." : "Sign up"}
          </button>
        </form>

        <p className="auth-switch">
          Already have an account? <Link to="/login">Log in</Link>
        </p>
      </section>
    </main>
  );
}
