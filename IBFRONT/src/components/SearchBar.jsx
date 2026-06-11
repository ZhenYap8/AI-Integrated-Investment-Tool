import React, { useRef, useState } from "react";

const EXCHANGE_SHORT = {
  US_NASDAQ: "NDQ",
  US_OTHER: "NYSE",
  TSX: "TSX",
  LSE: "LSE",
  ASX: "ASX",
  HKEX: "HK",
  TSE_JP: "TSE",
  GLOBAL: "GLB",
  INDEX: "IDX",
  EURONEXT: "EUR",
  XETRA: "ETR",
  US_ADR: "ADR",
  US_OTC: "OTC",
};

function SearchBar({
  value,
  onChange,
  onSubmit,
  suggestions = [],
  showSuggest,
  setShowSuggest,
  loading,
  onPickSuggestion,
}) {
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
          <circle cx="11" cy="11" r="7" stroke="currentColor" strokeWidth="2"/>
          <path d="M20 20l-3.5-3.5" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
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
        placeholder="Search globally — NVDA, BP.L, SHOP.TO, 0700.HK, Robotics…"
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
          onClick={() => { onChange(""); setShowSuggest(false); }}
          title="Clear"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" aria-hidden="true">
            <path d="M6 6l12 12M18 6L6 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
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
              <span className="suggest-badges">
                {s.exchange && (
                  <span className="exchange-badge">
                    {s.exchangeLabel || EXCHANGE_SHORT[s.exchange] || s.exchange}
                  </span>
                )}
                <span className="type">{s.type === "industry" ? "Industry" : "Company"}</span>
              </span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

export default SearchBar;
