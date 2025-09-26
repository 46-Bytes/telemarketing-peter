import axios from 'axios';
import { LoginCredentials, SignupData, AuthResponse, User } from '../types/auth';

const authAxios = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
});

// Add request interceptor to add token to all requests
authAxios.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

export const authApi = {
  login: async (credentials: LoginCredentials): Promise<AuthResponse> => {
    try {
      const response = await authAxios.post('/auth/login', credentials);
      if (response.data.access_token) {
        localStorage.setItem('token', response.data.access_token);
      }
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        throw new Error(error.response?.data?.message || 'Login failed');
      }
      throw new Error('Login failed');
    }
  },

  signup: async (data: SignupData): Promise<{ message: string }> => {
    try {
      const response = await authAxios.post('/auth/signup', data);
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        throw new Error(error.response?.data?.message || 'Signup failed');
      }
      throw new Error('Signup failed');
    }
  },

  getCurrentUser: async (): Promise<User> => {
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('No token found');
      }
      const response = await authAxios.get('/auth/me');
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        throw new Error(error.response?.data?.message || 'Failed to get user');
      }
      throw new Error('Failed to get user');
    }
  },

  logout: async (): Promise<void> => {
    localStorage.removeItem('token');
    localStorage.removeItem('userName');
    localStorage.removeItem('userId');

  },

  getBrokers: async (): Promise<User[]> => {
    try {
      const response = await authAxios.get('/auth/brokers');
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        throw new Error(error.response?.data?.message || 'Failed to fetch brokers');
      }
      throw new Error('Failed to fetch brokers');
    }
  },
}; 