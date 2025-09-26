import { useAuth } from '../contexts/AuthContext';

interface UseAuthorizationReturn {
  /**
   * Check if user has at least one of the specified roles
   */
  hasRole: (roles: string | string[]) => boolean;
  
  /**
   * Check if user has all the specified roles
   */
  hasAllRoles: (roles: string[]) => boolean;
  
  /**
   * Check if user is an admin
   */
  isAdmin: () => boolean;
  
  /**
   * Get the current user's role
   */
  userRole: string | undefined;
}

/**
 * Custom hook for checking user authorization in components
 * 
 * Example usage:
 * ```
 * const { hasRole, isAdmin } = useAuthorization();
 * 
 * // Conditionally render content
 * return (
 *   <div>
 *     {hasRole('super_admin') && <AdminPanel />}
 *     {isAdmin() && <ManageUsersButton />}
 *   </div>
 * );
 * ```
 */
export const useAuthorization = (): UseAuthorizationReturn => {
  const { user } = useAuth();
  
  const hasRole = (roles: string | string[]): boolean => {
    if (!user || !user.role) return false;
    
    const rolesToCheck = Array.isArray(roles) ? roles : [roles];
    return rolesToCheck.includes(user.role);
  };
  
  const hasAllRoles = (roles: string[]): boolean => {
    if (!user || !user.role) return false;
    
    // For now, a user can only have one role at a time
    // If in the future users can have multiple roles, this would check if the user has all the specified roles
    return roles.every(role => role === user.role);
  };
  
  const isAdmin = (): boolean => {
    return hasRole('super_admin');
  };
  
  return {
    hasRole,
    hasAllRoles,
    isAdmin,
    userRole: user?.role
  };
};

export default useAuthorization; 