import axios from "axios";
import { Campaign } from "../types/campaign";

interface CsvData {
  name: string;
  phoneNumber: string;
  businessName?: string;
  campaignName?: string;
  campaignId?: string;
}

interface CampaignResponse {
  status: string;
  message: string;
  data: Campaign[];
}

// Create axios instance with default config
const Axios = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
  withCredentials: false 
});

export const userApi = {
  uploadUsers: async (users: CsvData[], scheduledCallDate?: string, campaignName?: string, ownerName?: string, campaignId?: string) => {
    try {
      console.log("Uploading users to campaign:", {
        userCount: users.length,
        scheduledCallDate: scheduledCallDate || 'None',
        campaignName: campaignName || 'None',
        campaignId: campaignId || 'None',
        ownerName: ownerName || 'Unknown User'
      });
      
      if (!campaignName && !campaignId) {
        console.warn("No campaign information provided - prospects will not be associated with a campaign");
      }
      console.log('users', users);
      // Add campaign info to each user if not already set
      const usersWithCampaign = users.map(user => ({
        ...user,
        campaignName: user.campaignName || campaignName || '',
        campaignId: user.campaignId || campaignId || ''
      }));
      console.log('usersWithCampaign', usersWithCampaign);
      const response = await Axios.post('/api/create-prospects-and-call-initiation', { 
        users: usersWithCampaign, 
        campaignName: campaignName || '',
        campaignId: campaignId || '',
        ownerName: ownerName || 'Unknown User',
      });
      
      console.log("Upload response:", response.data);
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        console.error("Upload error:", error.response?.data);
        throw new Error(error.response?.data?.detail || error.response?.data?.message || "Failed to upload users");
      }
      console.error("Unexpected upload error:", error);
      throw new Error("Failed to upload users");
    }
  },
  getProspectsSummaryInfo: async () => {
    try {
      const getUserId = localStorage.getItem("userId")
      const response = await Axios.get(`/stats/prospects_summary?userId=${getUserId}`);
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        console.log("error", error);
        throw new Error(error.response?.data?.message || "Failed to fetch total calls");
      }
      throw new Error("Failed to fetch total calls");
    }
  },
  getCalendarEvents: async (month?: number, year?: number, ownerName?: string, userRole?: string) => {
    try {
      let url = '/stats/calendar_events';
      
      // Build query parameters
      const params: string[] = [];
      
      if (month !== undefined && year !== undefined) {
        params.push(`month=${month}&year=${year}`);
      }
      
      if (ownerName) {
        params.push(`owner_name=${encodeURIComponent(ownerName)}`);
      }

      if (userRole) {
        params.push(`user_role=${encodeURIComponent(userRole)}`);
      }
      
      // Add query parameters if any exist
      if (params.length > 0) {
        url += `?${params.join('&')}`;
      }
      
      const response = await Axios.get(url);
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        console.error("API Error:", error.response?.data);
        throw new Error(error.response?.data?.message || "Failed to fetch calendar events");
      }
      throw new Error("Failed to fetch calendar events");
    }
  },
  getProspectsByCampaign: async (campaignName?: string, campaignId?: string) => {
    try {
      const response = await Axios.post(`/api/get_prospects_by_campaign`, {
        campaignName: campaignName,
        campaignId: campaignId
      });
      return response.data.data;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        console.log("error", error);
        throw new Error(error.response?.data?.message || "Failed to fetch prospects");
      }
      throw new Error("Failed to fetch prospects");
    }
  },
  initiateCall: async (phoneNumber: string, campaignId: string) => {
    try {
      console.log(`Initiating call to: ${phoneNumber}`);
      console.log(`campaignId: ${campaignId}`);
      const response = await Axios.get(`/api/initiate_call?phoneNumber=${phoneNumber}&campaignId=${campaignId}`);
      console.log('Call initiation response:', response.data);
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        console.error("Error initiating call:", error.response?.data);
        throw new Error(error.response?.data?.detail || error.response?.data?.message || "Failed to initiate call");
      }
      throw new Error("Failed to initiate call");
    }
  },
  updateAppointment: async (phoneNumber: string, appointmentInterest: boolean, appointmentDateTime?: string, meetingLink?: string) => {
    try {
      const response = await Axios.post('/api/update_appointment', {
        phoneNumber,
        appointmentInterest,
        appointmentDateTime,
        meetingLink
      });
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        console.error("Error updating appointment:", error.response?.data);
        throw new Error(error.response?.data?.message || "Failed to update appointment");
      }
      throw new Error("Failed to update appointment");
    }
  },
  initiateCampaignCalls: async (campaignName: string, campaignId: string, phoneNumbers: string[]) => {
    try {
      const response = await Axios.post('/api/campaign_call', {
        campaign_name: campaignName,
        campaign_id: campaignId,
        phone_numbers: phoneNumbers
      });
      return response.data;
    } catch (error) {
      console.error('Error initiating campaign calls:', error);
      throw error;
    }
  },
  getUsers: async () =>{
    try {
      const response = await Axios.get('/users/get_users');
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        console.log("error", error);
        throw new Error(error.response?.data?.message || "Failed to fetch users");
      }
      throw new Error("Failed to fetch users");
    }
  },
  updateUser: async (userId: string, userData: any) => {
    try {
      const response = await Axios.put(`/users/update_user/${userId}`, userData);
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        console.error("Update user error:", error.response?.data);
        throw new Error(error.response?.data?.message || "Failed to update user");
      }
      throw new Error("Failed to update user");
    }
  }
};

