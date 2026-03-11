"use client"; // Required because we use useState, useEffect, and useRouter (client-side hooks)

import { useState } from "react";
import { supabase } from "@/lib/supabaseClient";
import { useRouter } from "next/navigation";
import Image from "next/image";
import { Lock } from "lucide-react";

export default function UpdatePassword() {
  // State to hold the new password string
  const [password, setPassword] = useState("");
  // State to handle button loading UI during the async database call
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  /**
   * handleUpdate: Sends the new password to Supabase.
   * This works because the user arrives here via a 'recovery' magic link
   * which grants them a temporary session to update their user data.
   */
  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault(); // Prevents the default browser form submission (page reload)
    setLoading(true);

    // Supabase built-in method to update user credentials
    const { error } = await supabase.auth.updateUser({
      password: password
    });

    if (error) {
      // Common errors include: link expired, or password doesn't meet requirements
      alert("Error: " + error.message);
      setLoading(false);
    } else {
      alert("Password updated successfully!");
      
      /** * Best Practice: Log the user out after a reset.
       * This clears the temporary recovery session and forces a fresh login 
       * with the new credentials for security.
       */
      await supabase.auth.signOut();
      router.push("/login"); // Redirect to the login page
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
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">New Password</label>
            <div className="relative">
              {/* Icon placement: Absolute positioning inside a relative container */}
              <Lock className="absolute left-3 top-3 text-gray-400" size={18} />
              <input 
                type="password" 
                placeholder="Min. 6 characters" 
                required 
                autoFocus // Automatically focuses the input when the page loads
                className="w-full pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none text-black border-gray-200"
                onChange={(e) => setPassword(e.target.value)}
              />
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