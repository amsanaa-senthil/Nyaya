'use client';

import { useAdminAuth } from '@/hooks/useAdminAuth';

export default function UsersPage() {
  const { admin, loading } = useAdminAuth();

  if (loading) return <div>Loading...</div>;

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">Manage Users</h1>

        <div className="bg-white p-6 rounded shadow">
          <p className="text-gray-600">User management coming soon.</p>
        </div>
      </div>
    </div>
  );
}