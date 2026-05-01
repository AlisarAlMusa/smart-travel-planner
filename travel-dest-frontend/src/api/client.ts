// Shared Axios client that attaches JWT auth and handles expired sessions.

import axios, { AxiosError } from "axios";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";
const TOKEN_STORAGE_KEY = "travel_planner_token";

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
  headers: {
    "Content-Type": "application/json",
  },
});

export function getStoredToken() {
  return localStorage.getItem(TOKEN_STORAGE_KEY);
}

export function storeToken(token: string) {
  localStorage.setItem(TOKEN_STORAGE_KEY, token);
}

export function clearStoredToken() {
  localStorage.removeItem(TOKEN_STORAGE_KEY);
}

export function getApiErrorMessage(error: unknown) {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<{ detail?: string; message?: string }>;
    const requestUrl = axiosError.config?.url ?? "";
    const isLoginRequest = requestUrl.includes("/auth/login");

    if (axiosError.code === "ECONNABORTED") {
      return "The backend did not respond in time. Check that FastAPI is running.";
    }

    if (!axiosError.response) {
      return "Cannot reach the backend. Check that FastAPI is running and VITE_API_BASE_URL is correct.";
    }

    if (isLoginRequest && axiosError.response.status === 401) {
      return "Incorrect email or password. Please try again.";
    }

    return (
      axiosError.response?.data?.detail ??
      axiosError.response?.data?.message ??
      axiosError.message ??
      "The request failed. Please try again."
    );
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Something went wrong. Please try again.";
}

apiClient.interceptors.request.use((config) => {
  const token = getStoredToken();

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const requestUrl = axios.isAxiosError(error) ? (error.config?.url ?? "") : "";
    const isAuthRequest = requestUrl.includes("/auth/login") || requestUrl.includes("/auth/signup");

    if (axios.isAxiosError(error) && error.response?.status === 401 && !isAuthRequest) {
      clearStoredToken();
      window.dispatchEvent(new Event("auth:logout"));
    }

    return Promise.reject(error);
  },
);
