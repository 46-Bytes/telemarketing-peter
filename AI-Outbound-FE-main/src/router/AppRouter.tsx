import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, Outlet } from 'react-router-dom';
import DashboardLayout from '../layout/DashboardLayout';
import Home from '../pages/Home';
import Analysis from '../pages/Analysis';
import Login from '../pages/Login';
import Signup from '../pages/Signup';
import CsvUpload from '../pages/CsvUpload';
import Calendar from '../pages/Calendar';
// import ApiKeyPage from '../pages/ApiKey';
import User from '../pages/User';
import CampaignsAdmin from '../pages/Campaigns-admin';
import UserCampaigns from '../pages/UserCampaigns';
import CampaignDetails from '../pages/CampaignDetails';
import { AuthMiddleware, AdminMiddleware  } from './middleware';

const AppRouter: React.FC = () => {
  return (
    <Router>
      <Routes>
        {/* Public routes */}
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />

        {/* Protected dashboard routes for authenticated users */}
        <Route
          path="/"
          element={
            <AuthMiddleware>
              <DashboardLayout>
                <Outlet />
              </DashboardLayout>
            </AuthMiddleware>
          }
        >
          <Route index element={<Home />} />
          <Route path="analysis" element={<Analysis />} />
          <Route path="csv-upload" element={<CsvUpload />} />
          <Route path="calendar" element={<Calendar />} />
          {/* <Route path="api-key" element={<ApiKeyPage />} /> */}
          
          {/* Users can see only their campaigns */}
          <Route path="my-campaigns" element={<UserCampaigns />} />
          {/* Campaign details for regular users */}
          <Route path="campaign/:id" element={<CampaignDetails />} />
        </Route>

        {/* Admin only routes */}
        <Route
          path="/admin"
          element={
            <AdminMiddleware>
              <DashboardLayout>
                <Outlet />
              </DashboardLayout>
            </AdminMiddleware>
          }
        >
          <Route path="users" element={<User />} />
          <Route path="campaigns" element={<CampaignsAdmin />} />
          
          {/* Campaign details for admin users */}
          <Route path="campaign/:id" element={<CampaignDetails />} />
        </Route>

        {/* Redirect to home for unknown routes */}
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </Router>
  );
};

export default AppRouter; 