// src/components/NumField.jsx
import React from "react";
export default function NumField({ label, suffix, value, placeholder, onChange, onBlur, hint }) {
  return (
    <label className="block mt-3">
      <div className="text-sm text-slate-700 dark:text-slate-300">{label} <span className="sub">{hint}</span></div>
      <div className="flex items-center gap-2 mt-1">
        <input
          type="number"
          value={value}
          placeholder={placeholder}
          onChange={(e) => onChange(e.target.value)}
          onBlur={onBlur}
          className="w-full rounded-lg border px-3 py-2"
          step="0.1"
        />
        {suffix && <span className="text-sm text-slate-600 dark:text-slate-400">{suffix}</span>}
      </div>
    </label>
  );
}
