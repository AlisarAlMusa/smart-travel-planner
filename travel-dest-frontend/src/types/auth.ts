// TypeScript types for authentication API requests and responses.

export type AuthPayload = {
  email: string;
  password: string;
};

export type User = {
  id?: string;
  email: string;
  created_at?: string;
};

export type AuthResponse = {
  access_token: string;
  token_type?: string;
  user?: User;
};
