"use client";

import { useState } from "react";

/**
 * useFooterLogic:
 * Manages the state and submission of the "Contact Us" form found in the footer.
 */
export function useFooterLogic() {
  // State object to store user input for the contact form
  const [formData, setFormData] = useState({
    name: "",
    phone: "",
    email: "",
    message: "",
  });

  // Loading state to disable the button during submission
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Status state to provide visual feedback (Success or Error) to the user
  const [status, setStatus] = useState<{ type: 'success' | 'error', msg: string } | null>(null);

  /**
   * handleChange:
   * Dynamically updates the formData state based on the input field's 'name' attribute.
   */
  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  /**
   * handleSubmit:
   * Handles the form submission logic. Currently simulates an API call.
   */
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setStatus(null); // Clear previous status

    try {
      // Logic for sending message (e.g., Supabase, EmailJS, or an API route)
      // Simulating a network delay of 1.5 seconds
      await new Promise((resolve) => setTimeout(resolve, 1500));
      
      // On success: update UI and reset the form
      setStatus({ type: 'success', msg: "Message sent! We'll get back to you soon." });
      setFormData({ name: "", phone: "", email: "", message: "" });
    } catch (error) {
      // On failure: notify the user
      setStatus({ type: 'error', msg: "Something went wrong. Please try again." });
    } finally {
      setIsSubmitting(false);
    }
  };

  return { formData, handleChange, handleSubmit, isSubmitting, status };
}