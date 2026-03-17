"use client";
import { useState, useEffect } from "react";
import { supabase } from "@/lib/supabaseClient";
import { useRouter } from "next/navigation";
import { Lock, Mail, UserCircle, ShieldCheck, Pencil, X, Camera } from "lucide-react";
import Image from "next/image";

/**
 * ProfileDisplay Component:
 * This component fetches user data from Supabase and renders a read-only 
 * view of the profile. This serves as the "Display State" before editing.
 */
export default function ProfileDisplay() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false); // State for the "Save" button loading
  const [errorMsg, setErrorMsg] = useState(""); // State to hold error messages
  
  // profile: Local state to hold the specific fields we want to show the user
  const [profile, setProfile] = useState({
    firstName: "",
    surname: "",
    username: "",
    email: "",
    avatarUrl: "/Nyaya_logo_temp.png", // Default image fallback
  });

  // --- MODAL STATES ---
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingField, setEditingField] = useState<{key: string, label: string}>({ key: "", label: "" });
  const [newValue, setNewValue] = useState("");

  // Clear error message when user starts typing
  useEffect(() => {
    if (errorMsg) setErrorMsg("");
  }, [newValue]);

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

    /**
   * Opens the edit modal for a specific field
   */
  const openEditModal = (fieldKey: string, label: string, currentValue: string) => {
    setEditingField({ key: fieldKey, label: label });
    setNewValue(currentValue === "Not Set" ? "" : currentValue);
    setIsModalOpen(true);
  };

