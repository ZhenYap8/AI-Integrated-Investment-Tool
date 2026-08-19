import React from 'react';
import { Link } from 'react-router-dom';
import Badge from '../../components/Badge.jsx';

function gradeTone(grade) {
  if (grade === 'A') return 'green';
  if (grade === 'B') return 'green';
  if (grade === 'C') return 'amber';
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

export default function ScreenerTable({ items = [], loading = false, selected, onSelect }) {
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
        <div className="screen-empty">No stocks match your filters yet. Try refreshing the pipeline.</div>
      </div>
    );
  }

  return (
    <div className="screen-table-wrap">
      <table className="screen-table">
        <thead>
          <tr>
            <th>#</th>
            <th>Ticker</th>
            <th>Company</th>
            <th>Score</th>
            <th>Grade</th>
            <th>Pass</th>
            <th>Rev CAGR</th>
            <th>Op Margin</th>
            <th>ROE</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {items.map((row) => {
            const metrics = row.metrics || {};
            const rev = metrics.revenue_cagr != null ? metrics.revenue_cagr * 100 : null;
            const margin = metrics.operating_margin != null ? metrics.operating_margin * 100 : null;
            const roe = metrics.roe != null ? metrics.roe * 100 : null;
            const active = selected?.ticker === row.ticker;
            return (
              <tr
                key={row.ticker}
                className={active ? 'screen-row-active' : ''}
                onClick={() => onSelect?.(row)}
              >
                <td>{row.rank}</td>
                <td>
                  <button type="button" className="screen-ticker-btn" onClick={(e) => { e.stopPropagation(); onSelect?.(row); }}>
                    {row.ticker}
                  </button>
                </td>
                <td>
                  <div className="screen-company">{row.companyName}</div>
                  <div className="screen-meta">{row.exchangeLabel || row.exchange}{row.sector ? ` · ${row.sector}` : ''}</div>
                </td>
                <td><span className={`screen-score screen-score-${scoreTone(row.compositeScore)}`}>{row.compositeScore}</span></td>
                <td><Badge tone={gradeTone(row.grade)}>{row.grade}</Badge></td>
                <td>{row.greens}/{row.totalMetrics}</td>
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

export function ScreenerDetail({ row }) {
  if (!row) {
    return (
      <div className="screen-detail-empty">
        Select a stock to see how its composite score was calculated.
      </div>
    );
  }

  return (
    <div className="screen-detail">
      <div className="screen-detail-header">
        <div>
          <h3>{row.ticker} · {row.companyName}</h3>
          <p className="screen-detail-sub">
            Composite score {row.compositeScore}/100 · Grade {row.grade} · {row.passRate}% pass rate
          </p>
        </div>
        <Link to={`/analyze?query=${encodeURIComponent(row.ticker)}`} className="btn-range">
          Full analysis
        </Link>
      </div>
      <div className="screen-breakdown">
        {(row.breakdown || []).map((item) => (
          <div key={item.id} className={`screen-breakdown-item score-${item.verdict === 'green' ? 'pass' : 'fail'}`}>
            <div className="screen-breakdown-top">
              <span>{item.label}</span>
              <span>{item.points}/{item.maxPoints} pts</span>
            </div>
            <div className="screen-breakdown-bar">
              <div
                className={`screen-breakdown-fill screen-breakdown-fill-${item.verdict === 'green' ? 'pass' : 'fail'}`}
                style={{ width: `${Math.min(100, (item.points / item.maxPoints) * 100)}%` }}
              />
            </div>
            <div className="score-detail">
              {item.value != null ? `${item.value}${item.unit === '%' ? '%' : item.unit || ''}` : '—'}
              {' vs '}
              {item.threshold != null ? `${item.threshold}${item.unit === '%' ? '%' : item.unit || ''}` : '—'}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
