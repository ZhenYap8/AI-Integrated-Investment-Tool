// src/components/KPI.jsx
import React from "react";
export default function KPI({ label, value }) {
  return (
    <div className="rounded-xl border p-4 bg-slate-50 dark:bg-slate-800/50">
      <div className="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">{label}</div>
      <div className="text-xl font-semibold mt-1">{value ?? '—'}</div>
    </div>
  );
}
