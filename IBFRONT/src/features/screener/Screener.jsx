import React, { useCallback, useEffect, useMemo, useState } from 'react';
import Card from '../../components/Card.jsx';
import Badge from '../../components/Badge.jsx';
import { fetchJSON, api } from '../../lib/api.js';
import ScreenerTable, { ScreenerDetail } from './ScreenerTable.jsx';

const MIN_SCORE_OPTIONS = [
  { label: 'All scores', value: '' },
  { label: '60+ (B or better)', value: '60' },
  { label: '80+ (A only)', value: '80' },
];

const UNIVERSE_OPTIONS = [
  { id: 'sp500', label: 'S&P 500', defaultMax: 500 },
  { id: 'nasdaq100', label: 'NASDAQ 100', defaultMax: 101 },
  { id: 'nasdaq', label: 'NASDAQ listed', defaultMax: 200 },
];

const SIZE_OPTIONS = [
  { label: '100 stocks', value: '100' },
  { label: '200 stocks', value: '200' },
  { label: '500 stocks', value: '500' },
];

function formatUpdated(value) {
  if (!value) return 'Never';
  try {
    return new Date(value).toLocaleString();
  } catch {
    return value;
  }
}

export default function Screener() {
  const [items, setItems] = useState([]);
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState('');
  const [minScore, setMinScore] = useState('');
  const [sort, setSort] = useState('score');
  const [universe, setUniverse] = useState('sp500');
  const [maxTickers, setMaxTickers] = useState('500');
  const [selected, setSelected] = useState(null);

  const loadStatus = useCallback(async () => {
    try {
      const data = await fetchJSON(api('/api/screen/status'));
      setStatus(data);
      return data;
    } catch (err) {
      setError(err.message || 'Failed to load pipeline status');
      return null;
    }
  }, []);

  const loadResults = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const params = new URLSearchParams({ sort, limit: '500' });
      if (minScore) params.set('min_score', minScore);
      const data = await fetchJSON(api(`/api/screen?${params.toString()}`));
      setItems(data.items || []);
      setSelected((prev) => {
        if (!data.items?.length) return null;
        if (prev && data.items.some((row) => row.ticker === prev.ticker)) return prev;
        return data.items[0];
      });
    } catch (err) {
      setError(err.message || 'Failed to load screening results');
    } finally {
      setLoading(false);
    }
  }, [minScore, sort]);

  const pollWhileRunning = useCallback(async () => {
    const data = await loadStatus();
    if (data?.status === 'running') {
      setRefreshing(true);
      window.setTimeout(pollWhileRunning, 4000);
      return;
    }
    setRefreshing(false);
    await loadResults();
  }, [loadResults, loadStatus]);

  useEffect(() => {
    loadStatus();
    loadResults();
  }, [loadResults, loadStatus]);

  useEffect(() => {
    if (status?.status === 'running') {
      pollWhileRunning();
    }
  }, [status?.status, pollWhileRunning]);

  useEffect(() => {
    if (!status) return;
    if (status.universe) setUniverse(status.universe);
    if (status.maxTickers) setMaxTickers(String(status.maxTickers));
  }, [status]);

  const onRefresh = async () => {
    setRefreshing(true);
    setError('');
    try {
      const params = new URLSearchParams({
        force: 'true',
        universe,
        max_tickers: maxTickers,
      });
      await fetchJSON(api(`/api/screen/refresh?${params.toString()}`), { method: 'POST' });
      await pollWhileRunning();
    } catch (err) {
      setError(err.message || 'Refresh failed');
      setRefreshing(false);
    }
  };

  const summary = useMemo(() => {
    if (!items.length) return null;
    const avg = items.reduce((sum, row) => sum + (row.compositeScore || 0), 0) / items.length;
    const aCount = items.filter((row) => row.grade === 'A').length;
    return { avg: avg.toFixed(1), aCount };
  }, [items]);

  return (
    <div className="stack-lg">
      <Card>
        <div className="screen-hero">
          <div>
            <h1 className="title">Investment Screener</h1>
            <p className="lead">
              Repeatable fundamentals feed from Yahoo Finance — screen S&amp;P 500, NASDAQ 100, or broader NASDAQ lists with interpretable quality scores.
            </p>
          </div>
          <div className="screen-hero-actions">
            <button type="button" className="btn-range" onClick={onRefresh} disabled={refreshing}>
              {refreshing ? 'Refreshing feed…' : 'Refresh pipeline'}
            </button>
          </div>
        </div>

        <div className="screen-status-row">
          <Badge tone={status?.status === 'ready' ? 'green' : status?.status === 'running' ? 'amber' : 'gray'}>
            {status?.status || 'idle'}
          </Badge>
          <span className="screen-status-text">
            Last updated {formatUpdated(status?.updatedAt)}
            {status?.universeLabel ? ` · ${status.universeLabel}` : ''}
            {status?.stats?.scored ? ` · ${status.stats.scored} companies scored` : ''}
            {status?.stale ? ' · cache stale, refresh queued' : ''}
          </span>
          {summary && (
            <span className="screen-status-text">
              · Avg score {summary.avg} · {summary.aCount} A-grade names
            </span>
          )}
        </div>

        <div className="screen-filters">
          <label>
            Universe
            <select value={universe} onChange={(e) => setUniverse(e.target.value)}>
              {UNIVERSE_OPTIONS.map((opt) => (
                <option key={opt.id} value={opt.id}>{opt.label}</option>
              ))}
            </select>
          </label>
          <label>
            Max stocks
            <select value={maxTickers} onChange={(e) => setMaxTickers(e.target.value)}>
              {SIZE_OPTIONS.map((opt) => (
                <option key={opt.label} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </label>
          <label>
            Min score
            <select value={minScore} onChange={(e) => setMinScore(e.target.value)}>
              {MIN_SCORE_OPTIONS.map((opt) => (
                <option key={opt.label} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </label>
          <label>
            Sort by
            <select value={sort} onChange={(e) => setSort(e.target.value)}>
              <option value="score">Composite score</option>
              <option value="ticker">Ticker</option>
            </select>
          </label>
        </div>

        {error && <div className="screen-error">{error}</div>}
      </Card>

      <div className="screen-layout">
        <Card className="screen-table-card">
          <h3 className="section-title">Ranked universe ({items.length} shown)</h3>
          <ScreenerTable items={items} loading={loading || refreshing} selected={selected} onSelect={setSelected} />
        </Card>
        <Card className="screen-detail-card">
          <h3 className="section-title">Score breakdown</h3>
          <ScreenerDetail row={selected} />
        </Card>
      </div>

      <Card>
        <h3 className="section-title">How scoring works</h3>
        <p className="text-sm" style={{ color: 'var(--muted)', marginBottom: 12 }}>
          Each stock earns up to 100 points across five fundamentals pulled from Yahoo Finance filings:
          revenue CAGR, operating margin, net debt/equity, interest coverage, and ROE. Full credit is awarded at the default threshold; partial credit applies when a metric is close. Grades: A ≥80, B ≥60, C ≥40, D ≥20.
        </p>
        <p className="text-sm" style={{ color: 'var(--muted)' }}>
          The pipeline refreshes automatically every 12 hours. Choose a universe and max size, then click Refresh pipeline — S&amp;P 500 at 500 stocks takes roughly 1–2 minutes.
        </p>
      </Card>
    </div>
  );
}
