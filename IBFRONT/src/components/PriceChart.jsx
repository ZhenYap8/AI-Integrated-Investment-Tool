// src/components/PriceChart.jsx
import React from "react";

export default function PriceChart({ series = [], width = '100%', height = 200 }) {
  if (!series || series.length < 2) {
    return <div className="chart-empty sub">ROE chart unavailable.</div>;
  }

  const xs = series.map(p => p.t.getTime());
  const ys = series.map(p => p.y);
  const minX = Math.min(...xs), maxX = Math.max(...xs);
  const minY = Math.min(...ys), maxY = Math.max(...ys);
  const padY = (maxY - minY) * 0.08 || 1;

  const W = 800;
  const H = typeof height === 'number' ? height : 200;
  const toX = t => ((t - minX) / (maxX - minX || 1)) * (W - 20) + 10;
  const toY = y => {
    const a = (y - (minY - padY)) / ((maxY + padY) - (minY - padY) || 1);
    return (1 - a) * (H - 20) + 10;
  };

  let d = `M ${toX(xs[0])} ${toY(ys[0])}`;
  for (let i = 1; i < series.length; i++) {
    d += ` L ${toX(xs[i])} ${toY(ys[i])}`;
  }

  const last = series[series.length - 1].y;
  const first = series[0].y;
  const pct = ((last - first) / first) * 100;

  return (
    <div className="chart-wrap">
      <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" style={{ width, height }}>
        <path d={d} fill="none" stroke="currentColor" strokeWidth="2" className={pct >= 0 ? 'chart-line up' : 'chart-line down'} />
        <line x1="10" x2={W-10} y1={toY(first)} y2={toY(first)} className="chart-baseline" />
      </svg>
      <div className="chart-meta">
        <span className="sub">ROE change</span>
        <span className={`chart-pct ${pct >= 0 ? 'up' : 'down'}`}>{pct >= 0 ? '+' : ''}{pct.toFixed(2)}%</span>
      </div>
    </div>
  );
}
