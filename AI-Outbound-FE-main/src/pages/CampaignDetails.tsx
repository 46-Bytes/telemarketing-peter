import React, { useState, useEffect, useRef, useMemo } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { campaignApi, uploadApi, userApi } from '../api/api';
import { Campaign } from '../types/campaign';
import FileUpload from '../components/FileUpload';
import { useMicrosoftGraph } from '../hooks/useMicrosoftGraph';
// import MicrosoftAuthRequired from '../components/MicrosoftAuthRequired';
import useAuthorization from '../hooks/useAuthorization';
import AddProspectModal from '../components/AddProspectModal';
import Papa from 'papaparse';
import { getBrisbaneDate } from '../utils/timezone';
import { useAuth } from '../contexts/AuthContext';
import ApiKeyRequired from '../components/ApiKeyRequired';
import { formatDuration } from '../components/MetricDetailsModal';

interface CsvData {
  name?: string;
  phoneNumber: string;
  businessName: string;
  email: string;
}

interface Prospect {
  id: string;
  name?: string;
  phoneNumber: string;
  businessName?: string;
  status: string;
  email?: string;
  ownerName?: string;
  createdAt?: string;
  campaignId: string;
  campaignName: string;
  scheduledCallDate?: string;
  appointment?: {
    appointmentInterest: boolean | null;
    appointmentDateTime: string | null;
    appointmentType?: 'selling' | 'advisory' | null;
  };
  calls?: Array<{
    id: string;
    callTime: string;
    duration?: string;
    transcript?: string;
    status?: string;
    timestamp?: string;
    callSummary?: string;
    callId?: string;
    batchId?: string;
    recordingUrl?: string;
  }>;
}

