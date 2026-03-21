"use client";

import Image from "next/image";
import { Mail, Phone, MapPin } from "lucide-react";
import { useFooterLogic } from "@/lib/Footer";
import { usePathname } from "next/navigation";

export default function Footer() {
  const pathname = usePathname();
  const { formData, handleChange, isSubmitting, status } = useFooterLogic();

  const hideOnPaths = ["/login", "/signup", "/signup_success"];
  if (hideOnPaths.includes(pathname)) return null;

  return (
    <footer className="bg-[#0f172a] text-white pt-20 pb-12 px-6 md:px-12 border-t border-white/5">
      <div className="max-w-7xl mx-auto">
        {/* TOP SECTION: Logo and Branding */}
        <div className="flex flex-col items-center text-center space-y-6 pb-12">
          <div className="flex items-center gap-4">
            <Image
              src="/Nyaya_logo_temp.png"
              alt="Nyaya Logo"
              width={48}
              height={48}
              className="rounded-full border border-white/10"
            />
            <h2 className="text-2xl font-bold tracking-tight">Nyaya</h2>
          </div>
          <p className="text-gray-400 leading-relaxed text-sm max-w-md">
            Your comprehensive Sri Lankan legal resource hub. Access legal
            information and learn about Sri Lankan law.
          </p>
        </div>

        {/* MIDDLE SECTION: Contact Row */}
        <div className="flex flex-col md:flex-row items-center justify-center gap-10 md:gap-24 py-12 border-y border-white/5">
          <a
            href="mailto:info@nyaya.lk"
            className="flex items-center gap-4 group transition-all"
          >
            <Mail
              size={18}
              className="text-[#c5a059] group-hover:scale-110 transition-transform"
            />
            <span className="text-sm font-medium text-gray-300 group-hover:text-white transition-colors tracking-widest uppercase">
              info@nyaya.lk
            </span>
          </a>

          <a
            href="tel:+94112345678"
            className="flex items-center gap-4 group transition-all"
          >
            <Phone
              size={18}
              className="text-[#c5a059] group-hover:scale-110 transition-transform"
            />
            <span className="text-sm font-medium text-gray-300 group-hover:text-white transition-colors tracking-widest uppercase">
              +94 11 234 5678
            </span>
          </a>

          <div className="flex items-center gap-4">
            <MapPin size={18} className="text-[#c5a059]" />
            <span className="text-sm font-medium text-gray-300 tracking-widest uppercase">
              Colombo 03, Sri Lanka
            </span>
          </div>
        </div>

        {/* BOTTOM SECTION: Legal & Copyright */}
        <div className="pt-6 flex flex-col items-center text-center gap-4">
          {/* Copyright Line */}
          <p className="text-gray-500 text-[10px] font-bold uppercase tracking-[0.2em] whitespace-nowrap">
            &copy; {new Date().getFullYear()} Nyaya. All rights reserved.
          </p>

          {/* Disclaimer Line */}
          <p className="text-gray-500 text-[11px] leading-[1.8] max-w-2xl">
            <span className="text-[#c5a059] font-bold uppercase text-[9px] tracking-wider mr-2">
              Legal Disclaimer:
            </span>
            Information provided is for educational purposes only and does not
            constitute legal advice. Please consult a qualified attorney for
            legal matters.
          </p>
        </div>
      </div>
    </footer>
  );
}
