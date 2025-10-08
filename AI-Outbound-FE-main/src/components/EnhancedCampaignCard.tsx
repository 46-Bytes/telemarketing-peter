import React, { useState } from 'react';
import { Campaign } from '../types/campaign';
import FileUpload from './FileUpload';
import Papa from 'papaparse';
import { userApi } from '../api/api';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';

interface EnhancedCampaignCardProps {
  campaign: Campaign;
}

interface CsvData {
  name?: string;
  phoneNumber: string;
  businessName: string;
}

const EnhancedCampaignCard: React.FC<EnhancedCampaignCardProps> = ({ campaign }) => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [isCsvModalOpen, setIsCsvModalOpen] = useState(false);
  const [csvData, setCsvData] = useState<CsvData[]>([]);
  const [uploadedFileName, setUploadedFileName] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitStatus, setSubmitStatus] = useState<'idle' | 'success' | 'error'>('idle');

  // Format date with fallback
  const formatDate = (dateString?: string) => {
    if (!dateString) return <span className="italic text-gray-400">No date</span>;
    
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
    if (csvData.length === 0 || !campaign.id) return;

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
      
      // Pass the campaign ID and name
      await userApi.uploadUsers(
        dataWithCampaign, 
        "", 
        campaign.campaignName || "", 
        user?.name || 'Unknown User', 
        campaign.id || ""
      );
      
      setSubmitStatus('success');
      
      // Close modal after a delay on success
      setTimeout(() => {
        setIsCsvModalOpen(false);
        // Reset CSV data
        setCsvData([]);
        setUploadedFileName(null);
        setUploadStatus('idle');
        setSubmitStatus('idle');
      }, 2000);
    } catch (error) {
      console.error('Error uploading prospects:', error);
      setSubmitStatus('error');
      setErrorMessage(error instanceof Error ? error.message : 'Failed to upload prospects');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCardClick = () => {
    // Check if we're in an admin route
    const isAdminRoute = window.location.pathname.includes('/admin/');
    
    // Navigate to the appropriate campaign details page
    if (isAdminRoute) {
      navigate(`/admin/campaign/${campaign.id}`);
    } else {
      navigate(`/campaign/${campaign.id}`);
    }
    
    console.log(`Navigating to ${isAdminRoute ? 'admin' : 'user'} campaign details for campaign ${campaign.id}`);
  };
  
  return (
    <>
      <div 
        className="bg-white rounded-xl shadow-lg border border-gray-200 flex flex-col min-h-[180px] relative overflow-hidden cursor-pointer hover:shadow-xl transition-all duration-200"
        onClick={handleCardClick}
      >
        {/* Sticky Card Header */}
        <div className="sticky top-0 z-10 bg-gradient-to-r from-blue-50 to-white px-4 py-3 border-b border-gray-100 flex items-center justify-between rounded-t-xl">
          <h3 className="text-lg font-bold text-blue-700 truncate">{campaign.campaignName}</h3>
        </div>
        
        <div className="flex-1 flex flex-col justify-between p-4">
          <div className="space-y-2">
            {campaign.description && (
              <p className="text-gray-600">{campaign.description}</p>
            )}
            
            <div className="flex justify-between text-sm">
              <span className="font-medium text-gray-700">Campaign Date:</span>
              <span className="text-gray-600">{formatDate(campaign.campaignDate)}</span>
            </div>
            
            <div className="flex justify-between text-sm">
              <span className="font-medium text-gray-700">Created:</span>
              <span className="text-gray-600">{formatDate(campaign.created_at)}</span>
            </div>

            <div className="flex justify-between text-sm">
              <span className="font-medium text-gray-700">Broker Email:</span>
              <span className="text-gray-600">{campaign.owner_email}</span>
            </div>

            <div className="flex justify-between text-sm">
              <span className="font-medium text-gray-700">Broker:</span>
              <span className="text-gray-600">{campaign.owner_name}</span>
            </div>
          </div>
        </div>
      </div>

      {/* CSV Upload Modal */}
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
    </>
  );
};

export default EnhancedCampaignCard; 