import React from 'react';

const GRADE_TONES = {
  A: 'grade-a',
  B: 'grade-b',
  C: 'grade-c',
  D: 'grade-d',
  F: 'grade-f',
};

export default function GradeDistribution({ distribution = [], activeGrade = '', onSelect }) {
  const max = Math.max(...distribution.map((d) => d.count), 1);

  return (
    <div className="grade-dist">
      <div className="grade-dist-bars">
        {distribution.map(({ grade, count, pct }) => {
          const active = activeGrade === grade;
          return (
            <button
              key={grade}
              type="button"
              className={`grade-dist-item ${GRADE_TONES[grade] || ''} ${active ? 'active' : ''}`}
              onClick={() => onSelect?.(active ? '' : grade)}
              title={`Filter ${grade}-grade stocks`}
            >
              <span className="grade-dist-label">{grade}</span>
              <div className="grade-dist-bar-track">
                <div
                  className="grade-dist-bar-fill"
                  style={{ height: `${Math.max(8, (count / max) * 100)}%` }}
                />
              </div>
              <span className="grade-dist-count">{count}</span>
              <span className="grade-dist-pct">{pct}%</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}

export function ScreenerSummaryStrip({ summary, sectorLabel, filteredCount, showAll, topN }) {
  if (!summary) return null;

  return (
    <div className="screen-summary-strip">
      <div className="screen-summary-stat">
        <span className="screen-summary-value">{summary.total}</span>
        <span className="screen-summary-label">{sectorLabel || 'Sector'} · companies</span>
      </div>
      <div className="screen-summary-stat">
        <span className="screen-summary-value">{summary.aCount}</span>
        <span className="screen-summary-label">A-grade in sector ({summary.aPct}%)</span>
      </div>
      <div className="screen-summary-stat">
        <span className="screen-summary-value">{summary.median}</span>
        <span className="screen-summary-label">Sector median score</span>
      </div>
      <div className="screen-summary-stat">
        <span className="screen-summary-value">{summary.avg}</span>
        <span className="screen-summary-label">Sector average</span>
      </div>
      <div className="screen-summary-stat">
        <span className="screen-summary-value">{filteredCount}</span>
        <span className="screen-summary-label">
          {showAll ? 'In this sector' : `Top ${topN} in sector`}
        </span>
      </div>
    </div>
  );
}
