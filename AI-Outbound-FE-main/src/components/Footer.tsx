import React from 'react';

const Footer: React.FC = () => {
  return (
    <footer className="bg-white border-t">
      <div className="px-4 py-3">
        <p className="text-center text-sm text-gray-600">
          © {new Date().getFullYear()} Sales Dashboard. All rights reserved.
        </p>
      </div>
    </footer>
  );
};

export default Footer; 