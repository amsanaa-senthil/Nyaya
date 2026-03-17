"use client";
import { useState, useEffect } from "react";
import { supabase } from "@/lib/supabaseClient";
import { useRouter } from "next/navigation";
import { User, Mail, UserCircle, ShieldCheck } from "lucide-react";
import Image from "next/image";

/**
 * ProfileDisplay Component:
 * This component fetches user data from Supabase and renders a read-only 
 * view of the profile. This serves as the "Display State" before editing.
 */
export default function ProfileDisplay() {
  const router = useRouter();
  
  // loading: Controls whether to show a placeholder while waiting for DB data
  const [loading, setLoading] = useState(true);
  
  // profile: Local state to hold the specific fields we want to show the user
  const [profile, setProfile] = useState({
    firstName: "",
    surname: "",
    username: "",
    email: "",
    avatarUrl: "/Nyaya_logo_temp.png", // Default image fallback
  });

  /**
   * fetchUserData:
   * 1. Checks if the user is authenticated.
   * 2. Pulls user-specific details from the PostgreSQL 'profiles' table.
   */
    useEffect(() => {
        const fetchUserData = async () => {
        try {
            // 1. Get the current user session
            const { data: { user }, error: authError } = await supabase.auth.getUser();
            
            if (authError || !user) {
            console.log("Auth Error or no user:", authError);
            router.push("/login");
            return;
            }

            // 2. Fetch the specific row from the profiles table
            // We use '*' first to see exactly what columns exist if it fails
            const { data, error: dbError } = await supabase
            .from("profiles")
            .select("*") 
            .eq("id", user.id)
            .single();

            if (dbError) {
            console.error("Database Error:", dbError.message);
            return;
            }

            if (data) {
            console.log("Supabase Data Received:", data); // Check your console for this!
            
            // 3. Map the data. Ensure these column names match your Supabase Table!
            setProfile({
                firstName: data.first_name || "Not Set",
                surname: data.surname || "Not Set",
                username: data.username || "Not Set",
                email: data.email || user.email || "Not Set",
                avatarUrl: data.avatar_url || "/Nyaya_logo_temp.png",
            });
            }
        } catch (err) {
            console.error("Unexpected Error:", err);
        } finally {
            setLoading(false);
        }
        };

        fetchUserData();
    }, [router]);

  // Temporary UI shown during the initial database handshake
  if (loading) return <p className="text-center text-gray-500 py-10">Loading Profile Details...</p>;

  return (
    <div className="bg-white p-8 rounded-3xl shadow-xl w-full max-w-md border border-gray-100 mx-auto">
      
      {/* Profile Header: Avatar and Title */}
      <div className="flex flex-col items-center mb-8">
        <div className="relative h-28 w-28 mb-4">
          <Image 
            src={profile.avatarUrl} 
            alt="User Avatar" 
            fill 
            className="rounded-full border-4 border-slate-800 object-cover bg-slate-900 shadow-md" 
          />
        </div>
        <h2 className="text-2xl font-bold text-gray-800">Account Details</h2>
        <p className="text-sm text-gray-400">View your current profile information</p>
      </div>

      <div className="space-y-6">

        {/* First Name  Row */}
        <div className="space-y-1">
          <label className="text-xs font-bold text-gray-400 uppercase tracking-wider ml-1">First Name</label>
          <div className="flex items-center gap-3 h-12 p-3 bg-gray-50 rounded-xl border border-gray-100 text-gray-700 font-medium">
            <span className="truncate">{profile.firstName}</span>
          </div>
        </div>

        {/* Surname Row */}
        <div className="space-y-1">
          <label className="text-xs font-bold text-gray-400 uppercase tracking-wider ml-1">Surname</label>
          <div className="flex items-center gap-3 h-12 p-3 bg-gray-50 rounded-xl border border-gray-100 text-gray-700 font-medium">
            <span className="truncate">{profile.surname}</span>
          </div>
        </div>

        {/* Username Row */}
        <div className="space-y-1">
          <label className="text-xs font-bold text-gray-400 uppercase tracking-wider ml-1">Username</label>
          <div className="flex items-center gap-3 h-12 p-3 bg-gray-50 rounded-xl border border-gray-100 text-gray-700 font-medium">
            <UserCircle size={18} className="text-gray-400 shrink-0" />
            <span className="truncate">{profile.username}</span>
          </div>
        </div>

        {/* Email Row */}
        <div className="space-y-1">
          <label className="text-xs font-bold text-gray-400 uppercase tracking-wider ml-1 flex items-center gap-1">
            Email Address <ShieldCheck size={12} className="text-green-500" />
          </label>
          <div className="flex items-center gap-3 h-12 p-3 bg-gray-100 rounded-xl border border-gray-200 text-gray-400 italic">
            <Mail size={18} className="shrink-0" />
            <span className="truncate">{profile.email}</span>
          </div>
        </div>
      </div>
    </div> // This closes the main white card
  );
}