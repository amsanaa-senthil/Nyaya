"use client";

import { LayoutDashboard, PlayCircle, Trophy, Clock, Target, BarChart2 } from "lucide-react";

export default function QuizDashboard() {
  // Mock data - replace with PostgreSQL fetch later
  const stats = {
    totalQuizzes: 12,
    avgScore: 78,
    highestScore: 95,
    lowestScore: 62,
    accuracy: 84,
    avgTime: "4m 20s",
    totalTime: "120m 45s"
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6 md:p-10">
      <div className="max-w-6xl mx-auto space-y-8">
        
        {/* User Header Section */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
          <div className="flex items-center gap-4">
            <div className="h-16 w-16 bg-blue-600 rounded-full flex items-center justify-center text-white text-2xl font-bold">
              S
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-800">Welcome back, Sanithu!</h1>
              <p className="text-gray-500 text-sm">Track your Nyaya learning progress here.</p>
            </div>
          </div>
          <button className="flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-xl font-semibold transition-all shadow-lg shadow-blue-200">
            <PlayCircle size={20} />
            Start New Quiz
          </button>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          
          {/* Total Quizzes */}
          <StatCard 
            title="Total Quizzes Taken" 
            value={stats.totalQuizzes} 
            icon={<LayoutDashboard className="text-blue-600" />} 
            color="bg-blue-50"
          />

          {/* Average Score */}
          <StatCard 
            title="Average Score" 
            value={`${stats.avgScore}%`} 
            icon={<BarChart2 className="text-purple-600" />} 
            color="bg-purple-50"
          />

          {/* Accuracy Rate */}
          <StatCard 
            title="Accuracy Rate" 
            value={`${stats.accuracy}%`} 
            icon={<Target className="text-green-600" />} 
            color="bg-green-50"
          />

          {/* Range: High/Low */}
          <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 bg-orange-50 rounded-lg">
                <Trophy className="text-orange-600" size={24} />
              </div>
              <span className="text-gray-600 font-medium">Score Range</span>
            </div>
            <div className="flex justify-between items-end">
              <div>
                <p className="text-xs text-gray-400 uppercase">Highest</p>
                <p className="text-2xl font-bold text-gray-800">{stats.highestScore}%</p>
              </div>
              <div className="text-right">
                <p className="text-xs text-gray-400 uppercase">Lowest</p>
                <p className="text-2xl font-bold text-gray-800">{stats.lowestScore}%</p>
              </div>
            </div>
          </div>

          {/* Time Spent */}
          <StatCard 
            title="Time Spent per Quiz" 
            value={stats.avgTime} 
            icon={<Clock className="text-red-600" />} 
            color="bg-red-50"
          />

                    <StatCard 
            title="Total Quizing Time" 
            value={stats.totalTime} 
            icon={<Clock className="text-blue-600" />} 
            color="bg-blue-50"
          />

        </div>
      </div>
    </div>
  );
}

// Reusable Card Component
function StatCard({ title, value, icon, color }: { title: string, value: string | number, icon: React.ReactNode, color: string }) {
  return (
    <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 flex items-center gap-4">
      <div className={`p-4 ${color} rounded-xl`}>
        {icon}
      </div>
      <div>
        <p className="text-sm text-gray-500 font-medium">{title}</p>
        <p className="text-2xl font-bold text-gray-800">{value}</p>
      </div>
    </div>
  );
}