const handleSave = async () => {
    const trimmedValue = newValue.trim();
    setErrorMsg(""); // Reset error state

    // 1. Basic Validation
    if (!trimmedValue) {
      alert("Field cannot be empty");
      return;
    }

    // 2. Username Specific Rules
    if (editingField.key === "username") {
      if (trimmedValue.includes("@")) {
        setErrorMsg("Usernames cannot contain the '@' symbol.");
        return;
      }

      setUpdating(true);

      try {
        // Check for Uniqueness
        const { data: { user } } = await supabase.auth.getUser();
        const { data: existingUser, error: checkError } = await supabase
          .from("profiles")
          .select("id")
          .ilike("username", trimmedValue) 
          .neq("id", user?.id) // Don't count the current user's own name
          .maybeSingle(); // Better than .single() as it doesn't throw error if 0 found

        if (existingUser) {
          setErrorMsg("This username is already taken. Please choose another.");
          setUpdating(false);
          return;
        }
      } catch (err) {
        console.error("Check Error:", err);
      }
    }

    // 3. Perform the actual Update
    setUpdating(true);
    try {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) throw new Error("No user session");

      const columnMap: Record<string, string> = {
        firstName: "first_name",
        surname: "surname",
        username: "username"
      };

      const { error: dbError } = await supabase
        .from("profiles")
        .update({ [columnMap[editingField.key]]: trimmedValue })
        .eq("id", user.id);

      if (dbError) throw dbError;

      // Update local UI and Close
      setProfile((prev) => ({ ...prev, [editingField.key]: trimmedValue }));
      setIsModalOpen(false);
      
    } catch (error: any) {
      setErrorMsg("Error: " + error.message);
    } finally {
      setUpdating(false);
    }
  };

  // Temporary UI shown during the initial database handshake
  if (loading) return <p className="text-center text-gray-500 py-10">Loading Profile Details...</p>;

  return (
    <div className="bg-white p-8 rounded-3xl shadow-xl w-full max-w-md border border-gray-100 mx-auto">
      
      {/* Profile Header: Avatar with Hover Effect */}
      <div className="flex flex-col items-center mb-8">
        <div className="relative h-28 w-28 mb-4 group cursor-pointer">
            
          {/* Main Avatar Image */}
          <Image 
            src={profile.avatarUrl} 
            alt="User Avatar" 
            fill 
            className="rounded-full border-4 border-slate-800 object-cover bg-slate-900 shadow-md transition-all duration-300 group-hover:opacity-60 group-hover:scale-105" 
          />
          
          {/* Camera Icon Overlay (Appears on Hover) */}
          <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-300">
            <div className="bg-slate-800/50 p-2 rounded-full backdrop-blur-sm">
                {/* Note: You may need to import Camera from lucide-react at the top */}
                <Camera size={24} className="text-white" />
            </div>
          </div>
        </div>
        
        <h2 className="text-2xl font-bold text-gray-800">Account Details</h2>
        <p className="text-sm text-gray-400">View and edit your current profile information</p>
      </div>

      <div className="space-y-6">

        {/* First Name  Row */}
        <div className="space-y-1">
          <label className="text-xs font-bold text-gray-400 uppercase tracking-wider ml-1">First Name</label>
          <div className="flex items-center justify-between gap-3 h-12 p-3 bg-gray-50 rounded-xl border border-gray-100 text-gray-700 font-medium">
            <span className="truncate">{profile.firstName}</span>
            <button onClick={() => openEditModal("firstName", "First Name", profile.firstName)} className="text-blue-500 hover:text-blue-700 transition-colors shrink-0 ml-2">
                <Pencil size={14} />
            </button>
          </div>
        </div>

        {/* Surname Row */}
        <div className="space-y-1">
          <label className="text-xs font-bold text-gray-400 uppercase tracking-wider ml-1">Surname</label>
          <div className="flex items-center justify-between gap-3 h-12 p-3 bg-gray-50 rounded-xl border border-gray-100 text-gray-700 font-medium">
            <span className="truncate">{profile.surname}</span>
            <button onClick={() => openEditModal("surname", "Surname", profile.surname)} className="text-blue-500 hover:text-blue-700 transition-colors shrink-0 ml-2">
                <Pencil size={14} />
            </button>
          </div>
        </div>

        {/* Username Row */}
        <div className="space-y-1">
          <label className="text-xs font-bold text-gray-400 uppercase tracking-wider ml-1">Username</label>
          <div className="flex items-center justify-between gap-3 h-12 p-3 bg-gray-50 rounded-xl border border-gray-100 text-gray-700 font-medium">
            <span className="truncate">{profile.username}</span>
            <button onClick={() => openEditModal("username", "Username", profile.username)} className="text-blue-500 hover:text-blue-700 transition-colors shrink-0 ml-2">
                <Pencil size={14} />
            </button>
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

        {/* Action Buttons */}
        <div className="pt-6 space-y-3">
          {/* Reset Password Button */}
          <button 
            type="button"
            onClick={() => router.push("/dashboard/profile/reset-password")}
            className="w-full flex items-center justify-center gap-2 h-12 bg-blue-600 rounded-xl text-white font-semibold hover:bg-blue-700 transition-all shadow-lg shadow-blue-100"
          >
            <Lock size={16} />
            Reset Password
          </button>

          {/* Back to Dashboard Button */}
          <button 
            type="button"
            onClick={() => router.push("/dashboard")} // Navigates back to the main dashboard route
            className="w-full flex items-center justify-center gap-2 h-12 bg-blue-600 rounded-xl text-white font-semibold hover:bg-blue-700 transition-all shadow-lg shadow-blue-100"
          >
            Go Back to Dashboard
          </button>
        </div>
      </div>

      {/* --- EDIT MODAL OVERLAY --- */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white w-full max-w-sm rounded-2xl p-6 shadow-2xl animate-in fade-in zoom-in duration-200">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-bold text-gray-800">Edit {editingField.label}</h3>
              <button onClick={() => setIsModalOpen(false)} className="text-gray-400 hover:text-gray-600">
                <X size={20} />
              </button>
            </div>

            {/* ERROR MESSAGE DISPLAY */}
            {errorMsg && (
                <div className="mb-4 p-3 bg-red-50 border-l-4 border-red-500 text-red-700 text-xs font-medium rounded">
                {errorMsg}
                </div>
            )}

            <p className="text-sm text-gray-500 mb-2">Current Value: <span className="font-medium text-gray-700">{profile[editingField.key as keyof typeof profile]}</span></p>
            
            <input 
              type="text" 
              value={newValue}
              onChange={(e) => setNewValue(e.target.value)}
              placeholder={`Enter new ${editingField.label.toLowerCase()}`}
              className="w-full p-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none text-black mb-6"
              autoFocus
            />

            <div className="flex gap-3">
              <button onClick={() => setIsModalOpen(false)} className="flex-1 py-2.5 border border-gray-200 rounded-lg text-gray-600 font-medium hover:bg-gray-50 transition">
                Cancel
              </button>
              <button 
                onClick={handleSave} 
                disabled={updating}
                className="flex-1 py-2.5 bg-blue-600 rounded-lg text-white font-medium hover:bg-blue-700 transition disabled:bg-blue-300"
              >
                {updating ? "Saving..." : "Save Changes"}
              </button>
            </div>
          </div>
        </div>
      )}

    </div> // This closes the main white card
  );
}