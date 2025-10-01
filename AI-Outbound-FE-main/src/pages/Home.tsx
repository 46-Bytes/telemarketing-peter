import React, { useState, useEffect, useMemo } from 'react';
import { FaPhoneAlt, FaCalendarCheck, FaBook } from 'react-icons/fa';
import { FaPhoneVolume } from "react-icons/fa6";
import { BsClockHistory } from 'react-icons/bs';
import MetricCard from '../components/MetricCard';
import Spinner from '../components/Spinner';
import { statsApi } from '../api/api';
import MetricDetailsModal, { formatDuration } from '../components/MetricDetailsModal';

const Home: React.FC = () => {
  const [totalCalls, setTotalCalls] = useState<number>(0);
  const [totalCallsConnected, setTotalCallsConnected] = useState<number>(0);
  const [totalBookedAppointments, setTotalBookedAppointments] = useState<number>(0);
  const [totalEbooksSent, setTotalEbooksSent] = useState<number>(0);
  const [totalCallbacksScheduled, setTotalCallbacksScheduled] = useState<number>(0);
  const [totalAverageCallDuration, setTotalAverageCallDuration] = useState<number>(0);
  const [converstionRate, setConverstionRate] = useState<any>({});
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  
  // Modal state
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [modalTitle, setModalTitle] = useState<string>('');
  const [selectedMetricId, setSelectedMetricId] = useState<string>('');
  const [prospectDetails, setProspectDetails] = useState<any[]>([]);
  const [_, setIsLoadingDetails] = useState<boolean>(false);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        setIsLoading(true);
        setError(null);

        // Use Promise.all to fetch multiple stats in parallel
        const [
          callsResponse, 
          connectedResponse, 
          bookedResponse, 
          ebooksResponse, 
          callbackSchedulesResponse,
          averageCallDurationResponse,
        ] = await Promise.all([
          statsApi.getTotalNoCalls(),
          statsApi.getTotalCallsConnected(),
          statsApi.getBookedAppointments(),
          statsApi.getSentEbooks(),
          statsApi.getCallBackShedules(),
          statsApi.getAverageCallDuration(),
        ]);

        setTotalCalls(callsResponse.total_calls);
        setTotalCallsConnected(connectedResponse.total_connected_calls);
        setTotalBookedAppointments(bookedResponse.total_appointments_booked);
        setTotalEbooksSent(ebooksResponse.total_ebook_sent);
        setTotalCallbacksScheduled(callbackSchedulesResponse.total_call_backs);
        setConverstionRate({
          A: (callbackSchedulesResponse.total_call_backs/connectedResponse.total_connected_calls)*100, 
          B: (bookedResponse.total_appointments_booked/connectedResponse.total_connected_calls)*100, 
          C: (ebooksResponse.total_ebook_sent/connectedResponse.total_connected_calls)*100, 
        });
        setTotalAverageCallDuration(averageCallDurationResponse.average_call_duration);
      } catch (err) {
        setError('Failed to fetch statistics');
        console.error('Error fetching statistics:', err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchStats();
  }, []);

  const metrics = useMemo(() => [
    {
      id: 'calls-made',
      title: 'Total Calls Made',
      value: isLoading ? <Spinner size="sm" /> : error ? '' : totalCalls,
      icon: <FaPhoneAlt className="w-6 h-6" />,
      color: 'bg-blue-500',
    },
    {
      id: 'calls-connected',
      title: 'Calls Connected',
      value: isLoading ? <Spinner size="sm" /> : error ? '' : totalCallsConnected,
      icon: <FaPhoneVolume className="w-6 h-6" />,
      color: 'bg-green-500',
    },
    {
      id: 'appointments',
      title: 'Appointments Booked',
      value: isLoading ? <Spinner size="sm" /> : error ? '' : totalBookedAppointments,
      icon: <FaCalendarCheck className="w-6 h-6" />,
      color: 'bg-purple-500',
    },
    {
      id: 'callbacks',
      title: 'Call-backs Scheduled',
      value: isLoading ? <Spinner size="sm" /> : error ? '' : totalCallbacksScheduled,
      icon: <BsClockHistory className="w-6 h-6" />,
      color: 'bg-yellow-500',
    },
    {
      id: 'ebooks',
      title: 'Ebooks Sent',
      value: isLoading ? <Spinner size="sm" /> : error ? '' : totalEbooksSent,
      icon: <FaBook className="w-6 h-6" />,
      color: 'bg-indigo-500',
    },
    {
      id: 'average-call-duration',
      title: 'Average Call Duration',
      value: isLoading ? <Spinner size="sm" /> : error ? '' : formatDuration(totalAverageCallDuration?.toFixed(1)),
      icon: <BsClockHistory className="w-6 h-6" />,
      color: 'bg-red-500',
    }
  ], [totalCalls, totalCallsConnected, totalBookedAppointments, totalCallbacksScheduled, totalEbooksSent, totalAverageCallDuration, isLoading, error]);

  const getDetails = async (id: string) => {
    try {
      setIsLoadingDetails(true);
      let userName = localStorage.getItem("userName");
      
      // Find the metric title
      const metric = metrics.find(m => m.id === id);
      if (metric) {
        setModalTitle(metric.title);
      }
      
      setSelectedMetricId(id);
      
      // Fetch prospect details for this metric
      const response = await statsApi.getMatrixDetails(id, userName || '');
      console.log("response", response);
      
      if (response && response.data) {
        setProspectDetails(response.data?.matrix_details?.data);
      } else {
        setProspectDetails([]);
      }
      
      // Open the modal
      setIsModalOpen(true);
    } catch (error) {
      console.log("Error fetching details:", error);
      setProspectDetails([]);
    } finally {
      setIsLoadingDetails(false);
    }
  }

  const closeModal = () => {
    setIsModalOpen(false);
    setProspectDetails([]);
  };

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-gray-800 mb-6">Dashboard Overview</h1>
      
      {/* Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
        {metrics.map((metric) => (
          <MetricCard 
            key={metric.id} 
            metric={metric} 
            onClick={() => getDetails(metric.id)}
          />
        ))}
        
        {/* Conversion Rates Card */}
        <div className="bg-white rounded-lg shadow p-6 col-span-1 md:col-span-2 lg:col-span-3">
          <h3 className="text-lg font-semibold text-gray-700 mb-4">Conversion Rates</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-gray-50 p-4 rounded-lg">
              <div className="text-xl font-bold text-gray-800">
                {converstionRate?.A ? converstionRate?.A?.toFixed(2) : 0}%
              </div>
              <p className="text-sm text-gray-600 mt-1">A. Callbacks / Connected</p>
            </div>
            
            <div className="bg-gray-50 p-4 rounded-lg">
              <div className="text-xl font-bold text-gray-800">
                {converstionRate?.B ? converstionRate?.B?.toFixed(2) : 0}%
              </div>
              <p className="text-sm text-gray-600 mt-1">B. Appointments / Connected</p>
            </div>
            
            <div className="bg-gray-50 p-4 rounded-lg">
              <div className="text-xl font-bold text-gray-800">
                {converstionRate?.C ? converstionRate?.C?.toFixed(2) : 0}%
              </div>
              <p className="text-sm text-gray-600 mt-1">C. E-books / Connected</p>
            </div>
          </div>
        </div>
      </div>

      {/* Metric Details Modal */}
      <MetricDetailsModal
        isOpen={isModalOpen}
        onClose={closeModal}
        title={modalTitle}
        metricId={selectedMetricId}
        prospects={prospectDetails}
      />
    </div>
  );
};

export default Home; 