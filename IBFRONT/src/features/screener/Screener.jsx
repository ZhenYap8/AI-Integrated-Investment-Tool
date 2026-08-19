import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import Card from '../../components/Card.jsx';
import Badge from '../../components/Badge.jsx';
import { fetchJSON, api } from '../../lib/api.js';
import ScreenerTable, { ScreenerDetail } from './ScreenerTable.jsx';
import GradeDistribution, { ScreenerSummaryStrip } from './ScreenerSummary.jsx';
import SectorTabs from './SectorTabs.jsx';
import {
  PRESETS,
  buildShortlistPool,
  computeGradeDistribution,
  computeSummary,
  filterItems,
  getSectorCounts,
  getSectors,
  isLikelyAlphabeticalSample,
  loadShortlist,
  pickDefaultSector,
  rankInSector,
  saveShortlist,
  toggleShortlist,
} from './screenerUtils.js';

const UNIVERSE_OPTIONS = [
  { id: 'sp500', label: 'S&P 500', defaultMax: 500 },
  { id: 'nasdaq100', label: 'NASDAQ 100', defaultMax: 101 },
  { id: 'nasdaq', label: 'NASDAQ listed', defaultMax: 200 },
];

const SIZE_CANDIDATES = [50, 100, 200, 500];

function sizeOptionsForUniverse(universeId) {
  const cap = UNIVERSE_OPTIONS.find((u) => u.id === universeId)?.defaultMax ?? 500;
  const sizes = SIZE_CANDIDATES.filter((s) => s <= cap);
  if (!sizes.includes(cap)) sizes.push(cap);
  return [...new Set(sizes)].sort((a, b) => a - b).map((s) => ({
    label: s === cap && cap < 500 ? `All (${s})` : `${s} stocks`,
    value: String(s),
  }));
}

