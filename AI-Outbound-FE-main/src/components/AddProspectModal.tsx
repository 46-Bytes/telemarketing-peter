import React, { useState, useEffect } from 'react';
import { userApi, campaignApi } from '../api/api';
import { useAuth } from '../contexts/AuthContext';
import { Campaign } from '../types/campaign';

// Country codes for common countries
const countryCodes = [
  { code: '+1', country: 'USA/Canada' },
  { code: '+44', country: 'UK' },
  { code: '+92', country: 'Pakistan' },
  { code: '+91', country: 'India' },
  { code: '+61', country: 'Australia' },
  { code: '+49', country: 'Germany' },
  { code: '+33', country: 'France' },
  { code: '+81', country: 'Japan' },
  { code: '+86', country: 'China' },
  { code: '+52', country: 'Mexico' },
  { code: '+55', country: 'Brazil' },
  { code: '+27', country: 'South Africa' },
  { code: '+65', country: 'Singapore' },
  { code: '+971', country: 'UAE' },
  { code: '+234', country: 'Nigeria' },
  { code: '+254', country: 'Kenya' },
];

interface AddProspectModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

const AddProspectModal: React.FC<AddProspectModalProps> = ({ isOpen, onClose, onSuccess }) => {
  const { user } = useAuth();
  const [newProspect, setNewProspect] = useState({
    name: '',
    phoneNumber: '',
    businessName: '',
    email: ""
  });
  const [countryCode, setCountryCode] = useState('+61');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [selectedCampaignId, setSelectedCampaignId] = useState<string>('');
  const [isLoadingCampaigns, setIsLoadingCampaigns] = useState<boolean>(false);

  // Fetch campaigns when the modal is opened
  useEffect(() => {
    if (isOpen) {
      const fetchCampaigns = async () => {
        setIsLoadingCampaigns(true);
        try {
          const campaignData = await campaignApi.getCampaignUsers();
          const userName = localStorage.getItem("userName");
          const filteredCampaignData = campaignData.filter((campaign: Campaign) => campaign.owner_name === userName);
          setCampaigns(userName === "outboundcallagent" ? campaignData : filteredCampaignData);
          const getURl = window.location.href;
          const getUrlId = getURl.split("/").pop();
          if (campaignData.length > 0) {
            setSelectedCampaignId(getUrlId || "");
          }
        } catch (error) {
          console.error('Error fetching campaign users:', error);
          setFormError('Failed to load campaign users. Please try again.');
        } finally {
          setIsLoadingCampaigns(false);
        }
      };

      fetchCampaigns();
    }
  }, [isOpen]);

  // Helper function to get campaign name from ID
  const getCampaignNameFromId = (id: string): string => {
    const campaign = campaigns.find(c => c.id === id);
    return campaign ? campaign.campaignName : '';
  };

  const handleAddProspect = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);
    setIsSubmitting(true);

    try {
      // Get the campaign name from the selected ID
      const campaignName = getCampaignNameFromId(selectedCampaignId);
      
      // Format phone number with country code
      const formattedPhoneNumber = `${countryCode}${newProspect.phoneNumber.trim().replace(/^0+/, '')}`;
      
      // Format data as expected by the API
      const userData = [{
        name: newProspect.name.trim() || undefined,
        phoneNumber: formattedPhoneNumber,
        email: newProspect.email.trim(),
        businessName: newProspect.businessName.trim(),
        campaignId: selectedCampaignId,
        campaignName: campaignName // Include both for backward compatibility
      }];

      const getUserName = campaigns.find((campaign: Campaign) => campaign.id === selectedCampaignId)?.owner_name;
      // Get the owner name from AuthContext
      const ownerName = getUserName || user?.name || 'Unknown User';
      console.log('Adding prospect with owner:', ownerName, 'to campaign ID:', selectedCampaignId, 'name:', campaignName); // Debug log
      
      // Pass both the selected campaign ID and name
      await userApi.uploadUsers(userData, "", campaignName, ownerName, selectedCampaignId);
      
      // Reset form and close modal
      setNewProspect({
        name: '',
        phoneNumber: '',
        businessName: '',
        email: ""
      });
      
      onSuccess();
      onClose();
      
    } catch (err) {
      console.error('Error adding prospect:', err);
      setFormError(err instanceof Error ? err.message : 'Failed to add prospect');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setNewProspect(prev => ({
      ...prev,
      [name]: value
    }));
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-[150]">
      <div className="bg-white rounded-xl p-6 max-w-lg w-full">
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-xl font-semibold text-gray-800">Add New Prospect</h3>
          <button onClick={() => {
            setNewProspect({
              name: '',
              phoneNumber: '',
              businessName: '',
              email: ""
            });
            onClose();
          }} className="text-gray-500 hover:text-gray-700">✕</button>
        </div>
        
        {formError && (
          <div className="p-4 bg-red-50 border border-red-100 rounded-lg mb-4">
            <p className="text-sm text-red-600">{formError}</p>
          </div>
        )}
        
        <form onSubmit={handleAddProspect}>
          <div className="space-y-4">
            <div>
              <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">Name</label>
              <input
                type="text"
                id="name"
                name="name"
                value={newProspect.name}
                onChange={handleInputChange}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg"
                placeholder="Optional"
              />
            </div>
            
            <div>
              <label htmlFor="phoneNumber" className="block text-sm font-medium text-gray-700 mb-1">Phone Number *</label>
              <div className="flex">
                <select
                  value={countryCode}
                  onChange={(e) => setCountryCode(e.target.value)}
                  className="px-1 py-2 border border-gray-300 rounded-l-lg bg-gray-50 text-gray-700"
                >
                  {countryCodes.map((country) => (
                    <option key={country.code} value={country.code}>
                      {country.code} ({country.country})
                    </option>
                  ))}
                </select>
                <input
                  type="tel"
                  id="phoneNumber"
                  name="phoneNumber"
                  value={newProspect.phoneNumber}
                  onChange={handleInputChange}
                  placeholder="Phone number"
                  className="w-full px-4 py-2 border border-gray-300 rounded-r-lg"
                  required
                />
              </div>
              <p className="text-xs text-gray-500 mt-1">
                Enter phone number without country code. Example: For US number (123) 456-7890, enter 1234567890
              </p>
            </div>
            
            <div>
              <label htmlFor="businessName" className="block text-sm font-medium text-gray-700 mb-1">Business Name</label>
              <input
                type="text"
                id="businessName"
                name="businessName"
                value={newProspect.businessName}
                onChange={handleInputChange}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg"
              />
            </div>

            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">Email</label>
              <input
                type="text"
                id="email"
                name="email"
                value={newProspect.email}
                onChange={handleInputChange}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg"
              />
            </div>
            
            <div>
              <label htmlFor="campaign-select" className="block text-sm font-medium text-gray-700 mb-1">
                Campaign *
              </label>
              {isLoadingCampaigns ? (
                <div className="flex items-center">
                  <div className="animate-spin h-4 w-4 mr-2 border-b-2 border-gray-500"></div>
                  <span className="text-sm text-gray-500">Loading campaigns...</span>
                </div>
              ) : campaigns.length > 0 ? (
                <select
                  id="campaign-select"
                  value={selectedCampaignId}
                  onChange={(e) => setSelectedCampaignId(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg"
                  required
                >
                  {campaigns.map((campaign) => (
                    <option key={campaign.id || campaign.campaignName} value={campaign.id || ''}>
                      {campaign.campaignName}
                    </option>
                  ))}
                </select>
              ) : (
                <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-md text-sm text-yellow-700">
                  No campaign groups found. Please create a campaign group first.
                </div>
              )}
            </div>
          </div>
          
          <div className="mt-6 flex justify-end space-x-3">
            <button type="button" onClick={onClose} className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg">
              Cancel
            </button>
            <button 
              type="submit" 
              className="px-4 py-2 bg-blue-600 text-white rounded-lg" 
              disabled={isSubmitting || campaigns.length === 0}
            >
              {isSubmitting ? 'Adding...' : 'Add Prospect'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AddProspectModal; 
