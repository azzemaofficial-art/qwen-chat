import React from 'react';
import { Pie } from 'react-chartjs-2';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';

ChartJS.register(ArcElement, Tooltip, Legend);

const AllocationChart = ({ allocation }) => {
  const data = {
    labels: Object.keys(allocation).map(key => 
      key.charAt(0).toUpperCase() + key.slice(1)
    ),
    datasets: [
      {
        data: Object.values(allocation),
        backgroundColor: [
          '#00bcd4',
          '#ff4081',
          '#00e676',
          '#ffc400',
          '#40c4ff',
          '#9c27b0',
        ],
        borderColor: '#1b263b',
        borderWidth: 2,
        hoverOffset: 10,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'right',
        labels: {
          color: '#ffffff',
          font: {
            size: 12,
            weight: 500,
          },
          padding: 15,
        },
      },
      tooltip: {
        backgroundColor: 'rgba(27, 38, 59, 0.95)',
        titleColor: '#00bcd4',
        bodyColor: '#ffffff',
        borderColor: '#00bcd4',
        borderWidth: 1,
        padding: 12,
        callbacks: {
          label: (context) => `${context.label}: ${context.parsed.toFixed(2)}%`,
        },
      },
    },
  };

  return (
    <div style={{ height: '300px', width: '100%' }}>
      <Pie data={data} options={options} />
    </div>
  );
};

export default AllocationChart;
