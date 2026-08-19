const GRADES = ['A', 'B', 'C', 'D', 'F'];

export const PRESETS = [
  { id: '', label: 'All companies' },
  { id: 'quality', label: 'Quality compounders', hint: 'Score ≥80, ROE & margin pass' },
  { id: 'growth', label: 'Growth + quality', hint: 'Score ≥60, revenue CAGR pass' },
  { id: 'safety', label: 'Balance sheet safety', hint: 'Low leverage & strong coverage' },
  { id: 'turnaround', label: 'Turnaround watch', hint: 'Score 40–60, 2+ weak metrics' },
  { id: 'shortlist', label: 'My shortlist', hint: 'Starred names only' },
];

export function metricPass(row, metricId) {
  return (row.breakdown || []).some((b) => b.id === metricId && b.verdict === 'green');
}

export function matchesPreset(row, presetId) {
  if (!presetId || presetId === 'shortlist') return true;
  const score = row.compositeScore || 0;
  const fails = (row.totalMetrics || 0) - (row.greens || 0);

  switch (presetId) {
    case 'quality':
      return score >= 80 && metricPass(row, 'roe') && metricPass(row, 'op_margin');
    case 'growth':
      return score >= 60 && metricPass(row, 'rev_cagr');
    case 'safety':
      return metricPass(row, 'nd_eq') && metricPass(row, 'interest_cover');
    case 'turnaround':
      return score >= 40 && score < 60 && fails >= 2;
    default:
      return true;
  }
}

export function getSectors(items) {
  const sectors = new Set();
  for (const row of items) {
    if (row.sector) sectors.add(row.sector);
  }
  return Array.from(sectors).sort();
}

export function computeGradeDistribution(items) {
  const counts = Object.fromEntries(GRADES.map((g) => [g, 0]));
  for (const row of items) {
    const g = row.grade || 'F';
    if (counts[g] != null) counts[g] += 1;
  }
  return GRADES.map((grade) => ({
    grade,
    count: counts[grade],
    pct: items.length ? Math.round((counts[grade] / items.length) * 100) : 0,
  }));
}

export function computeSummary(items) {
  if (!items.length) return null;
  const scores = items.map((r) => r.compositeScore || 0).sort((a, b) => a - b);
  const mid = Math.floor(scores.length / 2);
  const median = scores.length % 2
    ? scores[mid]
    : (scores[mid - 1] + scores[mid]) / 2;
  const avg = scores.reduce((s, v) => s + v, 0) / scores.length;
  const aCount = items.filter((r) => r.grade === 'A').length;
  return {
    total: items.length,
    avg: avg.toFixed(1),
    median: median.toFixed(1),
    aCount,
    aPct: Math.round((aCount / items.length) * 100),
  };
}

export function filterItems(items, filters) {
  const {
    search = '',
    sector = '',
    grade = '',
    preset = '',
    shortlist = [],
    shortlistOnly = false,
  } = filters;

  const q = search.trim().toLowerCase();
  const shortSet = new Set(shortlist);

  return items.filter((row) => {
    if (shortlistOnly || preset === 'shortlist') {
      if (!shortSet.has(row.ticker)) return false;
    }
    if (grade && row.grade !== grade) return false;
    if (sector && row.sector !== sector) return false;
    if (preset && preset !== 'shortlist' && !matchesPreset(row, preset)) return false;
    if (q) {
      const hay = `${row.ticker} ${row.companyName} ${row.sector || ''}`.toLowerCase();
      if (!hay.includes(q)) return false;
    }
    return true;
  });
}

export function loadShortlist() {
  try {
    const raw = localStorage.getItem('screener-shortlist');
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

export function saveShortlist(tickers) {
  localStorage.setItem('screener-shortlist', JSON.stringify(tickers));
}

export function toggleShortlist(tickers, ticker) {
  const set = new Set(tickers);
  if (set.has(ticker)) set.delete(ticker);
  else set.add(ticker);
  return Array.from(set);
}
