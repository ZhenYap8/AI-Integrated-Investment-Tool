// src/components/PriceChart.jsx
import React from "react";

export default function PriceChart({ series = [], width = '100%', height = 200, label = 'ROE' }) {
  if (!series || series.length < 2) {
    return <div className="chart-empty sub">{label} chart unavailable.</div>;
  }

  const xs = series.map(p => p.t.getTime());
  const ys = series.map(p => p.y);
  const minX = Math.min(...xs), maxX = Math.max(...xs);
  const minY = Math.min(...ys), maxY = Math.max(...ys);
  const padY = (maxY - minY) * 0.08 || 1;

  const W = 800; // logical width
  const H = typeof height === 'number' ? height : 200;

  // Ticks (computed early so we can size padding dynamically)
  const xTickCount = 5;
  const xTicks = Array.from({ length: xTickCount }, (_, i) => new Date(minX + (i / (xTickCount - 1 || 1)) * (maxX - minX || 1)));
  const yTickCount = 5;
  const yRangeMin = minY - padY;
  const yRangeMax = maxY + padY;
  const yTicks = Array.from({ length: yTickCount }, (_, i) => yRangeMin + (i / (yTickCount - 1 || 1)) * (yRangeMax - yRangeMin));

  const formatX = dt => {
    const spanDays = (maxX - minX) / 86400000;
    if (spanDays > 1825) return dt.getFullYear(); // >5y
    if (spanDays > 730) return dt.getFullYear();  // >2y keep year only
    return `${dt.getFullYear()}-${String(dt.getMonth() + 1).padStart(2, '0')}`;
  };
  const formatYNum = v => {
    if (Math.abs(v) >= 1000) return v.toFixed(0);
    if (Math.abs(v) >= 100) return v.toFixed(1);
    if (Math.abs(v) >= 10) return v.toFixed(1);
    return v.toFixed(2);
  };
  const formatY = v => formatYNum(v) + '%';

  const yTickStrings = yTicks.map(formatY);
  const maxYChars = Math.max(...yTickStrings.map(s => s.length), 2);

  // Approximate character width (SVG, monospace-ish assumption)
  const charW = 6.2;
  const leftPad = 10 + maxYChars * charW + 12; // label gap

  // Decide if x tick labels need rotation
  const xTickStrings = xTicks.map(formatX);
  const maxXChars = Math.max(...xTickStrings.map(s => s.length));
  const plotWTemp = W - leftPad - 16; // provisional
  const avgSlot = plotWTemp / (xTicks.length - 1 || 1);
  const rotateX = (maxXChars * 6.5 > avgSlot * 0.9) || avgSlot < 60; // heuristic
  const bottomPad = rotateX ? 48 : 34;
  const topPad = 16;
  const rightPad = 12;

  const plotW = W - leftPad - rightPad;
  const plotH = H - topPad - bottomPad;

  const toX = t => ((t - minX) / (maxX - minX || 1)) * plotW + leftPad;
  const toY = y => {
    const a = (y - (minY - padY)) / ((maxY + padY) - (minY - padY) || 1);
    return (1 - a) * plotH + topPad;
  };

  // Path
  let d = `M ${toX(xs[0])} ${toY(ys[0])}`;
  for (let i = 1; i < series.length; i++) d += ` L ${toX(xs[i])} ${toY(ys[i])}`;

  const last = series[series.length - 1].y;
  const first = series[0].y;
  const pct = ((last - first) / (first || 1)) * 100;

  return (
    <div className="chart-wrap" style={{ overflow: 'visible' }}>
      <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" style={{ width, height, overflow: 'visible' }} role="img" aria-label={`${label} time series with axes`}>
        {/* Target drawing area border (debug) */}
        {/* <rect x={pad.left} y={pad.top} width={plotW} height={plotH} fill="none" stroke="red" strokeWidth={0.5} /> */}
        {/* Y grid lines & ticks */}
        {yTicks.map((yv, i) => (
          <g key={`y-${i}`}> {/* horizontal grid */}
            <line x1={leftPad} x2={W - rightPad} y1={toY(yv)} y2={toY(yv)} stroke="currentColor" strokeOpacity={0.12} strokeWidth={0.8} />
            <text x={leftPad - 8} y={toY(yv)} textAnchor="end" dominantBaseline="middle" fontSize={11} fill="currentColor" fillOpacity={0.8}>{formatY(yv)}</text>
          </g>
        ))}
        {/* X axis line */}
        <line x1={leftPad} x2={W - rightPad} y1={H - bottomPad} y2={H - bottomPad} stroke="currentColor" strokeOpacity={0.3} strokeWidth={1} />
        {/* X ticks */}
        {xTicks.map((dt, i) => {
          const x = toX(dt.getTime());
          const y = H - bottomPad;
          return (
            <g key={`x-${i}`}> 
              <line x1={x} x2={x} y1={y} y2={y + 5} stroke="currentColor" strokeWidth={1} strokeOpacity={0.5} />
              {rotateX ? (
                <text transform={`translate(${x},${y + 7}) rotate(-30)`} fontSize={11} textAnchor="end" fill="currentColor" fillOpacity={0.75}>{formatX(dt)}</text>
              ) : (
                <text x={x} y={y + 9} textAnchor="middle" dominantBaseline="hanging" fontSize={11} fill="currentColor" fillOpacity={0.75}>{formatX(dt)}</text>
              )}
            </g>
          );
        })}
        {/* Y axis line */}
        <line x1={leftPad} x2={leftPad} y1={topPad} y2={H - bottomPad} stroke="currentColor" strokeOpacity={0.3} strokeWidth={1} />
        {/* Data path */}
        <path d={d} fill="none" stroke="currentColor" strokeWidth="2" className={pct >= 0 ? 'chart-line up' : 'chart-line down'} />
        <line x1={leftPad} x2={W - rightPad} y1={toY(first)} y2={toY(first)} className="chart-baseline" />
        {/* Axis labels */}
        <text transform={`translate(${leftPad - (maxYChars * charW + 20)},${H/2}) rotate(-90)`} fontSize={12} fill="currentColor" fillOpacity={0.75} textAnchor="middle">% {label}</text>
        <text x={W - rightPad} y={H - 4} fontSize={12} fill="currentColor" fillOpacity={0.75} textAnchor="end">Year</text>
      </svg>
      <div className="chart-meta" style={{ marginTop: 4 }}>
        <span className="sub">{label} change</span>
        <span className={`chart-pct ${pct >= 0 ? 'up' : 'down'}`}>{pct >= 0 ? '+' : ''}{pct.toFixed(2)}%</span>
      </div>
    </div>
  );
}
