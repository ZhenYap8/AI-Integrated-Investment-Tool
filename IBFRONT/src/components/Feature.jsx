// src/components/Feature.jsx
import React from "react";
export default function Feature({ title, text }) {
  return (
    <div className="rounded-2xl border bg-white dark:bg-slate-900 dark:border-slate-800 p-5">
      <div className="text-lg font-semibold">{title}</div>
      <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">{text}</p>
    </div>
  );
}
