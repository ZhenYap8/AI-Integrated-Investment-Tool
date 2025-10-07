// src/components/Bullets.jsx
import React from "react";
export default function Bullets({ title, items = [], tone = 'gray' }) {
  const toneMap = { green: 'border-green-200', amber: 'border-yellow-200', red: 'border-red-200', gray: 'border-slate-200' };
  return (
    <div>
      <h4 className="font-semibold mb-2">{title}</h4>
      {(!items || items.length === 0) && <p className="text-sm text-slate-500 dark:text-slate-400">No items available.</p>}
      <ul className="space-y-2">
        {items.map((it, i) => (
          <li key={i} className={`rounded-xl border ${toneMap[tone]} p-3 bg-slate-50 dark:bg-slate-800/40`}>
            <div className="text-sm">{it.text}</div>
            {(it.desc || it.snippet) && (
              <div className="sub" style={{ marginTop: 4 }}>{it.desc || it.snippet}</div>
            )}
            {it.source && (<a className="text-xs text-blue-700 hover:underline" href={it.source} target="_blank" rel="noreferrer">Source</a>)}
          </li>
        ))}
      </ul>
    </div>
  );
}
