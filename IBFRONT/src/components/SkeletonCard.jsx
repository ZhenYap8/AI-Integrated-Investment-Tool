// src/components/SkeletonCard.jsx
import React from "react";
export default function SkeletonCard({ className = "" }) {
  return (
    <div className={`rounded-2xl border bg-white dark:bg-slate-900 dark:border-slate-800 shadow-sm p-5 ${className}`}>
      <div className="animate-pulse space-y-3">
        <div className="h-5 bg-slate-200 dark:bg-slate-800 rounded w-1/3"></div>
        <div className="h-4 bg-slate-200 dark:bg-slate-800 rounded w-full"></div>
        <div className="h-4 bg-slate-200 dark:bg-slate-800 rounded w-5/6"></div>
        <div className="h-4 bg-slate-200 dark:bg-slate-800 rounded w-2/3"></div>
      </div>
    </div>
  );
}
