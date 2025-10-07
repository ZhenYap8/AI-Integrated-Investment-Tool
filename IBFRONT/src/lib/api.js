// src/lib/api.js
export const API_BASE = import.meta.env?.VITE_API_URL ? import.meta.env.VITE_API_URL.replace(/\/$/, "") : "";
export const api = (path) => `${API_BASE}${path}`;

export async function fetchJSON(input, init) {
  const res = await fetch(input, init);
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(text || `Request failed (${res.status})`);
  }
  return res.json();
}
