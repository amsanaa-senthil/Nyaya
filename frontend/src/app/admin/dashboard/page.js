'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

export default function AdminDashboard() {
  const router = useRouter();
  const [admin, setAdmin] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAdmin = async () => {
      const token = localStorage.getItem('admin_token');
      
      if (!token) {
        router.push('/admin/login');
        return;
      }

      try {
        const response = await fetch('http://localhost:8000/api/admin/me', {
          headers: { 'Authorization': `Bearer ${token}` },
        });

        if (!response.ok) throw new Error('Unauthorized');
        const data = await response.json();
        setAdmin(data);
      } catch {
        localStorage.removeItem('admin_token');
        localStorage.removeItem('admin_id');
        router.push('/admin/login');
      } finally {
        setLoading(false);
      }
    };

    fetchAdmin();
  }, [router]);

  const handleLogout = () => {
    localStorage.removeItem('admin_token');
    localStorage.removeItem('admin_id');
    localStorage.removeItem('admin_name');
    router.push('/admin/login');
  };

  if (loading) return <div className="flex items-center justify-center h-screen">Loading...</div>;
  if (!admin) return null;

  return (
    <div className="min-h-screen bg-gray-100">
      <nav className="bg-blue-600 text-white p-4 flex justify-between items-center shadow-lg">
        <h1 className="text-2xl font-bold">Nyaya Admin Dashboard</h1>
        <div className="flex items-center gap-4">
          <span className="text-sm">Welcome, {admin.full_name}</span>
          <button
            onClick={handleLogout}
            className="bg-red-600 px-4 py-2 rounded hover:bg-red-700 transition"
          >
            Logout
          </button>
        </div>
      </nav>

      <div className="p-8 max-w-6xl mx-auto">
        <h2 className="text-3xl font-bold mb-8">Dashboard</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Link href="/admin/quizzes">
            <div className="bg-white p-8 rounded-lg shadow hover:shadow-lg cursor-pointer transition">
              <div className="text-4xl mb-4">📝</div>
              <h3 className="font-bold text-xl mb-2">Manage Quizzes</h3>
              <p className="text-gray-600">Create, edit, and delete quizzes</p>
            </div>
          </Link>

          <Link href="/admin/questions">
            <div className="bg-white p-8 rounded-lg shadow hover:shadow-lg cursor-pointer transition">
              <div className="text-4xl mb-4">❓</div>
              <h3 className="font-bold text-xl mb-2">Manage Questions</h3>
              <p className="text-gray-600">Add and edit quiz questions</p>
            </div>
          </Link>

          <Link href="/admin/analytics">
            <div className="bg-white p-8 rounded-lg shadow hover:shadow-lg cursor-pointer transition">
              <div className="text-4xl mb-4">📊</div>
              <h3 className="font-bold text-xl mb-2">Analytics</h3>
              <p className="text-gray-600">View quiz performance and statistics</p>
            </div>
          </Link>

          <Link href="/admin/users">
            <div className="bg-white p-8 rounded-lg shadow hover:shadow-lg cursor-pointer transition">
              <div className="text-4xl mb-4">👥</div>
              <h3 className="font-bold text-xl mb-2">Manage Users</h3>
              <p className="text-gray-600">View and manage user accounts</p>
            </div>
          </Link>
        </div>
      </div>
    </div>
  );
}