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
  const [status, setStatus] = useState<{
    type: "success" | "error";
    msg: string;
  } | null>(null);

  /**
   * handleChange:
   * Dynamically updates the formData state based on the input field's 'name' attribute.
   */
  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>,
  ) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };



  return { formData, handleChange, isSubmitting, status };
}
