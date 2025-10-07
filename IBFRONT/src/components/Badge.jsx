// src/components/Badge.jsx
import React from "react";
export default function Badge({ children, tone = 'gray' }) {
  const tones = {
    green: 'bg-green-100 text-green-800 border-green-200',
    red: 'bg-red-100 text-red-800 border-red-200',
    gray: 'bg-slate-100 text-slate-800 border-slate-200',
  };
  return <span className={`inline-flex items-center rounded-full border px-3 py-1 text-xs font-medium ${tones[tone]}`}>{children}</span>;
}
