"use client";
import { User, Mail, Lock, UserCircle } from "lucide-react";
import { useState } from "react";
import Image from "next/image";
import { useRouter } from 'next/navigation';

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

  //Function to update the state as the user types
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  //Function to send data to your route.ts
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (formData.password !== formData.confirmPassword) {
      alert("Passwords do not match!");
      return;
    }

    const response = await fetch("/api/auth/signup", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(formData), // This sends the data to your route.ts
    });

    const result = await response.json();
    if (response.ok) {
      // 1. Destructure the data you want to pass (from the backend response)
      const { firstName, surname, username, email } = result.user;

      // 2. Create a query string so the success page can read these details
      const queryString = new URLSearchParams({
        firstName,
        surname,
        username,
        email,
      }).toString();

      // 3. Redirect the user to your new success page
      router.push(`/signup_success?${queryString}`);
    } else {
      alert(result.error || "Something went wrong");
    }
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
              onChange={handleChange}
              type="password" 
              placeholder="••••••••" 
              className="w-full pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none text-black" />
          </div>
        </div>

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
              placeholder="••••••••" 
              className="w-full pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none text-black" />
          </div>
        </div>

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