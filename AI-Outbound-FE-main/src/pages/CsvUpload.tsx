import React, { useState, useEffect, useRef } from 'react';
import FileUpload from '../components/FileUpload';
import Papa from 'papaparse';
import { userApi, campaignApi } from '../api/api';
import { useAuth } from '../contexts/AuthContext';
import ConnectMicrosoft from '../components/ConnectMicrosoft';
import { Navigate } from 'react-router-dom';
import { Campaign } from '../types/campaign';

interface CsvData {
    name?: string;
    phoneNumber: string;
    businessName: string;
}

const CsvUpload: React.FC = () => {
  const { user, isAuthenticated, isLoading } = useAuth();
  const [csvData, setCsvData] = useState<CsvData[]>([]);
  const [uploadedFileName, setUploadedFileName] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isScheduling, setIsScheduling] = useState(false);
  const [scheduleStatus, setScheduleStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [isMicrosoftConnected, setIsMicrosoftConnected] = useState<boolean>(
    Boolean(user?.microsoft_token) || localStorage.getItem('microsoft_connected') === 'true'
  );
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [selectedCampaignId, setSelectedCampaignId] = useState<string>('');
  const [isLoadingCampaigns, setIsLoadingCampaigns] = useState<boolean>(false);
  
  // Add a ref to track if campaigns have already been fetched
  const campaignsLoadedRef = useRef<boolean>(false);

  // const { ensureFreshToken } = useMicrosoftGraph();

  // Debug campaigns state
  useEffect(() => {
    console.log("Campaigns state updated:", { 
      campaignsCount: campaigns.length,
      selectedCampaignId,
      isLoadingCampaigns 
    });
  }, [campaigns, selectedCampaignId, isLoadingCampaigns]);

  // Fetch campaigns on component mount
  useEffect(() => {
    // Skip if campaigns already loaded
    if (campaignsLoadedRef.current) return;
    
    const fetchCampaigns = async () => {
      setIsLoadingCampaigns(true);
      try {
        console.log("Fetching campaign users...");
        const campaignData = await campaignApi.getCampaignUsers();
        console.log("Campaign users data received:", campaignData);
        
        if (Array.isArray(campaignData) && campaignData.length > 0) {
          console.log("Setting campaigns state with data:", campaignData);
          // Ensure each campaign has a campaignName property
          const validCampaigns = campaignData.filter(c => c && typeof c === 'object' && c.campaignName);
          console.log("Valid campaigns:", validCampaigns);
          
          setCampaigns(validCampaigns);
          
          if (validCampaigns.length > 0 && validCampaigns[0].id) {
            setSelectedCampaignId(validCampaigns[0].id || '');
          }
          
          // Mark campaigns as loaded
          campaignsLoadedRef.current = true;
        } else {
          console.warn("Campaign data is empty or not an array:", campaignData);
          // Create a default campaign group if none found
          console.log("Creating default campaign group...");
          try {
            const defaultCampaign = await campaignApi.createCampaign({
              campaignName: "Default Campaign Group",
              users: [],
              campaignDate: new Date().toISOString().split('T')[0]
            });
            console.log("Default campaign created:", defaultCampaign);
            
            // Fetch campaigns again
            const refreshedCampaigns = await campaignApi.getCampaignUsers();
            if (Array.isArray(refreshedCampaigns) && refreshedCampaigns.length > 0) {
              setCampaigns(refreshedCampaigns);
              setSelectedCampaignId(refreshedCampaigns[0].id || '');
            } else {
              // If still no campaigns, set a mock campaign for UI purposes
              const mockCampaign = {
                id: "default",
                campaignName: "Default Campaign Group",
                users: [],
                campaignDate: new Date().toISOString().split('T')[0],
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString()
              };
              setCampaigns([mockCampaign]);
              setSelectedCampaignId(mockCampaign.id);
            }
            
            // Mark campaigns as loaded even in this case
            campaignsLoadedRef.current = true;
          } catch (createError) {
            console.error("Failed to create default campaign:", createError);
            setCampaigns([]);
          }
        }
      } catch (error) {
        console.error('Error fetching campaign users:', error);
        setCampaigns([]);
      } finally {
        setIsLoadingCampaigns(false);
      }
    };

    fetchCampaigns();
  }, []);

  // Redirect to login if not authenticated
  if (!isLoading && !isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  const handleFileUpload = async (file: File) => {
    // Reset previous status
    setUploadStatus('idle');
    setErrorMessage(null);
    setIsUploading(true);
    setUploadedFileName(file.name);

    Papa.parse(file, {
      header: true,
      complete: async (results) => {
        try {
          const parsedData = results.data as CsvData[];
          setCsvData(parsedData);
    
          setIsUploading(false);
          setUploadStatus('success');
        } catch (error) {
          console.error('Error uploading users:', error);
          setIsUploading(false);
          setUploadStatus('error');
          setErrorMessage(error instanceof Error ? error.message : 'Failed to upload users');
        }
      },
      error: (error) => {
        console.error('Error parsing CSV:', error);
        setIsUploading(false);
        setUploadStatus('error');
        setErrorMessage('Error parsing CSV file');
      }
    });
  };

  const handleNewUpload = () => {
    // Reset all states when a new file is selected
    setCsvData([]);
    setUploadStatus('idle');
    setUploadedFileName(null);
    setErrorMessage(null);
    setIsUploading(false);
  };

  // Helper function to get campaign name from ID
  const getCampaignNameFromId = (id: string): string => {
    const campaign = campaigns.find(c => c.id === id);
    return campaign ? campaign.campaignName : '';
  };

  const handleScheduleCall = async () => {
    if (csvData.length === 0) return;

    setIsScheduling(true);
    setScheduleStatus('idle');
    
    try {
      // Ensure we have a fresh token before making API calls
      // await ensureFreshToken();
      
      // Pass the current user's name from AuthContext
      const ownerName = user?.name || 'Unknown User';
      
      // Get campaign name from ID
      const campaignName = getCampaignNameFromId(selectedCampaignId);
      
      // Add campaign data to each record
      const dataWithCampaign = csvData.map(record => ({
        ...record,
        campaignId: selectedCampaignId,
        campaignName: campaignName
      }));
      
      console.log("Uploading data with campaign:", {
        selectedCampaignId,
        campaignName,
        sampleRecord: dataWithCampaign[0]
      });
      
      // Pass both the selected campaign ID and name
      await userApi.uploadUsers(dataWithCampaign, "", campaignName, ownerName, selectedCampaignId);
      setScheduleStatus('success');
    } catch (error) {
      console.error('Error scheduling calls:', error);
      setScheduleStatus('error');
      setErrorMessage(error instanceof Error ? error.message : 'Failed to schedule calls');
    } finally {
      setIsScheduling(false);
    }
  };

  // // Function to handle Microsoft reconnection
  // const handleMicrosoftReconnect = () => {
  //   // Temporarily set to disconnected to show the full connect UI
  //   setIsMicrosoftConnected(false);
  //   // The ConnectMicrosoft component will set it back to true after reconnection
  // };

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

  // Standalone campaign dropdown component
  const CampaignGroupDropdown = () => {
    if (isLoadingCampaigns) {
      return (
        <div className="flex items-center">
          <div className="animate-spin h-4 w-4 mr-2 border-b-2 border-gray-500"></div>
          <span className="text-sm text-gray-500">Loading campaign groups...</span>
        </div>
      );
    }

    if (!campaigns || campaigns.length === 0) {
      return (
        <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-md text-sm text-yellow-700">
          No campaign groups found. Please create a campaign group first.
        </div>
      );
    }

    return (
      <select
        id="campaign-select"
        value={selectedCampaignId}
        onChange={(e) => setSelectedCampaignId(e.target.value)}
        className="mt-1 block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
      >
        {campaigns.map((campaign) => (
          <option key={campaign.id || campaign.campaignName} value={campaign.id || ''}>
            {campaign.campaignName}
          </option>
        ))}
      </select>
    );
  };

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="w-full mx-auto p-4"> 
      <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
        <h1 className="text-2xl font-bold text-gray-800 mb-6">CSV Upload</h1>
        
        {/* Microsoft Connection Section - Minimized when connected */}
        <div className={`mb-6 ${isMicrosoftConnected ? 'bg-green-50 rounded-lg border border-green-200 p-3' : ''}`}>
          <div className="flex justify-between items-center">
            <h2 className="text-lg font-semibold text-gray-700">Microsoft Account Connection</h2>
            {isMicrosoftConnected && (
              <span className="text-xs text-green-600 font-medium px-2 py-1 bg-green-100 rounded-full">Connected</span>
            )}
          </div>
          
          {isMicrosoftConnected ? (
            // Minimized version when connected
            <div className="mt-2">
              <ConnectMicrosoft 
                onSuccess={() => setIsMicrosoftConnected(true)} 
                compact={true} 
              />
            </div>
          ) : (
            // Full version when not connected
            <div className="bg-gray-50 p-6 rounded-lg border border-gray-200 mt-2">
              <p className="mb-4 text-gray-600">
                Please connect your Microsoft account to upload CSV files.
              </p>
              <ConnectMicrosoft onSuccess={() => setIsMicrosoftConnected(true)} />
            </div>
          )}
        </div>
        
        {/* CSV Upload Section - Only enabled when Microsoft is connected */}
        <div>
          <h2 className="text-lg font-semibold text-gray-700 mb-4">Upload Contact List</h2>
          <div className="bg-gray-50 p-6 rounded-lg border border-gray-200">
            {isMicrosoftConnected ? (
              <FileUpload 
                onFileSelect={handleFileUpload}
                onNewUpload={handleNewUpload}
              />
            ) : (
              <div className="p-4 bg-yellow-50 rounded-lg border border-yellow-200">
                <p className="text-sm text-yellow-700">
                  Please connect your Microsoft account first to upload CSV files.
                </p>
              </div>
            )}
            
            {isUploading && (
              <div className="flex items-center justify-center mt-4">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
                <span className="ml-2 text-gray-600">Processing file...</span>
              </div>
            )}

            {uploadStatus === 'success' && (
              <div className="mt-4 p-4 bg-green-50 rounded-lg border border-green-200">
                <div className="flex items-center">
                  <svg className="h-5 w-5 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                  </svg>
                  <p className="ml-2 text-sm text-green-700">
                    File "{uploadedFileName}" uploaded successfully!
                  </p>
                </div>
              </div>
            )}

            {uploadStatus === 'error' && (
              <div className="mt-4 p-4 bg-red-50 rounded-lg border border-red-200">
                <div className="flex items-center">
                  <svg className="h-5 w-5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                  <p className="ml-2 text-sm text-red-700">
                    {errorMessage || 'Error uploading file. Please try again.'}
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Upload Data Section - Only visible after CSV upload */}
        {csvData.length > 0 && (
          <div className="mt-6 border-t pt-6">
            <h3 className="text-lg font-semibold text-gray-700 mb-4">Schedule Calls</h3>
            <div className="bg-gray-50 p-6 rounded-lg border border-gray-200">
              {/* Campaign Selection Dropdown */}
              <div className="mb-4">
                <label htmlFor="campaign-select" className="block text-sm font-medium text-gray-700 mb-1">
                  Select Campaign Group
                </label>
                <CampaignGroupDropdown />
              </div>
              
              <div className="flex items-center gap-4">
                <button
                  onClick={handleScheduleCall}
                  disabled={csvData.length === 0 || isScheduling || campaigns.length === 0}
                  className="px-4 py-2 bg-gradient-to-r from-indigo-500 to-blue-600 text-white rounded-lg 
                    hover:shadow-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isScheduling ? 'Processing...' : 'Upload Data'}
                </button>
              </div>
              
              {scheduleStatus === 'success' && (
                <div className="mt-4 p-4 bg-green-50 rounded-lg border border-green-200">
                  <div className="flex items-center">
                    <svg className="h-5 w-5 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                    </svg>
                    <p className="ml-2 text-sm text-green-700">
                      Data uploaded and associated with campaign group "{getCampaignNameFromId(selectedCampaignId)}" successfully!
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Extracted Data Section */}
        {csvData.length > 0 && (
          <div className="mt-6 border-t pt-6">
            <h3 className="text-lg font-semibold text-gray-700 mb-4">Extracted Data Preview</h3>
            <div className="overflow-x-auto bg-gray-50 p-4 rounded-lg border border-gray-200">
              <table className="min-w-full divide-y divide-gray-200">
                <thead>
                  <tr>
                    <th className="px-4 py-2 text-left text-sm font-semibold text-gray-700">Name</th>
                    <th className="px-4 py-2 text-left text-sm font-semibold text-gray-700">Phone Number</th>
                    <th className="px-4 py-2 text-left text-sm font-semibold text-gray-700">Business Name</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {csvData.slice(0, 10).map((data, index) => (
                    <tr key={index} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                      <td className="px-4 py-2 text-sm text-gray-900">{data.name}</td>
                      <td className="px-4 py-2 text-sm text-gray-900">{data.phoneNumber}</td>
                      <td className="px-4 py-2 text-sm text-gray-900">{data.businessName}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {csvData.length > 10 && (
                <div className="mt-2 text-sm text-gray-500 text-right">
                  Showing 10 of {csvData.length} records
                </div>
              )}
            </div>
          </div>
        )}

        {errorMessage && (
          <div className="mt-4 p-4 bg-red-50 rounded-lg border border-red-200">
            <p className="text-sm text-red-700">{errorMessage}</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default CsvUpload; 