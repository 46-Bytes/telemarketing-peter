export interface LoginCredentials {
  email: string;
  password: string;
}

export interface SignupData {
  name: string;
  email: string;
  password: string;
  confirmPassword: string;
  businessName: string;
  role?: string;
  // hasEbook?: boolean;
  // ebookPath?: string;
}

export interface User {
  id: string;
  name: string;
  email: string;
  role: string;
  microsoft_token?: string;
  microsoft_refresh_token?: string;
  microsoft_token_expires?: string;
  microsoft_email?: string;
  api_key?: string;
  _id?: string | null | undefined;
  // campaign_user_ids?: string[];
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
} 