"use client"; 
import { Mail, Lock, UserCircle } from "lucide-react";
import { signIn } from "next-auth/react";
import { GoogleLogin } from '@react-oauth/google';
import { GoogleOAuthProvider } from '@react-oauth/google';
import Image from "next/image";

export default function LoginForm() {
  return (
    <div className="bg-white p-8 rounded-2xl shadow-xl w-full max-w-md border border-gray-100">

      {/* NYAYA Logo */}
      <div className="flex justify-center mb-4">
        <Image 
          src="/Nyaya_logo_temp.png"
          alt="NYAYA Logo" 
          width={80}           
          height={80}          
          className="rounded-full shadow-sm" 
        />
      </div>

      <h2 className="text-2xl font-bold text-gray-800 text-center mb-6">Nyaya Login</h2>
      
      <form className="space-y-4" onSubmit={(e) => e.preventDefault()}>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Username</label>
          <div className="relative">
            <UserCircle className="absolute left-3 top-3 text-gray-400" size={18} />
            <input 
              type="text" 
              placeholder="Enter your username"
              className="w-full pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none text-black" 
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
          <div className="relative">
            <Lock className="absolute left-3 top-3 text-gray-400" size={18} />
            <input 
              type="password" 
              placeholder="••••••••"
              className="w-full pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none text-black" 
            />
          </div>
        </div>

        <button className="w-full bg-blue-600 text-white py-2 rounded-lg font-semibold hover:bg-blue-700 transition">
          <a href="/dashboard" className="text-white no-underline">Login</a>
        </button>
      </form>

      <div className="flex items-center my-6">
        <div className="flex-grow border-t border-gray-300"></div>
        <span className="px-3 text-gray-500 text-sm">OR</span>
        <div className="flex-grow border-t border-gray-300"></div>
      </div>

      {/* Wrap your form or just the button in the Provider */}
      <GoogleOAuthProvider clientId="670242574631-em9cl4tn55v3kum9jkbbqtcgummeapih.apps.googleusercontent.com">
        <div className="flex justify-center w-full">
          <GoogleLogin
            onSuccess={credentialResponse => {
              console.log(credentialResponse);
              // This is where you would send the data to your backend
            }}
            onError={() => {
              console.log('Login Failed');
            }}
            useOneTap // One tap continue with google acc on the top right corner of the screen
          />
        </div>
      </GoogleOAuthProvider>

      <p className="text-center text-sm text-gray-600 mt-6">
        New here? <a href="/signup" className="text-blue-600 font-semibold hover:underline">Sign up</a>
      </p>
    </div>
  );
}