import React from 'react';
import Sidebar from '../components/Sidebar';
import Header from '../components/Header';
import Footer from '../components/Footer';

interface DashboardLayoutProps {
  children: React.ReactNode;
}

const DashboardLayout: React.FC<DashboardLayoutProps> = ({ children }) => {
  // const sidebarItems = [
  //   {
  //     label: 'My Campaigns',
  //     path: '/my-campaigns',
  //     requiredRoles: ['user', 'admin']  // Both users and admins can access
  //   },
  // ];

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Sidebar */}
      <Sidebar />
      
      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <Header />
        
        {/* Main Content Area */}
        <main className="flex-1 overflow-x-hidden overflow-y-auto bg-gray-100 p-4">
          {children}
        </main>
        
        {/* Footer */}
        <Footer />
      </div>
    </div>
  );
};

export default DashboardLayout; 