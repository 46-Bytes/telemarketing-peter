import React from 'react';

interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  color?: string;
}

const Spinner: React.FC<SpinnerProps> = ({ size = 'md', color = 'text-blue-500' }) => {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12'
  };

  return (
    <div className="flex justify-center items-center">
      <div
        className={`${sizeClasses[size]} ${color} animate-spin rounded-full border-2 border-solid border-current border-r-transparent`}
        role="status"
      >
        <span className="sr-only"></span>
      </div>
    </div>
  );
};

export default Spinner; 