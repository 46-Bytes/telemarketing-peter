import React, { JSX, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { FaHome, FaUsers, FaCalendarAlt, FaBullhorn } from 'react-icons/fa';
import { HiOutlineChevronLeft, HiOutlineChevronRight } from 'react-icons/hi';
import { useAuth } from '../contexts/AuthContext';
import useAuthorization from '../hooks/useAuthorization';

interface Item {
  path: string;
  label: string;
  icon: JSX.Element;
  roles?: string[];
}

const Sidebar: React.FC = () => {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const location = useLocation();
  const { user } = useAuth();
  const { isAdmin, hasRole } = useAuthorization();

  const navigationItems: Item[] = [
    { path: '/', label: 'Home', icon: <FaHome size={20} /> },
    // Analysis page is commented out as requested
    // { path: '/analysis', label: 'Analysis', icon: <FaChartBar size={20} /> },
    //{ path: '/prospects', label: 'Prospects', icon: <FaUsers size={20} /> },
    //{ path: '/csv-upload', label: 'CSV Upload', icon: <FaFileUpload size={20} /> },
    
    // ...(!isAdmin()
    //   ? [{ path: '/calendar', label: 'Calendar', icon: <FaCalendarAlt size={20} /> }]
    //   : []),

    { path: '/calendar', label: 'Calendar', icon: <FaCalendarAlt size={20} /> },
    
    // Add My Campaigns only for non-admin users
    ...(!isAdmin() 
      ? [{ path: '/my-campaigns', label: 'My Campaigns', icon: <FaBullhorn size={20} /> }]
      : []),
    
    // Admin-only routes
    ...(isAdmin()
      ? [{ path: '/admin/users', label: 'Users', icon: <FaUsers size={20} />}]
    : []),
    
    // Only show Campaigns for super admin
    ...(isAdmin()
      ? [{ path: '/admin/campaigns', label: 'Campaigns', icon: <FaBullhorn size={20} /> }]
      : []),

      // ...(!isAdmin()
      // ? [{ path: "/api-key", label: "API Key", icon: <FaKey size={20} /> }]
      // : []),
  ];

  // Filter navigation items based on user role
  const filteredNavigationItems = navigationItems.filter(item => {
    if (!item.roles) return true; // If no roles specified, show to everyone
    return item.roles.some(role => hasRole(role));
  });

  console.log("Current user:", user); // For debugging

  return (
    <div className={`bg-white shadow-lg h-screen flex flex-col ${isCollapsed ? 'w-20' : 'w-64'} transition-all duration-300`}>
      <div className="flex items-center justify-between p-4 border-b">
        <h1 className={`text-xl font-bold text-gray-800 ${isCollapsed ? 'hidden' : 'block'}`}>
          Sales Dashboard
        </h1>
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="p-2 rounded-lg hover:bg-gray-100 transition-colors duration-200"
          aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {isCollapsed ? <HiOutlineChevronRight size={20} /> : <HiOutlineChevronLeft size={20} />}
        </button>
      </div>

      <nav className="mt-4 flex-1">
        {filteredNavigationItems.map((item: Item) => (
          <Link
            key={item.path}
            to={item.path}
            className={`
              flex items-center ${isCollapsed ? 'justify-center' : 'justify-start px-4'} py-3
              ${location.pathname === item.path
                ? 'bg-blue-50 text-blue-600 border-r-4 border-blue-600'
                : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
              }
              transition-all duration-200
            `}
          >
            <span className={`flex items-center justify-center ${isCollapsed ? 'w-full' : 'w-8'}`}>
              {item.icon}
            </span>
            {!isCollapsed && (
              <span className="ml-3 font-medium">{item.label}</span>
            )}
          </Link>
        ))}
      </nav>
    </div>
  );
};

export default Sidebar; 