export const statsApi = {
  getTotalNoCalls: async () => {
    try {
      let getUserId = localStorage.getItem("userName");
      const response = await Axios.get(`/stats/total_calls?userId=${getUserId}`);
      return response.data; 
    } catch (error) {
      if (axios.isAxiosError(error)) {
        console.log("error", error);
        throw new Error(error.response?.data?.message || "Failed to fetch total calls");
      }
      throw new Error("Failed to fetch total calls");
    }
  },

  getMatrixDetails: async (id: string, userName: string) => {
    try {
      const response = await Axios.get(`/stats/matrix_details?id=${id}&userName=${userName}`);
      return response;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        console.log("error", error);
        throw new Error(error.response?.data?.message || "Failed to fetch matrix details");
      }
      throw new Error("Failed to fetch matrix details");
    }
  },
  
  getAverageCallDuration: async () => {
    try {
      let getUserId = localStorage.getItem("userName");
      const response = await Axios.get(`/stats/average_call_duration?userId=${getUserId}`);
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        console.log("error", error);
        throw new Error(error.response?.data?.message || "Failed to fetch average call duration");
      }
      throw new Error("Failed to fetch average call duration");
    }
  },
  getTotalCallsConnected: async () => {
    try {
      let getUserId = localStorage.getItem("userName");
      const response = await Axios.get(`/stats/total_connected_calls?userId=${getUserId}`);
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        console.log("error", error);
        throw new Error(error.response?.data?.message || "Failed to fetch total calls connected");
      }
      throw new Error("Failed to fetch total calls connected");
    }
  },
  getBookedAppointments: async () => {
    try {
      let getUserId = localStorage.getItem("userName");
      const response = await Axios.get(`/stats/appointments_booked?userId=${getUserId}`);
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        console.log("error", error);
        throw new Error(error.response?.data?.message || "Failed to fetch total booked appointments");
      }
      throw new Error("Failed to fetch total booked appointments");
    }
  },
  getSentEbooks: async () => {
    try {
      let getUserId = localStorage.getItem("userName");
      const response = await Axios.get(`/stats/total_ebook_sent?userId=${getUserId}`);
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error)) {  
        console.log("error", error);
        throw new Error(error.response?.data?.message || "Failed to fetch total sent ebooks sent");
      }
      throw new Error("Failed to fetch total ebooks sent");
    }
  },
  getCallBackShedules: async () => {
    try {
      let getUserId = localStorage.getItem("userName");
      const response = await Axios.get(`/stats/total_call_backs?userId=${getUserId}`);
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        console.log("error", error);
        throw new Error(error.response?.data?.message || "Failed to fetch total call backs");
      }
      throw new Error("Failed to fetch total call backs");
    }
  },
  getChartData: async (month: number, year: number) => {
    try {
      let getUserId = localStorage.getItem("userName");
      await Axios.post(`/stats/monthly_stats?userId=${getUserId}`, {
        month,
        year
      });
    } catch (error) {
      if (axios.isAxiosError(error)) {
        console.log("error", error);
        throw new Error(error.response?.data?.message || "Failed to fetch monthly statistics");
      }
      throw new Error("Failed to fetch monthly statistics");
    }
  }
};

