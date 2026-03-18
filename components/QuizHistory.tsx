"use client";
import { useEffect, useState } from "react";
import { supabase } from "@/lib/supabaseClient";
import { Clock, Trophy, Calendar, ChevronRight, Award } from "lucide-react";

/**
 * QuizHistory Component
 * Logic: Fetches all rows from 'quiz_history' for the logged-in user.
 * Design: Renders a vertical list of cards with conditional coloring based on score.
 */
export default function QuizHistory() {
  const [history, setHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchHistory = async () => {
      // 1. Identify the current user session
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) return;

      // 2. Query the 'quiz_history' table
      // We order by 'completed_at' descending to show the most recent quizzes at the top
      const { data, error } = await supabase
        .from("quiz_history")
        .select("*")
        .eq("user_id", user.id)
        .order("completed_at", { ascending: false });

      if (!error) {
        setHistory(data || []);
      } else {
        console.error("Error fetching quiz history:", error.message);
      }
      
      setLoading(false);
    };

    fetchHistory();
  }, []);

  // Loading state prevents layout shift while Supabase responds
  if (loading) return <div className="p-10 text-center text-gray-500 font-medium">Loading your history...</div>;

  return (
    <div className="space-y-6">
      {/* Header section with total count */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-800 tracking-tight">Quiz History</h2>
        <span className="bg-blue-50 text-blue-600 px-3 py-1 rounded-full text-xs font-bold">
          {history.length} Total Attempts
        </span>
      </div>

      {/* Conditional Rendering: Check if history has data */}
      {history.length > 0 ? (
        <div className="grid gap-4">
          {history.map((quiz) => (
            <div 
              key={quiz.id} 
              className="group bg-white p-5 rounded-2xl border border-gray-100 shadow-sm hover:shadow-md hover:border-blue-200 transition-all flex flex-col md:flex-row md:items-center justify-between gap-4"
            >
              <div className="flex items-center gap-4">
                {/* Score Badge: 
                  - Green: 75%+ (Excellent)
                  - Blue: 40-74% (Passed/Average)
                  - Red: Below 40% (Needs Review)
                */}
                <div className={`h-14 w-14 shrink-0 rounded-2xl flex flex-col items-center justify-center border transition-colors ${
                  quiz.score >= 75 ? 'bg-green-50 border-green-100 text-green-600' : 
                  quiz.score >= 40 ? 'bg-blue-50 border-blue-100 text-blue-600' : 
                  'bg-red-50 border-red-100 text-red-600'
                }`}>
                  <span className="text-lg font-bold">{quiz.score}%</span>
                  <span className="text-[10px] uppercase font-black opacity-60">Score</span>
                </div>

                <div>
                  <h4 className="font-bold text-gray-800 group-hover:text-blue-600 transition-colors">
                    {quiz.quiz_name}
                  </h4>
                  <div className="flex flex-wrap items-center gap-x-4 gap-y-1 mt-1">
                    {/* Format the date to a readable UK format */}
                    <span className="flex items-center gap-1 text-xs text-gray-400">
                      <Calendar size={12} />
                      {new Date(quiz.completed_at).toLocaleDateString('en-GB')}
                    </span>
                    {/* Calculate minutes and seconds from raw seconds */}
                    <span className="flex items-center gap-1 text-xs text-gray-400">
                      <Clock size={12} />
                      {Math.floor(quiz.time_taken_seconds / 60)}m {quiz.time_taken_seconds % 60}s
                    </span>
                  </div>
                </div>
              </div>

              {/* Right side: Questions count and arrow link */}
              <div className="flex items-center justify-between md:justify-end gap-6 border-t md:border-t-0 pt-3 md:pt-0">
                <div className="text-left md:text-right">
                  <p className="text-sm font-bold text-gray-700">
                    {Math.round((quiz.score / 100) * quiz.total_questions)} / {quiz.total_questions} Correct
                  </p>
                  <p className="text-[10px] text-gray-400 uppercase tracking-widest font-black">Performance</p>
                </div>
                <button className="p-2 bg-gray-50 rounded-full text-gray-300 group-hover:bg-blue-600 group-hover:text-white transition-all">
                  <ChevronRight size={20} />
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        /* Empty State: Shown if user has zero records in quiz_history */
        <div className="text-center py-20 bg-white rounded-3xl border-2 border-dashed border-gray-100">
          <Award size={48} className="mx-auto text-gray-200 mb-4" />
          <p className="text-gray-500 font-medium">No quiz records found.</p>
          <p className="text-sm text-gray-400 mt-1">Complete a quiz to see your history here!</p>
        </div>
      )}
    </div>
  );
}