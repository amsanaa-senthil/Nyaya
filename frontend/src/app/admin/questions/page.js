'use client';

import { useState } from 'react';
import { useAdminAuth } from '@/hooks/useAdminAuth';

export default function QuestionsPage() {
  const { admin, loading } = useAdminAuth();
  const [selectedQuiz, setSelectedQuiz] = useState('');
  const [questions, setQuestions] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [questionText, setQuestionText] = useState('');
  const [options, setOptions] = useState([
    { text: '', isCorrect: false },
    { text: '', isCorrect: false },
    { text: '', isCorrect: false },
    { text: '', isCorrect: false },
  ]);

  if (loading) return <div>Loading...</div>;

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">Manage Questions</h1>

        <div className="bg-white p-6 rounded shadow mb-8">
          <p className="text-gray-600 mb-4">Select a quiz to manage its questions</p>
          <select
            value={selectedQuiz}
            onChange={(e) => setSelectedQuiz(e.target.value)}
            className="w-full p-2 border rounded"
          >
            <option value="">-- Select Quiz --</option>
          </select>
        </div>

        {selectedQuiz && (
          <>
            <button
              onClick={() => setShowForm(!showForm)}
              className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 mb-8"
            >
              + Add Question
            </button>

            {showForm && (
              <form className="bg-white p-6 rounded shadow mb-8">
                <input
                  type="text"
                  placeholder="Question Text"
                  value={questionText}
                  onChange={(e) => setQuestionText(e.target.value)}
                  className="w-full p-2 border rounded mb-4"
                />
                
                <div className="mb-4">
                  <h3 className="font-semibold mb-2">Options</h3>
                  {options.map((opt, idx) => (
                    <div key={idx} className="mb-2 flex gap-2">
                      <input
                        type="text"
                        placeholder={`Option ${idx + 1}`}
                        value={opt.text}
                        onChange={(e) => {
                          const newOpts = [...options];
                          newOpts[idx].text = e.target.value;
                          setOptions(newOpts);
                        }}
                        className="flex-1 p-2 border rounded"
                      />
                      <label className="flex items-center gap-2">
                        <input
                          type="checkbox"
                          checked={opt.isCorrect}
                          onChange={(e) => {
                            const newOpts = [...options];
                            newOpts[idx].isCorrect = e.target.checked;
                            setOptions(newOpts);
                          }}
                        />
                        Correct
                      </label>
                    </div>
                  ))}
                </div>

                <button type="submit" className="bg-green-600 text-white px-4 py-2 rounded">
                  Add Question
                </button>
              </form>
            )}
          </>
        )}
      </div>
    </div>
  );
}