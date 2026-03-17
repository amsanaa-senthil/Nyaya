"use client"; // Required because we use useState, useEffect, and useRouter (client-side hooks)

import { useState } from "react";
import { supabase } from "@/lib/supabaseClient";
import { useRouter } from "next/navigation";
import Image from "next/image";
import { Lock, Eye, EyeOff } from "lucide-react";

export default function UpdatePassword() {
  // State to hold the new password string
  const [password, setPassword] = useState("");

  // State to hold the current password string
  const [currentPassword, setCurrentPassword] = useState("");

  // State to handle button loading UI during the async database call
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const [confirmPassword, setConfirmPassword] = useState(""); //Confirm Password
  const [strength, setStrength] = useState(0); // To set password strength
  const [errorMsg, setErrorMsg] = useState(""); //To set error msg
  const [showPassword, setShowPassword] = useState(false); //State to toggle password visibility
  const [showConfirmPassword, setShowConfirmPassword] = useState(false); //State to toggle confirm password visibility
  const [showCurrentPassword, setShowCurrentPassword] = useState(false); //State to toggle current password visibility

  // Function to calculate strength score (0 to 4)
  const checkStrength = (pw: string) => {
    let score = 0;
    if (pw.length >= 6) score++; 
    if (pw.length >= 10) score++; 
    if (/[0-9]/.test(pw)) score++; 
    if (/[!@#$%^&*]/.test(pw)) score++; 
    setStrength(score);
  };

  /**
   * handleUpdate: Sends the new password to Supabase.
   * This works because the user arrives here via a 'recovery' magic link
   * which grants them a temporary session to update their user data.
   */
  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(""); // Clear old errors
    
    // 1. Validation Checks
    if (strength < 2) {
      setErrorMsg("Password is too weak. Strength must be at least 'Fair'.");
      return;
    }

    if (password !== confirmPassword) {
      setErrorMsg("Passwords do not match!");
      return;
    }

    setLoading(true);

try {
      // --- STEP 1: MANUALLY VERIFY CURRENT PASSWORD ---
      // We try to sign in with the user's email and the current password they typed.
      const { data: { user } } = await supabase.auth.getUser();
      
      const { error: verifyError } = await supabase.auth.signInWithPassword({
        email: user?.email || "",
        password: currentPassword,
      });

      if (verifyError) {
        throw new Error("Current password is incorrect.");
      }

      // --- STEP 2: UPDATE TO NEW PASSWORD ---
      const { error: updateError } = await supabase.auth.updateUser({
        password: password,
      });

      if (updateError) throw updateError;

      // SUCCESS
      setErrorMsg("Password updated successfully! Logging out...");
      
      setTimeout(async () => {
        await supabase.auth.signOut();
        router.push("/login");
      }, 2000);

    } catch (error: any) {
      setErrorMsg(error.message);
      setLoading(false);
    }
};

  return (
    // Outer container ensures the card is centered on all screen sizes
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-6">
      
      {/* Main Card Container*/}
      <div className="bg-white p-8 rounded-2xl shadow-xl w-full max-w-md border border-gray-100">
        
        {/*Nyaya Logo*/}
        <div className="flex justify-center mb-4">
          <Image 
            src="/Nyaya_logo_temp.png" 
            alt="NYAYA Logo" 
            width={80} 
            height={80} 
            className="rounded-full shadow-sm" 
          />
        </div>

        <h2 className="text-2xl font-bold text-gray-800 text-center mb-2">Set New Password</h2>
        <p className="text-sm text-gray-500 text-center mb-8">
          Enter a strong password to secure your Nyaya account.
        </p>

        <form onSubmit={handleUpdate} className="space-y-6">

          {/* CURRENT PASSWORD FIELD */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Current Password</label>
            <div className="relative">
              <Lock className="absolute left-3 top-3 text-gray-400" size={18} />
              <input 
                type={showCurrentPassword ? "text" : "password"}
                placeholder="Enter current password"
                required
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none text-black border-gray-200"
              />

              {/* The Toggle Button */}
              <button
                type="button"
                onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                className="absolute right-3 top-2.5 text-gray-400 hover:text-blue-600"
              >
                {showCurrentPassword ? <EyeOff size={20} /> : <Eye size={20} />}
              </button>
            </div>
          </div>

          {/*New Password Field*/}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">New Password</label>
            <div className="relative">
              {/* Icon placement: Absolute positioning inside a relative container */}
              <Lock className="absolute left-3 top-3 text-gray-400" size={18} />
              <input 
                type={showPassword ? "text" : "password"} // Dynamic type switching
                placeholder="Min. 6 characters" 
                required 
                autoFocus // Automatically focuses the input when the page loads
                className="w-full pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none text-black border-gray-200"
                onChange={(e) => {
                  const newPassword = e.target.value;
                  setPassword(newPassword); // Updates the password state
                  checkStrength(newPassword); // Actually triggers the bar to move!
                }}
              />

              {/* The Toggle Button */}
              <button
                type="button" // CRITICAL: must be "button" so it doesn't submit the form
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-2.5 text-gray-400 hover:text-blue-600 transition-colors"
              >
                {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
              </button> 
              
            </div>

            {/*Strength Meter Visuals */}
            {password && (
              <div className="mt-2">
                <div className="h-1.5 w-full bg-gray-100 rounded-full overflow-hidden">
                  <div 
                    className={`h-full transition-all duration-300 ${
                      strength === 1 ? "w-1/4 bg-red-500" :
                      strength === 2 ? "w-2/4 bg-orange-500" :
                      strength === 3 ? "w-3/4 bg-yellow-500" :
                      strength === 4 ? "w-full bg-green-500" : "w-0"
                    }`}
                  />
                </div>
                <p className={`text-[10px] mt-1 font-bold uppercase tracking-wider ${
                  strength <= 1 ? "text-red-500" : strength <= 3 ? "text-orange-500" : "text-green-500"
                }`}>
                  Strength: {strength <= 1 ? "Weak" : strength <= 3 ? "Fair" : "Strong"}
                </p>
              </div>
            )}
            </div>

            {/* Inline Error Message Display */}
          {errorMsg && (
            <p className="text-red-500 text-xs font-medium bg-red-50 p-2 rounded border border-red-200 mt-4">
              {errorMsg}
            </p>
          )}

        {/* Confirm Password Field */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Confirm Password</label>
          <div className="relative">
            <Lock className="absolute left-3 top-3 text-gray-400" size={18} />
            <input 
              type={showConfirmPassword ? "text" : "password"} // Dynamic type 
              required
              placeholder="••••••••" 
              value={confirmPassword} 
              onChange={(e) => setConfirmPassword(e.target.value)} 
              className={`w-full pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none text-black transition-colors `}/>

            {/* Toggle Button */}
            <button
              type="button"
              onClick={() => setShowConfirmPassword(!showConfirmPassword)}
              className="absolute right-3 top-2.5 text-gray-400 hover:text-blue-600"
            >
              {showConfirmPassword ? <EyeOff size={20} /> : <Eye size={20} />}
            </button>

          </div>
        </div>

          {/* Submit Button: 
              Changes appearance when 'loading' to prevent double-submissions.
          */}
          <button 
            type="submit" 
            disabled={loading}
            className="w-full bg-blue-600 text-white py-3 rounded-xl font-semibold hover:bg-blue-700 transition shadow-lg shadow-blue-100 disabled:bg-blue-300"
          >
            {loading ? "Updating..." : "Update Password"}
          </button>
        </form>

        {/* Navigation link for users who clicked the reset link by mistake */}
        <p className="text-center text-sm text-gray-600 mt-8">
          Remembered your password? <a href="/login" className="text-blue-600 font-semibold hover:underline">Go back to Login</a>
        </p>
      </div>
    </div>
  );
}