import React, { useRef, useState } from "react";

export function Card({ children, className = "" }) {
  return <section className={`rounded-2xl border bg-white dark:bg-slate-900 dark:border-slate-800 p-5 shadow-sm ${className}`}>{children}</section>;
}

export function EmptyState({ onDemo }) {
  return (
    <div className="rounded-2xl border bg-white dark:bg-slate-900 dark:border-slate-800 p-8 shadow-sm text-slate-700 dark:text-slate-300">
      <div className="flex items-start gap-4">
        <div className="text-3xl">🔎</div>
        <div>
          <h3 className="text-lg font-semibold">Search to begin</h3>
          <p className="text-sm mt-1">
            Enter a company (e.g., <span className="font-medium">NVDA</span>) or an industry (e.g., <span className="font-medium">Robotics</span>), set the years slider, and click Analyze.
          </p>
          <button onClick={onDemo} className="mt-4 rounded-lg border px-3 py-1.5 text-sm hover:bg-slate-50 dark:hover:bg-slate-800">
            Run NVDA demo
          </button>
        </div>
      </div>
    </div>
  );
}

export function SkeletonCard({ className = "" }) {
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

export function SearchBar({ value, onChange, onSubmit, suggestions = [], showSuggest, setShowSuggest, loading, onPickSuggestion }) {
  const [active, setActive] = useState(0);
  const listRef = useRef(null);

  const onKeyDown = (e) => {
    if (!showSuggest || suggestions.length === 0) {
      if (e.key === "Enter") onSubmit();
      return;
    }
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActive((i) => (i + 1) % suggestions.length);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActive((i) => (i - 1 + suggestions.length) % suggestions.length);
    } else if (e.key === "Enter") {
      e.preventDefault();
      const s = suggestions[active];
      if (s) onPickSuggestion(s);
    } else if (e.key === "Escape") {
      setShowSuggest(false);
    }
  };

  return (
    <div className="search-wrap">
      <span className="search-icon" aria-hidden>
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
          <circle cx="11" cy="11" r="7" stroke="currentColor" strokeWidth="2" />
          <path d="M20 20l-3.5-3.5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
        </svg>
      </span>

      <input
        value={value}
        onChange={(e) => {
          onChange(e.target.value);
          setShowSuggest(true);
        }}
        onFocus={() => setShowSuggest(true)}
        onKeyDown={onKeyDown}
        placeholder="Search company or industry (e.g., NVDA, ABB, Robotics)…"
        className="search"
        aria-autocomplete="list"
        aria-expanded={showSuggest}
        aria-controls="suggest-list"
      />

      {loading && <span className="loading-spin" aria-hidden />}

      {value && !loading && (
        <button
          type="button"
          className="clear-btn"
          aria-label="Clear search"
          onMouseDown={(e) => e.preventDefault()}
          onClick={() => {
            onChange("");
            setShowSuggest(false);
          }}
          title="Clear"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" aria-hidden="true">
            <path d="M6 6l12 12M18 6L6 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
          </svg>
        </button>
      )}

      {showSuggest && suggestions.length > 0 && (
        <div id="suggest-list" role="listbox" className="suggest" ref={listRef}>
          {suggestions.map((s, i) => (
            <button
              key={`${s.value}-${i}`}
              role="option"
              aria-selected={i === active}
              className="suggest-item"
              onMouseEnter={() => setActive(i)}
              onClick={() => onPickSuggestion(s)}
            >
              <span className="label">{s.label || s.value}</span>
              <span className="type">{s.type === "industry" ? "Industry" : "Company"}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

export function fmtCurrency(v) {
  if (v == null || isNaN(v)) return "—";
  try {
    return new Intl.NumberFormat(undefined, { style: "currency", currency: "USD", maximumFractionDigits: 2 }).format(v);
  } catch {
    return `$${Number(v).toFixed(2)}`;
  }
}

export function Bullets({ title, items = [], tone = 'green' }) {
  const toneClass = tone === "green" ? "text-green-700 dark:text-green-400" : 
                   tone === "amber" ? "text-amber-700 dark:text-amber-400" : 
                   "text-red-700 dark:text-red-400";
  const bgClass = tone === "green" ? "bg-green-50 dark:bg-green-950/30" : 
                  tone === "amber" ? "bg-amber-50 dark:bg-amber-950/30" : 
                  "bg-red-50 dark:bg-red-950/30";

  return (
    <div>
      <h3 className={`text-sm font-semibold ${toneClass} mb-2`}>{title}</h3>
      {!items || items.length === 0 ? (
        <div className={`${bgClass} rounded-lg p-3 text-sm text-slate-600 dark:text-slate-400 italic`}>
          No items identified for this analysis period.
        </div>
      ) : (
        <ul className="space-y-2">
          {items.map((item, i) => (
            <li key={i} className={`${bgClass} rounded-lg p-3 text-sm leading-relaxed`}>
              <span className="font-medium">
                {/* Handle both string items and object items */}
                {typeof item === 'string' ? item : item.item || item.text || item}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

// ScoreItem removed - now using dedicated component in /components/ScoreItem.jsx
// This component has been replaced with a more feature-rich version that supports
// value, threshold, and unit props for better scorecard display