import { useState, useEffect, useCallback } from 'react';
import { useMsal } from '@azure/msal-react';
import { useMicrosoftGraph } from '../hooks/useMicrosoftGraph';
import Spinner from './Spinner';
import { format } from 'date-fns';

interface ConnectMicrosoftProps {
  onSuccess?: () => void;  // Add onSuccess callback prop
  compact?: boolean; // Add compact prop to support minimized display
}

const ConnectMicrosoft: React.FC<ConnectMicrosoftProps> = ({ onSuccess, compact = false }) => {
  const { instance } = useMsal();
  const { 
    connectMicrosoftAccount, 
    isLoading, 
    error, 
    clearError, 
    ensureFreshToken, 
    isTokenValid, 
    lastTokenRefresh,
    isTokenRefreshing,
    checkAndRefreshToken
  }:any = useMicrosoftGraph();
  
  const [connecting, setConnecting] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'disconnected' | 'connected' | 'expired'>('disconnected');
  const [connectionError, setConnectionError] = useState<string | null>(null);

  // Check connection status on component mount
  useEffect(() => {
    const checkTokenStatus = async () => {
      try {
        console.log("Checking Microsoft token status...");
        const isValid = await isTokenValid();
        
        if (isValid) {
          console.log("Microsoft token is valid");
          setConnectionStatus('connected');
          setConnectionError(null);
          if (onSuccess) onSuccess();
        } else {
          // Check if we have a token that might be expired
          const hasToken = localStorage.getItem('microsoft_token_expired') === 'true';
          console.log("Microsoft token status:", hasToken ? "expired" : "disconnected");
          setConnectionStatus(hasToken ? 'expired' : 'disconnected');
        }
      } catch (err) {
        console.error("Error checking token status:", err);
        setConnectionError("Failed to check token status");
        setConnectionStatus('disconnected');
      }
    };
    
    checkTokenStatus();
  }, [isTokenValid, onSuccess]);

  // Ensure we're properly detecting MSAL accounts
  useEffect(() => {
    const checkMsalAccounts = () => {
      const accounts = instance.getAllAccounts();
      console.log("Accounts:", accounts);
      console.log(`MSAL accounts found: ${accounts.length}`);
      
      if (accounts.length > 0) {
        console.log("Account details:", {
          username: accounts[0].username,
          name: accounts[0].name,
          homeAccountId: accounts[0].homeAccountId,
        });
      }
    };
    
    checkMsalAccounts();
  }, [instance]);

  const handleConnect = useCallback(async () => {
    try {
      setConnecting(true);
      setConnectionError(null);
      clearError();
      
      console.log("Starting Microsoft connection process...");
      console.log("Current connection status:", connectionStatus);
      
      // If token is expired, try refreshing first
      if (connectionStatus === 'expired') {
        console.log("Attempting to refresh expired token");
        try {
          const token = await ensureFreshToken();
          if (token) {
            console.log("Token refreshed successfully");
            setConnectionStatus('connected');
            if (onSuccess) onSuccess();
            return;
          } else {
            console.log("Token refresh returned null, continuing to new connection");
          }
        } catch (refreshError) {
          console.error("Token refresh failed:", refreshError);
          setConnectionError("Failed to refresh token. Trying new connection...");
          // Continue to new connection attempt
        }
      }
      
      // Connect fresh if needed
      console.log("Initiating new Microsoft connection");
      await connectMicrosoftAccount();
      
      console.log("Microsoft account connected successfully");
      setConnectionStatus('connected');
      setConnectionError(null);
      if (onSuccess) onSuccess();
    } catch (err) {
      console.error("Failed to connect Microsoft account:", err);
      const errorMessage = err instanceof Error ? err.message : "Unknown error connecting to Microsoft";
      setConnectionError(errorMessage);
    } finally {
      setConnecting(false);
    }
  }, [connectMicrosoftAccount, clearError, onSuccess, connectionStatus, ensureFreshToken, instance]);

  const handleRefreshToken = async () => {
    try {
      setConnecting(true);
      setConnectionError(null);
      clearError();
      
      console.log("Manually refreshing Microsoft token...");
      await checkAndRefreshToken();
      
      // Recheck the token status after refresh attempt
      const isValid = await isTokenValid();
      if (isValid) {
        setConnectionStatus('connected');
        setConnectionError(null);
        if (onSuccess) onSuccess();
      } else {
        setConnectionError("Token refresh failed. Please try reconnecting your account.");
      }
    } catch (err) {
      console.error("Failed to refresh Microsoft token:", err);
      const errorMessage = err instanceof Error ? err.message : "Unknown error refreshing Microsoft token";
      setConnectionError(errorMessage);
    } finally {
      setConnecting(false);
    }
  };

  // Compact version for when already connected
  if (compact && connectionStatus === 'connected') {
    return (
      <div className="flex items-center">
        <span className="text-sm text-green-700 flex items-center">
          <svg className="h-4 w-4 text-green-500 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
          </svg>
          Connected
          {lastTokenRefresh && (
            <span className="ml-1 text-xs text-gray-500">
              (Refreshed: {format(lastTokenRefresh, 'h:mm a')})
            </span>
          )}
        </span>
        <div className="ml-2 flex">
          <button
            onClick={handleRefreshToken}
            disabled={isLoading || connecting || isTokenRefreshing}
            className="px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded hover:bg-blue-200 disabled:opacity-50 mr-1"
          >
            {isTokenRefreshing ? 'Refreshing...' : 'Refresh'}
          </button>
          <button
            onClick={handleConnect}
            disabled={isLoading || connecting || isTokenRefreshing}
            className="px-2 py-1 text-xs bg-green-100 text-green-700 rounded hover:bg-green-200 disabled:opacity-50"
          >
            {(isLoading || connecting) ? 'Connecting...' : 'Reconnect'}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 bg-white rounded-lg shadow-md">
      {!compact && <h2 className="text-xl font-semibold mb-4">Microsoft Account Connection</h2>}
      
      {connectionStatus === 'connected' ? (
        <div className="mb-4 p-3 bg-green-100 text-green-800 rounded">
          <span className="font-medium">✓</span> Your Microsoft account is connected.
          {lastTokenRefresh && (
            <div className="text-xs mt-1">
              Last token refresh: {format(lastTokenRefresh, 'PPpp')}
            </div>
          )}
        </div>
      ) : connectionStatus === 'expired' ? (
        <div className="mb-4 p-3 bg-yellow-100 text-yellow-800 rounded">
          <span className="font-medium">⚠</span> Your Microsoft token has expired. Please reconnect.
        </div>
      ) : (
        <div className="mb-4 p-3 bg-blue-100 text-blue-800 rounded">
          Connect your Microsoft account to enable calendar scheduling.
        </div>
      )}
      
      {(error || connectionError) && (
        <div className="mb-4 p-3 bg-red-100 text-red-800 rounded">
          <span className="font-medium">Error:</span> {error || connectionError}
        </div>
      )}
      
      <div className="flex space-x-2">
        <button
          onClick={handleConnect}
          disabled={isLoading || connecting || isTokenRefreshing}
          className="flex items-center justify-center px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-blue-400"
        >
          {(isLoading || connecting) ? (
            <>
              <Spinner size="sm" color="text-white" />
              <span className="ml-2">Connecting...</span>
            </>
          ) : connectionStatus === 'connected' ? (
            'Reconnect Microsoft Account'
          ) : connectionStatus === 'expired' ? (
            'Refresh Connection'
          ) : (
            'Connect Microsoft Account'
          )}
        </button>
        
        {connectionStatus === 'connected' && (
          <button
            onClick={handleRefreshToken}
            disabled={isLoading || connecting || isTokenRefreshing}
            className="flex items-center justify-center px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:bg-green-400"
          >
            {isTokenRefreshing ? (
              <>
                <Spinner size="sm" color="text-white" />
                <span className="ml-2">Refreshing Token...</span>
              </>
            ) : (
              'Refresh Token'
            )}
          </button>
        )}
      </div>
    </div>
  );
};

export default ConnectMicrosoft; 