"use client";

import Image from "next/image";
import { Mail, Phone, MapPin, Send } from "lucide-react";
import { useFooterLogic } from "@/lib/Footer";
import { usePathname } from "next/navigation";

export default function Footer() {
  const pathname = usePathname();
  const { formData, handleChange, handleSubmit, isSubmitting, status } = useFooterLogic();

  // Hide footer on specific auth pages
  const hideOnPaths = ["/login", "/signup", "/signup_success"];
  if (hideOnPaths.includes(pathname)) return null;

  return (
    <footer className="bg-[#0f172a] text-white pt-24 pb-16 px-6 md:px-12 border-t border-white/5">
      <div className="max-w-7xl mx-auto">
        
        {/* MAIN 2-COLUMN GRID */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-start pb-12 pt-8 border-t border-white/5 flex flex-col md:flex-row justify-between items-center gap-6 text-gray-500 text-[10px] font-bold uppercase tracking-widest">
          
          {/*Branding & Professional Inf*/}
          <div className="space-y-10 pt-8 border-t border-white/5 flex flex-col md:flex-row justify-between items-center gap-6 text-gray-500 text-[10px] font-bold uppercase tracking-widest">
            <div className="flex flex-col md:flex-row justify-between items-start gap-8">
              {/* Branding Section */}
              <div className="space-y-4 max-w-xs">
                <div className="flex items-center gap-3 ">
                  <Image 
                    src="/Nyaya_logo_temp.png" 
                    alt="Nyaya Logo" 
                    width={52} 
                    height={52} 
                    className="rounded-full shadow-lg border border-white/10" 
                  />
                  <h2 className="text-2xl font-bold tracking-tight">Nyaya</h2>
                </div>
                <p className="text-gray-400 leading-relaxed text-sm">
                  Your comprehensive Sri Lankan legal resource hub. Access legal information and learn about Sri Lankan law.
                </p>
              </div>

              {/* CONTACT INFORMATION: Organized with visual hierarchy */}
              <div className="space-y-5 min-w-[220px]">
                
                
                <div className="space-y-4">
                  <div className="flex items-center gap-4 group cursor-pointer">
                    <div className="p-2 bg-white/5 rounded-lg text-[#c5a059] group-hover:bg-[#c5a059] group-hover:text-white transition-all">
                      <Mail size={16} />
                    </div>
                    <a href="mailto:info@nyaya.lk" className="text-sm font-medium hover:text-white transition-colors">info@nyaya.lk</a>
                  </div>

                  <div className="flex items-center gap-4 group cursor-pointer">
                    <div className="p-2 bg-white/5 rounded-lg text-[#c5a059] group-hover:bg-[#c5a059] group-hover:text-white transition-all">
                      <Phone size={16} />
                    </div>
                    <a href="tel:+94112345678" className="text-sm font-medium hover:text-white transition-colors">+94 11 234 5678</a>
                  </div>

                  <div className="flex items-center gap-4 group">
                    <div className="p-2 bg-white/5 rounded-lg text-[#c5a059]">
                      <MapPin size={16} />
                    </div>
                    <span className="text-sm font-medium text-gray-300">Colombo 03, Sri Lanka</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* --- RIGHT HAND SIDE: Contact Us Form --- */}
          <div className="space-y-6">
            <div className="pt-8 border-t border-white/5 flex flex-col md:flex-row justify-between items-center gap-6 text-gray-500 text-[10px] font-bold uppercase tracking-widest" >
              <h2 className="text-3xl font-bold">Contact Us</h2>
              <p className="text-gray-400 text-sm">Have a question? Send us a message below.</p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <input
                  type="text"
                  name="name"
                  placeholder="Your Name *"
                  required
                  value={formData.name}
                  onChange={handleChange}
                  className="bg-[#1c243d] border border-white/10 rounded-xl p-4 outline-none focus:border-[#3a96a5] transition-colors text-white placeholder-gray-500 text-sm"
                />
                <input
                  type="text"
                  name="phone"
                  placeholder="Phone Number *"
                  required
                  value={formData.phone}
                  onChange={handleChange}
                  className="bg-[#1c243d] border border-white/10 rounded-xl p-4 outline-none focus:border-[#3a96a5] transition-colors text-white placeholder-gray-500 text-sm"
                />
              </div>

              <input
                type="email"
                name="email"
                placeholder="Email Address *"
                required
                value={formData.email}
                onChange={handleChange}
                className="w-full bg-[#1c243d] border border-white/10 rounded-xl p-4 outline-none focus:border-[#3a96a5] transition-colors text-white placeholder-gray-500 text-sm"
              />

              <textarea
                name="message"
                placeholder="Your Message *"
                rows={4}
                required
                value={formData.message}
                onChange={handleChange}
                className="w-full bg-[#1c243d] border border-white/10 rounded-xl p-4 outline-none focus:border-[#3a96a5] transition-colors text-white placeholder-gray-500 text-sm resize-none"
              />

              {/* CENTERED BUTTON WRAPPER */}
              <div className="flex justify-center pt-2">
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="w-full md:w-auto min-w-[220px] bg-[#3a96a5] hover:bg-[#2d7a87] text-white px-10 py-4 rounded-xl font-bold flex items-center justify-center gap-3 transition-all active:scale-95 disabled:opacity-50 shadow-xl shadow-teal-900/10"
                >
                  <Send size={18} />
                  {isSubmitting ? "Sending..." : "Send Message"}
                </button>
              </div>
            </form>
          </div>
        </div>

        {/* BOTTOM SECTION */}
        <div className="pt-8 border-t border-white/5 flex flex-col md:flex-row justify-between items-center gap-6 text-gray-500 text-[10px] font-bold uppercase tracking-widest">
          <p>&copy; {new Date().getFullYear()} Nyaya. All rights reserved.</p>
          <p className="text-[#c5a059]">Information provided is for educational purposes only and does not constitute legal
advice. Please consult a qualified attorney for legal matters.</p>
        </div>
      </div>
    </footer>
  );
}