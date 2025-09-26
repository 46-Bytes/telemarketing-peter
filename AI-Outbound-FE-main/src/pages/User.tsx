import React, { useState, useEffect } from 'react';
import { userApi } from '../api/api';
import { authApi } from '../api/authApi';
import { SignupData } from '../types/auth';

interface UserFormData extends SignupData {
  businessName: string;
  role?: string;
  // hasEbook: boolean;
  // ebookPath: string;
}

interface User {
  id: string;
  name: string;
  email: string;
  businessName: string;
  role: string;
}
const User: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [isUserModalOpen, setIsUserModalOpen] = useState(false);
  const [userFormData, setUserFormData] = useState<UserFormData>({
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
    businessName: '',
    role: 'user'
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [userCreationError, setUserCreationError] = useState<string | null>(null);
  const [userCreationSuccess, setUserCreationSuccess] = useState<string | null>(null);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isEditMode, setIsEditMode] = useState(false);
  const [selectedUserId, setSelectedUserId] = useState<string | null>(null);
  
  useEffect(() => {
    const fetchUsers = async () => {
      try {
        setIsLoading(true);
        setError(null);
        
        // Use getCampaigns instead of getUserCampaigns
        const allUsers = await userApi.getUsers();
        // console.log("All users:", allUsers);
        const getUserName = localStorage.getItem("userName");
        const filteredUsers = allUsers.data.filter((user: User) => user.name !== getUserName);
        setUsers(filteredUsers);
      } catch (error) {
        console.error("Failed to fetch Users:", error);
        setError(error instanceof Error ? error.message : "Failed to fetch Users");
      } finally {
        setIsLoading(false);
      }
    };

    fetchUsers();
  }, []);

  const handleUserFormChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type, checked } = e.target as any;
    setUserFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleEditUser = (user: User) => {
    setIsEditMode(true);
    setSelectedUserId(user.id);
    setUserFormData({
      name: user.name,
      email: user.email,
      password: '',
      confirmPassword: '',
      businessName: user.businessName || '',
      role: user.role || 'user'
    });
    setIsUserModalOpen(true);
  };

  const handleUserSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setUserCreationError(null);
    setIsSubmitting(true);

    try {
      if (userFormData.password !== userFormData.confirmPassword) {
        throw new Error('Passwords do not match');
      }

      if (isEditMode && selectedUserId) {
        // Update existing user
        await userApi.updateUser(selectedUserId, {
          name: userFormData.name,
          email: userFormData.email,
          ...(userFormData.password ? { password: userFormData.password } : {}),
          businessName: userFormData.businessName,
          role: userFormData.role
        });
        setUserCreationSuccess('User updated successfully!');
      } else {
        // Create new user
        await authApi.signup({
          name: userFormData.name,
          email: userFormData.email,
          password: userFormData.password,
          confirmPassword: userFormData.confirmPassword,
          businessName: userFormData.businessName,
          role: userFormData.role
        });
        setUserCreationSuccess('User created successfully!');
      }

      // Refresh the users list
      try {
        setIsLoading(true);
        const refreshedUsers = await userApi.getUsers();
        const getUserName = localStorage.getItem("userName");
        const filteredUsers = refreshedUsers.data.filter((user: User) => user.name !== getUserName);
        setUsers(filteredUsers);
        console.log("Users refreshed after user creation/update:", refreshedUsers);
      } catch (error) {
        console.error("Failed to refresh users:", error);
      } finally {
        setIsLoading(false);
      }

      // Reset form and close modal
      setUserFormData({
        name: '',
        email: '',
        password: '',
        confirmPassword: '',
        businessName: '',
        role: 'user'  
      });
      setIsUserModalOpen(false);
      setIsEditMode(false);
      setSelectedUserId(null);
      
      // Clear success message after 3 seconds
      setTimeout(() => {
        setUserCreationSuccess(null);
      }, 3000);
    } catch (error) {
      setUserCreationError(error instanceof Error ? error.message : 'Failed to create user');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4" role="alert">
        <strong className="font-bold">Error: </strong>
        <span className="block sm:inline">{error}</span>
      </div>
    );
  }

  return (
    <div className="w-full mx-auto p-6">
      {userCreationSuccess && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-4 flex items-center">
          <svg className="w-5 h-5 text-green-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
          </svg>
          <p className="text-sm text-green-700">{userCreationSuccess}</p>
        </div>
      )}
      
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-semibold text-gray-800">Users</h1>
        <button
          onClick={() => setIsUserModalOpen(true)}
          className="inline-flex items-center px-4 py-2 bg-green-500 hover:bg-green-600 text-white font-medium rounded-lg text-sm transition-colors duration-200"
        >
          <svg
            className="w-5 h-5 mr-2"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              d="M12 4v16m8-8H4"
            />
          </svg>
          Create User
        </button>
      </div>

      {users.length === 0 ? (
        <div className="bg-blue-50 border-l-4 border-blue-500 text-blue-700 p-4 mb-4" role="alert">
          <p>No users found.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {users.map(user => (
            <div key={user.id} className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow duration-300">
              <div className="bg-blue-50 px-4 py-3 border-b border-gray-100">
                <h3 className="text-lg font-semibold text-blue-700">{user.name}</h3>
              </div>
              
              <div className="p-4">
                <div className="space-y-2">
                  {/* <div className="flex justify-between">
                    <span className="text-sm font-medium text-gray-500">Campaign Date:</span>
                    <span className="text-sm text-gray-700">
                      {campaign.campaignDate || 'No date'}
                    </span>
                  </div> */}
{/*                   
                  <div className="flex justify-between">
                    <span className="text-sm font-medium text-gray-500">Created:</span>
                    <span className="text-sm text-gray-700">
                      {formatDate(campaign.created_at)}
                    </span>
                  </div>
                   */}
                  {/* <div className="flex justify-between">
                    <span className="text-sm font-medium text-gray-500">Business:</span>
                    <span className="text-sm text-gray-700">
                      {user.businessName || 'N/A'}
                    </span>
                  </div> */}
                  
                  <div className="flex justify-between">
                    <span className="text-sm font-medium text-gray-500">Full Name:</span>
                    <span className="text-sm text-gray-700">
                      {user.name || 'N/A'}
                    </span>
                  </div>

                  <div className="flex justify-between">
                    <span className="text-sm font-medium text-gray-500">Role:</span>
                    <span className="text-sm text-gray-700">
                      {user.role === "super_admin" ? "Super Admin" : "User"}
                    </span>
                  </div>
                  
                  <div className="flex justify-between">
                    <span className="text-sm font-medium text-gray-500">Email:</span>
                    <span className="text-sm text-gray-700 truncate max-w-[150px]" title={user.email || ''}>
                      {user.email || 'N/A'}
                    </span>
                  </div>

                  <div className="mt-3 pt-3 border-t border-gray-100">
                    <button
                      onClick={() => handleEditUser(user)}
                      className="w-full py-1.5 px-3 bg-blue-500 hover:bg-blue-600 text-white text-sm font-medium rounded transition-colors duration-200"
                    >
                      Edit User
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* User Creation Modal */}
      {isUserModalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-[150] overflow-y-auto">
          <div className="bg-white rounded-lg shadow-lg w-full max-w-md my-4 mx-auto flex flex-col max-h-[90vh]">
            {/* Modal Header - Sticky */}
            <div className="sticky top-0 z-10 px-6 py-4 border-b border-gray-200 bg-white rounded-t-lg flex justify-between items-center">
              <h3 className="text-lg font-semibold text-gray-800">{isEditMode ? 'Edit User' : 'Create New User'}</h3>
              <button
                type="button"
                onClick={() => {
                  setIsUserModalOpen(false);
                  setIsEditMode(false);
                  setUserFormData({
                    name: '',
                    email: '',
                    password: '',
                    confirmPassword: '',
                    businessName: '',
                    role: 'user'
                  });
                  setSelectedUserId(null);
                }}
                className="text-gray-500 hover:text-gray-700 focus:outline-none"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            
            {/* Modal Body - Scrollable */}
            <div className="overflow-y-auto p-6 pt-4">
              <form onSubmit={handleUserSubmit} className="space-y-3">
                <div className="grid grid-cols-1 gap-3">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-0.5">
                      Full Name
                    </label>
                    <input
                      type="text"
                      name="name"
                      value={userFormData.name}
                      onChange={handleUserFormChange}
                      required
                      className="w-full py-1.5 px-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-0.5">
                      Email
                    </label>
                    <input
                      type="email"
                      name="email"
                      value={userFormData.email}
                      onChange={handleUserFormChange}
                      required
                      disabled={isEditMode}
                      className="w-full py-1.5 px-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-0.5">
                      Role
                    </label>
                    <select
                      name="role"
                      value={userFormData.role}
                      onChange={handleUserFormChange}
                      required
                      // disabled={isEditMode}
                      className="w-full py-1.5 px-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    >
                      <option value="super_admin">Admin</option>
                      <option value="user">User</option>
                    </select>
                  </div>


                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-0.5">
                        Password
                      </label>
                      <div className="relative">
                        <input
                          type={showPassword ? "text" : "password"}
                          name="password"
                          value={userFormData.password}
                          onChange={handleUserFormChange}
                          required
                          className="w-full py-1.5 px-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        />
                        <button 
                          type="button"
                          onClick={() => setShowPassword(!showPassword)}
                          className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-500 hover:text-gray-700 focus:outline-none"
                        >
                          {showPassword ? (
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                            </svg>
                          ) : (
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                            </svg>
                          )}
                        </button>
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-0.5">
                        Confirm Password
                      </label>
                      <div className="relative">
                        <input
                          type={showConfirmPassword ? "text" : "password"}
                          name="confirmPassword"
                          value={userFormData.confirmPassword}
                          onChange={handleUserFormChange}
                          required
                          className="w-full py-1.5 px-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        />
                        <button 
                          type="button"
                          onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                          className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-500 hover:text-gray-700 focus:outline-none"
                        >
                          {showConfirmPassword ? (
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                            </svg>
                          ) : (
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                            </svg>
                          )}
                        </button>
                      </div>
                    </div>
                  </div>

                  {/* <div>
                    <label className="block text-sm font-medium text-gray-700 mb-0.5">
                      Business Name
                    </label>
                    <input
                      type="text"
                      name="businessName"
                      value={userFormData.businessName}
                      onChange={handleUserFormChange}
                      required
                      className="w-full py-1.5 px-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div> */}

                  {/* <div className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      id="hasEbook"
                      name="hasEbook"
                      checked={userFormData.hasEbook}
                      onChange={handleUserFormChange}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    <label htmlFor="hasEbook" className="text-sm font-medium text-gray-700">
                      Include Ebook
                    </label>
                  </div>

                  {userFormData.hasEbook && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Upload Ebook (PDF)
                      </label>
                      <div 
                        className={`border-2 border-dashed rounded-lg p-2 flex flex-col items-center justify-center bg-gray-50 transition-colors ${isDragging ? 'border-blue-500 bg-blue-50' : 'border-gray-300'}`}
                        onDragOver={handleDragOver}
                        onDragLeave={handleDragLeave}
                        onDrop={handleDrop}
                        style={{ minHeight: '80px' }}
                      >
                        <div className="flex items-center justify-center gap-2">
                          <svg className="h-6 w-6 text-gray-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                          </svg>
                          <div>
                            <p className="text-xs text-gray-600">
                              <label htmlFor="file-upload" className="text-blue-600 hover:underline cursor-pointer">Browse</label> or drag PDF
                            </p>
                            <p className="text-xs text-gray-500">Max: 5MB</p>
                          </div>
                        </div>
                        <input
                          id="file-upload"
                          name="file-upload"
                          type="file"
                          accept=".pdf"
                          onChange={handleFileChange}
                          required={userFormData.hasEbook}
                          className="hidden"
                        />
                        {selectedFile && (
                          <div className="mt-1 text-xs text-gray-700 bg-blue-50 px-2 py-0.5 rounded-full w-full text-center truncate">
                            {selectedFile.name.length > 25 ? selectedFile.name.substring(0, 25) + '...' : selectedFile.name}
                          </div>
                        )}
                        
                        {isUploading && (
                          <div className="w-full mt-1">
                            <div className="w-full bg-gray-200 rounded-full h-1">
                              <div 
                                className="bg-blue-600 h-1 rounded-full transition-all duration-300" 
                                style={{ width: `${uploadProgress}%` }}
                              ></div>
                            </div>
                            <p className="text-xs text-gray-500 text-center">
                              {Math.round(uploadProgress)}%
                            </p>
                          </div>
                        )}
                      </div>
                    </div>
                  )} */}

                  {userCreationError && (
                    <div className="p-2 bg-red-50 border border-red-200 rounded-lg">
                      <p className="text-sm text-red-600">{userCreationError}</p>
                    </div>
                  )}
                </div>

                {/* Modal Footer - Sticky */}
                <div className="pt-3 mt-2">
                  <button
                    type="submit"
                    disabled={isSubmitting}
                    className="w-full px-3 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isSubmitting ? (isEditMode ? 'Updating...' : 'Creating...') : (isEditMode ? 'Update User' : 'Create User')}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default User;
