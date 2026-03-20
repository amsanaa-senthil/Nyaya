const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function askNyaya(question: string) {
  const res = await fetch(`${API_URL}/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });

  if (!res.ok) throw new Error("API error: " + res.status);
  return res.json();
}