const CampaignDetails: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const { checkAndRefreshToken } = useMicrosoftGraph();
  const { user } = useAuth();
  const { isAdmin } = useAuthorization();
  const [campaign, setCampaign] = useState<any | null>(null);
  const [prospects, setProspects] = useState<Prospect[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [filteredProspects, setFilteredProspects] = useState<Prospect[]>([]);
  const [selectedStatus, setSelectedStatus] = useState<string>('');
  const [isCallingCampaign, setIsCallingCampaign] = useState<boolean>(false);
  const [isCallingUser, setIsCallingUser] = useState<string | null>(null);
  const [callError, setCallError] = useState<string | null>(null);
  const [isCsvModalOpen, setIsCsvModalOpen] = useState(false);
  const [uploadedFileName, setUploadedFileName] = useState<string | null>(null);
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitStatus, setSubmitStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [csvData, setCsvData] = useState<CsvData[]>([]);

  
  // Ebook related state
  const [ebookLink, setEbookLink] = useState<string>('');
  
  // File upload modal states
  const [isEbookModalOpen, setIsEbookModalOpen] = useState<boolean>(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [uploadProgress, setUploadProgress] = useState<number>(0);
  const [uploadError, setUploadError] = useState<string | null>(null);
  
  
  // Use a ref to track if we've already fetched data
  const dataFetchedRef = useRef(false);
  
  // Determine if we're in admin mode based on the URL
  const isAdminRoute = location.pathname.includes('/admin/');
  
  // Check if user is admin
  const isUserAdmin = useMemo(() => isAdmin(), [isAdmin]);
  
  // First ensure Microsoft token is valid before any data fetching (only for non-admin users)
  useEffect(() => {
    // Skip Microsoft token validation for admin users
    if (isUserAdmin) {
      return;
    }
    
    const validateMicrosoftToken = async () => {
      try {
        await checkAndRefreshToken();
      } catch (tokenError) {
        console.error("Microsoft token refresh failed:", tokenError);
        setError("Microsoft authentication error. Please reconnect your account.");
        setIsLoading(false);
      }
    };
    
    validateMicrosoftToken();
  }, [isUserAdmin, checkAndRefreshToken]);
  
  // Separate effect for fetching campaign data after token validation
  useEffect(() => {
    // Skip if we've already fetched data or if we're still loading the token
    if (dataFetchedRef.current || error) {
      return;
    }
    
    const fetchCampaignDetails = async () => {
      if (!id) {
        setError('Campaign ID is missing');
        setIsLoading(false);
        return;
      }

      try {
        setIsLoading(true);
        setError(null);

        // Fetch campaign data - different approach based on whether we're in admin mode
        let selectedCampaign: Campaign | undefined;

        if (isAdminRoute) {
          // For admin users, fetch all campaigns
          console.log("Fetching campaign as admin");
          const allCampaigns = await campaignApi.getCampaignUsers();
          console.log("All campaigns:", allCampaigns);
          selectedCampaign = allCampaigns.find(c => c.id === id);
        } else {
          // For regular users, fetch just their campaigns
          console.log("Fetching campaign as regular user");
          const userCampaigns = await campaignApi.getUserCampaigns();
          console.log("User campaigns:", userCampaigns);

          console.log("User campaigns:", userCampaigns);
          selectedCampaign = userCampaigns.find(c => c.id === id);
        }   

        if (!selectedCampaign) {
          setError('Campaign not found');
          setIsLoading(false);
          return;
        }
        console.log("Selected campaign:", selectedCampaign);
        setCampaign(selectedCampaign);
        console.log("Campaign found:", selectedCampaign);

        // Set ebook link if available in the campaign data
        if (selectedCampaign.hasEbook && selectedCampaign.ebookPath) {
          setEbookLink(selectedCampaign.ebookPath);
        }

        // Fetch prospects for this campaign
        const campaignProspects = await campaignApi.getCampaignProspects(id);
        console.log("Fetched prospects:", campaignProspects);
        setProspects(campaignProspects);
        setFilteredProspects(campaignProspects);
        
        // Mark that we've successfully fetched data
        dataFetchedRef.current = true;
      } catch (error) {
        console.error("Failed to fetch campaign details:", error);
        setError(error instanceof Error ? error.message : "Failed to fetch campaign details");
      } finally {
        setIsLoading(false);
      }
    };

    fetchCampaignDetails();
  }, [id, isAdminRoute, error]);

  // Filter prospects based on search query and selected status
  useEffect(() => {
    console.log("Filtering prospects. Search query:", searchQuery, "Status:", selectedStatus);
    console.log("Total prospects before filtering:", prospects.length);

    if (!prospects.length) {
      setFilteredProspects([]);
      return;
    }

    let filtered = [...prospects];

    // Apply status filter
    if (selectedStatus) {
      filtered = filtered.filter(prospect => 
        prospect.status?.toLowerCase() === selectedStatus.toLowerCase()
      );
      console.log("After status filter:", filtered.length);
    }

    // Apply search filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase().trim();
      
      // Debug the first few prospects
      if (filtered.length > 0) {
        console.log("Sample prospect for search:", {
          name: filtered[0].name,
          phoneNumber: filtered[0].phoneNumber,
          businessName: filtered[0].businessName,
          ownerName: filtered[0].ownerName
        });
      }
      
      filtered = filtered.filter(prospect => {
        const nameMatch = (prospect.name || '').toLowerCase().includes(query);
        const phoneMatch = (prospect.phoneNumber || '').toLowerCase().includes(query);
        const businessMatch = (prospect.businessName || '').toLowerCase().includes(query);
        const ownerMatch = (prospect.ownerName || '').toLowerCase().includes(query);
        
        const isMatch = nameMatch || phoneMatch || businessMatch || ownerMatch;
        
        // Log detailed matching info for debugging
        if (isMatch) {
          console.log("Match found:", {
            prospect: prospect.name,
            nameMatch,
            phoneMatch,
            businessMatch,
            ownerMatch
          });
        }
        
        return isMatch;
      });
      
      console.log("After search filter:", filtered.length);
    }

    setFilteredProspects(filtered);
  }, [searchQuery, selectedStatus, prospects]);
  
  // Get the status color for the badge
  const getStatusColor = (status: string) => {
    const statusMap: Record<string, string> = {
      new: 'bg-blue-100 text-blue-800',
      contacted: 'bg-yellow-100 text-yellow-800',
      picked_up: 'bg-green-100 text-green-800',
      error: 'bg-red-100 text-red-800',
    };
    
    return statusMap[status?.toLowerCase()] || 'bg-gray-100 text-gray-800';
  };

  // Format date with fallback
  const formatDate = (dateString?: string) => {
    if (!dateString) return 'N/A';
    
    try {
      return new Date(dateString).toLocaleDateString('en-US', { 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric' 
      });
    } catch (e) {
      return dateString;
    }
  };

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(e.target.value);
  };

  const handleStatusChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedStatus(e.target.value);
  };

  const handleCallEveryone = async () => {
    if (!campaign || !filteredProspects.length) return;
    
    setIsCallingCampaign(true);
    setCallError(null);

    try {
      // Get all valid phone numbers from the campaign
      const phoneNumbers = filteredProspects
        .map(p => p.phoneNumber)
        .filter((number): number is string => 
          typeof number === 'string' && number.trim() !== ''
        );
      
      if (phoneNumbers.length === 0) {
        throw new Error('No valid phone numbers found in this campaign');
      }
      console.log('Campaign ID:', campaign?.id);
      // Call the API to initiate calls for all prospects in the campaign
      const campaignName = campaign.campaignName || '';
      console.log('Campaign name:', campaignName);
      console.log('Phone numbers:', phoneNumbers);
      const response = await userApi.initiateCampaignCalls(campaignName, campaign?.id || '', phoneNumbers);
      console.log('Campaign calls initiated successfully:', response);
      
      // Refresh prospects after initiating calls
      const refreshedProspects = await campaignApi.getCampaignProspects(id || '');
      setProspects(refreshedProspects);
      
    } catch (err) {
      console.error('Error initiating campaign calls:', err);
      setCallError(err instanceof Error ? err.message : 'Failed to initiate campaign calls');
    } finally {
      setIsCallingCampaign(false);
    }
  };

  const handleInitiateCall = async (phoneNumber: string) => {
    setIsCallingUser(phoneNumber);
    setCallError(null);

    try {
      const response = await userApi.initiateCall(phoneNumber,campaign?.id || '');
      console.log('Call initiated successfully:', response);

      // Refresh prospects after call
      const refreshedProspects = await campaignApi.getCampaignProspects(id || '');
      setProspects(refreshedProspects);
    } catch (err) {
      console.error('Error initiating call:', err);
      setCallError(err instanceof Error ? err.message : 'Failed to initiate call');
    } finally {
      setIsCallingUser(null);
    }
  };

  // Update the handleBackButton to navigate to the correct page based on the route
  const handleBackButton = () => {
    if (isAdminRoute) {
      navigate('/admin/campaigns');
    } else {
      navigate('/my-campaigns');
    }
  };

  // Ebook modal handlers
  const handleOpenEbookModal = () => {
    setIsEbookModalOpen(true);
    setSelectedFile(null);
    setUploadError(null);
    setUploadProgress(0);
  };

  const handleCloseEbookModal = () => {
    setIsEbookModalOpen(false);
    setSelectedFile(null);
    setUploadError(null);
    setIsDragging(false);
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      if (file.type !== 'application/pdf') {
        setUploadError('Only PDF files are allowed');
        setSelectedFile(null);
        return;
      }
      setSelectedFile(file);
      setUploadError(null);
    }
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (file.type !== 'application/pdf') {
        setUploadError('Only PDF files are allowed');
        return;
      }
      setSelectedFile(file);
      setUploadError(null);
    }
  };

  const handleUploadEbook = async () => {
    if (!selectedFile || !campaign || !id) return;
    
    setIsUploading(true);
    setUploadError(null);
    
    try {
      // Create a FormData object to upload the file
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('campaign_id', id);
      
      // Show upload progress
      for (let progress = 0; progress <= 100; progress += 10) {
        await new Promise(resolve => setTimeout(resolve, 200));
        setUploadProgress(progress);
      }
      
      // Call the API to upload the ebook
      const response = await uploadApi.uploadEbook(formData);
      
      // Update the campaign with the new ebook link
      setEbookLink(response.path);
      
      // Update campaign data
      setCampaign({
        ...campaign,
        hasEbook: true,
        ebookPath: response.path
      });
      
      // Close the modal after successful upload
      handleCloseEbookModal();
      
    } catch (error) {
      console.error("Failed to upload ebook:", error);
      setUploadError(error instanceof Error ? error.message : "Failed to upload ebook");
    } finally {
      setIsUploading(false);
    }
  };

  // Add state for Add Prospect modal
  const [isAddProspectModalOpen, setIsAddProspectModalOpen] = useState<boolean>(false);
  
  // Handle adding a new prospect
  const handleAddProspectSuccess = async () => {
    try {
      // Refresh prospects after successful addition
      const refreshedProspects = await campaignApi.getCampaignProspects(id || '');
      setProspects(refreshedProspects);
      
    } catch (error) {
      console.error("Failed to refresh prospects:", error);
    }
  };

  const handleCsvButtonClick = (e: React.MouseEvent) => {
    // Stop propagation to prevent navigation when clicking the CSV button
    e.stopPropagation();
    setIsCsvModalOpen(true);
  };

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

  const handleUploadProspects = async () => {
    if (csvData.length === 0 || !campaign?.id) return;

    setIsSubmitting(true);
    setSubmitStatus('idle');
    
    try {
      // Add campaign data to each record
      const dataWithCampaign = csvData.map(record => ({
        ...record,
        campaignId: campaign.id,
        campaignName: campaign.campaignName
      }));
      
      console.log("Uploading data with campaign:", {
        campaignId: campaign.id,
        campaignName: campaign.campaignName,
        sampleRecord: dataWithCampaign[0]
      });
      
      // console.log("campaign", campaign);
      // const getUserName = campaign.find((campaignId: Campaign) => campaignId.id === campaign.id)?.owner_name;
      // console.log("getUserName", getUserName);
      // Get the owner name from AuthContext
      const ownerName = campaign?.owner_name || user?.name || 'Unknown User';

      // Pass the campaign ID and name
      await userApi.uploadUsers(
        dataWithCampaign, 
        "", 
        campaign.campaignName || "", 
        ownerName || user?.name || 'Unknown User', 
        campaign.id || ""
      );
      
      setSubmitStatus('success');
      
      // Refresh prospects after successful upload
      try {
        const refreshedProspects = await campaignApi.getCampaignProspects(id || '');
        setProspects(refreshedProspects);
        console.log("Prospects refreshed after CSV upload:", refreshedProspects.length);
      } catch (refreshError) {
        console.error("Error refreshing prospects after CSV upload:", refreshError);
      }
      
      // Close modal after a delay on success
      setTimeout(() => {
        setIsCsvModalOpen(false);
        // Reset CSV data
        setCsvData([]);
        setUploadedFileName(null);
        setUploadStatus('idle');
        setSubmitStatus('idle');
      }, 1000);
    } catch (error) {
      console.error('Error uploading prospects:', error);
      setSubmitStatus('error');
      setErrorMessage(error instanceof Error ? error.message : 'Failed to upload prospects');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Add state for active tab
  const [activeTab, setActiveTab] = useState<string>('prospects');
  const [campaignName, setCampaignName] = useState(campaign?.campaignName || '');
  const [campaignDate, setCampaignDate] = useState(campaign?.campaignDate || '');
  const [campaignTime, setCampaignTime] = useState(campaign?.campaignTime || '');
  const [maxRetry, setMaxRetry] = useState(campaign?.maxRetry || 0);

  // Add loading state for settings save
  const [isSavingSettings, setIsSavingSettings] = useState<boolean>(false);
  const [saveSettingsSuccess, setSaveSettingsSuccess] = useState<boolean>(false);
  const [saveSettingsError, setSaveSettingsError] = useState<string | null>(null);

  useEffect(() => {
    setCampaignName(campaign?.campaignName || '');
    setCampaignDate(campaign?.campaignDate || '');
    setCampaignTime(campaign?.campaignTime || '');
    setMaxRetry(campaign?.maxRetry || 0);
  }, [campaign]);

  // Function to save settings to the database
  const saveCampaignSettings = async (settings: { campaignName: string; campaignDate: string; maxRetry: number; campaignTime: string }) => {
    try {
      setIsSavingSettings(true);
      setSaveSettingsSuccess(false);
      setSaveSettingsError(null);
      
      await campaignApi.updateCampaignSettings(id, settings);
      
      setSaveSettingsSuccess(true);
      // Reset success message after 3 seconds
      setTimeout(() => setSaveSettingsSuccess(false), 3000);
    } catch (error) {
      console.error('Error saving settings:', error);
      setSaveSettingsError(error instanceof Error ? error.message : 'Failed to save settings');
    } finally {
      setIsSavingSettings(false);
    }
  };

  const handleSaveSettings = async (event: React.FormEvent) => {
    event.preventDefault();
    await saveCampaignSettings({ campaignName, campaignDate, maxRetry, campaignTime });
  };

  console.log(activeTab);

  const [selectedProspect, setSelectedProspect] = useState<Prospect | null>(null);
  const [isViewDetailsModalOpen, setIsViewDetailsModalOpen] = useState<boolean>(false);
  const [metric, setMetric] = useState<any>(null);
  const handleViewDetails = (prospect: Prospect) => {
    setSelectedProspect(prospect);
    setIsViewDetailsModalOpen(true);
  };

  // Add this helper function near other utility functions
  const formatDateWithFallback = (dateString?: string | null) => {
    if (!dateString) return 'N/A';
    
    try {
      const date = new Date(dateString);
      // Check if date is valid
      if (isNaN(date.getTime())) {
        return 'N/A';
      }
      return date.toLocaleString();
    } catch (e) {
      return 'N/A';
    }
  };

  const campaignContent = () => {
    if (isLoading) {
      return (
        <div className="flex justify-center items-center h-64 p-6">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
        </div>
      );
    }

    if (error) {
      return (
        <div className="p-6">
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4" role="alert">
            <strong className="font-bold">Error: </strong>
            <span className="block sm:inline">{error}</span>
          </div>
        </div>
      );
    }

    if (!campaign) {
      return (
        <div className="p-6">
          <div className="bg-yellow-100 border border-yellow-400 text-yellow-700 px-4 py-3 rounded relative mb-4" role="alert">
            <strong className="font-bold">Warning: </strong>
            <span className="block sm:inline">Campaign not found</span>
          </div>
        </div>
      );
    }

   

    return (
      <div className="">
        {/* Call error notification */}
        {callError && (
          <div className="p-4 bg-red-50 border border-red-100 rounded-lg mb-4">
            <div className="flex items-center">
              <svg className="h-5 w-5 text-red-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <p className="text-sm text-red-600">{callError}</p>
            </div>
          </div>
        )}

        {/* Campaign Info Card */}
        <div className="bg-white rounded-lg p-6 border border-gray-200">
          <div className="flex items-center mb-6">
            <div className="flex-shrink-0 h-12 w-12 bg-blue-600 rounded-full flex items-center justify-center text-white font-bold text-xl">
              {campaign.campaignName.charAt(0).toUpperCase()}
            </div>
            <div className="ml-4">
              <h2 className="text-xl font-bold text-gray-800">{campaign.campaignName}</h2>
            </div>
            <div className="ml-auto flex space-x-3">
              <button
                onClick={() => setIsAddProspectModalOpen(true)}
                className="px-4 py-2 text-sm bg-purple-600 hover:bg-purple-700 text-white rounded-md transition flex items-center"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                Add Prospect
              </button>
              
              <button
                onClick={handleCsvButtonClick}
                className="px-4 py-2 text-sm bg-blue-600 hover:bg-blue-700 text-white rounded-md transition flex items-center"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
                Upload CSV
              </button>
              
              {user?.role === "super_admin" && <button
                onClick={handleCallEveryone}
                disabled={isCallingCampaign || filteredProspects.length === 0}
                className="px-5 py-2 bg-green-600 hover:bg-green-700 text-white rounded-md
                transition-all duration-300 text-sm font-medium
                disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isCallingCampaign ? (
                  <span className="flex items-center">
                    <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Calling...
                  </span>
                ) : filteredProspects.length === 0 ? 'No Prospects' : 'Call Everyone'}
              </button>}
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <p className="text-sm font-medium text-gray-500">Description</p>
              <p className="text-gray-800">{campaign.description || 'No description'}</p>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-500">Campaign Date</p>
              <p className="text-gray-800">{formatDate(campaign.campaignDate)}</p>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-500">Created</p>
              <p className="text-gray-800">{formatDate(campaign.created_at)}</p>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-500">Total Prospects</p>
              <p className="text-gray-800">{prospects.length}</p>
            </div>
          </div>
        </div>

        {/* Ebook Section */}
        <div className="bg-white rounded-lg p-6 border border-gray-200">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold text-gray-800">Campaign Ebook</h3>
            <button 
              onClick={handleOpenEbookModal}
              className="px-3 py-1 text-sm bg-blue-600 hover:bg-blue-700 text-white rounded-md transition flex items-center"
              title="Upload PDF or Edit Link"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
              </svg>
              {ebookLink ? 'Edit' : 'Add Ebook'}
            </button>
          </div>
          
          {ebookLink ? (
            <div className="flex items-center space-x-4">
              <div className="flex-shrink-0">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-10 w-10 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                </svg>
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-900">Campaign Ebook Available</p>
                <a 
                  href={ebookLink} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:text-blue-800 hover:underline text-sm mt-1 inline-flex items-center"
                >
                  {ebookLink.length > 50 ? `${ebookLink.substring(0, 50)}...` : ebookLink}
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 ml-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                  </svg>
                </a>
              </div>
            </div>
          ) : (
            <div className="text-center py-6 bg-gray-50 rounded-lg border border-dashed border-gray-300">
              <svg xmlns="http://www.w3.org/2000/svg" className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
              </svg>
              <h3 className="mt-2 text-sm font-medium text-gray-900">No ebook available</h3>
              <p className="mt-1 text-sm text-gray-500">Click the "Add Ebook" button to upload a PDF or add a link.</p>
            </div>
          )}
        </div>
        
        {/* Ebook Upload/Edit Modal */}
        {isEbookModalOpen && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold text-gray-900">
                  Upload Campaign Ebook
                </h3>
                <button
                  onClick={handleCloseEbookModal}
                  className="text-gray-400 hover:text-gray-500 focus:outline-none"
                >
                  <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              
              <div className="space-y-4">
                {/* Drag and drop area */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Upload PDF</label>
                  <div
                    className={`border-2 border-dashed rounded-lg p-6 text-center transition-colors
                      ${isDragging ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400'}
                      ${selectedFile ? 'bg-green-50 border-green-300' : ''}`}
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    onDrop={handleDrop}
                  >
                    {selectedFile ? (
                      <div className="space-y-2">
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-10 w-10 mx-auto text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <p className="text-sm font-medium text-gray-900">{selectedFile.name}</p>
                        <p className="text-xs text-gray-500">{(selectedFile.size / 1024 / 1024).toFixed(2)} MB</p>
                        <button
                          onClick={() => setSelectedFile(null)}
                          className="text-sm text-red-600 hover:text-red-800"
                        >
                          Remove
                        </button>
                      </div>
                    ) : (
                      <>
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-10 w-10 mx-auto text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                        </svg>
                        <p className="mt-2 text-sm text-gray-600">Drag and drop your PDF file here, or</p>
                        <label className="mt-2 inline-block">
                          <span className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 cursor-pointer">
                            Browse files
                          </span>
                          <input
                            type="file"
                            className="hidden"
                            accept=".pdf"
                            onChange={handleFileSelect}
                          />
                        </label>
                        <p className="mt-1 text-xs text-gray-500">Only PDF files are supported</p>
                      </>
                    )}
                  </div>
                </div>
                
                {/* Upload error */}
                {uploadError && (
                  <div className="text-red-500 text-sm">{uploadError}</div>
                )}
                
                {/* Upload progress */}
                {isUploading && (
                  <div className="space-y-2">
                    <div className="h-2 bg-gray-200 rounded-full">
                      <div 
                        className="h-2 bg-blue-600 rounded-full transition-all duration-300" 
                        style={{ width: `${uploadProgress}%` }}
                      ></div>
                    </div>
                    <p className="text-xs text-gray-500 text-right">{uploadProgress}% uploaded</p>
                  </div>
                )}
                
                {/* Modal actions */}
                <div className="flex justify-end space-x-3 mt-4">
                  <button
                    onClick={handleCloseEbookModal}
                    className="px-4 py-2 text-sm bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-md transition"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleUploadEbook}
                    disabled={!selectedFile || isUploading}
                    className="px-4 py-2 text-sm bg-blue-600 hover:bg-blue-700 text-white rounded-md transition disabled:opacity-50"
                  >
                    {isUploading ? 'Uploading...' : 'Upload'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
        {isCsvModalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-[150] overflow-y-auto">
          <div className="bg-white rounded-lg shadow-lg w-full max-w-md my-4 mx-auto flex flex-col max-h-[90vh]">
            {/* Modal Header */}
            <div className="sticky top-0 z-10 px-6 py-4 border-b border-gray-200 bg-white rounded-t-lg flex justify-between items-center">
              <h3 className="text-lg font-semibold text-gray-800">
                Upload Prospects to {campaign.campaignName}
              </h3>
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  setIsCsvModalOpen(false);
                }}
                className="text-gray-500 hover:text-gray-700 focus:outline-none"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            
            {/* Modal Body */}
            <div className="overflow-y-auto p-6 pt-4">
              {/* CSV File Upload */}
              <div className="mt-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Upload CSV File
                </label>
                <FileUpload 
                  onFileSelect={handleFileUpload}
                  onNewUpload={handleNewUpload}
                />
                
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
                        File "{uploadedFileName}" uploaded successfully! ({csvData.length} prospects found)
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

              {/* Submit Button */}
              <div className="mt-6">
                <button
                  onClick={handleUploadProspects}
                  disabled={csvData.length === 0 || isSubmitting}
                  className="w-full px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-md transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isSubmitting ? 'Uploading...' : 'Upload Prospects'}
                </button>
              </div>

              {submitStatus === 'success' && (
                <div className="mt-4 p-4 bg-green-50 rounded-lg border border-green-200">
                  <div className="flex items-center">
                    <svg className="h-5 w-5 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                    </svg>
                    <p className="ml-2 text-sm text-green-700">
                      {csvData.length} prospects successfully uploaded!
                    </p>
                  </div>
                </div>
              )}

              {submitStatus === 'error' && (
                <div className="mt-4 p-4 bg-red-50 rounded-lg border border-red-200">
                  <div className="flex items-center">
                    <svg className="h-5 w-5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                    <p className="ml-2 text-sm text-red-700">
                      {errorMessage || 'Error uploading prospects. Please try again.'}
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

        {/* Prospects List */}
        <div className="bg-white rounded-lg overflow-hidden border border-gray-200">
          {/* Search and Filter */}
          <div className="p-6 border-b border-gray-200">
            <div className="flex flex-col md:flex-row gap-4">
              <div className="flex-1">
                <label htmlFor="search" className="block text-sm font-medium text-gray-700 mb-1">Search Prospects</label>
                <div className="relative rounded-md shadow-sm">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <svg className="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                    </svg>
                  </div>
                  <input
                    id="search"
                    type="search"
                    className="focus:ring-blue-500 focus:border-blue-500 block w-full pl-10 pr-3 py-2 sm:text-sm border-gray-300 rounded-md"
                    placeholder="Search by name, phone, or business..."
                    value={searchQuery}
                    onChange={handleSearchChange}
                  />
                </div>
              </div>
              
              <div className="w-full md:w-60">
                <label htmlFor="status" className="block text-sm font-medium text-gray-700 mb-1">Filter by Status</label>
                <select
                  id="status"
                  className="focus:ring-blue-500 focus:border-blue-500 block w-full py-2 px-3 border border-gray-300 bg-white rounded-md shadow-sm focus:outline-none sm:text-sm"
                  value={selectedStatus}
                  onChange={handleStatusChange}
                >
                  <option value="">All Statuses</option>
                  <option value="new">New</option>
                  <option value="contacted">Contacted</option>
                  <option value="picked_up">Picked Up</option>
                  <option value="error">Error</option>
                </select>
              </div>
            </div>
            <div className="mt-2 text-xs text-gray-500">
              Showing {filteredProspects.length} of {prospects.length} prospects
            </div>
          </div>
          
          {filteredProspects.length === 0 ? (
            <div className="p-6">
              <div className="bg-blue-50 border-l-4 border-blue-500 text-blue-700 p-4" role="alert">
                <p className="text-sm">{prospects.length > 0 ? 'No prospects match your filters.' : 'No prospects found for this campaign.'}</p>
              </div>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Name
                    </th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Phone
                    </th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Business
                    </th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Owner
                    </th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Email
                    </th>
                    <th scope="col" className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {filteredProspects.map((prospect, index) => (
                    <tr key={prospect.id || index} className="hover:bg-gray-50 transition-colors duration-150">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">{prospect.name || 'N/A'}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-600">{prospect.phoneNumber || 'N/A'}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-600">{prospect.businessName || 'N/A'}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-600">{prospect.ownerName || 'N/A'}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusColor(prospect.status)}`}>
                          {prospect.status?.toUpperCase() === 'NEW' ? 'New' : prospect.status?.toUpperCase() === 'CONTACTED' ? 'Contacted' : prospect.status?.toUpperCase() === 'PICKED_UP' ? 'Picked Up' : prospect.status?.toUpperCase() === 'ERROR' ? 'Error' : 'UNKNOWN'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-600">{prospect.email || 'N/A'}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-center">
                        <div className="flex space-x-2 justify-center">
                          <button
                            onClick={() => handleViewDetails(prospect)}
                            className="px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md
                              transition duration-300 text-xs font-medium"
                          >
                            View Details
                          </button>
                          {user?.role === "super_admin" && <button
                            onClick={() => prospect.phoneNumber && handleInitiateCall(prospect.phoneNumber)}
                            disabled={!prospect.phoneNumber || isCallingUser === prospect.phoneNumber}
                            className="px-3 py-2 bg-green-600 hover:bg-green-700 text-white rounded-md
                              transition duration-300 text-xs font-medium
                              disabled:opacity-50 disabled:cursor-not-allowed"
                          >
                            {isCallingUser === prospect.phoneNumber ? (
                              <span className="flex items-center">
                                <svg className="animate-spin -ml-1 mr-1 h-3 w-3 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                </svg>
                                Calling...
                              </span>
                            ) : 'Call Now'}
                          </button>}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Add Prospect Modal */}
        <AddProspectModal 
          isOpen={isAddProspectModalOpen}
          onClose={() => setIsAddProspectModalOpen(false)}
          onSuccess={handleAddProspectSuccess}
        />

        {/* View Details Modal */}
        {isViewDetailsModalOpen && selectedProspect && (
          <div className="fixed inset-0 bg-black bg-opacity-70 flex items-center justify-center z-[170] p-4">
            <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] flex flex-col">
              <div className="flex justify-between items-center p-6 border-b">
                <h3 className="text-lg font-semibold text-gray-900">
                  Prospect Details
                </h3>
                <button
                  onClick={() => setIsViewDetailsModalOpen(false)}
                  className="text-gray-400 hover:text-gray-500 focus:outline-none"
                >
                  <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              
              <div className="overflow-y-auto p-6 flex-1">
                <div className="space-y-4">
                  <div className="border-b pb-3">
                    <div className="flex items-center space-x-3 mb-3">
                      <div className="h-10 w-10 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 font-bold">
                        {selectedProspect.name?.charAt(0) || '?'}
                      </div>
                      <div>
                        <h4 className="text-lg font-medium">{selectedProspect.name || 'N/A'}</h4>
                        <span className={`px-2 py-1 text-xs leading-5 font-semibold rounded-full ${getStatusColor(selectedProspect.status)}`}>
                          {selectedProspect.status?.toUpperCase() === 'NEW' ? 'New' : selectedProspect.status?.toUpperCase() === 'CONTACTED' ? 'Contacted' : selectedProspect.status?.toUpperCase() === 'PICKED_UP' ? 'Picked Up' : selectedProspect.status?.toUpperCase() === 'ERROR' ? 'Error' : 'UNKNOWN'}
                        </span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="space-y-3">
                    <div className="grid grid-cols-3 gap-2">
                      <div className="text-sm font-medium text-gray-500">Phone Number</div>
                      <div className="col-span-2 text-sm text-gray-900">{selectedProspect.phoneNumber || 'N/A'}</div>
                    </div>
                    
                    <div className="grid grid-cols-3 gap-2">
                      <div className="text-sm font-medium text-gray-500">Business Name</div>
                      <div className="col-span-2 text-sm text-gray-900">{selectedProspect.businessName || 'N/A'}</div>
                    </div>
                    
                    <div className="grid grid-cols-3 gap-2">
                      <div className="text-sm font-medium text-gray-500">Owner Name</div>
                      <div className="col-span-2 text-sm text-gray-900">{selectedProspect.ownerName || 'N/A'}</div>
                    </div>
                    
                    {/* <div className="grid grid-cols-3 gap-2">
                      <div className="text-sm font-medium text-gray-500">Email</div>
                      <div className="col-span-2 text-sm text-gray-900">{selectedProspect.email || 'N/A'}</div>
                    </div> */}
                    
                    {/* <div className="grid grid-cols-3 gap-2">
                      <div className="text-sm font-medium text-gray-500">Scheduled Call Date</div>
                      <div className="col-span-2 text-sm text-gray-900">{formatDateWithFallback(selectedProspect.scheduledCallDate)}</div>
                    </div> */}
                    
                    <div className="grid grid-cols-3 gap-2">
                      <div className="text-sm font-medium text-gray-500">Campaign</div>
                      <div className="col-span-2 text-sm text-gray-900">{selectedProspect.campaignName || 'N/A'}</div>
                    </div>
                    
                    <div className="grid grid-cols-3 gap-2">
                      <div className="text-sm font-medium text-gray-500">Appointment Interest</div>
                      <div className="col-span-2 text-sm text-gray-900">
                        {selectedProspect.appointment?.appointmentInterest === true ? 'Yes' : 
                         selectedProspect.appointment?.appointmentInterest === false ? 'No' : 'Not specified'}
                      </div>
                    </div>
                    
                    {selectedProspect.appointment?.appointmentDateTime && (
                      <div className="grid grid-cols-3 gap-2">
                        <div className="text-sm font-medium text-gray-500">Appointment Date</div>
                        <div className="col-span-2 text-sm text-gray-900">
                          {formatDateWithFallback(selectedProspect.appointment.appointmentDateTime)}
                        </div>
                      </div>
                    )}

                    {selectedProspect.appointment?.appointmentType && (
                      <div className="grid grid-cols-3 gap-2">
                        <div className="text-sm font-medium text-gray-500">Appointment Type</div>
                        <div className="col-span-2 text-sm text-gray-900 capitalize">
                          {selectedProspect.appointment.appointmentType}
                        </div>
                      </div>
                    )}
                  </div>
                  
                  {/* Call History Section */}
                  {selectedProspect.calls && selectedProspect.calls.length > 0 && (
                    <div className="mt-6">
                      <h4 className="text-md font-semibold mb-3 text-gray-800 border-b pb-2">Call History</h4>
                      <div className="space-y-4">
                        {selectedProspect.calls.map((call, index) => (
                          <div key={call.id || index} className="border rounded-lg p-3 bg-gray-50">
                            <div className="flex justify-between mb-2">
                              <span className="text-sm font-medium">
                                {formatDateWithFallback(call.timestamp)}
                              </span>
                              {call.status && (
                                <span className={`px-2 py-0.5 text-xs rounded-full ${
                                  call.status === 'ended' ? 'bg-green-100 text-green-800' : 
                                  call.status === 'error' ? 'bg-red-100 text-red-800' : 
                                  call.status === 'not_connected' || call.status === 'NOT_CONNECTED' ? 'bg-gray-100 text-gray-800' :
                                  'bg-yellow-100 text-yellow-800'
                                }`}>
                                  {call.status.toUpperCase()}
                                </span>
                              )}
                            </div>

                            {(call.callId || call.batchId) && (
                              <div className="text-xs text-gray-500 mb-2">
                                {call.batchId ? `Batch ID: ${call.batchId}` : `Call ID: ${call.callId}`}
                              </div>
                            )}

                            {/* Show different content based on call type */}
                            {call.batchId ? (
                              // Batch call display - show full info if completed, processing if not
                              <>
                                {call.status === 'NOT_CONNECTED' || call.status === 'not_connected' ? (
                                  <div className="text-xs text-gray-500 mb-2">
                                    Not Connected
                                  </div>
                                ) : call.status === 'ended' ? (
                                  // Show full call details for completed batch calls
                                  <>
                                    {call.recordingUrl && (
                                      <div className="text-xs text-gray-500 text-blue-500 truncate mb-2">
                                        Recording URL: <a href={call.recordingUrl} target="_blank" rel="noopener noreferrer">{call.recordingUrl}</a>
                                      </div>
                                    )}
                                    
                                    {call.duration && (
                                      <div className="text-xs text-gray-500 mb-2">
                                        Duration: {call.duration}sec
                                      </div>
                                    )}
                                  </>
                                ) : (
                                  // Still processing
                                  <div className="text-xs text-gray-500 mb-2">
                                    Processing...
                                  </div>
                                )}
                              </>
                            ) : (
                              // Individual call display - full information
                              <>
                                {call.recordingUrl && (
                                  <div className="text-xs text-gray-500 text-blue-500 truncate mb-2">
                                    Recording URL: <a href={call.recordingUrl} target="_blank" rel="noopener noreferrer">{call.recordingUrl}</a>
                                  </div>
                                )}
                                
                                {call.duration && (
                                  <div className="text-xs text-gray-500 mb-2">
                                    Duration: {call.duration}sec
                                  </div>
                                )}
                              </>
                            )}

                            {/* Show call summary for individual calls and completed batch calls */}
                            {(!call.batchId || (call.batchId && (call.status === 'ended'))) && call.callSummary && (
                              <div className="text-xs text-gray-500 mb-2">
                                Call Summary: {call.callSummary}
                              </div>
                            )}
                            
                            {/* Show transcript for individual calls and completed batch calls */}
                            {(!call.batchId || (call.batchId && (call.status === 'ended'))) && call.transcript && (
  <div className="mt-2">
    <div className="text-xs font-medium text-gray-500 mb-1">Transcript:</div>
    <div className="text-sm bg-white p-3 rounded border border-gray-200 max-h-64 overflow-y-auto space-y-3">
      {(() => {
        const lines = call.transcript.split('\n').map(line => line.trim()).filter(Boolean);
        const groups = [];
        let currentSpeaker = null;
        let currentLines:any = [];

        for (const line of lines) {
          const isAgent = line.startsWith('Agent:');
          const isUser = line.startsWith('User:');
          const speaker = isAgent ? 'Agent' : isUser ? selectedProspect.name || 'User' : null;
          const content = line.replace(/^Agent:|^User:/, '').trim();

          if (speaker !== currentSpeaker) {
            if (currentLines.length > 0) {
              groups.push({ speaker: currentSpeaker, lines: currentLines });
            }
            currentSpeaker = speaker;
            currentLines = [content];
          } else {
            currentLines.push(content);
          }
        }

        if (currentLines.length > 0) {
          groups.push({ speaker: currentSpeaker, lines: currentLines });
        }

        return groups.map((group, index) => (
          <div key={index}>
            <div className="font-semibold text-gray-700 mb-0.5">{group.speaker}:</div>
            <div className="text-gray-800 whitespace-pre-line">
              {group.lines.join('\n')}
            </div>
          </div>
        ));
      })()}
    </div>
  </div>
)}

                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
              
              <div className="p-6 border-t flex justify-end">
               {user?.role === "super_admin" && <button
                  onClick={() => selectedProspect.phoneNumber && handleInitiateCall(selectedProspect.phoneNumber)}
                  disabled={!selectedProspect.phoneNumber || isCallingUser === selectedProspect.phoneNumber}
                  className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-md
                    transition duration-300 text-sm font-medium
                    disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
                >
                  {isCallingUser === selectedProspect.phoneNumber ? (
                    <>
                      <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      Calling...
                    </>
                  ) : (
                    <>
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                      </svg>
                      Call Now
                    </>
                  )}
                </button>}
              </div>
            </div>
          </div>
        )}
      </div>
    );
  };

  const handleDeleteCampaign = async () => {
    try {
      await campaignApi.deleteCampaign(id || '');
      navigate('/admin/campaigns');
    } catch (error) {
      console.error('Error deleting campaign:', error);
    }
  };

  const getCampaignAnalytics = async () => {
    try {
      const response = await campaignApi.getCampaignAnalytics(id || '');

      setMetric(response.data);
    } catch (error) {
      console.error('Error getting campaign analytics:', error);
    }
  };

  console.log("metric", metric);

  useEffect(() => {
    if (activeTab === 'analytics') {
      getCampaignAnalytics();
    }
  }, [activeTab]);

  // Admin users don't need Microsoft auth
  if (isUserAdmin) {
    return (
      <div className="bg-gray-50 min-h-screen">
        <div className="max-w-7xl mx-auto px-6 pt-6">
          {/* Navigation and tabs */}
          <div className="flex items-center justify-between mb-8">
            <button
              onClick={handleBackButton}
              className="inline-flex items-center text-gray-700 hover:text-gray-900 transition-colors"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M9.707 16.707a1 1 0 01-1.414 0l-6-6a1 1 0 010-1.414l6-6a1 1 0 011.414 1.414L5.414 9H17a1 1 0 110 2H5.414l4.293 4.293a1 1 0 010 1.414z" clipRule="evenodd" />
              </svg>
              Back to All Campaigns
            </button>
            
            <div>
              <div className="inline-flex rounded-md shadow-sm">
                <button
                  className={`px-4 py-2 text-sm font-medium ${activeTab === 'prospects' ? 'bg-blue-100 text-blue-800' : 'bg-white text-gray-600'} border border-gray-200 rounded-l-lg`}
                  onClick={() => setActiveTab('prospects')}
                >
                  Prospects
                </button>
                <button
                  className={`px-4 py-2 text-sm font-medium ${activeTab === 'analytics' ? 'bg-blue-100 text-blue-800' : 'bg-white text-gray-600'} border-t border-b border-r border-gray-200`}
                  onClick={() => setActiveTab('analytics')}
                >
                  Analytics
                </button>
                <button
                  className={`px-4 py-2 text-sm font-medium ${activeTab === 'settings' ? 'bg-blue-100 text-blue-800' : 'bg-white text-gray-600'} border-t border-b border-r border-gray-200 rounded-r-lg`}
                  onClick={() => setActiveTab('settings')}
                >
                  Settings
                </button>
              </div>
            </div>
            
            <div className="w-40"></div>
          </div>

          {/* Main content */}
         {activeTab === 'prospects' && <div className="bg-white rounded-lg mb-6">
            {campaignContent()}
          </div>}
          {activeTab === 'analytics' && <div className="bg-white rounded-lg mb-6">
            <div className="bg-white rounded-lg shadow-sm p-6 hover:shadow-md transition-shadow duration-300">
                <h2 className="text-xl font-bold mb-6 text-gray-800 border-b pb-3">Campaign Analytics</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {/* Total Calls Card */}
                  <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg shadow p-6 hover:shadow-md transition-shadow duration-300">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-lg font-semibold text-gray-700">Total Calls</h3>
                      <div className="p-2 bg-blue-500 rounded-full">
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                        </svg>
                      </div>
                    </div>
                    <div className="text-3xl font-bold text-gray-800">{metric?.totalCalls || 0}</div>
                    <p className="text-sm text-gray-600 mt-2">Total calls made in this campaign</p>
                  </div>

                  {/* Connected Calls Card */}
                  <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-lg shadow p-6 hover:shadow-md transition-shadow duration-300">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-lg font-semibold text-gray-700">Connected Calls</h3>
                      <div className="p-2 bg-green-500 rounded-full">
                        <svg xmlns="http://www.w3.org/2000/svg" className= "h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                      </div>
                    </div>
                    <div className="text-3xl font-bold text-gray-800">{metric?.totalConnectedCalls || 0}</div>
                    <p className="text-sm text-gray-600 mt-2">Calls that were successfully connected</p>
                  </div>

                  {/* Appointments Booked Card */}
                  <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg shadow p-6 hover:shadow-md transition-shadow duration-300">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-lg font-semibold text-gray-700">Appointments</h3>
                      <div className="p-2 bg-purple-500 rounded-full">
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                        </svg>
                      </div>
                    </div>
                    <div className="text-3xl font-bold text-gray-800">{metric?.totalAppointmentsBooked || 0}</div>
                    <p className="text-sm text-gray-600 mt-2">Total appointments booked</p>
                  </div>

                  {/* E-Books Sent Card */}
                  <div className="bg-gradient-to-br from-amber-50 to-amber-100 rounded-lg shadow p-6 hover:shadow-md transition-shadow duration-300">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-lg font-semibold text-gray-700">E-Books Sent</h3>
                      <div className="p-2 bg-amber-500 rounded-full">
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                        </svg>
                      </div>
                    </div>
                    <div className="text-3xl font-bold text-gray-800">{metric?.totalEbooksSent || 0}</div>
                    <p className="text-sm text-gray-600 mt-2">Total e-books sent to prospects</p>
                  </div>

                {/* Average Call Duration Card */}
                <div className="bg-gradient-to-br from-red-50 to-red-100 rounded-lg shadow p-6 hover:shadow-md transition-shadow duration-300">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-lg font-semibold text-gray-700">Average Call Duration</h3>
                      <div className="p-2 bg-red-500 rounded-full">
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                        </svg>
                      </div>
                    </div>
                    <div className="text-3xl font-bold text-gray-800">{formatDuration(metric?.averageCallDuration?.toFixed(1))}</div>
                    <p className="text-sm text-gray-600 mt-2">Average call duration</p>
                  </div>


                  {/* Callbacks Scheduled Card */}
                  <div className="bg-gradient-to-br from-rose-50 to-rose-100 rounded-lg shadow p-6 hover:shadow-md transition-shadow duration-300">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-lg font-semibold text-gray-700">Callbacks</h3>
                      <div className="p-2 bg-rose-500 rounded-full">
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                      </div>
                    </div>
                    <div className="text-3xl font-bold text-gray-800">{metric?.totalScheduledCallbacks || 0}</div>
                    <p className="text-sm text-gray-600 mt-2">Scheduled callbacks with prospects</p>
                  </div>

                  {/* Conversion Rate Card */}
                  <div className="bg-gradient-to-br from-cyan-50 to-cyan-100 rounded-lg shadow p-6 hover:shadow-md transition-shadow duration-300">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-lg font-semibold text-gray-700">Conversion Rates</h3>
                      <div className="p-2 bg-cyan-500 rounded-full">
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                        </svg>
                      </div>
                    </div>
                    <div className="grid grid-cols-3 gap-2 mt-2">
                      <div className="bg-white bg-opacity-50 p-3 rounded-lg">
                        <div className="text-xl font-bold text-gray-800">
                          {metric?.totalScheduledCallbacks && metric?.totalConnectedCalls > 0 
                            ? `${((metric.totalScheduledCallbacks / metric.totalConnectedCalls) * 100).toFixed(1)}%` 
                            : '0%'}
                        </div>
                        <p className="text-xs text-gray-600 mt-1">A. Callbacks / Connected</p>
                      </div>
                      
                      <div className="bg-white bg-opacity-50 p-3 rounded-lg">
                        <div className="text-xl font-bold text-gray-800">
                          {metric?.totalAppointmentsBooked && metric?.totalConnectedCalls > 0 
                            ? `${((metric.totalAppointmentsBooked / metric.totalConnectedCalls) * 100).toFixed(1)}%` 
                            : '0%'}
                        </div>
                        <p className="text-xs text-gray-600 mt-1">B. Appointments / Connected</p>
                      </div>
                      
                      <div className="bg-white bg-opacity-50 p-3 rounded-lg">
                        <div className="text-xl font-bold text-gray-800">
                          {metric?.totalEbooksSent && metric?.totalConnectedCalls > 0 
                            ? `${((metric.totalEbooksSent / metric.totalConnectedCalls) * 100).toFixed(1)}%` 
                            : '0%'}
                        </div>
                        <p className="text-xs text-gray-600 mt-1">C. E-books / Connected</p>
                      </div>
                    </div>
                    <p className="text-sm text-gray-600 mt-3">Key conversion metrics for this campaign</p>
                  </div>
                </div>
              </div>
          </div>}
          {activeTab === 'settings' && (
          <div className="bg-white rounded-lg shadow-md mb-6 p-6">
            <h2 className="text-xl font-bold mb-6 text-gray-800 border-b pb-3">Campaign Settings</h2>
           
            <form onSubmit={handleSaveSettings} className="space-y-5">
              <div className="mb-4">
                <label className="block text-gray-700 font-medium mb-2">Campaign Name</label>
                <input
                  type="text"
                  value={campaignName}
                  onChange={(e) => setCampaignName(e.target.value)}
                  className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Enter campaign name"
                />
              </div>
              <div className="mb-4">
                <label className="block text-gray-700 font-medium mb-2">Campaign Date</label>
                <input
                  type="date"
                  value={campaignDate}
                  onChange={(e) => setCampaignDate(e.target.value)}
                  min={getBrisbaneDate()}
                  className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <div className="mb-4">
                <label className="block text-gray-700 font-medium mb-2">Campaign Time</label>
                <input
                  type="time"
                  value={campaignTime}
                  onChange={(e) => setCampaignTime(e.target.value)}
                  className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              {/* <div className="mb-4">
                <label className="block text-gray-700 font-medium mb-2">Max Retry</label>
                <input
                  type="number"
                  value={maxRetry}
                  onChange={(e) => setMaxRetry(Number(e.target.value))}
                  className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2 focus:ring-blue-500 focus:border-blue-500"
                  min="0"
                />
              </div> */}
              <div className="pt-4 border-t flex justify-between">
                <button
                  type="submit"
                  disabled={isSavingSettings}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md transition 
                             disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
                >
                  {isSavingSettings ? (
                    <>
                      <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      Saving...
                    </>
                  ) : 'Save Settings'}
                </button>

            <button className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-md transition 
                             disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
                             onClick={handleDeleteCampaign}>Archive Campaign</button>
              </div>
            </form>

            {/* Success message */}
            {saveSettingsSuccess && (
              <div className="mt-3 p-2 bg-green-50 text-green-700 rounded-md text-sm flex items-center">
                <svg className="h-5 w-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                </svg>
                Settings saved successfully!
              </div>
            )}


            {/* Error message */}
            {saveSettingsError && (
              <div className="mt-3 p-2 bg-red-50 text-red-700 rounded-md text-sm flex items-center">
                <svg className="h-5 w-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                {saveSettingsError}
              </div>
            )}
          </div>
        )}
        </div>
      </div>
    );
  }
  return (
    <div className="bg-gray-50 min-h-screen">
      <div className="max-w-7xl mx-auto px-6 pt-6">
        {/* Navigation and tabs */}
        <div className="flex items-center justify-between mb-8">
          <button
            onClick={handleBackButton}
            className="inline-flex items-center text-gray-700 hover:text-gray-900 transition-colors"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M9.707 16.707a1 1 0 01-1.414 0l-6-6a1 1 0 010-1.414l6-6a1 1 0 011.414 1.414L5.414 9H17a1 1 0 110 2H5.414l4.293 4.293a1 1 0 010 1.414z" clipRule="evenodd" />
            </svg>
            Back to My Campaigns
          </button>
          
          <div>
            <div className="inline-flex rounded-md shadow-sm">
              <button
                className={`px-4 py-2 text-sm font-medium ${activeTab === 'prospects' ? 'bg-blue-100 text-blue-800' : 'bg-white text-gray-600'} border border-gray-200 rounded-l-lg`}
                onClick={() => setActiveTab('prospects')}
              >
                Prospects
              </button>
              {/* <button
                className={`px-4 py-2 text-sm font-medium ${activeTab === 'analytics' ? 'bg-blue-100 text-blue-800' : 'bg-white text-gray-600'} border-t border-b border-r border-gray-200`}
                onClick={() => setActiveTab('analytics')}
              >
                Analytics
              </button> */}
              <button
                className={`px-4 py-2 text-sm font-medium ${activeTab === 'settings' ? 'bg-blue-100 text-blue-800' : 'bg-white text-gray-600'} border-t border-b border-r border-gray-200 rounded-r-lg`}
                onClick={() => setActiveTab('settings')}
              >
                Settings
              </button>
            </div>
          </div>
          
          <div className="w-40"></div>
        </div>

        {/* Main content */}
        {activeTab === 'prospects' && <div className="rounded-lg mb-6">
          <ApiKeyRequired
              pageTitle="API Key Required"
              pageDescription="Enter your API key to access campaign details."
            >
              {campaignContent()}
            </ApiKeyRequired>
          {/* <MicrosoftAuthRequired
            pageTitle={`${campaign?.campaignName || 'Campaign Details'}${isAdminRoute ? ' (Admin View)' : ''}`}
          >
            {campaignContent()}
          </MicrosoftAuthRequired> */}
        </div>}
        {/* {activeTab === 'analytics' && <div className="bg-white rounded-lg mb-6">
          Analytics
        </div>} */}
        {activeTab === 'settings' && (
          <div className="bg-white rounded-lg shadow-md mb-6 p-6">
            <h2 className="text-xl font-bold mb-6 text-gray-800 border-b pb-3">Campaign Settings</h2>
            <form onSubmit={handleSaveSettings} className="space-y-5">
              <div className="mb-4">
                <label className="block text-gray-700 font-medium mb-2">Campaign Name</label>
                <input
                  type="text"
                  value={campaignName}
                  onChange={(e) => setCampaignName(e.target.value)}
                  className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Enter campaign name"
                />
              </div>
              <div className="mb-4">
                <label className="block text-gray-700 font-medium mb-2">Campaign Date</label>
                <input
                  type="date"
                  value={campaignDate}
                  onChange={(e) => setCampaignDate(e.target.value)}
                  min={getBrisbaneDate()}
                  className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <div className="mb-4">
                <label className="block text-gray-700 font-medium mb-2">Campaign Time</label>
                <input
                  type="time"
                  value={campaignTime}
                  onChange={(e) => setCampaignTime(e.target.value)}
                  className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              {/* <div className="mb-4">
                <label className="block text-gray-700 font-medium mb-2">Max Retry</label>
                <input
                  type="number"
                  value={maxRetry}
                  onChange={(e) => setMaxRetry(Number(e.target.value))}
                  className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2 focus:ring-blue-500 focus:border-blue-500"
                  min="0"
                />
              </div> */}
              <div className="pt-4 border-t">
                <button
                  type="submit"
                  disabled={isSavingSettings}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md transition 
                             disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
                >
                  {isSavingSettings ? (
                    <>
                      <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      Saving...
                    </>
                  ) : 'Save Settings'}
                </button>
              </div>
            </form>

            {/* Success message */}
            {saveSettingsSuccess && (
              <div className="mt-3 p-2 bg-green-50 text-green-700 rounded-md text-sm flex items-center">
                <svg className="h-5 w-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                </svg>
                Settings saved successfully!
              </div>
            )}

            {/* Error message */}
            {saveSettingsError && (
              <div className="mt-3 p-2 bg-red-50 text-red-700 rounded-md text-sm flex items-center">
                <svg className="h-5 w-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                {saveSettingsError}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default CampaignDetails; 