import React from 'react';
import Badge from './Badge.jsx';

const FACTOR_LABELS = {
  growth: 'Growth',
  margins: 'Margins',
  leverage: 'Leverage',
  competition: 'Competition',
  guidance: 'Guidance',
  legal_esg: 'Legal/ESG',
  valuation: 'Valuation',
  other: 'Other',
};

const TIMEFRAME_LABELS = {
  near_term: 'Near-term',
  multi_year: 'Multi-year',
  unspecified: '',
};

function MaterialityBar({ value = 0.5 }) {
  const pct = Math.round(Math.max(0, Math.min(1, value)) * 100);
  return (
    <div className="materiality-bar" title={`Materiality: ${pct}%`}>
      <div className="materiality-fill" style={{ width: `${pct}%` }} />
    </div>
  );
}

function FindingCard({ finding, tone }) {
  const text = finding?.text || finding?.item || '';
  const factor = finding?.factor;
  const timeframe = finding?.timeframe;
  const materiality = finding?.materiality;
  const outlet = finding?.outlet || finding?.source || finding?.evidence?.[0]?.source;
  const sourceUrl = finding?.sourceUrl || finding?.evidence?.[0]?.url;
  const snippet = finding?.snippet || finding?.evidence?.[0]?.snippet;

  return (
    <li className={`finding-card finding-${tone}`}>
      <div className="finding-meta">
        {factor && (
          <span className="finding-tag">{FACTOR_LABELS[factor] || factor}</span>
        )}
        {timeframe && TIMEFRAME_LABELS[timeframe] && (
          <span className="finding-tag muted">{TIMEFRAME_LABELS[timeframe]}</span>
        )}
        {outlet && (
          <span className="finding-tag outlet">{outlet}</span>
        )}
        {typeof materiality === 'number' && <MaterialityBar value={materiality} />}
      </div>
      <p className="finding-text">{text}</p>
      {snippet && snippet !== text && (
        <p className="finding-snippet">{snippet}</p>
      )}
      {sourceUrl && (
        <a className="finding-source" href={sourceUrl} target="_blank" rel="noreferrer">
          {outlet ? `Read on ${outlet}` : 'View source'}
        </a>
      )}
    </li>
  );
}

export default function ProsCons({ pros = [], cons = [], risks = [], loading = false }) {
  const hasPros = pros.length > 0;
  const hasCons = cons.length > 0;
  const hasRisks = risks.length > 0;

  if (loading) {
    return (
      <div className="proscons-grid">
        <div className="proscons-col skeleton-pulse">Loading analysis…</div>
        <div className="proscons-col skeleton-pulse">Loading analysis…</div>
      </div>
    );
  }

  if (!hasPros && !hasCons && !hasRisks) {
    return <p className="sub">No AI findings available. Run analysis on a company ticker.</p>;
  }

  return (
    <div className="proscons-wrap">
      <div className="proscons-grid">
        <div className="proscons-col">
          <div className="proscons-header">
            <span className="proscons-icon pro">+</span>
            <h4>Bull Case</h4>
            {hasPros && <Badge tone="green">{pros.length}</Badge>}
          </div>
          {!hasPros ? (
            <p className="sub">No bullish signals identified.</p>
          ) : (
            <ul className="finding-list">
              {pros.map((f, i) => (
                <FindingCard key={`pro-${i}`} finding={f} tone="pro" />
              ))}
            </ul>
          )}
        </div>

        <div className="proscons-col">
          <div className="proscons-header">
            <span className="proscons-icon con">−</span>
            <h4>Bear Case</h4>
            {hasCons && <Badge tone="red">{cons.length}</Badge>}
          </div>
          {!hasCons ? (
            <p className="sub">No bearish signals identified.</p>
          ) : (
            <ul className="finding-list">
              {cons.map((f, i) => (
                <FindingCard key={`con-${i}`} finding={f} tone="con" />
              ))}
            </ul>
          )}
        </div>
      </div>

      {hasRisks && (
        <div className="risks-section">
          <h4 className="risks-title">Key Risks</h4>
          <ul className="risks-list">
            {risks.map((r, i) => (
              <li key={i}>{r.text || r}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
