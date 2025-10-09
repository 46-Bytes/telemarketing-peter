import { useEffect, useState } from 'react';
import { userApi, campaignApi } from '../api/api';
import AddProspectModal from './AddProspectModal';
import { useAuth } from '../contexts/AuthContext';
import { Campaign } from '../types/campaign';

interface ProspectDetails {
  name: string;
  phoneNumber: string;
  email: string | null;
  status: string;
  isCallBack: boolean | null;
  callBackDate: string | null;
  isEbook: boolean | null;
  campaignName: string;
  campaignId: string | null;
  businessName?: string;
  ownerName?: string;
  scheduledCallDate: string | null;
  userId?: string;
  appointment: {
    appointmentInterest: boolean | null;
    appointmentDateTime: string | null;
    meetingLink?: string | null;
    appointmentType?: string | null;
  };
  calls: Array<{
    callId?: string;
    batchId?: string;
    timestamp: string;
    status: string;
    duration: number;
    callSummary: string;
  }>;
}

interface Prospect {
  name: string;
  phoneNumber: string;
  status: string;
  businessName?: string;
  scheduledCallDate: string | null;
  ownerName?: string;
  userId?: string;
  campaignName?: string;
  campaignId?: string;
}

const ProspectSummary = () => {
  const { user } = useAuth();
  const [prospects, setProspects] = useState<Prospect[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [selectedProspect, setSelectedProspect] = useState<ProspectDetails | null>(null);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [isLoading, setIsLoading] = useState({
    prospects: true,
    details: false,
    campaigns: true
  });
  const [selectedStatus, setSelectedStatus] = useState<string>('');
  const [selectedOwner, setSelectedOwner] = useState<string>('');
  const [selectedCampaign, setSelectedCampaign] = useState<string>('');
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [isCallingUser, setIsCallingUser] = useState<string | null>(null);
  const [callError, setCallError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [allProspects, setAllProspects] = useState<Prospect[]>([]);
  const [isAddProspectModalOpen, setIsAddProspectModalOpen] = useState(false);

  const statusOptions = ['new', 'contacted', 'picked_up', 'error'];
  
  // Fetch campaigns
  useEffect(() => {
    const fetchCampaigns = async () => {
      setIsLoading(prev => ({ ...prev, campaigns: true }));
      try {
        const campaignData = await campaignApi.getCampaignUsers();
        setCampaigns(campaignData);
      } catch (error) {
        console.error('Error fetching campaign users:', error);
      } finally {
        setIsLoading(prev => ({ ...prev, campaigns: false }));
      }
    };

    fetchCampaigns();
  }, []);

  useEffect(() => {
    const fetchProspects = async () => {
      setIsLoading(prev => ({ ...prev, prospects: true }));
      try {
        const response = await userApi.getProspectsSummaryInfo();
        console.log("response for getProspectsSummaryInfo", response);
        let fetchedProspects = response.prospects_summary;

        // Filter prospects based on user role
        // if (user && user.role === 'user') {
        //   fetchedProspects = fetchedProspects.filter(
        //     (prospect: Prospect) => prospect.userId === user.id
        //   );
        // }

        setAllProspects(fetchedProspects);

        let filteredProspects = fetchedProspects;

        // Apply status filter
        if (selectedStatus) {
          filteredProspects = filteredProspects.filter(
            (prospect: Prospect) => prospect.status?.toLowerCase() === selectedStatus.toLowerCase()
          );
        }

        // Apply owner filter
        if (selectedOwner) {
          filteredProspects = filteredProspects.filter(
            (prospect: Prospect) => prospect.ownerName === selectedOwner
          );
        }
        
        // Apply campaign filter
        if (selectedCampaign) {
          filteredProspects = filteredProspects.filter(
            (prospect: Prospect) => prospect.campaignId === selectedCampaign || prospect.campaignName === selectedCampaign
          );
        }

        setProspects(filteredProspects);
      } catch (err) {
        console.error('Error fetching prospects data:', err);
        setError('Failed to fetch prospects data');
      } finally {
        setIsLoading(prev => ({ ...prev, prospects: false }));
      }
    };

    fetchProspects();
  }, [selectedStatus, selectedOwner, selectedCampaign, user]);

  // Filter prospects based on search query and status
  useEffect(() => {
    if (!allProspects.length) return;

    let filtered = [...allProspects];

    // Apply status filter
    if (selectedStatus) {
      filtered = filtered.filter(
        (prospect: Prospect) => prospect.status?.toLowerCase() === selectedStatus.toLowerCase()
      );
    }

    // Apply owner filter
    if (selectedOwner) {
      filtered = filtered.filter(
        (prospect: Prospect) => prospect.ownerName === selectedOwner
      );
    }
    
    // Apply campaign filter
    if (selectedCampaign) {
      filtered = filtered.filter(
        (prospect: Prospect) => prospect.campaignId === selectedCampaign || prospect.campaignName === selectedCampaign
      );
    }

    // Apply search filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase().trim();
      console.log('Applying search filter:', { 
        query, 
        fields: 'name, phoneNumber, businessName, ownerName',
        totalProspects: filtered.length
      });
      
      filtered = filtered.filter(
        (prospect: Prospect) =>
          prospect.name?.toLowerCase().includes(query) ||
          prospect.phoneNumber?.toLowerCase().includes(query) ||
          prospect.businessName?.toLowerCase().includes(query) ||
          prospect.ownerName?.toLowerCase().includes(query)
      );
      
      console.log('After search filter applied:', { 
        matchingProspects: filtered.length,
        firstMatch: filtered.length > 0 ? {
          name: filtered[0].name,
          owner: filtered[0].ownerName
        } : null
      });
    }

    setProspects(filtered);
  }, [searchQuery, selectedStatus, selectedOwner, selectedCampaign, allProspects]);

  const getStatusColor = (status: string | undefined) => {
    const statusColors = {
      picked_up: 'bg-gradient-to-r from-emerald-400 via-green-500 to-teal-600 text-white shadow-[0_0_15px_rgba(16,185,129,0.35)]',
      error: 'bg-gradient-to-r from-rose-500 via-red-500 to-pink-600 text-white shadow-[0_0_15px_rgba(239,68,68,0.35)]',
      default: 'bg-gradient-to-r from-slate-400 to-slate-600 text-white'
    };

    if (!status) return statusColors.default;

    return statusColors[status.toLowerCase() as keyof typeof statusColors] || statusColors.default;
  };

  // const handleViewDetails = async (phoneNumber: string) => {
  //   setIsLoading(prev => ({ ...prev, details: true }));
  //   try {
  //     const details = await userApi.getProspectDetails(phoneNumber);
  //     setSelectedProspect(details);
  //     setIsDialogOpen(true);
  //   } catch (err) {
  //     console.error('Error fetching prospect details:', err);
  //     // Optionally show an error toast/message here
  //   } finally {
  //     setIsLoading(prev => ({ ...prev, details: false }));
  //   }
  // };

  const handleInitiateCall = async (phoneNumber: string) => {
    setIsCallingUser(phoneNumber);
    setCallError(null);

    try {
      const response = await userApi.initiateCall(phoneNumber, '');
      console.log('Call initiated successfully:', response);

      // After successful call initiation, refresh the prospects list
      const refreshResponse = await userApi.getProspectsSummaryInfo();

      const refreshedProspects = refreshResponse.prospects_summary;
      setAllProspects(refreshedProspects);

      let filteredProspects = refreshedProspects;

      // Apply status filter
      if (selectedStatus) {
        filteredProspects = filteredProspects.filter(
          (prospect: Prospect) => prospect.status?.toLowerCase() === selectedStatus.toLowerCase()
        );
      }

      // Apply owner filter
      if (selectedOwner) {
        filteredProspects = filteredProspects.filter(
          (prospect: Prospect) => prospect.ownerName === selectedOwner
        );
      }
      
      // Apply campaign filter
      if (selectedCampaign) {
        filteredProspects = filteredProspects.filter(
          (prospect: Prospect) => prospect.campaignId === selectedCampaign || prospect.campaignName === selectedCampaign
        );
      }

      // Apply search filter
      if (searchQuery.trim()) {
        const query = searchQuery.toLowerCase().trim();
        filteredProspects = filteredProspects.filter(
          (prospect: Prospect) =>
            prospect.name?.toLowerCase().includes(query) ||
            prospect.phoneNumber?.toLowerCase().includes(query) ||
            prospect.businessName?.toLowerCase().includes(query) ||
            prospect.ownerName?.toLowerCase().includes(query)
        );
      }

      setProspects(filteredProspects);

      // Show success toast or message
      // You can implement a toast notification here if needed
    } catch (err) {
      console.error('Error initiating call:', err);
      setCallError(err instanceof Error ? err.message : 'Failed to initiate call');
    } finally {
      setIsCallingUser(null);
    }
  };

  const getUniqueOwners = () => {
    if (!allProspects.length) return [];
    
    const owners = allProspects
      .map(prospect => prospect.ownerName)
      .filter((ownerName): ownerName is string => 
        ownerName !== undefined && ownerName !== null && ownerName !== ''
      );
    
    return [...new Set(owners)].sort();
  };

  // Add this function to render the campaign dropdown
  const renderCampaignFilter = () => {
    return (
      <select
        value={selectedCampaign}
        onChange={(e) => setSelectedCampaign(e.target.value)}
        className="px-4 py-2 border border-slate-200 rounded-lg bg-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        <option value="">All Campaign Groups</option>
        {campaigns.map((campaign) => (
          <option key={campaign.id || campaign.campaignName} value={campaign.id || ''}>
            {campaign.campaignName}
          </option>
        ))}
      </select>
    );
  };

  if (isLoading.prospects) {
    return (
      <div className="min-h-[400px] flex items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100">
        <div className="relative">
          <div className="animate-ping absolute h-16 w-16 rounded-full bg-gray-500 opacity-20"></div>
          <div className="animate-spin relative rounded-full h-16 w-16 border-t-4 border-b-4 border-gray-500"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-[200px] flex items-center justify-center">
        <div className="text-center">
          <p className="text-2xl font-bold bg-gradient-to-r from-rose-500 to-pink-600 text-transparent bg-clip-text mb-4">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="mt-4 px-6 py-3 bg-gradient-to-r from-rose-500 to-pink-600 text-white rounded-full 
            hover:shadow-[0_0_20px_rgba(239,68,68,0.4)] transition-all duration-300 transform hover:scale-105"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }
  return (
    <div className="bg-white rounded-xl shadow-lg overflow-hidden border border-slate-200">
      <div className="p-8">
        <div className="flex justify-between items-center mb-8">
          <h2 className="text-xl font-semibold text-gray-600 bg-gradient-to-r bg-clip-text">
            Prospects Call Status
          </h2>
          <div className="flex items-center gap-4">
            <div className="relative">
              <input
                type="text"
                placeholder="Search by name, phone, business, or owner"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="px-4 py-2 pl-10 border border-slate-200 rounded-lg bg-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 w-64"
              />
              <svg
                className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="px-4 py-2 border border-slate-200 rounded-lg bg-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Statuses</option>
              {statusOptions.map((status) => (
                <option key={status} value={status}>
                  {status.replace('_', ' ').toUpperCase()}
                </option>
              ))}
            </select>
            <select
              value={selectedOwner}
              onChange={(e) => setSelectedOwner(e.target.value)}
              className="px-4 py-2 border border-slate-200 rounded-lg bg-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Owners</option>
              {getUniqueOwners().map((owner) => (
                <option key={owner} value={owner}>
                  {owner}
                </option>
              ))}
            </select>
            {/* Add campaign dropdown */}
            {renderCampaignFilter()}
            <button
              onClick={() => setIsAddProspectModalOpen(true)}
              className="px-4 py-2 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-full
              hover:shadow-[0_0_15px_rgba(59,130,246,0.35)] transition-all duration-300 text-sm font-medium
              flex items-center gap-2"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
              Add Prospect
            </button>
          </div>
        </div>

        {/* Add call error notification if there's an error */}
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

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gradient-to-r from-slate-100 to-slate-50">
              <tr>
                <th className="px-6 py-4 text-left text-xs font-bold text-slate-600 uppercase tracking-wider">
                  Name
                </th>
                <th className="px-6 py-4 text-left text-xs font-bold text-slate-600 uppercase tracking-wider">
                  Phone Number
                </th>
                <th className="px-6 py-4 text-left text-xs font-bold text-slate-600 uppercase tracking-wider">
                  Business Name
                </th>
                <th className="px-6 py-4 text-left text-xs font-bold text-slate-600 uppercase tracking-wider">
                  Owner Name
                </th>
                <th className="px-6 py-4 text-left text-xs font-bold text-slate-600 uppercase tracking-wider">
                  Campaign
                </th>
                <th className="px-6 py-4 text-left text-xs font-bold text-slate-600 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-4 text-left text-xs font-bold text-slate-600 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {(prospects || []).map((prospect, index) => (
                <tr
                  key={`${prospect.phoneNumber}-${index}`}
                  className={`${index % 2 === 0 ? 'bg-white' : 'bg-slate-100/50'
                    } hover:bg-gradient-to-r hover:from-slate-100 hover:to-slate-50 transition-colors duration-150`}
                >
                  <td className="px-6 py-5 whitespace-nowrap">
                    <div className="text-sm font-semibold text-slate-900">{prospect.name || 'N/A'}</div>
                  </td>
                  <td className="px-6 py-5 whitespace-nowrap">
                    <div className="text-sm text-slate-600">{prospect.phoneNumber || 'N/A'}</div>
                  </td>
                  <td className="px-6 py-5 whitespace-nowrap">
                    <div className="text-sm text-slate-600">{prospect.businessName || 'N/A'}</div>
                  </td>
                  <td className="px-6 py-5 whitespace-nowrap">
                    <div className="text-sm text-slate-600">{prospect.ownerName || 'N/A'}</div>
                  </td>
                  <td className="px-6 py-5 whitespace-nowrap">
                    <div className="text-sm text-slate-600">{prospect.campaignName || 'N/A'}</div>
                  </td>
                  <td className="px-6 py-5 whitespace-nowrap">
                    <span className={`px-4 py-2 rounded-full text-xs font-medium ${getStatusColor(prospect.status)}`}>
                      {(prospect.status || 'Unknown').replace('_', ' ').toUpperCase()}
                    </span>
                  </td>
                  <td className="px-6 py-5 whitespace-nowrap">
                    <div className="flex space-x-2">
                      {/* <button
                        onClick={() => prospect.phoneNumber && handleViewDetails(prospect.phoneNumber)}
                        disabled={!prospect.phoneNumber || isLoading.details}
                        className="px-4 py-2 bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-full 
                        hover:shadow-[0_0_15px_rgba(59,130,246,0.35)] transition-all duration-300 text-xs font-medium
                        disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {isLoading.details && selectedProspect?.phoneNumber === prospect.phoneNumber ? 'Loading...' : 'View Details'}
                      </button> */}

                     {user?.role === "super_admin" && <button
                        onClick={() => prospect.phoneNumber && handleInitiateCall(prospect.phoneNumber)}
                        disabled={!prospect.phoneNumber || isCallingUser === prospect.phoneNumber}
                        className="px-4 py-2 bg-gradient-to-r from-green-500 to-green-600 text-white rounded-full
                        hover:shadow-[0_0_15px_rgba(34,197,94,0.35)] transition-all duration-300 text-xs font-medium
                        disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {isCallingUser === prospect.phoneNumber ? 'Calling...' : 'Call Now asd'}
                      </button>}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {/* No results message - moved below the table */}
          {prospects.length === 0 && !isLoading.prospects && (
            <div className="text-center py-10">
              <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <h3 className="mt-2 text-sm font-medium text-gray-900">No prospects found</h3>
              <p className="mt-1 text-sm text-gray-500">Try adjusting your search or filter to find what you're looking for.</p>
            </div>
          )}
        </div>
      </div>

      {/* Details Dialog */}
      {isDialogOpen && selectedProspect && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl px-6 max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <div className="sticky top-0 z-10 bg-gradient-to-r from-slate-50 to-white border-b border-slate-200 flex justify-between items-center mb-6 px-6 py-4 rounded-t-xl shadow-sm">
              <h3 className="text-xl font-semibold text-gray-800">Prospect Details</h3>
              <button
                onClick={() => {
                  setIsDialogOpen(false);
                  setSelectedProspect(null); // Clean up selected prospect when closing
                }}
                className="w-8 h-8 flex items-center justify-center rounded-full text-gray-500 hover:text-white hover:bg-rose-500 transition-colors duration-200"
                aria-label="Close"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div className="space-y-6">
              {/* Basic Information Card */}
              <div className="bg-gradient-to-r from-slate-50 to-white p-6 rounded-xl border border-slate-100">
                <h4 className="text-lg font-semibold text-slate-800 mb-4">Basic Information</h4>
                <div className="grid grid-cols-2 gap-6">
                  <div className="space-y-1">
                    <p className="text-sm font-medium text-slate-400">Name</p>
                    <p className="text-base font-semibold text-slate-700">{selectedProspect.name || 'N/A'}</p>
                  </div>
                  <div className="space-y-1">
                    <p className="text-sm font-medium text-slate-400">Phone Number</p>
                    <p className="text-base font-semibold text-slate-700">{selectedProspect.phoneNumber || 'N/A'}</p>
                  </div>
                  <div className="space-y-1">
                    <p className="text-sm font-medium text-slate-400">Status</p>
                    <span className={`inline-block px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(selectedProspect.status)}`}>
                      {(selectedProspect.status || 'Unknown').replace('_', ' ').toUpperCase()}
                    </span>
                  </div>
                  <div className="space-y-1">
                    <p className="text-sm font-medium text-slate-400">Business Name</p>
                    <p className="text-base font-semibold text-slate-700">{selectedProspect.businessName || 'N/A'}</p>
                  </div>
                  <div className="space-y-1">
                    <p className="text-sm font-medium text-slate-400">Campaign</p>
                    <p className="text-base font-semibold text-slate-700">{selectedProspect.campaignName || 'N/A'}</p>
                  </div>
                  <div className="space-y-1">
                    <p className="text-sm font-medium text-slate-400">Owner</p>
                    <p className="text-base font-semibold text-slate-700">
                      {selectedProspect.ownerName || user?.name || 'N/A'}
                    </p>
                  </div>
                </div>
              </div>

              {/* Engagement Details Card */}
              <div className="bg-gradient-to-r from-slate-50 to-white p-6 rounded-xl border border-slate-100">
                <h4 className="text-lg font-semibold text-slate-800 mb-4">Engagement Details</h4>
                <div className="grid grid-cols-2 gap-6">
                  <div className="space-y-1">
                    <p className="text-sm font-medium text-slate-400">Call Back</p>
                    <p className="text-base font-semibold text-slate-700">
                      {selectedProspect.isCallBack && selectedProspect.callBackDate
                        ? new Date(selectedProspect.callBackDate).toLocaleDateString()
                        : 'Not interested'}
                    </p>
                  </div>
                  <div className="space-y-1">
                    <p className="text-sm font-medium text-slate-400">E-Book Interest</p>
                    <p className="text-base font-semibold text-slate-700">
                      {selectedProspect.isEbook === null ? 'Not specified' : selectedProspect.isEbook ? 'Interested' : 'Not interested'}
                    </p>
                  </div>
                  <div className="col-span-2 space-y-1">
                    <p className="text-sm font-medium text-slate-400">Appointment</p>
                    <p className="text-base font-semibold text-slate-700">
                      {selectedProspect.appointment?.appointmentInterest ? (
                        selectedProspect.appointment.appointmentDateTime ? (
                          <span className="inline-flex items-center gap-2">
                            <svg className="w-4 h-4 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                            </svg>
                            {new Date(selectedProspect.appointment.appointmentDateTime).toLocaleString('en-GB', {
                              timeZone: 'UTC',
                              year: 'numeric',
                              month: 'long',
                              day: 'numeric',
                              hour: 'numeric',
                              minute: 'numeric',
                              hour12: true
                            })}
                            {selectedProspect.appointment.appointmentType && (
                              <span className="ml-1 text-sm font-medium text-blue-600 capitalize">
                                ({selectedProspect.appointment.appointmentType})
                              </span>
                            )}
                          </span>
                        ) : 'Interested (No date set)'
                      ) : 'Not interested'}
                    </p>
                  </div>
                </div>
              </div>

              {/* Campaign List Card */}
              <div className="bg-gradient-to-r from-slate-50 to-white p-6 rounded-xl border border-slate-100">
                <h4 className="text-lg font-semibold text-slate-800 mb-4">Associated Upload Type</h4>
                <div className="flex flex-wrap gap-2">
                  {selectedProspect.campaignName ? (
                    <span
                      className="px-4 py-2 bg-blue-50 text-blue-600 rounded-lg text-sm font-medium inline-flex items-center gap-2 hover:bg-blue-100 transition-colors duration-200"
                    >
                      <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                      </svg>
                      {selectedProspect.campaignName}
                    </span>
                  ) : (
                    <p className="text-sm text-slate-500 italic">No upload type associated</p>
                  )}
                </div>
              </div>

              {/* Call History Card */}
              <div className="bg-gradient-to-r from-slate-50 to-white p-6 rounded-xl border border-slate-100">
                <h4 className="text-lg font-semibold text-slate-800 mb-4">Call History</h4>
                <div className="space-y-3">
                  {(selectedProspect.calls || []).length > 0 ? (
                    [...(selectedProspect?.calls || [])].reverse().map((call:any, index) => (
                      <div key={call.callId || call.batchId || index} className="bg-white p-4 rounded-lg border border-slate-100 hover:shadow-md transition-shadow duration-200">
                        <div className="grid grid-cols-2 gap-4 mb-2">
                          <div className="space-y-1">
                            <p className="text-sm font-medium text-slate-400">Status</p>
                            <p className="text-sm font-semibold text-slate-700">{(call.status || 'Unknown').replace('_', ' ')}</p>
                          </div>
                          <div className="space-y-1">
                            <p className="text-sm font-medium text-slate-400">
                              {call.batchId ? 'Batch ID' : 'Duration'}
                            </p>
                            <p className="text-sm font-semibold text-slate-700">
                              {call.batchId ? call.batchId : 
                               typeof call.duration === 'number' ? `${call.duration.toFixed(2)} seconds` : 'N/A'}
                            </p>
                          </div>
                        </div>
                        <div className="space-y-1">
                          <p className="text-sm font-medium text-slate-400">Time</p>
                          <p className="text-sm font-semibold text-slate-700">
                            {call.timestamp ? new Date(call.timestamp).toLocaleString('en-GB') : 'N/A'}
                          </p>
                        </div>
                        {/* Show call summary and transcript for individual calls and completed batch calls */}
                        {(!call.batchId || (call.batchId && (call.status === 'ended' || call.status === 'completed' || call.status === 'busy' || call.status === 'no_answer' || call.status === 'voicemail'))) && (
                          <div className="mt-2 pt-2 border-t border-slate-100">
                            <p className="text-sm font-medium text-slate-400">Call Outcome</p>
                            <p className="text-sm text-slate-700 mt-1">{call.callSummary || 'No summary available'}</p>
                            <p className="text-sm font-medium text-slate-400">Transcript</p>
                                <p className="text-sm text-slate-700 mt-1">
                                {call.transcript 
                                ? call.transcript
                                .replace(/(agent:)/gi, '<br /><strong>$1</strong>')
                                .replace(/(user:)/gi, '<br /><strong>$1</strong>')
                                .replace(/^<br \/>/, '') // Remove leading <br /> if any
                                .split('<br />')
                                .map((line:any , index:any) => (
                                <span key={index}>
                                {index > 0 && <br />}
                                <span dangerouslySetInnerHTML={{ __html: line }} />
                                </span>
                                ))
                                : 'No transcript available'}
                                </p>
                          {/* <p className="text-sm text-slate-700 mt-1">{call.transcript || 'No transcript available'}</p> */}
                          </div>
                        )}
                      </div>
                    ))
                  ) : (
                    <p className="text-sm text-slate-500 italic">No call history available</p>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Add Prospect Modal */}
      <AddProspectModal
        isOpen={isAddProspectModalOpen}
        onClose={() => setIsAddProspectModalOpen(false)}
        onSuccess={async () => {
          // Refresh the prospects list
          const response = await userApi.getProspectsSummaryInfo();
          const refreshedProspects = response.prospects_summary;
          setAllProspects(refreshedProspects);

          // Apply existing filters
          let filteredProspects = refreshedProspects;

          if (selectedStatus) {
            filteredProspects = filteredProspects.filter(
              (prospect: Prospect) => prospect.status?.toLowerCase() === selectedStatus.toLowerCase()
            );
          }

          if (selectedOwner) {
            filteredProspects = filteredProspects.filter(
              (prospect: Prospect) => prospect.ownerName === selectedOwner
            );
          }

          if (selectedCampaign) {
            filteredProspects = filteredProspects.filter(
              (prospect: Prospect) => prospect.campaignId === selectedCampaign || prospect.campaignName === selectedCampaign
            );
          }

          if (searchQuery.trim()) {
            const query = searchQuery.toLowerCase().trim();
            filteredProspects = filteredProspects.filter(
              (prospect: Prospect) =>
                prospect.name?.toLowerCase().includes(query) ||
                prospect.phoneNumber?.toLowerCase().includes(query) ||
                prospect.businessName?.toLowerCase().includes(query) ||
                prospect.ownerName?.toLowerCase().includes(query)
            );
          }

          setProspects(filteredProspects);
        }}
      />
    </div>
  );
};

export default ProspectSummary;
