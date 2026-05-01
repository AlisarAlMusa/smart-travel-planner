// API helpers for signup and login.

import { apiClient } from "./client";
import type { AuthPayload, AuthResponse } from "../types/auth";

export async function signup(payload: AuthPayload) {
  const response = await apiClient.post<AuthResponse>("/auth/signup", payload);
  return response.data;
}

export async function login(payload: AuthPayload) {
  const response = await apiClient.post<AuthResponse>("/auth/login", payload);
  return response.data;
}
