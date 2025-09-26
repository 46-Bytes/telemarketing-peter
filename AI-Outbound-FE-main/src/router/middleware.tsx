import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import Loading from '../components/Loading';

interface ProtectedRouteProps {
  children?: React.ReactNode;
  allowedRoles?: string[];
  redirectPath?: string;
}

/**
 * Role-based authorization middleware
 * This component handles authentication and authorization in one place
 * 
 * @param children - The components to render if authorized
 * @param allowedRoles - Array of roles allowed to access the route (if empty, any authenticated user can access)
 * @param redirectPath - Where to redirect if unauthorized (defaults to /login for unauthenticated, / for unauthorized)
 */
export const AuthMiddleware: React.FC<ProtectedRouteProps> = ({
  children,
  allowedRoles = [],
  redirectPath,
}) => {
  const { user, isAuthenticated, isLoading } = useAuth();

  // Show loading indicator while checking authentication
  if (isLoading) {
    return <Loading fullScreen message="Loading..." />;
  }

  console.log(isAuthenticated, "isAuthenticated");
  // If not authenticated, redirect to login
  if (!isAuthenticated) {
    return <Navigate to={redirectPath || '/login'} />;
  }

  // If roles are specified and user doesn't have the required role
  if (allowedRoles.length > 0 && (!user?.role || !allowedRoles.includes(user.role))) {
    console.log(`Access denied: User role ${user?.role} is not in allowed roles: ${allowedRoles.join(', ')}`);
    return <Navigate to={redirectPath || '/'} />;
  }

  // User is authenticated and authorized
  return <>{children || <Outlet />}</>;
};

// Pre-configured middleware for common scenarios
export const AdminMiddleware: React.FC<Omit<ProtectedRouteProps, 'allowedRoles'>> = (props) => {
  return <AuthMiddleware {...props} allowedRoles={['super_admin']} />;
};

export const UserMiddleware: React.FC<Omit<ProtectedRouteProps, 'allowedRoles'>> = (props) => {
  return <AuthMiddleware {...props} allowedRoles={['user', 'super_admin']} />;
};

// You can add more specialized middleware as needed
export const AgentMiddleware: React.FC<Omit<ProtectedRouteProps, 'allowedRoles'>> = (props) => {
  return <AuthMiddleware {...props} allowedRoles={['agent', 'super_admin']} />;
}; 