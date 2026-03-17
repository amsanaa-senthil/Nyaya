"use client";

import { LayoutDashboard, PlayCircle, Trophy, Clock, Target, BarChart2, LogOut, User } from "lucide-react";
import { useEffect, useState } from "react";
import { supabase } from "../lib/supabaseClient";
import { useRouter } from "next/navigation";

export default function QuizDashboard() {
  const router = useRouter();
  const [userProfile, setUserProfile] = useState<any>(null);
  const [userStats, setUserStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  // Helper to convert seconds to "Xm Ys"
  const formatTime = (seconds: number) => {
    if (!seconds) return "0m 0s";
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs}s`;
  };

  useEffect(() => {
    async function getDashboardData() {
      // 1. Get current user
      const { data: { user }, error: authError } = await supabase.auth.getUser();

      if (authError || !user) {
        router.push("/login");
        return;
      }

      // 2. Fetch Profile and Stats from your new tables
      const [profileRes, statsRes] = await Promise.all([
        supabase.from("profiles").select("*").eq("id", user.id).single(),
        supabase.from("user_stats").select("*").eq("id", user.id).single()
      ]);

      setUserProfile(profileRes.data);
      setUserStats(statsRes.data);
      setLoading(false);
    }

    getDashboardData();
  }, [router]);

  const handleLogout = async () => {
    await supabase.auth.signOut();
    router.push("/login");
  };

  if (loading) {
    return <div className="min-h-screen flex items-center justify-center">Loading Nyaya Dashboard...</div>;
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6 md:p-10">
      <div className="max-w-6xl mx-auto space-y-8">
        
        {/* User Header Section */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
          <div className="flex items-center gap-4">
            <div className="h-16 w-16 bg-blue-600 rounded-full flex items-center justify-center text-white text-2xl font-bold uppercase">
              {userProfile?.first_name?.charAt(0) || "U"}
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-800">
                Welcome back, {userProfile?.first_name || "Student"}!
              </h1>
              <p className="text-gray-500 text-sm">Track your Nyaya learning progress here.</p>
            </div>
          </div>
          
          <div className="flex gap-3">

            {/*Edit Profile Button*/}
            <button 
              onClick={() => router.push("/dashboard/profile")}
              className="flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-xl font-semibold transition-all shadow-lg shadow-blue-200"
            >
              <User size={20} />
              Edit Profile
            </button>

            {/*Start New Quiz Button*/}
            <button className="flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-xl font-semibold transition-all shadow-lg shadow-blue-200">
              <PlayCircle size={20} />
              Start New Quiz
            </button>

            {/*Log Out Button*/}
             <button 
              onClick={handleLogout}
              className="flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-xl font-semibold transition-all shadow-lg shadow-blue-200"
            >
              <LogOut size={20} />
              Sign Out
            </button>

          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          
          <StatCard 
            title="Total Quizzes Taken" 
            value={userStats?.total_quizzes_taken || 0} 
            icon={<LayoutDashboard className="text-blue-600" />} 
            color="bg-blue-50"
          />

          <StatCard 
            title="Average Score" 
            value={`${userStats?.average_score || 0}%`} 
            icon={<BarChart2 className="text-purple-600" />} 
            color="bg-purple-50"
          />

          <StatCard 
            title="Accuracy Rate" 
            value={`${userStats?.accuracy_rate || 0}%`} 
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
                <p className="text-2xl font-bold text-gray-800">{userStats?.highest_score || 0}%</p>
              </div>
              <div className="text-right">
                <p className="text-xs text-gray-400 uppercase">Lowest</p>
                <p className="text-2xl font-bold text-gray-800">{userStats?.lowest_score || 0}%</p>
              </div>
            </div>
          </div>

          <StatCard 
            title="Time Spent per Quiz" 
            value={formatTime(userStats?.time_spent_per_quiz_seconds)} 
            icon={<Clock className="text-red-600" />} 
            color="bg-red-50"
          />

          <StatCard 
            title="Total Quizing Time" 
            value={formatTime(userStats?.total_quizzing_time_seconds)} 
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