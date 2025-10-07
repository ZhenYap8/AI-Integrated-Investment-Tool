// src/features/analyzer/Analyzer.jsx
import React, { useEffect, useMemo, useState } from "react";
import Card from "../../components/Card.jsx";
import KPI from "../../components/KPI.jsx";
import Scorecard from "../../components/Scorecard.jsx";
import Valuation from "../../components/Valuation.jsx";
import ValuationKPIs from "../../components/ValuationKPIs.jsx";
import Bullets from "../../components/Bullets.jsx";
import PriceChart from "../../components/PriceChart.jsx";
import SearchBar from "../../components/SearchBar.jsx";
import Badge from "../../components/Badge.jsx";
import NumField from "../../components/NumField.jsx";
import SkeletonCard from "../../components/SkeletonCard.jsx";
import EmptyState from "../../components/EmptyState.jsx";
import { api, fetchJSON } from "../../lib/api.js";

const YF_PRESETS = ["1y","3y","5y","10y","max"]; // ROE is annual; keep standard long-term presets

function periodLabel(p){ return (p || "").toUpperCase(); }
function yearsFromPeriod(p){
  if (!p) return undefined;
  const v = String(p).toLowerCase();
  if (v.endsWith('y') && !Number.isNaN(parseInt(v))) return parseInt(v);
  if (v === 'max') return undefined; // show full ROE history
  return undefined;
}

