import axios from 'axios';

const microsoftAxios = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
});

// Add request interceptor to add token to all requests
microsoftAxios.interceptors.request.use(
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

export const microsoftApi = {
  
  // Initiate Microsoft OAuth flow
  initiateLogin: async (): Promise<string> => {
    try {
      const user_id = localStorage.getItem('userId');
      const response = await microsoftAxios.get(`/api/auth/microsoft/login/${user_id}`);
      
      if (response.data?.authUrl) {
        return response.data.authUrl;
      }
      
      throw new Error("Failed to get Microsoft login URL");
    } catch (error) {
      console.error("Error initiating Microsoft login:", error);
      throw error;
    }
  },
  
  // Connect Microsoft account (called after OAuth callback)
  connectAccount: async (code: string): Promise<any> => {
    try {
      console.log("Connecting Microsoft account to backend with auth code...");
      
      const user_id = localStorage.getItem('userId');
      const response = await microsoftAxios.post(`/api/auth/microsoft/connect/${user_id}`, {
        code
      });
      
      console.log("Response from Microsoft connect:", response.data);
      
      // Check for error in the response
      if (response.data?.error || (response.data?.data?.error)) {
        const errorMessage = response.data?.error || response.data?.data?.error;
        console.error("Error in Microsoft connect response:", errorMessage);
        throw new Error(errorMessage || "Failed to connect Microsoft account");
      }
      
      // Store connection information in localStorage
      localStorage.setItem('microsoft_connected', 'true');
      
      // If we have expiry info, store it
      if (response.data?.data?.expiresIn) {
        localStorage.setItem('microsoft_token_expiry', 
          (Date.now() + (response.data.data.expiresIn * 1000)).toString());
      }
      
      // If we have refresh token expiry info, store it
      if (response.data?.data?.refresh_token_expires_in) {
        localStorage.setItem('microsoft_refresh_token_expiry',
          (Date.now() + (response.data.data.refresh_token_expires_in * 1000)).toString());
      }
      
      return response.data;
    } catch (error) {
      console.error("Error connecting Microsoft account:", error);
      if (axios.isAxiosError(error)) {
        throw new Error(error.response?.data?.message || 'Failed to connect Microsoft account');
      }
      throw error; // Re-throw the original error if not an Axios error
    }
  },

  // Call Microsoft Graph API through backend
  callGraphApi: async (endpoint: string, method: string = 'GET', data: any = null): Promise<any> => {
    try {
      const user_id = localStorage.getItem('userId');
      const response = await microsoftAxios.post(`/api/auth/microsoft/graph-api/${endpoint}`, {
        user_id,
        method,
        body: data
      });
      
      return response.data;
    } catch (error) {
      console.error('Error calling Graph API:', error);
      if (axios.isAxiosError(error) && error.response) {
        // Log detailed error information
        console.error('Graph API Error Details:', error.response.data);
        
        // Special handling for token expiration
        if (error.response.status === 401) {
          throw new Error('Microsoft token expired. Please try reconnecting your Microsoft account.');
        }
        
        throw new Error(error.response.data.error?.message || 'Failed to call Microsoft Graph API');
      }
      throw error;
    }
  },
  
  // Create a calendar event
  createCalendarEvent: async (eventDetails: any): Promise<any> => {
    try {
      const user_id = localStorage.getItem('userId');
      const response = await microsoftAxios.post('/api/auth/microsoft/calendar/event', {
        user_id,
        event_details: eventDetails
      });
      
      return response.data;
    } catch (error) {
      console.error('Error creating calendar event:', error);
      throw error;
    }
  },

  // Check token status
  checkTokenStatus: async (): Promise<{ 
    valid: boolean; 
    exists?: boolean;
    isExpired?: boolean;
    expiresIn?: number; 
    expiresAt?: string;
    refresh_token_expires_in?: number;
  }> => {
    try {
      const user_id = localStorage.getItem('userId');
      const response = await microsoftAxios.get(`/api/auth/microsoft/token/status/${user_id}`);
      console.log("Token status response:", response.data);
      
      // Store Microsoft connection status in localStorage based on valid token
      if (response.data.valid) {
        localStorage.setItem('microsoft_connected', 'true');
        // Store expiry info if available
        if (response.data.expiresIn) {
          localStorage.setItem('microsoft_token_expiry', 
            (Date.now() + (response.data.expiresIn * 1000)).toString());
        }
        
        // Store refresh token expiry if available
        if (response.data.refresh_token_expires_in) {
          localStorage.setItem('microsoft_refresh_token_expiry',
            (Date.now() + (response.data.refresh_token_expires_in * 1000)).toString());
        }
      } else if (response.data.exists && response.data.isExpired) {
        // Token exists but is expired - needs refresh
        console.log("Token exists but has expired. Needs refresh.");
        localStorage.setItem('microsoft_token_expired', 'true');
        localStorage.removeItem('microsoft_connected');
      } else {
        // No valid token
        localStorage.removeItem('microsoft_connected');
        localStorage.removeItem('microsoft_token_expiry');
      }
      
      return response.data;
    } catch (error) {
      console.error("Error checking token status:", error);
      localStorage.removeItem('microsoft_connected');
      return { valid: false };
    }
  },
  
  // Disconnect Microsoft account
  disconnectAccount: async (): Promise<boolean> => {
    try {
      const user_id = localStorage.getItem('userId');
      const response = await microsoftAxios.post(`/api/auth/microsoft/disconnect/${user_id}`);
      
      // Clear local storage
      localStorage.removeItem('microsoft_connected');
      localStorage.removeItem('microsoft_token_expiry');
      localStorage.removeItem('microsoft_refresh_token_expiry');
      localStorage.removeItem('microsoft_token_expired');
      
      return response.data?.success || false;
    } catch (error) {
      console.error("Error disconnecting Microsoft account:", error);
      return false;
    }
  }
}; 