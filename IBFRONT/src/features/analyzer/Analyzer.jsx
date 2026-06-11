// src/features/analyzer/Analyzer.jsx
import React, { useEffect, useMemo, useState } from "react";
import { api, fetchJSON } from "../../lib/api.js";

// importing necessary components
import Card from "../../components/Card.jsx";
import SearchBar from "../../components/SearchBar.jsx";
import NumField from "../../components/NumField.jsx";
import SkeletonCard from "../../components/SkeletonCard.jsx";
import EmptyState from "../../components/EmptyState.jsx";
// cleaning the search system
import useFuzzySearch, { fuzzyFilter } from "../FuzzySearchFixing";
// calling analyzer results for the AI analysis display
import AnalyzerResults from "./AnalyzerResults";
import PreAnalyzer from "./PreAnalyzer";

const HISTORY_PRESETS = ["6m", "1y", "3y", "5y", "10y", "max"];

// default thresholds shared by the UI
const DEFAULT_THRESH = { rev_cagr_min: 5, op_margin_min: 10, nd_eq_max: 1.0, interest_cover_min: 4.0, roe_min: 10 };

function periodLabel(p) {
  if (p === "max") return "All";
  return (p || "").toUpperCase();
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

export default function Analyzer() {
  const [query, setQuery] = useState("");
  const [period, setPeriod] = useState('5y');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [resp, setResp] = useState(null);
  const [findings, setFindings] = useState(null);
  const [headlines, setHeadlines] = useState([]);
  const [insightMode, setInsightMode] = useState("");
  const [aiLoading, setAiLoading] = useState(false);
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggest, setShowSuggest] = useState(false);
  const [allTickers, setAllTickers] = useState(null); // full list (optional client-side fuzzy)
  const [thresh, setThresh] = useState(DEFAULT_THRESH);

  // Initialize period from URL (?period= or ?range=) or localStorage
  useEffect(() => {
    try {
      const usp = new URLSearchParams(window.location.search);
      const p = (usp.get('period') || usp.get('range') || '').toLowerCase();
      if (HISTORY_PRESETS.includes(p)) {
        setPeriod(p);
        return;
      }
      const saved = localStorage.getItem('agent-period');
      if (saved && HISTORY_PRESETS.includes(saved)) setPeriod(saved);
    } catch {}
  }, []);

  // Persist period to URL and localStorage
  useEffect(() => {
    try {
      localStorage.setItem('agent-period', period);
      const usp = new URLSearchParams(window.location.search);
      usp.set('period', period);
      const yMap = yearsFromPeriod(period);
      if (yMap) usp.set('years', String(yMap)); else usp.delete('years');
      const newUrl = `${window.location.pathname}?${usp.toString()}${window.location.hash}`;
      window.history.replaceState({}, '', newUrl);
    } catch {}
  }, [period]);

  // Load full ticker list once (optional): used for client-side fuzzy filtering if available
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

  // Fetch suggestions as user types (debounced). If we have the full ticker list, use client-side fuzzyFilter; otherwise fallback to server suggest.
  useEffect(() => {
    let stopped = false;
    const q = query.trim();
    if (!q) { setSuggestions([]); return; }

    const handler = setTimeout(async () => {
      if (stopped) return;
      // client-side fuzzy if we have the full list
      if (Array.isArray(allTickers) && allTickers.length > 0) {
        try {
          const items = fuzzyFilter(allTickers, q, { limit: 50 });
          if (!stopped) setSuggestions(items || []);
          return;
        } catch (e) {
          if (!stopped) setSuggestions([]);
          return;
        }
      }

      // fallback to server suggest
      try {
        const items = await fetchJSON(api(`/api/suggest?q=${encodeURIComponent(q)}`));
        if (!stopped) setSuggestions(items || []);
      } catch {
        if (!stopped) setSuggestions([]);
      }
    }, 250);

    return () => { stopped = true; clearTimeout(handler); };
  }, [query, allTickers]);


  // RUN ANALYSIS //

  const runAnalyze = async (qVal, periodOverride) => {
    const val = (qVal ?? query).trim();
    if (!val) return;
    const activePeriod = periodOverride ?? period;
    setLoading(true); setError(""); setResp(null); setFindings(null); setHeadlines([]); setInsightMode(""); setAiLoading(false); setShowSuggest(false);
    try {
      const params = new URLSearchParams({ query: val });
      if (activePeriod) params.set('period', activePeriod);
      const yMap = yearsFromPeriod(activePeriod);
      if (yMap) params.set('years', String(yMap));
      // Only send overrides if present
      const toNum = (x) => (x === "" || x === null || x === undefined ? undefined : Number(x));
      const o = {
        rev_cagr_min: toNum(thresh.rev_cagr_min) / 100,
        op_margin_min: toNum(thresh.op_margin_min) / 100,
        nd_eq_max: toNum(thresh.nd_eq_max),
        interest_cover_min: toNum(thresh.interest_cover_min),
        roe_min: toNum(thresh.roe_min) / 100,
      };
      Object.entries(o).forEach(([k,v]) => { if (v !== undefined && !Number.isNaN(v)) params.set(k, String(v)); });
      // Debug: log request params so we can inspect the exact API call
      try { console.debug('[runAnalyze] request ->', `/api/analyze?${params.toString()}`); } catch(e){}
      const data = await fetchJSON(api(`/api/analyze?${params.toString()}`));
      // Debug: log raw response for troubleshooting
      try { console.debug('[runAnalyze] response ->', data); } catch(e){}
      setResp(data || null);

      // Pros/Cons findings (ticker-only). Non-blocking.
      if (data?.meta?.queryType === 'company' && data?.meta?.ticker) {
        setAiLoading(true);
        try {
          const yrs = yearsFromPeriod(activePeriod);
          const f = await fetchJSON(api('/api/proscons/analyze'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ticker: data.meta.ticker, max: 8, period: activePeriod, years: yrs })
          });
          setFindings(f?.findings || []);
          setHeadlines(f?.headlines || []);
          setInsightMode(f?.mode || "");
        } catch {} finally {
          setAiLoading(false);
        }
      }
    } catch (e) {
      // Log error to console to help track frontend failures
      try { console.error('[runAnalyze] error', e); } catch (ee) {}
      setError(typeof e?.message === 'string' ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  };

  const onPeriodChange = (p) => {
    setPeriod(p);
    if (query.trim()) runAnalyze(query.trim(), p);
  };

  const onPickSuggestion = (s) => {
    const val = s?.value || s?.label || "";
    setQuery(val);
    runAnalyze(val);
  };

  const series = useMemo(() => {
    if (!resp?.prices) return [];
    return resp.prices
      .map(p => ({ t: new Date(p.date || p._ts || Date.now()), y: typeof p.y === 'number' ? p.y : (typeof p.roe === 'number' ? p.roe : null) }))
      .filter(p => p.y !== null);
  }, [resp]);

  const valuationRows = resp?.valuation?.table || [];

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

      {!loading && !resp && <EmptyState title="No analysis yet" text="Search for a ticker (e.g., NVDA, BP.L, SHOP.TO) or an industry (e.g., Robotics) and hit Run." />}

      {resp && (
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
