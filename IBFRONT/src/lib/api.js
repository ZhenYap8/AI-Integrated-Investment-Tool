// src/lib/api.js
function normalizeApiBase(raw) {
  let base = (raw || "").trim().replace(/\/$/, "");
  if (!base) return "";
  if (!/^https?:\/\//i.test(base)) {
    base = `https://${base}`;
  }
  return base;
}

export const API_BASE = normalizeApiBase(import.meta.env?.VITE_API_URL);
export const api = (path) => `${API_BASE}${path}`;

export async function fetchJSON(input, init) {
  const res = await fetch(input, init);
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(text || `Request failed (${res.status})`);
  }
  return res.json();
}
