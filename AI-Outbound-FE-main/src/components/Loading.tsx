import React from 'react';

interface LoadingProps {
  size?: 'small' | 'medium' | 'large';
  color?: 'primary' | 'secondary' | 'white';
  fullScreen?: boolean;
  message?: string;
}

const Loading: React.FC<LoadingProps> = ({
  size = 'medium',
  color = 'primary',
  fullScreen = false,
  message,
}) => {
  // Size classes
  const sizeClasses = {
    small: 'w-6 h-6',
    medium: 'w-10 h-10',
    large: 'w-16 h-16',
  };

  // Color classes
  const colorClasses = {
    primary: 'text-blue-600',
    secondary: 'text-purple-600',
    white: 'text-white',
  };

  // Container classes
  const containerClasses = fullScreen
    ? 'fixed inset-0 flex items-center justify-center bg-gray-900/50 z-50'
    : 'flex flex-col items-center justify-center p-4';

  return (
    <div className={containerClasses}>
      <div className="flex flex-col items-center">
        <div className="relative">
          <div className={`${sizeClasses[size]} ${colorClasses[color]} animate-spin`}>
            <svg
              className="w-full h-full"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              ></circle>
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              ></path>
            </svg>
          </div>
        </div>
        {message && (
          <p className={`mt-3 text-center font-medium ${colorClasses[color]}`}>
            {message}
          </p>
        )}
      </div>
    </div>
  );
};

export default Loading;
