import React, { createContext, useContext, useState, useEffect } from 'react';
import { authApi } from '../api/authApi';
import { AuthState, LoginCredentials, SignupData, User } from '../types/auth';

interface AuthContextType extends AuthState {
  login: (credentials: LoginCredentials) => Promise<void>;
  signup: (data: SignupData) => Promise<void>;
  logout: () => Promise<void>;
  updateUser: (userData: any) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [state, setState] = useState<AuthState>({
    user: null,
    token: localStorage.getItem('token'),
    isAuthenticated: false,
    isLoading: true,
    error: null
  });

  useEffect(() => {
    const initializeAuth = async () => {
      try {
        const token = localStorage.getItem('token');
        if (token) {
          try {
            const user:User = await authApi.getCurrentUser();
            localStorage.setItem("userId", user._id || "")
            localStorage.setItem("userName", user.name)
            setState({
              user,
              token,
              isAuthenticated: true,
              isLoading: false,
              error: null
            });
          } catch (error) {
            console.log("Error fetching current user:", error);
            localStorage.removeItem('token');
            localStorage.removeItem('userId');
            localStorage.removeItem('userName');
            setState({
              user: null,
              token: null,
              isAuthenticated: false,
              isLoading: false,
              error: 'Session expired'
            });
          }
        } else {
          setState(prev => ({ ...prev, isLoading: false }));
        }
      } catch (error) {
        console.log("error in auth context", error);
        localStorage.removeItem('token');
        setState(prev => ({ ...prev, isLoading: false, error: 'Session expired' }));
      }
    };

    initializeAuth();
  }, []);

  const login = async (credentials: LoginCredentials) => {
    try {
      setState(prev => ({ ...prev, isLoading: true, error: null }));
      const response = await authApi.login(credentials);
      const user:User = await authApi.getCurrentUser();
      
      // Store user info in localStorage for use in other components
      localStorage.setItem('token', response.access_token);
      localStorage.setItem('userId', user._id || "");
      localStorage.setItem("userName", user.name)
      
      setState({
        user,
        token: response.access_token,
        isAuthenticated: true,
        isLoading: false,
        error: null
      });
    } catch (error) {
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: error instanceof Error ? error.message : 'Login failed'
      }));
      throw error;
    }
  };

  const signup = async (data: SignupData) => {
    try {
      setState(prev => ({ ...prev, isLoading: true, error: null }));
      await authApi.signup(data);
      setState(prev => ({ ...prev, isLoading: false }));
    } catch (error) {
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: error instanceof Error ? error.message : 'Signup failed'
      }));
      throw error;
    }
  };

  const logout = async () => {
    try {
      setState(prev => ({ ...prev, isLoading: true, error: null }));
      await authApi.logout();
      
      // Clear all user info from localStorage
      localStorage.removeItem('token');
      
      setState({
        user: null,
        token: null,
        isAuthenticated: false,
        isLoading: false,
        error: null
      });
    } catch (error) {
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: error instanceof Error ? error.message : 'Logout failed'
      }));
      throw error;
    }
  };

  const updateUser = async (userData: any) => {
    if (!userData) return;
    
    setState(prev => ({
      ...prev,
      user: userData
    }));
  };

  return (
    <AuthContext.Provider value={{ 
      ...state, 
      login, 
      signup, 
      logout,
      updateUser
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}; 