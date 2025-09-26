import React, { useState, useEffect } from 'react';
import { userApi } from '../api/api';
import { User } from '../types/auth';

interface ExtendedUser extends User {
  id: string;
  businessName?: string;
}

const UsersList: React.FC = () => {
  const [users, setUsers] = useState<ExtendedUser[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchUsers = async () => {
      setIsLoading(true);
      try {
        const response = await userApi.getUsers();
        setUsers(response.data || []);
      } catch (err) {
        console.error('Error fetching users:', err);
        setError('Failed to fetch users');
      } finally {
        setIsLoading(false);
      }
    };

    fetchUsers();
  }, []);

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border-l-4 border-red-500 text-red-700 p-4 mb-4" role="alert">
        <p>{error}</p>
      </div>
    );
  }

  if (users.length === 0) {
    return (
      <div className="bg-blue-50 border-l-4 border-blue-500 text-blue-700 p-4 mb-4" role="alert">
        <p>No users found.</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full bg-white">
        <thead className="bg-gray-100">
          <tr>
            <th className="py-3 px-4 text-left text-sm font-semibold text-gray-700">Name</th>
            <th className="py-3 px-4 text-left text-sm font-semibold text-gray-700">Email</th>
            <th className="py-3 px-4 text-left text-sm font-semibold text-gray-700">Business Name</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200">
          {users.map((user) => (
            <tr key={user.id} className="hover:bg-gray-50">
              <td className="py-3 px-4 text-sm text-gray-900">{user.name}</td>
              <td className="py-3 px-4 text-sm text-gray-900">{user.email}</td>
              <td className="py-3 px-4 text-sm text-gray-900">{user.businessName || '-'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default UsersList; 