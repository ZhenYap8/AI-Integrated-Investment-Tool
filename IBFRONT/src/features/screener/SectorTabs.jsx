import React from 'react';

export default function SectorTabs({ sectors = [], counts = {}, active = '', onSelect }) {
  if (!sectors.length) return null;

  return (
    <div className="sector-tabs-wrap">
      <div className="sector-tabs-label">Sector</div>
      <div className="sector-tabs">
        {sectors.map((name) => (
          <button
            key={name}
            type="button"
            className={`sector-tab ${active === name ? 'active' : ''}`}
            onClick={() => onSelect(name)}
          >
            {name}
            <span className="sector-tab-count">{counts[name] ?? 0}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
