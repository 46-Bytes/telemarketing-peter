import React, { useState } from 'react';
import Chart from 'react-apexcharts';
import { ChartSeries, ChartFilter } from '../types/charts';

interface MetricsChartProps {
  series: ChartSeries[];
  filter: ChartFilter;
  onFilterChange: (filter: ChartFilter) => void;
}

const MetricsChart: React.FC<MetricsChartProps> = ({ series, filter, onFilterChange }) => {
  const [selectedSeries, setSelectedSeries] = useState<string[]>(series.map(s => s.name));

  const options:any = {
    chart: {
      type: 'line',
      height: 350,
      toolbar: {
        show: true,
        tools: {
          download: true,
          selection: true,
          zoom: true,
          zoomin: true,
          zoomout: true,
          pan: true,
          reset: true
        }
      },
      animations: {
        enabled: true,
        easing: 'linear',
        dynamicAnimation: {
          speed: 1000
        }
      }
    },
    stroke: {
      curve: 'smooth',
      width: 2
    },
    markers: {
      size: 4
    },
    xaxis: {
      type: 'datetime',
      labels: {
        format: 'dd MMM'
      }
    },
    yaxis: {
      title: {
        text: 'Count'
      }
    },
    tooltip: {
      shared: true,
      intersect: false,
      x: {
        format: 'dd MMM yyyy'
      }
    },
    legend: {
      position: 'top',
      horizontalAlign: 'right',
      floating: true,
      offsetY: -25,
      offsetX: -5
    }
  };

  const handleSeriesToggle = (seriesName: string) => {
    setSelectedSeries(prev => 
      prev.includes(seriesName)
        ? prev.filter(name => name !== seriesName)
        : [...prev, seriesName]
    );
  };

  const filteredSeries = series.filter(s => selectedSeries.includes(s.name));

  return (
    <div className="bg-white rounded-lg shadow-sm p-6">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-gray-800">Performance Metrics</h3>
        <div className="flex items-center space-x-4">
          <select
            value={filter.month}
            onChange={(e) => onFilterChange({ ...filter, month: parseInt(e.target.value) })}
            className="border rounded-md px-3 py-2 text-sm"
          >
            {Array.from({ length: 12 }, (_, i) => (
              <option key={i} value={i + 1}>
                {new Date(2000, i, 1).toLocaleString('default', { month: 'long' })}
              </option>
            ))}
          </select>
          <select
            value={filter.year}
            onChange={(e) => onFilterChange({ ...filter, year: parseInt(e.target.value) })}
            className="border rounded-md px-3 py-2 text-sm"
          >
            {Array.from({ length: 5 }, (_, i) => new Date().getFullYear() - i).map(year => (
              <option key={year} value={year}>{year}</option>
            ))}
          </select>
        </div>
      </div>
      <div className="flex flex-wrap gap-2 mb-4">
        {series.map((s) => (
          <button
            key={s.name}
            onClick={() => handleSeriesToggle(s.name)}
            className={`px-3 py-1 rounded-full text-sm ${
              selectedSeries.includes(s.name)
                ? 'bg-opacity-20'
                : 'bg-opacity-10'
            } ${s.color}`}
          >
            {s.name}
          </button>
        ))}
      </div>
      <Chart
        options={options}
        series={filteredSeries}
        type="line"
        height={350}
      />
    </div>
  );
};

export default MetricsChart; 