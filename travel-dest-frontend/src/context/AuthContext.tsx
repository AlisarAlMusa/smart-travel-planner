// Provides JWT auth state, login/signup actions, and logout behavior.

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import { login as loginRequest, signup as signupRequest } from "../api/authApi";
import { clearStoredToken, getStoredToken, storeToken } from "../api/client";
import type { AuthPayload, User } from "../types/auth";

type AuthContextValue = {
  token: string | null;
  user: User | null;
  isAuthenticated: boolean;
  login: (payload: AuthPayload) => Promise<void>;
  signup: (payload: AuthPayload) => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);
const USER_STORAGE_KEY = "travel_planner_user";

function getStoredUser() {
  const rawUser = localStorage.getItem(USER_STORAGE_KEY);

  if (!rawUser) {
    return null;
  }

  try {
    return JSON.parse(rawUser) as User;
  } catch {
    localStorage.removeItem(USER_STORAGE_KEY);
    return null;
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => getStoredToken());
  const [user, setUser] = useState<User | null>(() => getStoredUser());

  const saveAuth = useCallback((nextToken: string, nextUser?: User) => {
    storeToken(nextToken);
    setToken(nextToken);

    if (nextUser) {
      localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(nextUser));
      setUser(nextUser);
    }
  }, []);

  const logout = useCallback(() => {
    clearStoredToken();
    localStorage.removeItem(USER_STORAGE_KEY);
    setToken(null);
    setUser(null);
  }, []);

  const login = useCallback(
    async (payload: AuthPayload) => {
      const response = await loginRequest(payload);
      saveAuth(response.access_token, response.user ?? { email: payload.email });
    },
    [saveAuth],
  );

  const signup = useCallback(
    async (payload: AuthPayload) => {
      const response = await signupRequest(payload);
      saveAuth(response.access_token, response.user ?? { email: payload.email });
    },
    [saveAuth],
  );

  useEffect(() => {
    window.addEventListener("auth:logout", logout);
    return () => window.removeEventListener("auth:logout", logout);
  }, [logout]);

  const value = useMemo(
    () => ({
      token,
      user,
      isAuthenticated: Boolean(token),
      login,
      signup,
      logout,
    }),
    [login, logout, signup, token, user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// This hook lives beside the provider so auth stays easy to follow in a small app.
// eslint-disable-next-line react-refresh/only-export-components
export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider");
  }

  return context;
}
