import React from 'react';
import { Link } from 'react-router-dom';
import Badge from '../../components/Badge.jsx';

function gradeTone(grade) {
  if (grade === 'A') return 'green';
  if (grade === 'B') return 'green';
  if (grade === 'C') return 'amber';
  if (grade === '—' || grade === 'ND') return 'gray';
  return 'red';
}

function scoreTone(score) {
  if (score >= 80) return 'green';
  if (score >= 60) return 'amber';
  return 'red';
}

function fmtPct(value) {
  if (value == null || Number.isNaN(value)) return '—';
  return `${Number(value).toFixed(1)}%`;
}

function PassDots({ breakdown = [] }) {
  const dots = breakdown.length >= 5
    ? breakdown
    : [...breakdown, ...Array(Math.max(0, 5 - breakdown.length)).fill({ verdict: 'missing' })];

  return (
    <span className="pass-dots" title={`${dots.filter((d) => d.verdict === 'green').length}/5 metrics pass`}>
      {dots.slice(0, 5).map((d, i) => (
        <span key={i} className={`pass-dot ${d.verdict === 'green' ? 'pass' : d.verdict === 'missing' ? 'missing' : 'fail'}`} />
      ))}
    </span>
  );
}

export default function ScreenerTable({
  items = [],
  loading = false,
  selected,
  onSelect,
  shortlist = [],
  onToggleShortlist,
  page = 1,
  pageSize = 50,
  showPagination = false,
}) {
  const pageItems = showPagination
    ? items.slice((page - 1) * pageSize, page * pageSize)
    : items;

  if (loading && !items.length) {
    return (
      <div className="screen-table-wrap">
        <div className="screen-empty">Loading screening results…</div>
      </div>
    );
  }

  if (!items.length) {
    return (
      <div className="screen-table-wrap">
        <div className="screen-empty">No stocks match your filters. Try a different preset or clear filters.</div>
      </div>
    );
  }

  return (
    <div className="screen-table-wrap">
      <table className="screen-table screen-table-compact">
        <thead>
          <tr>
            <th aria-label="Shortlist" />
            <th>#</th>
            <th>Ticker</th>
            <th>Company</th>
            <th>Quality</th>
            <th>Grade</th>
            <th>Metrics</th>
            <th>Rev CAGR</th>
            <th>Margin</th>
            <th>ROE</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {pageItems.map((row, idx) => {
            const metrics = row.metrics || {};
            const rev = metrics.revenue_cagr != null ? metrics.revenue_cagr * 100 : null;
            const margin = metrics.operating_margin != null ? metrics.operating_margin * 100 : null;
            const roe = metrics.roe != null ? metrics.roe * 100 : null;
            const active = selected?.ticker === row.ticker;
            const starred = shortlist.includes(row.ticker);
            const displayRank = showPagination ? (page - 1) * pageSize + idx + 1 : idx + 1;

            return (
              <tr
                key={row.ticker}
                className={active ? 'screen-row-active' : ''}
                onClick={() => onSelect?.(row)}
              >
                <td>
                  <button
                    type="button"
                    className={`screen-star ${starred ? 'starred' : ''}`}
                    aria-label={starred ? 'Remove from shortlist' : 'Add to shortlist'}
                    onClick={(e) => { e.stopPropagation(); onToggleShortlist?.(row.ticker); }}
                  >
                    {starred ? '★' : '☆'}
                  </button>
                </td>
                <td>{row.rank ?? displayRank}</td>
                <td>
                  <button type="button" className="screen-ticker-btn" onClick={(e) => { e.stopPropagation(); onSelect?.(row); }}>
                    {row.ticker}
                  </button>
                </td>
                <td>
                  <div className="screen-company">{row.companyName}</div>
                  <div className="screen-meta">{row.sector || row.exchangeLabel || ''}</div>
                </td>
                <td>
                  <span className={`screen-score screen-score-${scoreTone(row.compositeScore)}`}>
                    {row.compositeScore}
                  </span>
                </td>
                <td><Badge tone={gradeTone(row.grade)}>{row.grade}</Badge></td>
                <td><PassDots breakdown={row.breakdown} /></td>
                <td>{fmtPct(rev)}</td>
                <td>{fmtPct(margin)}</td>
                <td>{fmtPct(roe)}</td>
                <td>
                  <Link to={`/analyze?query=${encodeURIComponent(row.ticker)}`} className="screen-link" onClick={(e) => e.stopPropagation()}>
                    Analyse
                  </Link>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export function ScreenerDetail({ row, starred = false, onToggleShortlist }) {
  if (!row) {
    return (
      <div className="screen-detail-empty">
        Select a stock to see how its quality score was calculated.
      </div>
    );
  }

  return (
    <div className="screen-detail">
      <div className="screen-detail-header">
        <div>
          <h3>{row.ticker} · {row.companyName}</h3>
          <p className="screen-detail-sub">
            Quality score {row.compositeScore}/100 · Grade {row.grade}
            {' · '}{row.greens}/{row.totalMetrics} metrics pass
            {row.metricsAvailable != null && row.metricsAvailable < 5
              ? ` · ${row.metricsAvailable}/5 data available`
              : ''}
          </p>
        </div>
        <div className="screen-detail-actions">
          <button
            type="button"
            className={`btn-secondary screen-star-btn ${starred ? 'starred' : ''}`}
            onClick={() => onToggleShortlist?.(row.ticker)}
          >
            {starred ? '★ Shortlisted' : '☆ Add to shortlist'}
          </button>
          <Link to={`/analyze?query=${encodeURIComponent(row.ticker)}`} className="btn-range">
            Full analysis
          </Link>
        </div>
      </div>
      <div className="screen-breakdown">
        {(row.breakdown || []).map((item) => (
          <div
            key={item.id}
            className={`screen-breakdown-item score-${
              item.verdict === 'green' ? 'pass' : item.verdict === 'missing' ? 'warn' : 'fail'
            }`}
          >
            <div className="screen-breakdown-top">
              <span>{item.label}{item.verdict === 'missing' ? ' (no data)' : ''}</span>
              <span>{item.points}/{item.maxPoints} pts</span>
            </div>
            <div className="screen-breakdown-bar">
              <div
                className={`screen-breakdown-fill screen-breakdown-fill-${
                  item.verdict === 'green' ? 'pass' : item.verdict === 'missing' ? 'warn' : 'fail'
                }`}
                style={{ width: `${Math.min(100, (item.points / item.maxPoints) * 100)}%` }}
              />
            </div>
            <div className="score-detail">
              {item.verdict === 'missing'
                ? 'Insufficient Yahoo Finance data for this metric'
                : (
                  <>
                    {item.value != null ? `${item.value}${item.unit === '%' ? '%' : item.unit || ''}` : '—'}
                    {' vs '}
                    {item.threshold != null ? `${item.threshold}${item.unit === '%' ? '%' : item.unit || ''}` : '—'}
                  </>
                )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
