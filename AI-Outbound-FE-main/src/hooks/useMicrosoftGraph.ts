import { useState, useEffect, useCallback, useRef } from "react";
import { microsoftApi } from "../api/microsoftApi";

// Add type definitions for the API responses
interface TokenStatusResponse {
  valid: boolean;
  exists?: boolean;
  isExpired?: boolean;
  expiresIn?: number;
  expiresAt?: string;
  refresh_token_expires_in?: number;
}

export function useMicrosoftGraph() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isTokenRefreshing, _] = useState(false);
  const [lastTokenRefresh, setLastTokenRefresh] = useState<Date | null>(null);
  
  // Add a cooldown ref to prevent too frequent token checks
  const lastCheckTimeRef = useRef<number>(0);
  // Cooldown period in milliseconds (5 seconds)
  const TOKEN_CHECK_COOLDOWN = 5000;

  // Function to check if token needs refreshing
  const checkAndRefreshToken = useCallback(async () => {
    try {
      // Skip if already refreshing
      if (isTokenRefreshing) {
        return;
      }
      
      // Check if we've checked recently (within cooldown period)
      const currentTime = Date.now();
      if (currentTime - lastCheckTimeRef.current < TOKEN_CHECK_COOLDOWN) {
        console.log("Token check cooldown active, skipping check");
        return;
      }
      
      // Update last check time
      lastCheckTimeRef.current = currentTime;
      
      console.log("Checking Microsoft token status...");
      
      // Check if Microsoft connection exists
      const isConnected = localStorage.getItem('microsoft_connected') === 'true';
      if (!isConnected) {
        console.log("No Microsoft connection established. Skipping token refresh.");
        return;
      }
      
      // Check token status with backend
      const tokenStatus = await microsoftApi.checkTokenStatus();
      
      if (tokenStatus.valid) {
        console.log(`Microsoft token valid for another ${Math.floor((tokenStatus.expiresIn || 0) / 60)} minutes`);
      } else {
        console.log("Token is not valid according to backend check.");
        // The backend will handle token refresh automatically on next API call
      }
    } catch (error) {
      console.error("Error in token refresh check:", error);
    }
  }, [isTokenRefreshing]);

  // Set up token refresh on a scheduled basis
  useEffect(() => {
    // Immediately check token status on mount, but with a slight delay to avoid too many simultaneous requests
    const initialCheckTimeout = setTimeout(() => {
      checkAndRefreshToken();
    }, 2000);
    
    // Set up periodic token refresh checks
    // Run more frequently (every 30 minutes) to ensure we don't miss refresh windows
    const refreshInterval = setInterval(() => {
      console.log("Running scheduled Microsoft token refresh check...");
      checkAndRefreshToken();
    }, 30 * 60 * 1000); // 30 minutes in milliseconds
    
    // Clean up interval and timeout on unmount
    return () => {
      console.log("Clearing Microsoft token refresh interval");
      clearInterval(refreshInterval);
      clearTimeout(initialCheckTimeout);
    };
  }, [checkAndRefreshToken]);

  // Add a window focus event listener to check tokens when user returns to the app
  useEffect(() => {
    const handleFocus = () => {
      console.log("Window focused, checking token status...");
      checkAndRefreshToken();
    };
    
    window.addEventListener('focus', handleFocus);
    
    return () => {
      window.removeEventListener('focus', handleFocus);
    };
  }, [checkAndRefreshToken]);

  const callGraphApi = async (endpoint: string, method: string = 'GET', data: any = null) => {
    setIsLoading(true);
    setError(null);
    
    try {
      // Backend will handle token refresh automatically
      const result = await microsoftApi.callGraphApi(endpoint, method, data);
      setIsLoading(false);
      console.log("Graph API result:", result);
      return result;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unknown error occurred');
      setIsLoading(false);
      throw err;
    }
  };

  const createCalendarEvent = async (eventDetails: any) => {
    setIsLoading(true);
    setError(null);
    
    try {
      // Backend will handle token refresh automatically
      const result = await microsoftApi.createCalendarEvent(eventDetails);
      setIsLoading(false);
      console.log("Calendar event created:", result);
      return result;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create calendar event');
      setIsLoading(false);
      throw err;
    }
  };

  const connectMicrosoftAccount = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      // Clear any previous connection status
      localStorage.removeItem('microsoft_connected');
      localStorage.removeItem('microsoft_token_expiry');
      localStorage.removeItem('microsoft_refresh_token_expiry');
      localStorage.removeItem('microsoft_token_expired');
      
      // Get the login URL from the backend
      const authUrl = await microsoftApi.initiateLogin();
      
      // Open the Microsoft login page in a new window
      const loginWindow = window.open(authUrl, '_blank', 'width=800,height=600');
      
      // Set up a message listener for the OAuth callback
      const messageHandler = async (event: MessageEvent) => {
        // Verify origin for security
        if (event.origin !== window.location.origin) return;
        
        // Check if this is our OAuth callback message
        if (event.data && event.data.type === 'MICROSOFT_AUTH_CALLBACK' && event.data.code) {
          // Remove the event listener
          window.removeEventListener('message', messageHandler);
          
          // Close the login window
          if (loginWindow) loginWindow.close();
          
          try {
            // Connect the account using the authorization code
            const response = await microsoftApi.connectAccount(event.data.code);
            
            setIsLoading(false);
            setLastTokenRefresh(new Date());
            return response;
          } catch (error) {
            console.error("Error completing Microsoft connection:", error);
            setError(error instanceof Error ? error.message : 'Failed to connect Microsoft account');
            setIsLoading(false);
            throw error;
          }
        }
      };
      
      // Add the message listener
      window.addEventListener('message', messageHandler);
      
      // Start polling for authentication status
      let pollingCount = 0;
      const maxPolls = 20; // Poll for up to 20 times (200 seconds total)
      const pollingInterval = 10000; // 10 seconds
      
      const pollForAuthentication = async () => {
        if (pollingCount >= maxPolls) {
          console.log("Max polling attempts reached, stopping polling");
          setIsLoading(false);
          setError("Authentication timed out. Please try again.");
          return;
        }
        
        pollingCount++;
        console.log(`Polling for Microsoft authentication status (${pollingCount}/${maxPolls})...`);
        
        try {
          // Check if the user has been authenticated
          const statusResponse = await microsoftApi.checkTokenStatus() as TokenStatusResponse;
          
          if (statusResponse.valid && statusResponse.exists) {
            console.log("Authentication successful via polling!");
            setIsLoading(false);
            setLastTokenRefresh(new Date());
            localStorage.setItem('microsoft_connected', 'true');
            return;
          } else {
            // If not authenticated yet, continue polling
            setTimeout(pollForAuthentication, pollingInterval);
          }
        } catch (error) {
          console.error("Error polling for authentication status:", error);
          // Continue polling even if there's an error
          setTimeout(pollForAuthentication, pollingInterval);
        }
      };
      
      // Start the polling process
      setTimeout(pollForAuthentication, pollingInterval);
      
      // Return a cleanup function
      return () => {
        window.removeEventListener('message', messageHandler);
        pollingCount = maxPolls; // This will stop any active polling
      };
    } catch (err) {
      console.error("Microsoft connection error:", err);
      // Clear connection status on error
      localStorage.removeItem('microsoft_connected');
      setError(err instanceof Error ? err.message : 'Failed to connect Microsoft account');
      setIsLoading(false);
      throw err;
    }
  };

  const disconnectMicrosoftAccount = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const result = await microsoftApi.disconnectAccount();
      setIsLoading(false);
      return result;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to disconnect Microsoft account');
      setIsLoading(false);
      throw err;
    }
  };

  const isTokenValid = async (): Promise<boolean> => {
    try {
      const statusResponse = await microsoftApi.checkTokenStatus() as TokenStatusResponse;
      console.log("Token status check:", statusResponse);
      return statusResponse.valid;
    } catch (error) {
      console.error("Error checking token status:", error);
      return false;
    }
  };

  return {
    callGraphApi,
    createCalendarEvent,
    connectMicrosoftAccount,
    disconnectMicrosoftAccount,
    isTokenValid,
    isLoading,
    error,
    clearError: () => setError(null),
    lastTokenRefresh,
    isTokenRefreshing,
    checkAndRefreshToken
  };
} 