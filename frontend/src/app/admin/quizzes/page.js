'use client';

import { useEffect, useState } from 'react';
import { useAdminAuth } from '@/hooks/useAdminAuth';
import { adminAPI } from '@/lib/api';

export default function QuizzesPage() {
  const { admin, loading } = useAdminAuth();
  const [quizzes, setQuizzes] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (admin) fetchQuizzes();
  }, [admin]);

  const fetchQuizzes = async () => {
    try {
      const data = await adminAPI.request('/quizzes');
      setQuizzes(data);
    } catch (err) {
      console.error('Failed to fetch quizzes:', err);
    }
  };

  const handleCreateQuiz = async (e) => {
    e.preventDefault();
    setSubmitting(true);

    try {
      await adminAPI.request('/quizzes', {
        method: 'POST',
        body: JSON.stringify({ title, description }),
      });
      setTitle('');
      setDescription('');
      setShowForm(false);
      await fetchQuizzes();
    } catch (err) {
      alert('Failed to create quiz: ' + err.message);
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteQuiz = async (quizId) => {
    if (!confirm('Are you sure?')) return;

    try {
      await adminAPI.request(`/quizzes/${quizId}`, { method: 'DELETE' });
      await fetchQuizzes();
    } catch (err) {
      alert('Failed to delete quiz: ' + err.message);
    }
  };

  if (loading) return <div>Loading...</div>;

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-6xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold">Manage Quizzes</h1>
          <button
            onClick={() => setShowForm(!showForm)}
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
          >
            + New Quiz
          </button>
        </div>

        {showForm && (
          <form onSubmit={handleCreateQuiz} className="bg-white p-6 rounded shadow mb-8">
            <input
              type="text"
              placeholder="Quiz Title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full p-2 border rounded mb-4"
              required
            />
            <textarea
              placeholder="Description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full p-2 border rounded mb-4"
              rows="3"
            />
            <button
              type="submit"
              disabled={submitting}
              className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700"
            >
              {submitting ? 'Creating...' : 'Create Quiz'}
            </button>
          </form>
        )}

        <div className="bg-white rounded shadow">
          {quizzes.length === 0 ? (
            <p className="p-6 text-gray-600">No quizzes yet. Create one to get started!</p>
          ) : (
            <table className="w-full">
              <thead className="bg-gray-200">
                <tr>
                  <th className="p-4 text-left">Title</th>
                  <th className="p-4 text-left">Questions</th>
                  <th className="p-4 text-left">Created</th>
                  <th className="p-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {quizzes.map((quiz) => (
                  <tr key={quiz.id} className="border-t hover:bg-gray-50">
                    <td className="p-4">{quiz.title}</td>
                    <td className="p-4">{quiz.question_count}</td>
                    <td className="p-4">{new Date(quiz.created_at).toLocaleDateString()}</td>
                    <td className="p-4 text-right">
                      <button
                        onClick={() => handleDeleteQuiz(quiz.id)}
                        className="text-red-600 hover:text-red-800"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}