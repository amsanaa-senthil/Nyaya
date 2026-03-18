"use client";
import { useState, useEffect, useRef } from "react";
import { supabase } from "@/lib/supabaseClient";
import { useRouter } from "next/navigation";
import { Lock, Mail, UserCircle, ShieldCheck, Pencil, X, Camera, Eye, EyeOff } from "lucide-react";
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
  const fileInputRef = useRef<HTMLInputElement>(null); // 2. Ref for the hidden input
  const [uploadingImage, setUploadingImage] = useState(false); // New state for image upload

  //States for Deleation of account
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [deletePassword, setDeletePassword] = useState("");
  const [isDeleting, setIsDeleting] = useState(false);
  const [deleteStep, setDeleteStep] = useState<"initial" | "confirm" | "password">("initial");
  const [showDeletePassword, setShowDeletePassword] = useState(false);
  
  // profile: Local state to hold the specific fields we want to show the user
  const [profile, setProfile] = useState({
    id: "",
    firstName: "",
    surname: "",
    username: "",
    email: "",
    avatarUrl: "/Profile_Pic_Icon.png", // Default image fallback
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
                id: user.id, // Set the ID here
                firstName: data.first_name || "Not Set",
                surname: data.surname || "Not Set",
                username: data.username || "Not Set",
                email: data.email || user.email || "Not Set",
                avatarUrl: data.avatar_url || "/Profile_Pic_Icon.png",
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

    const handleDeleteAccount = async () => {
    // 1. Ensure the user actually typed something
    if (!deletePassword) {
      alert("Please enter your password to confirm.");
      return;
    }

    setIsDeleting(true);
    setErrorMsg("");

    try {
      // 2. MANUAL CREDENTIAL CHECK
      // We attempt to sign in again with the current user's email and the password they just typed
      const { error: verifyError } = await supabase.auth.signInWithPassword({
        email: profile.email,
        password: deletePassword,
      });

      // If the password is wrong, Supabase will return an error here
      if (verifyError) {
        throw new Error("Verification failed: Incorrect password.");
      }

      // 3. DELETE FROM DATABASE
      // If the password was correct, we proceed to wipe the user's profile row
      const { error: deleteError } = await supabase
        .from("profiles")
        .delete()
        .eq("id", profile.id);

      if (deleteError) throw deleteError;

      // 4. CLEANUP
      // Log the user out of the session and redirect to signup
      await supabase.auth.signOut();
      alert("Account deleted successfully.");
      router.push("/signup");

    } catch (error: any) {
      // Display the error (e.g., "Invalid login credentials")
      setErrorMsg(error.message);
    } finally {
      setIsDeleting(false);
    }
  };

// IMAGE UPLOAD LOGIC  
  const handleAvatarClick = () => {
    if (!uploadingImage) fileInputRef.current?.click();
  };

  const uploadAvatar = async (event: React.ChangeEvent<HTMLInputElement>) => {
    try {
      setUploadingImage(true);
      setErrorMsg("");

      if (!event.target.files || event.target.files.length === 0) return;
      const file = event.target.files[0];
      const fileExt = file.name.split('.').pop();
      const fileName = `avatar-${Math.random()}.${fileExt}`;
      const filePath = `${profile.id}/${fileName}`; // Folder named after User ID

      // 1. Upload to Supabase Storage
      const { error: uploadError } = await supabase.storage
        .from('avatars')
        .upload(filePath, file, { upsert: true });

      if (uploadError) throw uploadError;

      // 2. Get Public URL
      const { data: { publicUrl } } = supabase.storage
        .from('avatars')
        .getPublicUrl(filePath);

      // 3. Update Database profiles table
      const { error: updateError } = await supabase
        .from('profiles')
        .update({ avatar_url: publicUrl })
        .eq('id', profile.id);

      if (updateError) throw updateError;

      // 4. Update UI
      setProfile((prev) => ({ ...prev, avatarUrl: publicUrl }));
      
    } catch (error: any) {
      setErrorMsg("Image upload failed: " + error.message);
    } finally {
      setUploadingImage(false);
    }
  };

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
      
    {/*HIDDEN INPUT FIELD */}
      <input 
        type="file" 
        ref={fileInputRef} 
        onChange={uploadAvatar} 
        accept="image/*" 
        className="hidden" 
      />

      {/* Profile Header: Avatar with Hover Effect */}
      <div className="flex flex-col items-center mb-8">
        <div 
        onClick={handleAvatarClick}
        className="relative h-28 w-28 mb-4 group cursor-pointer">

          {/* Main Avatar Image */}
          <Image 
            src={profile.avatarUrl} 
            alt="User Avatar" 
            fill 
            className="rounded-full border-4 border-slate-800 object-cover bg-slate-900 shadow-md transition-all duration-300 group-hover:opacity-60 group-hover:scale-105" 
          />
          
          {/* Camera Icon Overlay or Spinner */}
          <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-300">
            {!uploadingImage ? (
              <div className="bg-slate-800/50 p-2 rounded-full backdrop-blur-sm">
                <Camera size={24} className="text-white" />
              </div>
            ) : (
              <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-600"></div>
            )}
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
          
          {/* Top Row: Reset & Delete side-by-side */}
          <div className="flex gap-3">

            {/* Reset Password Buttons */}
            <button 
              type="button"
              onClick={() => router.push("/dashboard/profile/reset-password")}
              className="flex-1 flex items-center justify-center gap-2 h-12 bg-blue-600 rounded-xl text-white font-semibold hover:bg-blue-700 transition-all shadow-lg shadow-blue-100"
            >
              <Lock size={16} />
              Reset Password
            </button>

            {/* Delete Account */}
            <button 
              type="button"
              onClick={() => {
                setIsDeleteModalOpen(true);
                setDeleteStep("confirm"); // Start at the confirmation question
              }}
              className="flex-1 flex items-center justify-center gap-2 h-12 bg-blue-600 rounded-xl text-white font-semibold hover:bg-blue-700 transition-all shadow-lg shadow-blue-100"
            >
              <X size={16} />
              Delete Account
            </button>
          </div>

          {/* Bottom Row: Back to Dashboard */}
          <button 
            type="button"
            onClick={() => router.push("/dashboard")} 
            className="w-full flex items-center justify-center gap-2 h-12 bg-blue-600 rounded-xl text-white font-semibold hover:bg-blue-700 transition-all shadow-lg shadow-gray-200"
          >
            Go Back to Dashboard
          </button>
        </div>
      </div>

      {/*EDIT MODAL OVERLAY*/}
      {isModalOpen && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white w-full max-w-sm rounded-2xl p-6 shadow-2xl animate-in fade-in zoom-in duration-200">

            <div className="flex justify-center mb-4">
                  <Image src="/Nyaya_logo_temp.png" alt="NYAYA Logo" width={80} height={80} className="rounded-full shadow-sm" />
            </div>

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

      {/* DELETE ACCOUNT SECURITY MODAL */}
      {isDeleteModalOpen && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-md flex items-center justify-center z-[60] p-4">
          <div className="bg-white w-full max-w-sm rounded-2xl p-6 shadow-2xl border border-red-100 animate-in fade-in zoom-in duration-200">
            
            {/* STEP 1: ARE YOU SURE? */}
            {deleteStep === "confirm" && (
              <div className="text-center">
                <div className="mx-auto w-16 h-16 bg-red-50 text-red-600 rounded-full flex items-center justify-center mb-4">
                  <X size={32} />
                </div>
                <h3 className="text-xl font-bold text-gray-800 mb-2">Are you absolutely sure?</h3>
                <p className="text-sm text-gray-500 mb-6">
                  This will permanently delete your profile, quiz history, and stats. You cannot undo this.
                </p>
                <div className="flex gap-3">
                  <button 
                    onClick={() => { setIsDeleteModalOpen(false); setDeleteStep("initial"); }}
                    className="flex-1 py-3 bg-gray-100 rounded-xl font-semibold text-gray-600 hover:bg-gray-200 transition"
                  >
                    No, Keep it
                  </button>
                  <button 
                    onClick={() => setDeleteStep("password")}
                    className="flex-1 py-3 bg-red-600 rounded-xl font-semibold text-white hover:bg-red-700 transition"
                  >
                    Yes, Delete
                  </button>
                </div>
              </div>
            )}

            {/* STEP 2: PASSWORD VERIFICATION */}
            {deleteStep === "password" && (
              <>

                <div className="flex justify-center mb-4">
                          <Image src="/Nyaya_logo_temp.png" alt="NYAYA Logo" width={80} height={80} className="rounded-full shadow-sm" />
                </div>

                <div className="flex items-center gap-3 text-red-600 mb-4">
                  <ShieldCheck size={24} />
                  <h3 className="text-lg font-bold">Verify Identity</h3>
                </div>
                <p className="text-sm text-gray-600 mb-6">
                  Please enter your password to finalize the deletion.
                </p>
                {errorMsg && (
                  <div className="mb-4 p-2 bg-red-50 text-red-700 text-xs rounded border border-red-200">
                    {errorMsg}
                  </div>
                )}

                {/* PASSWORD INPUT WITH TOGGLE */}
                <div className="relative mb-6">
                  <input 
                    type={showDeletePassword ? "text" : "password"} 
                    value={deletePassword}
                    onChange={(e) => setDeletePassword(e.target.value)}
                    placeholder="Your password"
                    className="w-full p-3 pr-12 border border-red-200 rounded-xl focus:ring-2 focus:ring-red-500 outline-none text-black transition-all"
                    autoFocus
                  />
                  <button
                    type="button"
                    onClick={() => setShowDeletePassword(!showDeletePassword)}
                    className="absolute right-3 top-3 text-gray-400 hover:text-red-600 transition-colors"
                  >
                    {showDeletePassword ? <EyeOff size={20} /> : <Eye size={20} />}
                  </button>
                </div>

                <div className="flex gap-3">
                  <button 
                    onClick={() => setDeleteStep("confirm")} 
                    className="flex-1 py-2.5 bg-gray-100 rounded-lg text-gray-600 font-medium hover:bg-gray-200 transition"
                  >
                    Back
                  </button>
                  <button 
                    onClick={handleDeleteAccount}
                    disabled={isDeleting}
                    className="flex-1 py-2.5 bg-red-600 rounded-lg text-white font-medium hover:bg-red-700 transition disabled:bg-red-300"
                  >
                    {isDeleting ? "Deleting..." : "Confirm Delete"}
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      )}

    </div> // This closes the main white card
  );
}