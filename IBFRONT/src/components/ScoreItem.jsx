// src/components/ScoreItem.jsx
import React from 'react';

const ScoreItem = ({ label, verdict, detail, value, threshold, unit, loading }) => {
  const verdictClass = verdict === 'green' ? 'pass' : verdict === 'amber' ? 'warn' : 'fail';

  return (
    <div className={`score-card score-${verdictClass} ${loading ? 'loading' : ''}`}>
      <div className="score-head">
        <span className="score-label">{label}</span>
        {!loading && verdict && (
          <span className={`pill ${verdict}`}>{verdict === 'green' ? 'PASS' : verdict === 'amber' ? 'WARN' : 'FAIL'}</span>
        )}
        {loading && <span className="pill">…</span>}
      </div>
      {!loading && value != null && (
        <div className="score-value">
          {value}{unit === '%' ? '%' : unit === 'x' ? 'x' : unit || ''}
          {threshold != null && (
            <span className="score-threshold"> vs {threshold}{unit === '%' ? '%' : unit === 'x' ? 'x' : ''}</span>
          )}
        </div>
      )}
      <div className="score-detail">{detail || (loading ? 'Loading…' : '')}</div>
    </div>
  );
};

export default ScoreItem;
