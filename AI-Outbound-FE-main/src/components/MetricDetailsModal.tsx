import React from 'react';

export function formatDuration(durationInSeconds: any): string {
  if (!durationInSeconds || durationInSeconds <= 0) return "0s";

  const minutes = Math.floor(durationInSeconds / 60);
  const seconds = durationInSeconds % 60;

  // Show in decimal minutes if over 60 seconds and has remainder
  if (durationInSeconds >= 60 && seconds !== 0) {
    const decimalMinutes = durationInSeconds / 60;
    return `${decimalMinutes.toFixed(1)} min`;
  }

  // Just minutes if exact
  if (minutes > 0 && seconds === 0) {
    return `${minutes} min`;
  }

  // Just seconds if under 60 seconds
  return `${seconds}s`;
}
interface Prospect {
  name: string;
  phoneNumber: string;
  businessName?: string;
  email?: string;
  status?: string;
  ownerName?: string;
  campaignName?: string;
  scheduledCallDate?: string;
  callBackDate?: string;
  callBackTime?: string;
  calls?: Array<{
    id?: string;
    callTime?: string;
    duration?: number;
    status?: string;
    timestamp?: string;
  }>;
  appointment?: {
    appointmentInterest?: boolean;
    appointmentDateTime?: string;
    appointmentType?: string;
    meetingLink?: string;
  };
  averageCallDuration?: number;
}

interface MetricDetailsModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  metricId: string;
  prospects: Prospect[];
}

const MetricDetailsModal: React.FC<MetricDetailsModalProps> = ({ 
  isOpen, 
  onClose, 
  title, 
  metricId, 
  prospects 
}) => {
  if (!isOpen) return null;

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'N/A';
    try {
      return new Date(dateString).toLocaleDateString();
    } catch (e) {
      return dateString;
    }
  };
  

  const renderProspectDetails = (prospect: Prospect) => {
    return (
      <div className="border rounded-lg p-4 mb-4 bg-white shadow-sm hover:shadow-md transition-shadow">
        <div className="flex flex-wrap justify-between">
          <div className="w-full md:w-1/2 mb-2">
            <p className="text-sm text-gray-500">Name</p>
            <p className="font-medium">{prospect.name || 'N/A'}</p>
          </div>
          <div className="w-full md:w-1/2 mb-2">
            <p className="text-sm text-gray-500">Phone</p>
            <p className="font-medium">{prospect.phoneNumber || 'N/A'}</p>
          </div>
          <div className="w-full md:w-1/2 mb-2">
            <p className="text-sm text-gray-500">Business</p>
            <p className="font-medium">{prospect.businessName || 'N/A'}</p>
          </div>
          <div className="w-full md:w-1/2 mb-2">
            <p className="text-sm text-gray-500">Email</p>
            <p className="font-medium">{prospect.email || 'N/A'}</p>
          </div>
          <div className="w-full md:w-1/2 mb-2">
            <p className="text-sm text-gray-500">Status</p>
            <p className="font-medium">{prospect.status || 'N/A'}</p>
          </div>
          <div className="w-full md:w-1/2 mb-2">
            <p className="text-sm text-gray-500">Owner</p>
            <p className="font-medium">{prospect.ownerName || 'N/A'}</p>
          </div>
          <div className="w-full md:w-1/2 mb-2">
            <p className="text-sm text-gray-500">Campaign</p>
            <p className="font-medium">{prospect.campaignName || 'N/A'}</p>
          </div>
        </div>

        {/* Metric-specific details */}
        {metricId === 'calls-made' && prospect.calls && prospect.calls.length > 0 && (
          <div className="mt-3 pt-3 border-t">
            <p className="font-semibold mb-2">Call History</p>
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead>
                  <tr className="bg-gray-50">
                    <th className="px-4 py-2 text-left">Time</th>
                    <th className="px-4 py-2 text-left">Duration</th>
                    <th className="px-4 py-2 text-left">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {prospect.calls.map((call, index) => (
                    <tr key={index} className="border-t">
                      <td className="px-4 py-2">{formatDate(call.timestamp || call.callTime)}</td>
                      <td className="px-4 py-2">{formatDuration(call.duration)}</td>
                      <td className="px-4 py-2">{call.status || 'N/A'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {metricId === 'calls-connected' && prospect.calls && prospect.calls.length > 0 && (
          <div className="mt-3 pt-3 border-t">
            <p className="font-semibold mb-2">Connected Calls</p>
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead>
                  <tr className="bg-gray-50">
                    <th className="px-4 py-2 text-left">Time</th>
                    <th className="px-4 py-2 text-left">Duration</th>
                  </tr>
                </thead>
                <tbody>
                  {prospect.calls
                    .filter(call => call.status === 'ended')
                    .map((call, index) => (
                      <tr key={index} className="border-t">
                        <td className="px-4 py-2">{formatDate(call.timestamp || call.callTime)}</td>
                        <td className="px-4 py-2">{formatDuration(call.duration)}</td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {metricId === 'appointments' && prospect.appointment && (
          <div className="mt-3 pt-3 border-t">
            <p className="font-semibold mb-2">Appointment Details</p>
            <div className="grid grid-cols-2 gap-2">
              <div>
                <p className="text-sm text-gray-500">Date & Time</p>
                <p className="font-medium">{formatDate(prospect.appointment.appointmentDateTime)}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Type</p>
                <p className="font-medium">{prospect.appointment.appointmentType || 'N/A'}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Appointment Link</p>
                <a href={prospect.appointment.meetingLink || 'N/A'} target="_blank" rel="noopener noreferrer" className="font-medium text-blue-500 hover:text-blue-700">
                  {prospect?.appointment?.meetingLink ? prospect?.appointment?.meetingLink?.slice(0, 30) + '...' : 'N/A'}
                </a>
              </div>
            </div>
          </div>
        )}

        {metricId === 'callbacks' && (
          <div className="mt-3 pt-3 border-t">
            <p className="font-semibold mb-2">Callback Details</p>
            <div className="grid grid-cols-2 gap-2">
              <div>
                <p className="text-sm text-gray-500">Date</p>
                <p className="font-medium">{formatDate(prospect.callBackDate)}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Time</p>
                <p className="font-medium">{prospect.callBackTime || 'N/A'}</p>
              </div>
            </div>
          </div>
        )}

        {metricId === 'average-call-duration' && (
          <div className="mt-3 pt-3 border-t">
            <p className="font-semibold mb-2">Call Duration</p>
            <p className="font-medium">{formatDuration(prospect.averageCallDuration)}</p>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
        <div className="px-6 py-4 border-b flex justify-between items-center">
          <h2 className="text-xl font-bold text-gray-800">{title} Details</h2>
          <button 
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        <div className="p-6 overflow-y-auto flex-grow">
          {prospects.length > 0 ? (
            prospects.map((prospect, index) => (
              <div key={index}>
                {renderProspectDetails(prospect)}
              </div>
            ))
          ) : (
            <div className="text-center py-8 text-gray-500">
              No data available for this metric.
            </div>
          )}
        </div>
        
        <div className="px-6 py-4 border-t bg-gray-50">
          <div className="flex justify-end">
            <button
              onClick={onClose}
              className="px-4 py-2 bg-gray-200 hover:bg-gray-300 rounded-md text-gray-800 transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MetricDetailsModal; 