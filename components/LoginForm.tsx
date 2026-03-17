"use client"; 

import { Mail, Lock, UserCircle, EyeOff, Eye } from "lucide-react";
import Image from "next/image";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { supabase } from "../lib/supabaseClient";

export default function LoginForm() {
  const router = useRouter();
  const [email, setEmail] = useState(""); // Use Email for Supabase Auth
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState(""); // State to store the error text   
  const [showPassword, setShowPassword] = useState(false);  //State to toggle password visibility

const handleLogin = async (e: React.FormEvent) => {
  e.preventDefault();
  setLoading(true);
  setErrorMsg(""); // Clear old errors

  let loginEmail = email; // Staring with whatever the user typed

  // 1. CHECK IF INPUT IS A USERNAME (doesn't contain '@')
  if (!email.includes("@")) {
    const { data: profile, error: profileError } = await supabase
      .from("profiles")
      .select("email") 
      .eq("username", email)
      .single();

    if (profileError || !profile) {
      //Setting the appropriate error message to display in the UI
      setErrorMsg("Username not found. Please check or use your email.");      
      setLoading(false);
      return;
    }
    
    loginEmail = profile.email; // Switch to the actual email found in DB
  }

  // 2. PROCEED WITH SUPABASE LOGIN
  const { error } = await supabase.auth.signInWithPassword({
    email: loginEmail,
    password: password,
  });

  if (error) {
    setErrorMsg(error.message); // Set Error message
    setLoading(false);
  } else {
    router.push("/dashboard"); 
  }
};

// Reset Password
const handleResetPassword = async (email: string) => {
  setErrorMsg(""); // Clear old errors
  const { error } = await supabase.auth.resetPasswordForEmail(email, {
    // This is where the user is sent AFTER clicking the link in their email
    redirectTo: `${window.location.origin}/auth/update-password`,
  });

  if (error) {
    setErrorMsg(error.message);
  } else {
    alert("Password reset email sent! Check your inbox.");
  }
};

  // Google Login 
  const handleGoogleLogin = async () => {
    const { error } = await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: {
        redirectTo: `${window.location.origin}/dashboard`,
        // This forces the "Select an Account" screen
        queryParams: {
          prompt: 'select_account',
        },
      },
    });

    if (error) {
      alert("Error: " + error.message);
    }
  };

  return (
    <div className="bg-white p-8 rounded-2xl shadow-xl w-full max-w-md border border-gray-100">

      <div className="flex justify-center mb-4">
        <Image src="/Nyaya_logo_temp.png" alt="NYAYA Logo" width={80} height={80} className="rounded-full shadow-sm" />
      </div>

      <h2 className="text-2xl font-bold text-gray-800 text-center mb-6">Nyaya Login</h2>
      
      {/*handleLogin to onSubmit */}
      <form className="space-y-4" onSubmit={handleLogin}>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Email or User Name</label>
          <div className="relative">
            <UserCircle className="absolute left-3 top-3 text-gray-400" size={18} />
            <input 
              type="text" 
              required
              value={email} 
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Enter your email or User Name"
              className="w-full pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none text-black" 
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
          <div className="relative">
            <Lock className="absolute left-3 top-3 text-gray-400" size={18} />
            <input 
              type={showPassword ? "text" : "password"} // Dynamic type 
              required
              value={password} // 3. FIXED: Connected state
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none text-black" 
            />

            {/* Toggle Button */}
            <button
              type="button" // Important: prevents form submission
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-3 top-2.5 text-gray-400 hover:text-blue-600"
            >
              {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
            </button>
          </div>
        </div>

        {/* Inline Error Message */}
        {errorMsg && (
          <div className="text-red-500 text-xs font-medium bg-red-50 p-2 rounded border border-red-200 mb-2 animate-in fade-in duration-300">
            {errorMsg}
          </div>
        )}

        <button 
          type="submit" 
          disabled={loading}
          className="w-full bg-blue-600 text-white py-2 rounded-lg font-semibold hover:bg-blue-700 transition disabled:bg-gray-400"
        >
          {loading ? "Logging in..." : "Login"}
        </button>

        <div className="flex justify-center mb-4">
          <button 
            type="button"
            onClick={() => {
              if (!email) {
                alert("Please enter your email address first!");
                return;
              }
              handleResetPassword(email);
            }}
            className="text-xs text-blue-600 hover:underline font-medium"
          >
            Forgot password?
          </button>
        </div>

        <div className="flex items-center my-6">
          <div className="flex-grow border-t border-gray-300"></div>
          <span className="px-3 text-gray-500 text-sm">OR</span>
          <div className="flex-grow border-t border-gray-300"></div>
        </div>

        {/*Using Supabase native method for Google login*/}
        <button 
          onClick={handleGoogleLogin}
          type="button"
          className="w-full border border-gray-300 py-2 rounded-lg font-medium flex items-center justify-center gap-2 hover:bg-gray-50 transition text-black"
        >
          <img src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg" width="18" alt="Google" />
          Continue with Google
        </button>
      </form>

      <p className="text-center text-sm text-gray-600 mt-6">
        New here? <a href="/signup" className="text-blue-600 font-semibold hover:underline">Sign up</a>
      </p>
    </div>
  );
}