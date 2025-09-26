import React from 'react';
import { Metric } from '../types/metrics';

interface MetricCardProps {
  metric: Metric;
  onClick: () => void;
}

const MetricCard: React.FC<MetricCardProps> = ({ metric, onClick }) => {
  return (
    <div className="bg-white rounded-lg cursor-pointer shadow-sm p-6 hover:shadow-md transition-shadow duration-300" onClick={onClick}>
      <div className="flex items-center justify-between">
        <div className="flex items-center">
          <div className={`p-3 rounded-lg ${metric.color} bg-opacity-10`}>
            <span className="text-2xl">{metric.icon}</span>
          </div>
          <div className="ml-4">
            <h3 className="text-sm font-medium text-gray-500">{metric.title}</h3>
            <div className="text-2xl font-semibold text-gray-900">{metric.value}</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MetricCard; 