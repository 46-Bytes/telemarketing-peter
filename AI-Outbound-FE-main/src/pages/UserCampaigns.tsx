import React, { useState, useEffect, useRef } from 'react';
import { campaignApi } from '../api/api';
import { Campaign } from '../types/campaign';
import EnhancedCampaignCard from '../components/EnhancedCampaignCard';
// import { useAuth } from '../contexts/AuthContext';
import { useMicrosoftGraph } from '../hooks/useMicrosoftGraph';
// import MicrosoftAuthRequired from '../components/MicrosoftAuthRequired';

const UserCampaigns: React.FC = () => {
  const { checkAndRefreshToken } = useMicrosoftGraph();
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const dataFetchedRef = useRef<boolean>(false);

  useEffect(() => {
    // Prevent multiple fetch requests
    if (dataFetchedRef.current) return;

    const fetchUserCampaigns = async () => {
      try {
        setIsLoading(true);
        setError(null);
        
        // Ensure Microsoft token is valid before fetching data
        try {
          await checkAndRefreshToken();
        } catch (tokenError) {
          console.error("Microsoft token refresh failed:", tokenError);
          setError("Microsoft authentication error. Please reconnect your account.");
          setIsLoading(false);
          return;
        }
        
        // Fetch campaigns for the current user
        const userCampaigns = await campaignApi.getUserCampaigns();
        setCampaigns(userCampaigns);
        // Mark that data has been fetched
        dataFetchedRef.current = true;
      } catch (error) {
        console.error("Failed to fetch user campaigns:", error);
        setError(error instanceof Error ? error.message : "Failed to fetch campaigns");
      } finally {
        setIsLoading(false);
      }
    };

    fetchUserCampaigns();
    // Remove checkAndRefreshToken from dependencies to prevent continuous refreshing
  }, []);

  // Content to display inside the MicrosoftAuthRequired wrapper
  const campaignsContent = () => {
    if (isLoading) {
      return (
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
        </div>
      );
    }

    if (error) {
      return (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4" role="alert">
          <strong className="font-bold">Error: </strong>
          <span className="block sm:inline">{error}</span>
        </div>
      );
    }

    return (
      <>
        {campaigns.length === 0 ? (
          <div className="bg-blue-50 border-l-4 border-blue-500 text-blue-700 p-4 mb-4" role="alert">
            <p>You don't have any campaigns yet.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {campaigns.map(campaign => (
              <EnhancedCampaignCard 
                key={campaign.id} 
                campaign={campaign} 
              />
            ))}
          </div>
        )}
      </>
    );
  };

  return (
    <>
    {campaignsContent()}
    </>
    // <MicrosoftAuthRequired 
    //   pageTitle="My Campaigns asd"
    //   pageDescription="View and manage your campaigns"
    // >
    // </MicrosoftAuthRequired>
  );
};

export default UserCampaigns; 