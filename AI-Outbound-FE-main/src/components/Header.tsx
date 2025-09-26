import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const Header: React.FC = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsMenuOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleLogout = async () => {
    try {
      console.log("logging out");
      await logout();
      navigate('/login');
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  const getInitials = (name: string) => {
    return name
      .split(' ')
      .map(word => word[0])
      .join('')
      .toUpperCase();
  };

  return (
    <header className="bg-white shadow-sm z-[22] relative">
      <div className="max-w-7xl mx-auto flex items-center justify-between px-4 py-4 sm:px-6 lg:px-8">
        <div className="flex items-center">
          <h2 className="text-lg font-semibold text-gray-800">Dashboard</h2>
        </div>
        <div className="flex items-center relative" ref={menuRef}>
          {user && (
            <>
              <button
                onClick={() => setIsMenuOpen(!isMenuOpen)}
                className="flex items-center space-x-3 focus:outline-none group"
              >
                <div className="hidden sm:block">
                  <span className="text-sm text-gray-700 mr-3 max-w-[150px] truncate">
                    {user.name}
                  </span>
                </div>
                <div className="h-10 w-10 rounded-full bg-indigo-600 flex items-center justify-center text-white font-medium text-sm ring-4 ring-transparent group-hover:ring-indigo-100 transition-all duration-200">
                  {getInitials(user.name)}
                </div>
              </button>

              {isMenuOpen && (
                <div className="absolute right-0 top-14 w-64 rounded-lg shadow-lg bg-white ring-1 ring-black ring-opacity-5 transform transition-all duration-200 ease-out z-[110]">
                  <div className="py-2" role="menu">
                    <div className="px-4 py-3 border-b border-gray-100">
                      <div className="font-medium text-sm text-gray-900">{user.name}</div>
                      <div className="text-sm text-gray-500 truncate mt-1">{user.email}</div>
                    </div>
                    <div className="px-2 py-2">
                      <button
                        onClick={handleLogout}
                        className="w-full text-left px-3 py-2 text-sm text-gray-700 hover:bg-indigo-50 hover:text-indigo-700 rounded-md transition-colors duration-150 flex items-center space-x-2"
                        role="menuitem"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                        </svg>
                        <span>Sign out</span>
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </header>
  );
};

export default Header; 