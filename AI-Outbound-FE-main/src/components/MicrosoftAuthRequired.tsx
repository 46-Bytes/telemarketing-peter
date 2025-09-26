import React, { useState, useEffect, ReactNode, useRef } from 'react';
import { useAuth } from '../contexts/AuthContext';
import ConnectMicrosoft from './ConnectMicrosoft';
import { useMicrosoftGraph } from '../hooks/useMicrosoftGraph';

interface MicrosoftAuthRequiredProps {
  children: ReactNode;
  pageTitle: string;
  pageDescription?: string;
}

/**
 * A wrapper component that requires Microsoft authentication.
 * If the user is not connected to Microsoft, shows the connection UI.
 * Otherwise, renders the children components.
 */
const MicrosoftAuthRequired: React.FC<MicrosoftAuthRequiredProps> = ({ 
  children, 
  pageTitle,
  pageDescription 
}) => {
  const { user } = useAuth();
  const { checkAndRefreshToken } = useMicrosoftGraph();
  const [isLoading, setIsLoading] = useState(true);
  const [tokenError, setTokenError] = useState<string | null>(null);
  
  // Microsoft connection state
  const [isMicrosoftConnected, setIsMicrosoftConnected] = useState<boolean>(
    Boolean(user?.microsoft_token) || localStorage.getItem('microsoft_connected') === 'true'
  );
  
  // Track if the token has already been checked to prevent continuous refreshing
  const tokenCheckedRef = useRef<boolean>(false);

  // Update Microsoft connection status when user changes
  useEffect(() => {
    const hasTokenInUser = Boolean(user?.microsoft_token);
    const hasTokenInStorage = localStorage.getItem('microsoft_connected') === 'true';
    
    console.log("Microsoft connection check:", {
      hasTokenInUser,
      hasTokenInStorage,
      user: user
    });
    
    setIsMicrosoftConnected(hasTokenInUser || hasTokenInStorage);
  }, [user]);

  // Check token validity on mount
  useEffect(() => {
    // Skip if already checked
    if (tokenCheckedRef.current) {
      setIsLoading(false);
      return;
    }
    
    const validateToken = async () => {
      if (!isMicrosoftConnected) {
        setIsLoading(false);
        return;
      }
      
      try {
        await checkAndRefreshToken();
        setTokenError(null);
      } catch (error) {
        console.error("Microsoft token validation error:", error);
        setTokenError("Microsoft authentication error. Please reconnect your account.");
      } finally {
        setIsLoading(false);
        // Mark that token has been checked
        tokenCheckedRef.current = true;
      }
    };
    
    validateToken();
  }, [isMicrosoftConnected]);

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  // If Microsoft is not connected, show the connection UI
  if (!isMicrosoftConnected) {
    return (
      <div className="w-full mx-auto p-6">
        <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
          <h1 className="text-2xl font-bold text-gray-800 mb-6">{pageTitle}</h1>
          
          {pageDescription && (
            <p className="text-gray-600 mb-6">{pageDescription}</p>
          )}
          
          <div className="mb-6">
            <div className="flex justify-between items-center">
              <h2 className="text-lg font-semibold text-gray-700">Microsoft Account Connection Required</h2>
            </div>
            
            <div className="bg-gray-50 p-6 rounded-lg border border-gray-200 mt-2">
              <p className="mb-4 text-gray-600">
                Please connect your Microsoft account to access this feature.
              </p>
              <ConnectMicrosoft onSuccess={() => setIsMicrosoftConnected(true)} />
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Show token error if present
  if (tokenError) {
    return (
      <div className="w-full mx-auto p-6">
        <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
          <h1 className="text-2xl font-bold text-gray-800 mb-6">{pageTitle}</h1>
          
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4" role="alert">
            <strong className="font-bold">Error: </strong>
            <span className="block sm:inline">{tokenError}</span>
          </div>
          
          <div className="mt-4">
            <ConnectMicrosoft onSuccess={() => {
              setIsMicrosoftConnected(true);
              setTokenError(null);
            }} />
          </div>
        </div>
      </div>
    );
  }

  // Render the Microsoft connection status indicator and children
  return (
    <div className="w-full mx-auto p-6">
      <div className="rounded-lg mb-6">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-800">{pageTitle}</h1>
            {pageDescription && (
              <p className="text-gray-600 mt-1">{pageDescription}</p>
            )}
          </div>
          
          {/* Microsoft connection status indicator */}
          <div className="mt-4 md:mt-0">
            <div className="bg-green-50 rounded-lg border border-green-200 p-2">
              <div className="flex items-center">
                <span className="text-xs text-green-600 font-medium px-2 py-1 bg-green-100 rounded-full mr-2">Microsoft Connected</span>
                <ConnectMicrosoft 
                  onSuccess={() => setIsMicrosoftConnected(true)} 
                  compact={true} 
                />
              </div>
            </div>
          </div>
        </div>
        
        {/* Render the children */}
        {children}
      </div>
    </div>
  );
};

export default MicrosoftAuthRequired; 