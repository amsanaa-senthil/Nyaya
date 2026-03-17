"use client";
import { User, Mail, Lock, UserCircle } from "lucide-react";
import { useState } from "react";
import Image from "next/image";
import { useRouter } from 'next/navigation';
import { supabase } from "../lib/supabaseClient";

export default function SignUpForm() {

  const router = useRouter();

  //State object to hold all form data
  const [formData, setFormData] = useState({
    firstName: "",
    surname: "",
    username: "",
    email: "",
    password: "",
    confirmPassword:""
  });

  const [errorMsg, setErrorMsg] = useState(""); // State to store the error text
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      setFormData({ ...formData, [e.target.name]: e.target.value });
    };

  const [strength, setStrength] = useState(0);

  // Function to calculate strength score (0 to 4)
  const checkStrength = (pw: string) => {
    let score = 0;
    if (pw.length >= 6) score++; // Minimum length
    if (pw.length >= 10) score++; // Bonus for length
    if (/[0-9]/.test(pw)) score++; // PW Contains numbers
    if (/[!@#$%^&*]/.test(pw)) score++; // Contains special characters
    setStrength(score); //Setting the strength state to the calculated score
  };

  //Function to update the state as the user types
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(""); // Clear previous errors

    // Validate Username: No '@' allowed
    if (formData.username.includes("@")) {
      //Setting up the appropriate error message to display in the UI
      setErrorMsg("Usernames cannot contain the '@' symbol. Please choose another.");
      return;
    }

    // Validate Password Strength (Must be at least 'Fair')
    if (strength < 2) {
      setErrorMsg("Password is too weak. Strength must be at least 'Fair'.");
      return;
    }

    // Validate password match
    if (formData.password !== formData.confirmPassword) {
      //Setting up the appropriate error message to display in the UI
      setErrorMsg("Passwords do not match!");
      return;
    }

  const { data, error } = await supabase.auth.signUp({
    email: formData.email,
    password: formData.password,
    options: {
      data: {
        first_name: formData.firstName,
        surname: formData.surname,
        username: formData.username,
      },
    },
  });

  if (error) {
    // This will catch "User already registered", "Password too short", etc.
    setErrorMsg(error.message); 
    return; // Stop the code here so it doesn't redirect!
  }

  // Supabase "Fake Success" Check:
  // If email confirmation is ON, Supabase returns data but no session.
  // If the user already exists, sometimes 'data.user' is null or identities are empty.
  if (data.user && data.user.identities && data.user.identities.length === 0) {
    //Setting up the appropriate error message to display in the UI
    setErrorMsg("This email is already in use. Please try logging in.");
    return;
  }

  // ONLY redirect if there was no error and it's a new user
  const queryString = new URLSearchParams({
    firstName: formData.firstName,
    surname: formData.surname,
    username: formData.username,
    email: formData.email,
  }).toString();

  router.push(`/signup_success?${queryString}`);
};

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

      <h2 className="text-2xl font-bold text-gray-800 text-center mb-6">Create Nyaya Account</h2>
      
      <form className="space-y-4" onSubmit={handleSubmit}>
        {/* First Name & Surname */}
        <div className="flex gap-4">
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-1">First Name</label>
            <input 
              name = "firstName"
              value={formData.firstName}
              onChange={handleChange}
              type="text" 
              required
              placeholder="John" 
              className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none text-black" name="firstName" onChange={handleChange} />
          </div>

          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-1">Surname</label>
            <input 
              name = "surname"
              value={formData.surname}
              onChange={handleChange}
              type="text" 
              required
              placeholder="Doe" 
              className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none text-black" name="surname" onChange={handleChange} />
          </div>
        </div>

        {/* Email Field */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
          <div className="relative">
            <Mail className="absolute left-3 top-3 text-gray-400" size={18} />
            <input 
              name = "email"
              value={formData.email}
              onChange={handleChange}
              type="email" 
              required
              placeholder="john@example.com" 
              className="w-full pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none text-black" />
          </div>
        </div>

        {/* Username Field */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Username</label>
          <div className="relative">
            <UserCircle className="absolute left-3 top-3 text-gray-400" size={18} />
            <input 
              name = "username"
              value={formData.username}
              onChange={handleChange}
              type="text" 
              required
              placeholder="johndoe123" 
              className="w-full pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none text-black" />
          </div>
        </div>

        {/* Password Field */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
          <div className="relative">
            <Lock className="absolute left-3 top-3 text-gray-400" size={18} />
            <input 
              name = "password"
              value={formData.password}
              onChange={(e) => {
                handleChange(e); // Keep your existing data update
                checkStrength(e.target.value); // Add strength check
             }}
              type="password" 
              required
              placeholder="••••••••" 
              className="w-full pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none text-black" />
          </div>
        </div>

        {/* Password Strength Bar */}
        <div className="mt-2 h-1.5 w-full bg-gray-200 rounded-full overflow-hidden">
          <div 
            className={`h-full transition-all duration-300 ${
              strength === 0 ? "w-0" :
              strength === 1 ? "w-1/4 bg-red-500" :
              strength === 2 ? "w-2/4 bg-orange-500" :
              strength === 3 ? "w-3/4 bg-yellow-500" :
              "w-full bg-green-500"
            }`}
          />
        </div>

        {/* Strength Label */}
        <p className="text-[10px] mt-1 font-medium uppercase tracking-wider text-gray-400">
          Strength: 
          <span className={
            strength <= 1 ? "text-red-500" : 
            strength <= 3 ? "text-orange-500" : 
            "text-green-500"
          }>
            {strength <= 1 ? " Weak" : strength <= 3 ? " Fair" : " Strong"}
          </span>
        </p>

        {/* Confirm Password Field */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Confirm Password</label>
          <div className="relative">
            <Lock className="absolute left-3 top-3 text-gray-400" size={18} />
            <input 
              name = "confirmPassword"
              value={formData.confirmPassword}
              onChange={handleChange}
              type="password" 
              required
              placeholder="••••••••" 
              className="w-full pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none text-black" />
          </div>
        </div>

        {/* Inline Error Message */}
        {errorMsg && (
          <div className="text-red-500 text-xs font-medium bg-red-50 p-2 rounded border border-red-200 mb-2">
            {errorMsg}
          </div>
        )}

        <button className="w-full bg-blue-600 text-white py-2 rounded-lg font-semibold hover:bg-blue-700 transition">
          Create Account
        </button>
      </form>

      <p className="text-center text-sm text-gray-600 mt-6">
        Already have an account? <a href="/login" className="text-blue-600 font-semibold hover:underline">Log in</a>
      </p>
    </div>
  );
}