import React, { ReactNode } from 'react';
// import { useNavigate } from 'react-router-dom';
// import { useAuth } from '../contexts/AuthContext';

interface ApiKeyRequiredProps {
  children: ReactNode;
  pageTitle: string;
  pageDescription?: string;
}

/**
 * A wrapper component that requires API key connection.
 * If the user does not have an API key, shows the connection UI.
 * Otherwise, renders the children components.
 */
const ApiKeyRequired: React.FC<ApiKeyRequiredProps> = ({
  children,
  // pageTitle,
  // pageDescription,
}) => {
  // const { user } = useAuth();
  // const navigate = useNavigate();
  // TODO: Replace this with actual API key check logic (e.g., from context or user object)
  // const hasApiKey = user?.api_key; // Placeholder: set to true if API key is present

  // if (!hasApiKey) {
  //   return (
  //     <div className="w-full mx-auto p-6">
  //       <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
  //         <h1 className="text-2xl font-bold text-gray-800 mb-6">{pageTitle}</h1>
  //         {pageDescription && (
  //           <p className="text-gray-600 mb-6">{pageDescription}</p>
  //         )}
  //         <div className="mb-6">
  //           <div className="flex justify-between items-center">
  //             <h2 className="text-lg font-semibold text-gray-700">API Key Connection Required</h2>
  //           </div>
  //           <div className="bg-gray-50 p-6 rounded-lg border border-gray-200 mt-2">
  //             <p className="mb-4 text-gray-600">
  //               Please connect your API key to access this feature.
  //             </p>
  //             <button
  //               className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition-colors duration-200"
  //               onClick={() => navigate('/api-key')}
  //             >
  //               Add API Key
  //             </button>
  //           </div>
  //         </div>
  //       </div>
  //     </div>
  //   );
  // }

  // Render the children if API key is present
  return <>{children}</>;
};

export default ApiKeyRequired; 