const TOP_N = 10;
const PAGE_SIZE = 50;

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
  const [universe, setUniverse] = useState('sp500');
  const [maxTickers, setMaxTickers] = useState('100');
  const [selected, setSelected] = useState(null);

  const [showAll, setShowAll] = useState(false);
  const [gradeFilter, setGradeFilter] = useState('');
  const [search, setSearch] = useState('');
  const [sector, setSector] = useState('');
  const [preset, setPreset] = useState('');
  const [page, setPage] = useState(1);
  const [shortlist, setShortlist] = useState(() => loadShortlist());
  const configSynced = useRef(false);

  const loadedUniverse = status?.universe || 'sp500';
  const loadedMaxTickers = String(status?.maxTickers ?? '100');
  const settingsDirty = Boolean(
    status?.status === 'ready'
    && (universe !== loadedUniverse || maxTickers !== loadedMaxTickers),
  );

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
      const params = new URLSearchParams({ sort: 'score', limit: '500' });
      const data = await fetchJSON(api(`/api/screen?${params.toString()}`));
      setItems(data.items || []);
    } catch (err) {
      setError(err.message || 'Failed to load screening results');
    } finally {
      setLoading(false);
    }
  }, []);

  const pollWhileRunning = useCallback(async () => {
    const data = await loadStatus();
    await loadResults();
    if (data?.status === 'running') {
      setRefreshing(true);
      window.setTimeout(pollWhileRunning, 3000);
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
    if (status?.status === 'running') pollWhileRunning();
  }, [status?.status, pollWhileRunning]);

  useEffect(() => {
    if (!status || configSynced.current) return;
    if (status.universe) setUniverse(status.universe);
    if (status.maxTickers != null) setMaxTickers(String(status.maxTickers));
    configSynced.current = true;
  }, [status]);

  useEffect(() => {
    if (!items.length) return;
    const available = getSectors(items);
    if (!sector || !available.includes(sector)) {
      setSector(pickDefaultSector(items));
    }
  }, [items, sector]);

  const onUniverseChange = (nextUniverse) => {
    setUniverse(nextUniverse);
    const opt = UNIVERSE_OPTIONS.find((o) => o.id === nextUniverse);
    if (opt) {
      setMaxTickers((current) => {
        const n = Number(current);
        return String(Number.isFinite(n) ? Math.min(n, opt.defaultMax) : opt.defaultMax);
      });
    }
  };

  useEffect(() => {
    setPage(1);
  }, [showAll, gradeFilter, search, sector, preset, items.length]);

  const sectors = useMemo(() => getSectors(items), [items]);
  const sectorCounts = useMemo(() => getSectorCounts(items), [items]);
  const sizeOptions = useMemo(() => sizeOptionsForUniverse(universe), [universe]);

  const isShortlistView = preset === 'shortlist';

  const viewPool = useMemo(() => {
    if (isShortlistView) return buildShortlistPool(items, shortlist);
    if (!sector) return [];
    return rankInSector(items, sector);
  }, [items, sector, isShortlistView, shortlist]);

  const viewSummary = useMemo(() => computeSummary(viewPool), [viewPool]);
  const gradeDistribution = useMemo(() => computeGradeDistribution(viewPool), [viewPool]);

  const filtered = useMemo(() => filterItems(viewPool, {
    search,
    grade: gradeFilter,
    preset: isShortlistView ? '' : preset,
    shortlist: [],
    minMetrics: 0,
  }), [viewPool, search, gradeFilter, preset, isShortlistView]);

  const staleSample = useMemo(() => isLikelyAlphabeticalSample(items), [items]);

  const displayed = useMemo(() => {
    if (isShortlistView || search.trim() || showAll) return filtered;
    return filtered.slice(0, TOP_N);
  }, [filtered, showAll, search, isShortlistView]);

  const totalPages = Math.max(1, Math.ceil(displayed.length / PAGE_SIZE));

  useEffect(() => {
    if (!displayed.length) {
      setSelected(null);
      return;
    }
    setSelected((prev) => {
      if (prev && displayed.some((r) => r.ticker === prev.ticker)) return prev;
      return displayed[0];
    });
  }, [displayed]);

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
      const latest = await loadStatus();
      if (latest?.universe) setUniverse(latest.universe);
      if (latest?.maxTickers != null) setMaxTickers(String(latest.maxTickers));
    } catch (err) {
      setError(err.message || 'Refresh failed');
      setRefreshing(false);
    }
  };

  const onApplySettings = () => onRefresh();

  const onToggleShortlist = (ticker) => {
    setShortlist((prev) => {
      const next = toggleShortlist(prev, ticker);
      saveShortlist(next);
      return next;
    });
  };

  const clearFilters = () => {
    setGradeFilter('');
    setSearch('');
    setPreset('');
    setShowAll(false);
    if (items.length) setSector(pickDefaultSector(items));
  };

  const progressLabel = useMemo(() => {
    const scored = status?.stats?.scored;
    const total = status?.stats?.total;
    if (status?.status === 'running' && total) {
      return `Scoring ${scored ?? 0}/${total}…`;
    }
    return null;
  }, [status]);

  const hasActiveFilters = gradeFilter || search || preset || showAll;
  const activePreset = PRESETS.find((p) => p.id === preset);

  return (
    <div className="stack-lg">
      <Card>
        <div className="screen-hero">
          <div>
            <h1 className="title">Investment Screener</h1>
            <p className="lead">
              Compare companies within the same sector — not across the whole market. Pick a sector, review the top names, then drill into full analysis.
            </p>
          </div>
          <div className="screen-hero-actions">
            {settingsDirty && (
              <button type="button" className="btn-range" onClick={onApplySettings} disabled={refreshing}>
                {refreshing ? 'Applying…' : 'Apply settings'}
              </button>
            )}
            <button type="button" className="btn-secondary" onClick={onRefresh} disabled={refreshing}>
              {refreshing ? 'Updating…' : 'Update data'}
            </button>
          </div>
        </div>

        <div className="screen-status-row">
          <Badge tone={status?.status === 'ready' ? 'green' : status?.status === 'running' ? 'amber' : 'gray'}>
            {status?.status || 'idle'}
          </Badge>
          <span className="screen-status-text">
            Updated {formatUpdated(status?.updatedAt)}
            {status?.universeLabel ? ` · ${status.universeLabel}` : ''}
            {status?.maxTickers ? ` · ${status.maxTickers} stocks` : ''}
            {progressLabel ? ` · ${progressLabel}` : ''}
            {shortlist.length ? ` · ${shortlist.length} shortlisted` : ''}
          </span>
        </div>

        {sectors.length > 0 && !isShortlistView && (
          <SectorTabs
            sectors={sectors}
            counts={sectorCounts}
            active={sector}
            onSelect={(next) => {
              setSector(next);
              setPreset('');
            }}
          />
        )}

        {isShortlistView && (
          <p className="screen-preset-hint">Showing all shortlisted companies across sectors.</p>
        )}

        {viewSummary && (isShortlistView || sector) && (
          <>
            <ScreenerSummaryStrip
              summary={viewSummary}
              sectorLabel={isShortlistView ? 'Shortlist' : sector}
              filteredCount={filtered.length}
              showAll={showAll || isShortlistView}
              topN={TOP_N}
            />
            <GradeDistribution
              distribution={gradeDistribution}
              activeGrade={gradeFilter}
              onSelect={setGradeFilter}
            />
          </>
        )}

        <div className="screen-preset-row">
          {PRESETS.map((p) => (
            <button
              key={p.id || 'all'}
              type="button"
              className={`screen-preset-chip ${preset === p.id ? 'active' : ''}`}
              title={p.hint}
              onClick={() => setPreset(preset === p.id ? '' : p.id)}
            >
              {p.label}
              {p.id === 'shortlist' && shortlist.length ? ` (${shortlist.length})` : ''}
            </button>
          ))}
        </div>

        <div className="screen-filters">
          <label className="screen-search-label">
            Search {isShortlistView ? 'shortlist' : `in ${sector || 'sector'}`}
            <input
              type="search"
              placeholder="Ticker or company…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </label>
          <label>
            Universe
            <select value={universe} onChange={(e) => onUniverseChange(e.target.value)}>
              {UNIVERSE_OPTIONS.map((opt) => (
                <option key={opt.id} value={opt.id}>{opt.label}</option>
              ))}
            </select>
          </label>
          <label>
            Max stocks
            <select value={maxTickers} onChange={(e) => setMaxTickers(e.target.value)}>
              {sizeOptions.map((opt) => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </label>
        </div>

        {settingsDirty && (
          <p className="screen-settings-hint">
            Universe or max size changed — click <strong>Apply settings</strong> to rescore with the new list.
          </p>
        )}

        {activePreset?.hint && (
          <p className="screen-preset-hint">{activePreset.hint}</p>
        )}

        {status?.status === 'running' && !items.length && (
          <div className="screen-warning">
            Scoring stocks for the first time — results will appear in batches. Start with 100 stocks for faster loads.
          </div>
        )}

        {error && <div className="screen-error">{error}</div>}

        {staleSample && (
          <div className="screen-warning">
            This looks like an old alphabetical NASDAQ sample (mostly tickers starting with &quot;A&quot;).
            Select <strong>S&amp;P 500</strong>, set max stocks to <strong>100</strong>, then click <strong>Apply settings</strong>.
          </div>
        )}
      </Card>

      <div className="screen-layout">
        <Card className="screen-table-card">
          <div className="screen-table-header">
            <h3 className="section-title">
              {isShortlistView
                ? `${displayed.length} shortlisted compan${displayed.length === 1 ? 'y' : 'ies'} across sectors`
                : !sector
                  ? 'Select a sector to compare peers'
                  : search.trim()
                    ? `${displayed.length} result${displayed.length === 1 ? '' : 's'} for “${search.trim()}” in ${sector}`
                    : showAll
                      ? `${displayed.length} of ${filtered.length} in ${sector}`
                      : `Top ${Math.min(TOP_N, filtered.length)} in ${sector}`}
              {!isShortlistView && sector && !search.trim() && !showAll && filtered.length > TOP_N
                ? ` · ${filtered.length} rankable in sector`
                : ''}
            </h3>
            <div className="screen-table-header-actions">
              {hasActiveFilters && (
                <button type="button" className="btn-secondary" onClick={clearFilters}>
                  Clear filters
                </button>
              )}
              {!isShortlistView && filtered.length > TOP_N && (
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={() => setShowAll((v) => !v)}
                >
                  {showAll ? `Show top ${TOP_N}` : `Show all in sector (${filtered.length})`}
                </button>
              )}
            </div>
          </div>

          <ScreenerTable
            items={displayed}
            loading={loading || refreshing}
            selected={selected}
            onSelect={setSelected}
            shortlist={shortlist}
            onToggleShortlist={onToggleShortlist}
            page={page}
            pageSize={PAGE_SIZE}
            showPagination={Boolean(search.trim()) || (showAll && displayed.length > PAGE_SIZE) || (isShortlistView && displayed.length > PAGE_SIZE)}
            searchQuery={search.trim()}
            sectorLabel={isShortlistView ? 'shortlist' : sector}
            sectorSize={viewPool.length}
            shortlistMode={isShortlistView}
          />

          {(showAll || isShortlistView) && displayed.length > PAGE_SIZE && (
            <div className="screen-pagination">
              <button
                type="button"
                className="btn-secondary"
                disabled={page <= 1}
                onClick={() => setPage((p) => p - 1)}
              >
                Previous
              </button>
              <span className="screen-pagination-label">
                Page {page} of {totalPages}
              </span>
              <button
                type="button"
                className="btn-secondary"
                disabled={page >= totalPages}
                onClick={() => setPage((p) => p + 1)}
              >
                Next
              </button>
            </div>
          )}
        </Card>

        <Card className="screen-detail-card">
          <h3 className="section-title">Score breakdown</h3>
          <ScreenerDetail
            row={selected}
            starred={selected ? shortlist.includes(selected.ticker) : false}
            onToggleShortlist={onToggleShortlist}
          />
        </Card>
      </div>
    </div>
  );
}
