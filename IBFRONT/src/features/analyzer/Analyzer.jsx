// src/features/analyzer/Analyzer.jsx
import React, { useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { api, fetchJSON } from "../../lib/api.js";

import Card from "../../components/Card.jsx";
import SkeletonCard from "../../components/SkeletonCard.jsx";
import EmptyState from "../../components/EmptyState.jsx";
import { fuzzyFilter } from "../FuzzySearchFixing";
import AnalyzerResults from "./AnalyzerResults";
import PreAnalyzer from "./PreAnalyzer";
import {
  loadAnalyzerSession,
  saveAnalyzerSession,
  sessionMatches,
} from "./analyzerSession.js";

const HISTORY_PRESETS = ["6m", "1y", "3y", "5y", "10y", "max"];
const DEFAULT_THRESH = { rev_cagr_min: 5, op_margin_min: 10, nd_eq_max: 1.0, interest_cover_min: 4.0, roe_min: 10 };

function readInitialSession() {
  return loadAnalyzerSession() || {};
}

function yearsFromPeriod(p) {
  if (!p) return 5;
  const v = String(p).toLowerCase();
  if (v === "max" || v === "6m") return undefined;
  if (v.endsWith("y") && !Number.isNaN(parseInt(v))) return parseInt(v);
  return 5;
}

function historyLabel(p) {
  const v = String(p || "5y").toLowerCase();
  if (v === "max") return "All available";
  if (v === "6m") return "6 months (quarterly ROE)";
  if (v === "1y") return "1 year (quarterly ROE)";
  return v.toUpperCase();
}

function initialPeriod(searchParams) {
  const fromUrl = (searchParams.get('period') || searchParams.get('range') || '').toLowerCase();
  if (HISTORY_PRESETS.includes(fromUrl)) return fromUrl;
  const saved = readInitialSession();
  if (saved.period && HISTORY_PRESETS.includes(saved.period)) return saved.period;
  try {
    const stored = localStorage.getItem('agent-period');
    if (stored && HISTORY_PRESETS.includes(stored)) return stored;
  } catch {}
  return '5y';
}

export default function Analyzer() {
  const [searchParams, setSearchParams] = useSearchParams();
  const boot = useMemo(() => readInitialSession(), []);

  const [query, setQuery] = useState(() => boot.query || searchParams.get('query') || '');
  const [period, setPeriod] = useState(() => initialPeriod(searchParams));
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [resp, setResp] = useState(() => boot.resp || null);
  const [findings, setFindings] = useState(() => boot.findings || null);
  const [headlines, setHeadlines] = useState(() => boot.headlines || []);
  const [insightMode, setInsightMode] = useState(() => boot.insightMode || '');
  const [aiLoading, setAiLoading] = useState(false);
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggest, setShowSuggest] = useState(false);
  const [allTickers, setAllTickers] = useState(null);
  const [thresh, setThresh] = useState(() => boot.thresh || DEFAULT_THRESH);

  const lastAutoQuery = useRef(
    boot.resp && boot.query ? boot.query : '',
  );
  const analyzeRequestId = useRef(0);
  const hydrated = useRef(false);

  const urlQuery = searchParams.get('query') || '';

  // Restore URL from session when returning without ?query=
  useEffect(() => {
    if (hydrated.current) return;
    hydrated.current = true;
    if (!urlQuery && boot.query && boot.resp) {
      setSearchParams((prev) => {
        const next = new URLSearchParams(prev);
        next.set('query', boot.query);
        if (boot.period) next.set('period', boot.period);
        const yMap = yearsFromPeriod(boot.period || period);
        if (yMap) next.set('years', String(yMap));
        return next;
      }, { replace: true });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Persist period to URL and localStorage
  useEffect(() => {
    try {
      localStorage.setItem('agent-period', period);
      setSearchParams((prev) => {
        const next = new URLSearchParams(prev);
        next.set('period', period);
        const yMap = yearsFromPeriod(period);
        if (yMap) next.set('years', String(yMap));
        else next.delete('years');
        if (next.toString() === prev.toString()) return prev;
        return next;
      }, { replace: true });
    } catch {}
  }, [period, setSearchParams]);

  // Save session whenever analysis state changes
  useEffect(() => {
    if (!resp && !query.trim()) return;
    saveAnalyzerSession({
      query,
      period,
      resp,
      findings,
      headlines,
      insightMode,
      thresh,
    });
  }, [query, period, resp, findings, headlines, insightMode, thresh]);

  useEffect(() => {
    let stop = false;
    (async () => {
      try {
        const list = await fetchJSON(api('/api/tickers?max_count=5000'));
        if (!stop) setAllTickers(Array.isArray(list) ? list : []);
      } catch {
        if (!stop) setAllTickers(null);
      }
    })();
    return () => { stop = true; };
  }, []);

  useEffect(() => {
    let stopped = false;
    const q = query.trim();
    if (!q) { setSuggestions([]); return; }

    const handler = setTimeout(async () => {
      if (stopped) return;
      if (Array.isArray(allTickers) && allTickers.length > 0) {
        try {
          const items = fuzzyFilter(allTickers, q, { limit: 50 });
          if (!stopped) setSuggestions(items || []);
          return;
        } catch {
          if (!stopped) setSuggestions([]);
          return;
        }
      }
      try {
        const items = await fetchJSON(api(`/api/suggest?q=${encodeURIComponent(q)}`));
        if (!stopped) setSuggestions(items || []);
      } catch {
        if (!stopped) setSuggestions([]);
      }
    }, 250);

    return () => { stopped = true; clearTimeout(handler); };
  }, [query, allTickers]);

  const runAnalyze = async (qVal, periodOverride) => {
    const val = (qVal ?? query).trim();
    if (!val) return;
    const activePeriod = periodOverride ?? period;
    const requestId = ++analyzeRequestId.current;
    setQuery(val);
    lastAutoQuery.current = val;
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      next.set('query', val);
      return next;
    }, { replace: true });
    setLoading(true);
    setError('');
    setResp(null);
    setFindings(null);
    setHeadlines([]);
    setInsightMode('');
    setAiLoading(false);
    setShowSuggest(false);
    try {
      const params = new URLSearchParams({ query: val });
      if (activePeriod) params.set('period', activePeriod);
      const yMap = yearsFromPeriod(activePeriod);
      if (yMap) params.set('years', String(yMap));
      const toNum = (x) => (x === "" || x === null || x === undefined ? undefined : Number(x));
      const o = {
        rev_cagr_min: toNum(thresh.rev_cagr_min) / 100,
        op_margin_min: toNum(thresh.op_margin_min) / 100,
        nd_eq_max: toNum(thresh.nd_eq_max),
        interest_cover_min: toNum(thresh.interest_cover_min),
        roe_min: toNum(thresh.roe_min) / 100,
      };
      Object.entries(o).forEach(([k, v]) => { if (v !== undefined && !Number.isNaN(v)) params.set(k, String(v)); });
      const data = await fetchJSON(api(`/api/analyze?${params.toString()}`));
      if (requestId !== analyzeRequestId.current) return;

      setResp(data || null);

      if (data?.meta?.queryType === 'company' && data?.meta?.ticker) {
        setAiLoading(true);
        try {
          const yrs = yearsFromPeriod(activePeriod);
          const f = await fetchJSON(api('/api/proscons/analyze'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ticker: data.meta.ticker, max: 8, period: activePeriod, years: yrs }),
          });
          if (requestId !== analyzeRequestId.current) return;
          setFindings(f?.findings || []);
          setHeadlines(f?.headlines || []);
          setInsightMode(f?.mode || '');
        } catch {} finally {
          if (requestId === analyzeRequestId.current) setAiLoading(false);
        }
      }
    } catch (e) {
      if (requestId !== analyzeRequestId.current) return;
      setError(typeof e?.message === 'string' ? e.message : String(e));
    } finally {
      if (requestId === analyzeRequestId.current) setLoading(false);
    }
  };

  const onPeriodChange = (p) => {
    setPeriod(p);
    const q = query.trim() || resp?.meta?.ticker || urlQuery.trim();
    if (q) runAnalyze(q, p);
  };

  const onPickSuggestion = (s) => {
    const val = s?.value || s?.label || "";
    setQuery(val);
    runAnalyze(val);
  };

  // Auto-run only for new ?query= links — not when restoring a saved session
  useEffect(() => {
    const q = urlQuery.trim();
    if (!q) return;

    const cached = loadAnalyzerSession();
    if (sessionMatches(cached, q, period)) {
      lastAutoQuery.current = q;
      if (!resp) {
        setQuery(cached.query || q);
        setResp(cached.resp);
        setFindings(cached.findings || null);
        setHeadlines(cached.headlines || []);
        setInsightMode(cached.insightMode || '');
        if (cached.thresh) setThresh(cached.thresh);
        if (cached.period) setPeriod(cached.period);
      }
      return;
    }

    if (q === lastAutoQuery.current) return;
    lastAutoQuery.current = q;
    setQuery(q);
    runAnalyze(q);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [urlQuery]);

  const series = useMemo(() => {
    if (!resp?.prices) return [];
    return resp.prices
      .map(p => ({ t: new Date(p.date || p._ts || Date.now()), y: typeof p.y === 'number' ? p.y : (typeof p.roe === 'number' ? p.roe : null) }))
      .filter(p => p.y !== null);
  }, [resp]);

  return (
    <div className="stack-lg">
      <PreAnalyzer
        query={query}
        setQuery={setQuery}
        runAnalyze={runAnalyze}
        suggestions={suggestions}
        showSuggest={showSuggest}
        setShowSuggest={setShowSuggest}
        loading={loading}
        onPickSuggestion={onPickSuggestion}
        period={period}
        onPeriodChange={onPeriodChange}
        HISTORY_PRESETS={HISTORY_PRESETS}
        thresholds={thresh}
        setThresholds={setThresh}
        onApply={() => runAnalyze()}
        onReset={() => setThresh(DEFAULT_THRESH)}
      />

      {error && (
        <Card className="border-red-300">
          <div className="text-red-700">{error}</div>
        </Card>
      )}

      {loading && (
        <>
          <SkeletonCard />
          <SkeletonCard />
        </>
      )}

      {!loading && !resp && (
        <EmptyState
          title="No analysis yet"
          text="Search for a ticker (e.g., NVDA, BP.L, SHOP.TO) or an industry (e.g., Robotics) and hit Run."
        />
      )}

      {resp && !loading && (
        <AnalyzerResults
          resp={resp}
          series={series}
          findings={findings || []}
          headlines={headlines}
          insightMode={insightMode}
          loading={loading}
          aiLoading={aiLoading}
          period={period}
          years={yearsFromPeriod(period) || 5}
          historyLabel={historyLabel(period)}
        />
      )}
    </div>
  );
}
