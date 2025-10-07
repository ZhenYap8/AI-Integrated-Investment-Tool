// src/components/ScoreItem.jsx
import React from 'react';

/**
 * ScoreItem Component
 * Displays a single scorecard metric with verdict badge
 */
const ScoreItem = ({ label, verdict, detail, value, threshold, unit, loading }) => {
  return (
    <div className={`score-card ${loading ? 'loading' : ''}`}>
      <div className="score-head">
        <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>{label}</span>
        {!loading && verdict && (
          <span className={`pill ${verdict}`}>{verdict?.toUpperCase()}</span>
        )}
        {loading && (
          <span className="pill" style={{ backgroundColor: '#e5e7eb', color: '#9ca3af' }}>...</span>
        )}
      </div>
      <div style={{ fontSize: '0.85rem', color: loading ? 'var(--muted)' : 'var(--text)', marginTop: '8px' }}>
        {detail || 'Loading...'}
      </div>
    </div>
  );
};

export default ScoreItem;