export const campaignApi = {
  createCampaign: async (campaign: any) => {
    try {
      // Make sure field names match the backend expectations
      const campaignData = {
        campaignName: campaign.campaignName,
        description: campaign.description,
        campaignDate: campaign.campaignDate,
        users: campaign.users || null,
        campaignTime: campaign.campaignTime,
        hasEbook: campaign.hasEbook || false
      };

      console.log("Sending campaign data to backend:", campaignData);
      const response = await Axios.post('/campaign/create_campaign', campaignData);
      return response.data.data;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        // Check for duplicate campaign name error
        const errorMessage = error.response?.data?.detail;
        if (errorMessage?.includes('already exists')) {
          throw new Error('A campaign with this name already exists');
        }
        throw new Error(error.response?.data?.detail || "Failed to create campaign");
      }
      throw new Error("Failed to create campaign");
    }
  },

  getCampaigns: async (): Promise<Campaign[]> => {
    try {
      const response = await Axios.get<CampaignResponse>('/campaign/get_campaigns');

      console.log("response", response.data);
      return response.data.data;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        throw new Error(error.response?.data?.message || "Failed to fetch campaigns");
      }
      throw new Error("Failed to fetch campaigns");
    }
  },

  unarchiveCampaign: async (campaignId: string) => {
    const response = await Axios.put(`/campaign/unarchive_campaign/${campaignId}`);
    return response.data;
  },

   getArcheivedCampaigns: async (): Promise<Campaign[]> => {
    const response = await Axios.get<any>('/campaign/get_archived_campaigns');
    return response.data;
  },

  getCampaignAnalytics: async (campaignId: string): Promise<any> => {
    const response = await Axios.get(`/campaign/get_campaign_analytics/${campaignId}`);
    return response.data;
  },

  getCampaignUsers: async (): Promise<Campaign[]> => {
    try {
      console.log("Making API call to /campaign/get_campaign_users");
      const response = await Axios.get<CampaignResponse>('/campaign/get_campaign_users');

      console.log("getCampaignUsers raw response:", response);
      console.log("getCampaignUsers response data:", response.data);
      
      // Handle different response structures
      if (response.data) {
        if (response.data.data && Array.isArray(response.data.data)) {
          console.log("Found data array in response:", response.data.data);
          return response.data.data;
        } else if (Array.isArray(response.data)) {
          console.log("Response data is itself an array:", response.data);
          return response.data;
        } else {
          console.warn("Unexpected response structure:", response.data);
          // Try to extract any campaign-like objects from the response
          const extractedData = Object.values(response.data).find(val => Array.isArray(val));
          if (extractedData) {
            console.log("Extracted potential campaign data:", extractedData);
            return extractedData as Campaign[];
          }
        }
      }
      
      console.warn("Could not find valid campaign data in response");
      return [];
    } catch (error) {
      console.error("Error in getCampaignUsers:", error);
      if (axios.isAxiosError(error)) {
        console.error("API error details:", error.response?.data);
        throw new Error(error.response?.data?.message || "Failed to fetch campaign users");
      }
      throw new Error("Failed to fetch campaign users");
    }
  },

  getUserCampaigns: async (): Promise<Campaign[]> => {
    try {
      const userId = localStorage.getItem("userId");
      if (!userId) {
        throw new Error("User ID not found");
      }
      
      const response = await Axios.get(`/campaign/user_campaigns/${userId}`);
      console.log("getUserCampaigns response:", response.data);
      return response.data.data;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        throw new Error(error.response?.data?.message || "Failed to fetch user campaigns");
      }
      throw new Error("Failed to fetch user campaigns");
    }
  },

  getCampaignProspects: async (campaignId: string): Promise<any[]> => {
    try {
      const response = await Axios.get(`/campaign/campaign_prospects/${campaignId}`);
      return response.data.data;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        throw new Error(error.response?.data?.message || "Failed to fetch campaign prospects");
      }
      throw new Error("Failed to fetch campaign prospects");
    }
  },

  updateCampaignSettings: async (campaignId: any, campaignUpdate: any) => {
    const response = await Axios.put(`/campaign/update_campaign/${campaignId}`, campaignUpdate);
    return response.data;
  },

  deleteCampaign: async (campaignId: string) => {
    const response = await Axios.delete(`/campaign/delete_campaign/${campaignId}`);
    return response.data;
  }
};

export const uploadApi = {
  uploadEbook: async (formData: FormData) => {
    try {
      // Debug: Log form data contents
      console.log("FormData contents:");
      for (const pair of formData.entries()) {
        console.log(pair[0], pair[1]);
      }
      
      const token = localStorage.getItem('token');
      console.log("Using token:", token ? "Token exists" : "No token");
      
      // Use fetch instead of Axios for FormData
      // Send token as query parameter
      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/upload/ebook?token=${token}`, {
        method: 'POST',
        body: formData,
      });
      
      console.log("Response status:", response.status);
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error("Error response:", errorText);
        throw new Error(errorText || "Failed to upload ebook");
      }
      
      const data = await response.json();
      console.log("Success response:", data);
      return data;
    } catch (error) {
      console.error("Upload error:", error);
      throw error;
    }
  }
};