export default function Analyzer() {
  const [query, setQuery] = useState("");
  const [period, setPeriod] = useState('5y');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [resp, setResp] = useState(null);
  const [findings, setFindings] = useState(null);
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggest, setShowSuggest] = useState(false);
  const [thresh, setThresh] = useState({ rev_cagr_min: 5, op_margin_min: 10, nd_eq_max: 1.0, interest_cover_min: 4.0, roe_min: 10 });

  // Initialize period from URL (?period= or ?range=) or localStorage
  useEffect(() => {
    try {
      const usp = new URLSearchParams(window.location.search);
      const p = (usp.get('period') || usp.get('range') || '').toLowerCase();
      if (YF_PRESETS.includes(p)) {
        setPeriod(p);
        return;
      }
      const saved = localStorage.getItem('agent-period');
      if (saved && YF_PRESETS.includes(saved)) setPeriod(saved);
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

  // Fetch suggestions as user types
  useEffect(() => {
    let stop = false;
    const q = query.trim();
    if (!q) { setSuggestions([]); return; }
    (async () => {
      try {
        const items = await fetchJSON(api(`/api/suggest?q=${encodeURIComponent(q)}`));
        if (!stop) setSuggestions(items || []);
      } catch { if (!stop) setSuggestions([]); }
    })();
    return () => { stop = true; };
  }, [query]);

  const runAnalyze = async (qVal) => {
    const val = (qVal ?? query).trim();
    if (!val) return;
    setLoading(true); setError(""); setResp(null); setFindings(null); setShowSuggest(false);
    try {
      const params = new URLSearchParams({ query: val });
      if (period) params.set('period', period);
      const yMap = yearsFromPeriod(period);
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
      const data = await fetchJSON(api(`/api/analyze?${params.toString()}`));
      setResp(data || null);

      // Pros/Cons findings (ticker-only). Non-blocking.
      if (data?.meta?.queryType === 'company' && data?.meta?.ticker) {
        try {
          const yrs = yearsFromPeriod(period);
          const f = await fetchJSON(api('/api/proscons/analyze'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ticker: data.meta.ticker, max: 8, period, years: yrs })
          });
          setFindings(f?.findings || []);
        } catch {}
      }
    } catch (e) {
      setError(typeof e?.message === 'string' ? e.message : String(e));
    } finally {
      setLoading(false);
    }
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

  const prosEnriched = useMemo(() => {
    if (!Array.isArray(findings) || findings.length === 0) return null;
    return findings
      .filter(f => f?.direction === 'pro')
      .map(f => ({ text: f.item, source: f?.evidence?.[0]?.url, snippet: f?.evidence?.[0]?.snippet }))
  }, [findings]);

  const consEnriched = useMemo(() => {
    if (!Array.isArray(findings) || findings.length === 0) return null;
    return findings
      .filter(f => f?.direction === 'con')
      .map(f => ({ text: f.item, source: f?.evidence?.[0]?.url, snippet: f?.evidence?.[0]?.snippet }))
  }, [findings]);

  return (
    <div className="stack-lg">
      <Card>
        <h2 className="section-title">Analyse Companies or Industries</h2>
        <SearchBar
          value={query}
          onChange={setQuery}
          onSubmit={() => runAnalyze()}
          suggestions={suggestions}
          showSuggest={showSuggest}
          setShowSuggest={setShowSuggest}
          loading={loading}
          onPickSuggestion={onPickSuggestion}
        />
        <div className="segmented" style={{ marginTop: 8 }}>
          {YF_PRESETS.map(p => (
            <button
              key={p}
              className={`btn-range ${period === p ? 'active' : ''}`}
              aria-pressed={period === p}
              onClick={() => setPeriod(p)}
              disabled={loading}
            >{periodLabel(p)}</button>
          ))}
          <button className="btn-range" onClick={() => runAnalyze()} disabled={loading || !query}>Run</button>
        </div>
      </Card>

      <Card>
        <h3 className="section-title">Thresholds</h3>
        <p className="text-sm text-slate-500 mb-4">
          Configure thresholds that will be used for scorecard evaluation.
        </p>
        <div className="thresh-grid">
          <NumField label="Revenue CAGR min" value={thresh.rev_cagr_min} onChange={(v)=>setThresh(t=>({...t, rev_cagr_min:v}))} suffix="%" hint="1-10y" />
          <NumField label="Operating margin min" value={thresh.op_margin_min} onChange={(v)=>setThresh(t=>({...t, op_margin_min:v}))} suffix="%" />
          <NumField label="Net debt / Equity max" value={thresh.nd_eq_max} onChange={(v)=>setThresh(t=>({...t, nd_eq_max:v}))} suffix="x" />
          <NumField label="Interest coverage min" value={thresh.interest_cover_min} onChange={(v)=>setThresh(t=>({...t, interest_cover_min:v}))} suffix="x" />
          <NumField label="ROE min" value={thresh.roe_min} onChange={(v)=>setThresh(t=>({...t, roe_min:v}))} suffix="%" />
        </div>
        <div className="thresh-actions">
          <button className="btn-range" onClick={()=>runAnalyze()} disabled={loading || !query}>Apply Thresholds</button>
        </div>
      </Card>

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

      {!loading && !resp && <EmptyState title="No analysis yet" text="Search for a ticker (e.g., NVDA) or an industry (e.g., Robotics) and hit Run." />}

      {resp && (
        <>
          {/* Move ROE trend to the top of results, just below the year presets */}
          <Card>
            <h3 className="section-title">Return on Equity (ROE) Chart</h3>
            <PriceChart series={series} height={300} />
          </Card>

          <Card>
            <div className="kpis">
              <KPI label="Type" value={resp?.meta?.queryType} />
              <KPI label="As of" value={resp?.meta?.asOf} />
            </div>
            <ValuationKPIs valuation={resp?.valuation} />
          </Card>

          <hr style={{ margin: '12px 0', borderColor: 'var(--border)' }} />

          <Card>
            <h2 className="section-title" style={{ marginBottom: 8 }}>Scorecard</h2>
            <Scorecard
              scorecard={resp?.scorecard || null}
              loading={loading}
              years={yearsFromPeriod(period) || 5}
            />
          </Card>

          <hr style={{ margin: '12px 0', borderColor: 'var(--border)' }} />

          <Card>
            <h2 className="section-title" style={{ marginBottom: 8 }}>Valuation</h2>
            <Valuation 
              valuation={resp?.valuation} 
              ticker={resp?.meta?.ticker}
            />
          </Card>

          <Card>
            <h2 className="section-title" style={{ marginBottom: 8 }}>AI Analysis</h2>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div>
                <Bullets
                  title="Pros"
                  items={prosEnriched || (resp?.findings || []).filter(f => f?.direction === 'pro').map(f => f?.item) || resp?.pros}
                  tone="green"
                />
              </div>
              <div>
                <Bullets
                  title="Cons"
                  items={consEnriched || (resp?.findings || []).filter(f => f?.direction === 'con').map(f => f?.item) || resp?.cons}
                  tone="red"
                />
              </div>
            </div>
          </Card>

          {resp?.sources?.length > 0 && (
            <Card id="sources">
              <h3 className="section-title">Sources</h3>
              <ul>
                {resp.sources.map((s, i) => (
                  <li key={i}><a href={s.url} target="_blank" rel="noreferrer">{s.title || s.url}</a></li>
                ))}
              </ul>
            </Card>
          )}
        </>
      )}
    </div>
  );
}
