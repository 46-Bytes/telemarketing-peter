import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import ConnectMicrosoft from './ConnectMicrosoft';

interface MicrosoftAuthGuardProps {
  children: React.ReactNode;
}

const MicrosoftAuthGuard: React.FC<MicrosoftAuthGuardProps> = ({ children }) => {
  const { user } = useAuth();
  const [isMicrosoftConnected, setIsMicrosoftConnected] = useState<boolean>(false);
  const [isChecking, setIsChecking] = useState<boolean>(true);

  useEffect(() => {
    // Check if user is connected to Microsoft
    const hasTokenInUser = Boolean(user?.microsoft_token);
    const hasTokenInStorage = localStorage.getItem('microsoft_connected') === 'true';
    
    setIsMicrosoftConnected(hasTokenInUser || hasTokenInStorage);
    setIsChecking(false);
  }, [user]);

  if (isChecking) {
    return (
      <div className="min-h-[400px] flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (!isMicrosoftConnected) {
    return (
      <div className="p-8 bg-white rounded-xl shadow-lg max-w-2xl mx-auto my-8">
        <div className="text-center mb-8">
          <h2 className="text-2xl font-bold text-gray-800 mb-2">Microsoft Connection Required</h2>
          <p className="text-gray-600">
            Please connect your Microsoft account to access this feature. This allows us to manage your calendar and schedule appointments.
          </p>
        </div>
        
        <ConnectMicrosoft 
          onSuccess={() => setIsMicrosoftConnected(true)} 
        />
      </div>
    );
  }

  return <>{children}</>;
};

export default MicrosoftAuthGuard;
