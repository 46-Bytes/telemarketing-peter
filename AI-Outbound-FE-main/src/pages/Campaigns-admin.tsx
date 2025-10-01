import React, { useState, useEffect, useRef, useMemo } from "react";
import { campaignApi, uploadApi } from "../api/api";
import { authApi } from "../api/authApi";
// import { useAuth } from "../contexts/AuthContext";
import useAuthorization from "../hooks/useAuthorization";
import EnhancedCampaignCard from "../components/EnhancedCampaignCard";
import { getBrisbaneDate } from "../utils/timezone";
import { Campaign } from "../types/campaign";

const CampaignsAdmin: React.FC = () => {
  const [isCampaignModalOpen, setIsCampaignModalOpen] = useState(false);
  const [campaignName, setCampaignName] = useState("");
  const [campaignDescription, setCampaignDescription] = useState("");
  const [brokers, setBrokers] = useState<
    { id: string; name: string; email: string }[]
  >([]);
  const [selectedBroker, setSelectedBroker] = useState("");
  const [campaignError, setCampaignError] = useState<string | null>(null);
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [campaignDate, setCampaignDate] = useState("");
  const [campaignTime, setCampaignTime] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isArchiveModalOpen, setIsArchiveModalOpen] = useState(false);
  const [archeivedCampaigns, setArcheivedCampaigns] = useState<Campaign[]>([]);
  // const { user } = useAuth();
  const { isAdmin } = useAuthorization();
  
  // Add a ref to track if we've already fetched brokers
  const hasFetchedBrokersRef = useRef(false);
  const hasFetchedCampaignsRef = useRef(false);
  
  // Memoize the admin status
  const userIsAdmin = useMemo(() => isAdmin(), []);
  
  // Add states for ebook functionality
  const [hasEbook, setHasEbook] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  // Fetch brokers for dropdown - with proper dependency tracking
  useEffect(() => {
    // Skip if already fetched
    if (hasFetchedBrokersRef.current) {
      return;
    }
    
    const fetchBrokers = async () => {
      try {
        // Set the ref before the API call to prevent race conditions
        hasFetchedBrokersRef.current = true;
        const response = await authApi.getBrokers();
        setBrokers(response);
      } catch (error) {
        setCampaignError("Failed to fetch brokers");
        // Reset the flag so we can try again
        hasFetchedBrokersRef.current = false;
      }
    };
    
    fetchBrokers();
  }, []); // Empty dependency array - only run once on mount

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      if (file.size > 5 * 1024 * 1024) { // 5MB in bytes
        setCampaignError('File size exceeds 5MB limit');
        setTimeout(() => setCampaignError(null), 3000);
        return;
      }
      setSelectedFile(file);
    }
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (file.type !== 'application/pdf') {
        setCampaignError('Only PDF files are allowed');
        setTimeout(() => setCampaignError(null), 3000);
        return;
      }
      
      if (file.size > 5 * 1024 * 1024) { // 5MB in bytes
        setCampaignError('File size exceeds 5MB limit');
        setTimeout(() => setCampaignError(null), 3000);
        return;
      }
      
      setSelectedFile(file);
    }
  };

  const handleCreateCampaign = async (e: React.FormEvent) => {
    e.preventDefault();
    setCampaignError(null);

    // Validate inputs
    if (!campaignName || !selectedBroker) {
      setCampaignError("Please enter campaign name and select a broker.");
      return;
    }

    // Validate ebook selection if hasEbook is checked
    if (hasEbook && !selectedFile) {
      setCampaignError("Please select an ebook PDF file.");
      return;
    }

    try {
      // Set loading state
      setIsLoading(true);

      // First create the campaign to get its ID
      const createdCampaign = await campaignApi.createCampaign({
        campaignName,
        description: campaignDescription,
        campaignDate,
        campaignTime,
        users: selectedBroker,
        hasEbook: hasEbook
      });
      
      console.log("Created campaign:", createdCampaign);
      let campaignId = createdCampaign.id;
      
      // If has ebook, upload it with the campaign ID
      if (hasEbook && selectedFile && campaignId) {
        try {
          setIsUploading(true);
          setUploadProgress(0);
          
          // Create FormData for file upload
          const formData = new FormData();
          formData.append('file', selectedFile);
          formData.append('campaign_id', campaignId);
          
          // Show upload progress
          const progressInterval = setInterval(() => {
            setUploadProgress(prev => {
              const newProgress = prev + Math.random() * 20;
              return newProgress > 90 ? 90 : newProgress;
            });
          }, 500);
          
          // Upload the file
          console.log("Starting ebook upload for campaign:", campaignId);
          const response = await uploadApi.uploadEbook(formData);
          console.log("Upload complete, response:", response);
          
          clearInterval(progressInterval);
          setUploadProgress(100);
        } catch (error: any) {
          console.error("Failed to upload ebook:", error);
          setCampaignError(error.message || "Campaign created but failed to upload ebook. Please try again.");
        } finally {
          setIsUploading(false);
        }
      }

      setCampaignName("");
      setCampaignDescription("");
      setSelectedBroker("");
      setCampaignDate("");
      setHasEbook(false);
      setSelectedFile(null);
      setUploadProgress(0);

      // Close modal
      setIsCampaignModalOpen(false);

      // Refresh campaigns with proper error handling
      try {
        const refreshedCampaigns = await campaignApi.getCampaignUsers();
        console.log("Refreshed campaigns after creation:", refreshedCampaigns);
        setCampaigns(refreshedCampaigns);
      } catch (refreshError: any) {
        console.error("Failed to refresh campaigns:", refreshError);
        setCampaignError(
          "Campaign created but failed to refresh list. Please reload the page."
        );
      }
    } catch (error: any) {
      console.error("Campaign creation error:", error);
      setCampaignError(error.message || "Failed to create campaign");
    } finally {
      setIsLoading(false);
    }
  };

  const getArcheivedCampaigns = async () => {
    try {
      const refreshedCampaigns = await campaignApi.getArcheivedCampaigns();
      setArcheivedCampaigns(refreshedCampaigns);
    } catch (error: any) {
      console.error("Failed to refresh campaigns:", error);
      setCampaignError(
        "Campaign created but failed to refresh list. Please reload the page."
      );
    }
  }

  useEffect(() => {
    if (isArchiveModalOpen) {
      getArcheivedCampaigns();
    }
  }, [isArchiveModalOpen]);

  const unarchiveCampaign = async (campaignId: string) => {
    try {
      await campaignApi.unarchiveCampaign(campaignId);
      getArcheivedCampaigns();
      fetchCampaigns();
    } catch (error: any) {
      console.error("Failed to unarchive campaign:", error);
    }
  }

  // Fetch campaigns with proper ref tracking
  const fetchCampaigns = async () => {
    try {
      setIsLoading(true);
      const refreshedCampaigns = await campaignApi.getCampaignUsers();
      setCampaigns(refreshedCampaigns);
    } catch (error: any) {
      setCampaignError(error.message || "Failed to fetch campaigns");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    // Skip if already fetched
    if (hasFetchedCampaignsRef.current) {
      return;
    }
    
    // Set the ref before async operations to prevent race conditions
    hasFetchedCampaignsRef.current = true;
    
    fetchCampaigns().catch(() => {
      // Reset the flag on error so we can try again
      hasFetchedCampaignsRef.current = false;
    });
  }, []); // Empty dependency array - only run once on mount


  return (
    <div className="w-full mx-auto p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-semibold text-gray-800">Campaigns</h1>

        {userIsAdmin && (
          <div className="flex items-center gap-2">
          <button
            onClick={() => setIsCampaignModalOpen(true)}
            className="inline-flex items-center px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors duration-200"
          >
            <svg
              className="w-5 h-5 mr-2"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2"
                d="M12 4v16m8-8H4"
              />
            </svg>
            Create Campaign
          </button>
           <button
           onClick={() => setIsArchiveModalOpen(true)}
           className="inline-flex items-center px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors duration-200"
         >
           Archive Campaigns
         </button>
         </div>
        )}
      </div>

      {isLoading ? (
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
        </div>
      ) : campaigns.length === 0 ? (
        <div
          className="bg-blue-50 border-l-4 border-blue-500 text-blue-700 p-4 mb-4"
          role="alert"
        >
          <p>No campaigns found.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {campaigns.map((campaign) => (
            <EnhancedCampaignCard key={campaign.id} campaign={campaign} />
          ))}
        </div>
      )}

          {isArchiveModalOpen && (
                  <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-[100] overflow-y-auto">
                    <div className="bg-white rounded-lg shadow-lg w-full max-w-md my-4 mx-auto flex flex-col max-h-[90vh]">
                      <div className="sticky top-0 z-10 px-6 py-4 border-b border-gray-200 bg-white rounded-t-lg flex justify-between items-center">
                        <h3 className="text-lg font-semibold text-gray-800">
                          Archive Campaigns
                        </h3>
                        <button
                type="button"
                onClick={() => setIsArchiveModalOpen(false)}
                className="text-gray-500 hover:text-gray-700 focus:outline-none"
              >
                <svg
                  className="w-5 h-5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="2"
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </button>
                      </div>
                      {archeivedCampaigns.length > 0 ? (
                        <div className="overflow-y-auto p-6 pt-4">
                          {archeivedCampaigns.map((campaign) => (
                            <div key={campaign.id} className="flex justify-between items-center">
                              <p>{campaign.campaignName}</p>
                              <button className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors duration-200" onClick={() => unarchiveCampaign(campaign.id || "")}>
                                Unarchive
                              </button>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className="overflow-y-auto p-6 pt-4">
                          <p>No archived campaigns found.</p>
                        </div>
                      )}
                    </div>
                  </div>
                )}

      {isCampaignModalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-[100] overflow-y-auto">
          <div className="bg-white rounded-lg shadow-lg w-full max-w-md my-4 mx-auto flex flex-col max-h-[90vh]">
            <div className="sticky top-0 z-10 px-6 py-4 border-b border-gray-200 bg-white rounded-t-lg flex justify-between items-center">
              <h3 className="text-lg font-semibold text-gray-800">
                Create New Campaign
              </h3>
              <button
                type="button"
                onClick={() => setIsCampaignModalOpen(false)}
                className="text-gray-500 hover:text-gray-700 focus:outline-none"
              >
                <svg
                  className="w-5 h-5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="2"
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </button>
            </div>

            <div className="overflow-y-auto p-6 pt-4">
              <form onSubmit={handleCreateCampaign} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-0.5">
                    Campaign Name
                  </label>
                  <input
                    type="text"
                    value={campaignName}
                    onChange={(e) => setCampaignName(e.target.value)}
                    required
                    className="w-full py-1.5 px-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-0.5">
                    Description
                  </label>
                  <textarea
                    value={campaignDescription}
                    onChange={(e) => setCampaignDescription(e.target.value)}
                    className="w-full py-1.5 px-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    rows={3}
                    placeholder="Enter campaign description (optional)"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-0.5">
                    Campaign Date
                  </label>
                  <input
                    type="date"
                    value={campaignDate}
                    min={getBrisbaneDate()}
                    onChange={(e) => setCampaignDate(e.target.value)}
                    className="w-full py-1.5 px-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-0.5">
                    Campaign Time
                  </label>
                  <input
                    type="time"
                    value={campaignTime}
                    onChange={(e) => setCampaignTime(e.target.value)}
                    className="w-full py-1.5 px-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-0.5">
                    Assign to Broker
                  </label>
                  <select
                    value={selectedBroker}
                    onChange={(e) => setSelectedBroker(e.target.value)}
                    required
                    className="w-full py-1.5 px-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="">Select a broker</option>
                    {brokers.map((broker) => (
                      <option key={broker.id} value={broker.id}>
                        {broker.name} ({broker.email})
                      </option>
                    ))}
                  </select>
                </div>

                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="hasEbook"
                    name="hasEbook"
                    checked={hasEbook}
                    onChange={(e) => setHasEbook(e.target.checked)}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <label
                    htmlFor="hasEbook"
                    className="text-sm font-medium text-gray-700"
                  >
                    Include Ebook
                  </label>
                </div>

                {hasEbook && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Upload Ebook (PDF)
                    </label>
                    <div
                      className={`border-2 border-dashed rounded-lg p-2 flex flex-col items-center justify-center bg-gray-50 transition-colors ${
                        isDragging
                          ? "border-blue-500 bg-blue-50"
                          : "border-gray-300"
                      }`}
                      onDragOver={handleDragOver}
                      onDragLeave={handleDragLeave}
                      onDrop={handleDrop}
                      style={{ minHeight: "80px" }}
                    >
                      <div className="flex items-center justify-center gap-2">
                        <svg
                          className="h-6 w-6 text-gray-400"
                          xmlns="http://www.w3.org/2000/svg"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                          />
                        </svg>
                        <div>
                          <p className="text-xs text-gray-600">
                            <label
                              htmlFor="file-upload"
                              className="text-blue-600 hover:underline cursor-pointer"
                            >
                              Browse
                            </label>{" "}
                            or drag PDF
                          </p>
                          <p className="text-xs text-gray-500">Max: 5MB</p>
                        </div>
                      </div>
                      <input
                        id="file-upload"
                        name="file-upload"
                        type="file"
                        accept=".pdf"
                        onChange={handleFileChange}
                        required={hasEbook}
                        className="hidden"
                      />
                      {selectedFile && (
                        <div className="mt-1 text-xs text-gray-700 bg-blue-50 px-2 py-0.5 rounded-full w-full text-center truncate">
                          {selectedFile.name.length > 25
                            ? selectedFile.name.substring(0, 25) + "..."
                            : selectedFile.name}
                        </div>
                      )}

                      {isUploading && (
                        <div className="w-full mt-1">
                          <div className="w-full bg-gray-200 rounded-full h-1">
                            <div
                              className="bg-blue-600 h-1 rounded-full transition-all duration-300"
                              style={{ width: `${uploadProgress}%` }}
                            ></div>
                          </div>
                          <p className="text-xs text-gray-500 text-center">
                            {Math.round(uploadProgress)}%
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                )}
                
                {campaignError && (
                  <div className="p-2 bg-red-50 border border-red-200 rounded-lg">
                    <p className="text-sm text-red-600">{campaignError}</p>
                  </div>
                )}

                <div className="flex justify-end">
                  <button
                    type="submit"
                    disabled={isLoading}
                    className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors duration-200 disabled:opacity-50"
                  >
                    {isLoading ? "Creating..." : "Create Campaign"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CampaignsAdmin;
