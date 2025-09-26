import React from 'react';
import { BrowserRouter as Router, Routes, Route, Outlet } from 'react-router-dom';
import DashboardLayout from '../layout/DashboardLayout';
import Home from '../pages/Home';
import Analysis from '../pages/Analysis';
import Calendar from '../pages/Calendar';
// import ApiKeyPage from '../pages/ApiKey';
import MicrosoftAuthGuard from '../components/MicrosoftAuthGuard';
const AppRouter: React.FC = () => {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<DashboardLayout><Outlet /></DashboardLayout>}>
          <Route index element={<Home />} />
          <Route path="analysis" element={<Analysis />} />
          <Route path="calendar" element={
            <MicrosoftAuthGuard>
              <Calendar />
            </MicrosoftAuthGuard>
          } />
          {/* <Route path="api-key" element={<ApiKeyPage />} /> */}
        </Route>
      </Routes>
    </Router>
  );
};

export default AppRouter; 