import React from 'react';
import { Campaign } from '../types/campaign';

interface CampaignCardProps {
  campaign: Campaign;
}

const CampaignCard: React.FC<CampaignCardProps> = ({ campaign }) => {

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

  return (
    <div className="bg-white rounded-xl shadow-lg border border-gray-200 flex flex-col min-h-[180px] relative overflow-hidden">
      {/* Sticky Card Header */}
      <div className="sticky top-0 z-10 bg-gradient-to-r from-blue-50 to-white px-4 py-3 border-b border-gray-100 flex items-center justify-between rounded-t-xl">
        <h3 className="text-lg font-bold text-blue-700 truncate">{campaign.campaignName}</h3>
      </div>asdasd
      
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
  );
};

export default CampaignCard; 