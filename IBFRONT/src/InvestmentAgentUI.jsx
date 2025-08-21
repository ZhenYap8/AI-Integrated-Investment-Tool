import React, { useEffect, useRef, useState } from "react";
import { BrowserRouter, Routes, Route, Link, NavLink, useLocation } from "react-router-dom";
import "./styles.css"; // Import the new CSS file

const API_BASE = (import.meta?.env?.VITE_API_URL || "").replace(/\/$/, "");
const api = (path) => `${API_BASE}${path}`;

export default function App() {
  return (
    <BrowserRouter>
      <SiteChrome>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/analyze" element={<AnalyzePage />} />
          <Route path="/about" element={<About />} />
          <Route path="/docs" element={<Docs />} />
          <Route path="/disclaimer" element={<Disclaimer />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </SiteChrome>
    </BrowserRouter>
  );
}



function SiteChrome({ children }) {
  const [dark, setDark] = useDarkMode();
  const location = useLocation();
  usePageTitle(location);

  return (
    <div className={dark ? "dark-mode" : ""}>
      <div className="layout">
        <nav className="navbar">
          <div className="navbar-content">
            <div className="navbar-left">
              <Logo />
              <Link to="/" className="brand">Sudut Invest</Link>
            </div>
            <div className="navbar-right">
              <Nav to="/analyze">Analyze</Nav>
              <Nav to="/docs">Docs</Nav>
              <Nav to="/about">About</Nav>
              <Nav to="/disclaimer">Disclaimer</Nav>
              <button onClick={() => setDark(!dark)} className="toggle-theme">
                {dark ? "Light" : "Dark"}
              </button>
            </div>
          </div>
        </nav>

        <main className="main-content">{children}</main>

        <footer className="footer">
          <div className="footer-content">
            <span>© {new Date().getFullYear()} Sudut Invest</span>
            <div className="footer-links">
              <Link to="/disclaimer">Not investment advice</Link>
              <a href="#sources">Sources</a>
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
}

function Nav({ to, children }) {
  return (
    <NavLink to={to} className={({ isActive }) => (isActive ? "nav-link active" : "nav-link")}>
      {children}
    </NavLink>
  );
}

function useDarkMode() {
  const [dark, setDark] = useState(() => window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches);
  useEffect(() => {
    document.documentElement.classList.toggle("dark-mode", dark);
  }, [dark]);
  return [dark, setDark];
}

function usePageTitle(location) {
  useEffect(() => {
    const map = {
      "/": "Sudut Invest",
      "/analyze": "Analyze • Sudut Invest",
      "/about": "About •  Sudut Invest",
      "/docs": "Docs • Sudut Invest",
      "/disclaimer": "Disclaimer • Sudut Invest",
    };
    document.title = map[location.pathname] || "Sudut Invest";
  }, [location]);
}

// ---------------- Pages ---------------- //
function Home() {
  return (
    <div>
      <section className="py-8">
        <h1 className="text-3xl md:text-4xl font-semibold tracking-tight">Robotics & Tech Stock Agent</h1>
        <p className="mt-3 text-slate-600 dark:text-slate-300 max-w-2xl">Search companies and industries, see financial scorecards and simple valuation, and get AI-generated pros/cons. Built for fast desktop research.</p>
        <div className="mt-6 flex items-center gap-3">
          <Link to="/analyze" className="rounded-xl bg-blue-600 hover:bg-blue-700 text-white px-5 py-3 font-medium shadow">Open Analyzer</Link>
          <Link to="/docs" className="rounded-xl border hover:bg-slate-50 dark:hover:bg-slate-800 px-5 py-3">Read Docs</Link>
        </div>
      </section>

      <section className="mt-10 grid grid-cols-1 md:grid-cols-3 gap-4">
        <Feature title="One-box research" text="Type a name or ticker; get suggestions, metrics, and sources in seconds."/>
        <Feature title="Explainable signals" text="Simple scorecard (growth, margins, leverage, ROE) with clear thresholds."/>
        <Feature title="Lightweight valuation" text="Quick EV/EBIT fair value with editable peer multiple (coming soon)."/>
      </section>

      <section className="mt-12 rounded-2xl border bg-white dark:bg-slate-900 dark:border-slate-800 p-6">
        <h2 className="text-lg font-semibold">Quick demo</h2>
        <p className="text-sm text-slate-600 dark:text-slate-400">Jump straight in with NVIDIA.</p>
        <Link to="/analyze" state={{ demo: 'NVDA' }} className="mt-3 inline-block rounded-lg border px-3 py-2 hover:bg-slate-50 dark:hover:bg-slate-800">Analyze NVDA</Link>
      </section>
    </div>
  );
}

function AnalyzePage() {
  const location = useLocation();
  const demoQuery = location.state?.demo;
  return <InvestmentAgentUI initialQuery={demoQuery} />;
}

function About() {
  return (
    <article className="prose prose-slate dark:prose-invert">
      <h1>About</h1>
      <p>This project is a lightweight research assistant for robotics & technology equities. It aggregates public market data (via yfinance) and applies transparent heuristics you can tweak.</p>
      <ul>
        <li>FastAPI backend (Python) with yfinance/pandas</li>
        <li>React + Vite frontend with Tailwind</li>
        <li>Clear, editable thresholds and valuation assumptions</li>
      </ul>
    </article>
  );
}

function Docs() {
  return (
    <article className="prose prose-slate dark:prose-invert">
      <h1>Docs</h1>
      <h3>Endpoints</h3>
      <pre><code>GET /api/suggest?q=...
GET /api/analyze?query=...&years=1..10</code></pre>
      <h3>Env</h3>
      <pre><code>VITE_API_URL=http://127.0.0.1:8000</code></pre>
      <h3>Notes</h3>
      <ul>
        <li>Use a proper data vendor for production reliability.</li>
        <li>AI pros/cons are rule-based placeholders – swap in your RAG/LLM later.</li>
        <li>Always verify signals with primary filings and transcripts.</li>
      </ul>
    </article>
  );
}

function Disclaimer() {
  return (
    <article className="prose prose-slate dark:prose-invert">
      <h1>Disclaimer</h1>
      <p>Educational tool only. Not investment advice. Data may be delayed or inaccurate. Do your own research.</p>
    </article>
  );
}

function NotFound() {
  return (
    <div className="text-center py-16">
      <h1 className="text-3xl font-semibold">404</h1>
      <p className="mt-2 text-slate-600 dark:text-slate-400">Page not found.</p>
      <Link to="/" className="mt-4 inline-block rounded-lg border px-4 py-2 hover:bg-slate-50 dark:hover:bg-slate-800">Go home</Link>
    </div>
  );
}

// ---------------- Analyzer (was InvestmentAgentUI) ---------------- //
function InvestmentAgentUI({ initialQuery = "" }) {
  const [query, setQuery] = useState(initialQuery || "");
  const [years, setYears] = useState(10);
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggest, setShowSuggest] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [data, setData] = useState(null);
  const [chartData, setChartData] = useState([]); // New state for chart data
  const abortRef = useRef(null);

  const [thresh, setThresh] = useState({
    rev_cagr_min: 0.05,
    op_margin_min: 0.10,
    nd_eq_max: 1.0,
    interest_cover_min: 4.0,
    roe_min: 0.10,
  });


// price chart state (default 1y)
const [chartRange, setChartRange] = useState('1y');

// helper: pick a price series from backend payload (support a few keys)
const getSeries = (d) =>
  d?.prices || d?.priceSeries || d?.meta?.prices || []; // array of { date, close } (date: ISO or epoch)

function sliceByRange(series, range) {
  if (!Array.isArray(series) || series.length === 0) return [];
  const norm = series
    .map(p => {
      const t = typeof p.date === 'number' ? new Date(p.date * (p.date < 2e10 ? 1000 : 1)) : new Date(p.date);
      const y = Number(p.close ?? p.price ?? p.y);
      return (isFinite(t) && isFinite(y)) ? { t, y } : null;
    })
    .filter(Boolean)
    .sort((a, b) => a.t - b.t);

  const end = norm[norm.length - 1]?.t ?? new Date();
  const start = new Date(end);
  const ytd = new Date(end.getFullYear(), 0, 1);

  switch (range) {
    case '5d':   start.setDate(end.getDate() - 5); break;
    case '1m':   start.setMonth(end.getMonth() - 1); break;
    case '6m':   start.setMonth(end.getMonth() - 6); break;
    case 'YTD':  return norm.filter(p => p.t >= ytd);
    case '1y':   start.setFullYear(end.getFullYear() - 1); break;
    case '5y':   start.setFullYear(end.getFullYear() - 5); break;
    case '10y':  start.setFullYear(end.getFullYear() - 10); break;
    default:     start.setFullYear(end.getFullYear() - 1);
  }
  return norm.filter(p => p.t >= start);
}


  useEffect(() => {
    const saved = localStorage.getItem("agent-thresholds");
    if (saved) setThresh(JSON.parse(saved));
  }, []);

  useEffect(() => {
    localStorage.setItem("agent-thresholds", JSON.stringify(thresh));
  }, [thresh]);

  useEffect(() => { if (initialQuery) runAnalyze(initialQuery); }, [initialQuery]);

  useEffect(() => {
    const id = setTimeout(() => {
      const q = query.trim();
      if (!q) { setSuggestions([]); return; }
      if (abortRef.current) abortRef.current.abort();
      const ctrl = new AbortController();
      abortRef.current = ctrl;
      fetch(api(`/api/suggest?q=${encodeURIComponent(q)}`), { signal: ctrl.signal })
        .then(r => r.ok ? r.json() : Promise.reject())
        .then(json => setSuggestions(Array.isArray(json) ? json.slice(0, 8) : []))
        .catch(() => setSuggestions([]));
    }, 180);
    return () => clearTimeout(id);
  }, [query]);

  const runAnalyze = (value) => {
    const q = (typeof value === 'string' && value) ? value : query;
    if (!q) return;
    setShowSuggest(false);
    setLoading(true);
    setError("");

    const params = new URLSearchParams({
      query: q,
      years: String(years),
      rev_cagr_min: String(thresh.rev_cagr_min),
      op_margin_min: String(thresh.op_margin_min),
      nd_eq_max: String(thresh.nd_eq_max),
      interest_cover_min: String(thresh.interest_cover_min),
      roe_min: String(thresh.roe_min),
    });

    fetch(api(`/api/analyze?${params.toString()}`))
      .then(r => r.ok ? r.json() : r.text().then(t => Promise.reject(new Error(t || "Analyze failed"))))
      .then(json => {
      console.log("Prices from backend:", json.prices); // Debugging statement
      setData(json);
      const series = sliceByRange(getSeries(json), chartRange); // Extract and filter price data
      setChartData(series); // Update chart data
    })
      .catch(e => setError(e.message || "Something went wrong"))
      .finally(() => setLoading(false));
  };
  

  const onKeyDown = (e) => { if (e.key === 'Enter') runAnalyze(); };

  return (
    <div>
      <header className="rounded-2xl border bg-white dark:bg-slate-900 dark:border-slate-800 p-6">
        <h1 className="text-2xl font-semibold tracking-tight">Analyze</h1>
        <p className="text-slate-600 dark:text-slate-400">Search a company or industry, set the years window, then analyze.</p>

        <div className="controls">
          <SearchBar
            value={query}
            onChange={setQuery}
            onSubmit={() => runAnalyze()}
            suggestions={suggestions}
            showSuggest={showSuggest}
            setShowSuggest={setShowSuggest}
            loading={loading}
            onPickSuggestion={(s) => {
              setQuery(s.label || s.value);
              setShowSuggest(false);
              runAnalyze(s.value);
            }}
          />

          <div className="flex items-center gap-3 rounded-xl border bg-white dark:bg-slate-900 dark:border-slate-800 p-3">
            <label className="text-xs font-medium text-slate-600 dark:text-slate-300">Years</label>
            <input
              type="range"
              min={1}
              max={10}
              step={1}
              value={years}
              onChange={(e) => setYears(parseInt(e.target.value, 10))}
              onMouseUp={() => runAnalyze()}
              onTouchEnd={() => runAnalyze()}
              className="w-40 align-middle"
            />
            <span className="text-sm tabular-nums">{years}</span>
          </div>

          <button
            onClick={() => runAnalyze()}
            disabled={loading}
            className="rounded-xl bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 font-medium shadow disabled:opacity-60"
            style={{ marginTop: '12px' }}
          >
            {loading ? 'Analyzing…' : 'Analyze'}
          </button>
        </div>

        <hr style={{ margin: '12px 0', borderColor: 'var(--border)' }} /> {/* Line after Analyze button */}

        {error && (
          <div className="mt-3 rounded-lg border border-red-200 bg-red-50 dark:bg-red-950/30 dark:border-red-900 px-3 py-2 text-sm text-red-700 dark:text-red-300">
            {error}
          </div>
        )}
      </header>

      <section className="mt-6">
        {!data && !loading && <EmptyState onDemo={() => { setQuery('NVDA'); runAnalyze('NVDA'); }} />}

        {loading && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <SkeletonCard className="lg:col-span-2 h-48" />
            <SkeletonCard className="h-48" />
            <SkeletonCard className="lg:col-span-2 h-80" />
            <SkeletonCard className="h-80" />
          </div>
        )}

        {data && !loading && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* LEFT: Overview + Scorecard + Valuation */}
            <section className="lg:col-span-2 stack-lg">
              <Card>
                <div style={{ display:'flex', alignItems:'center', gap:8, flexWrap:'wrap', marginBottom:12 }}>
                  {['5d','1m','6m','YTD','1y','5y','10y'].map(r => (
                    <button
                      key={r}
                      onClick={() => setChartRange(r)}
                      className={`btn-range ${chartRange === r ? 'active' : ''}`}
                      type="button"
                    >
                      {r}
                    </button>
                  ))}
                </div>

                <PriceChart
                  series={chartData} // Use the updated chart data
                  height={220}
                />
              </Card>
              <Card>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12 }}>
                  <div>
                    <h2 className="section-title">Overview</h2>
                    <p className="sub">
                      {data?.meta?.queryType === 'industry' ? 'Industry' : 'Company'} • As of {data?.meta?.asOf || '—'}
                    </p>
                  </div>
                  {typeof data?.valuation?.upsidePct === 'number' && (
                    <span className={`badge ${data.valuation.upsidePct >= 0 ? 'green' : 'red'}`}>
                      {data.valuation.upsidePct >= 0 ? '+' : ''}{data.valuation.upsidePct.toFixed(1)}% Upside
                    </span>
                  )}
                </div>

                <div className="kpis" style={{ marginTop: 12 }}>
                  <div className="kpi">
                    <div className="label">Current Price</div>
                    <div className="value">{fmtCurrency(data?.valuation?.currentPrice)}</div>
                  </div>
                  <div className="kpi">
                    <div className="label">Fair Value (est.)</div>
                    <div className="value">{fmtCurrency(data?.valuation?.fairValue)}</div>
                  </div>
                </div>
              </Card>

              <hr style={{ margin: '12px 0', borderColor: 'var(--border)' }} /> {/* Line before Scorecard */}

              <Card>
                <h2 className="section-title" style={{ marginBottom: 8 }}>Scorecard</h2>
                <div className="score-grid">
                  {(data?.scorecard || []).map((s) => (
                    <ScoreItem key={s.id} label={s.label} verdict={s.verdict} detail={s.detail} value={s.value} threshold={s.threshold} unit={s.unit} />
                  ))}
                </div>
              </Card>

              <hr style={{ margin: '12px 0', borderColor: 'var(--border)' }} /> {/* Line before Valuation */}

              <Card>
                <h2 className="section-title" style={{ marginBottom: 8 }}>Valuation</h2>
                <div className="overflow-x-auto">
                  <table className="table">
                    <thead>
                      <tr>
                        <th style={{ textAlign: 'left' }}>Metric</th>
                        <th style={{ textAlign: 'left' }}>Value</th>
                        <th style={{ textAlign: 'left' }}>Notes</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(data?.valuation?.table || []).map((row, idx) => (
                        <tr key={idx}>
                          <td style={{ fontWeight: 600 }}>{row.metric}</td>
                          <td className="num">{row.value}</td>
                          <td style={{ color: 'var(--muted)' }}>{row.note}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </Card>
            </section>

            <hr style={{ margin: '12px 0', borderColor: 'var(--border)' }} /> {/* Line before AI Analysis */}

            {/* RIGHT: AI bullets + Filters */}
            <aside className="stack-lg">
              <Card>
                <h2 className="section-title" style={{ marginBottom: 8 }}>AI Analysis</h2>
                <Bullets title="Pros" items={data?.pros} tone="green" />
                <div style={{ height: 12 }} />
                <Bullets title="Cons" items={data?.cons} tone="amber" />
                <div style={{ height: 12 }} />
                <Bullets title="Key Risks" items={data?.risks} tone="red" />
              </Card>
              <Card>
                <h2 className="section-title" style={{ marginBottom: 8 }}>Filters</h2>

                {/* Years slider in flex box */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginTop: '12px' }}>
                  <span className="sub">Years</span>
                  <input
                    type="range"
                    min={1}
                    max={10}
                    step={1}
                    value={years}
                    onChange={(e) => setYears(parseInt(e.target.value, 10))}
                    onMouseUp={() => runAnalyze()}
                    onTouchEnd={() => runAnalyze()}
                    style={{ flex: 1 }}
                  />
                  <span>{years} year{years > 1 ? 's' : ''}</span>
                </div>


                {/* Thresholds */}
                <hr style={{ margin: '12px 0', borderColor: 'var(--border)' }} />
                <h3 className="text-sm font-semibold">Thresholds</h3>
                <p className="sub" style={{ marginTop: 4 }}>Adjust the scorecard rules (defaults in () ).</p>

                <div className="thresh-grid">
                  <label className="field">
                    <span className="field-label">Revenue CAGR ≥ <span className="muted">(5%)</span></span>
                    <div className="field-input">
                      <input
                        type="number"
                        step="0.1"
                        value={(thresh.rev_cagr_min * 100).toString()}
                        onChange={(e) => setThresh(t => ({ ...t, rev_cagr_min: Number(e.target.value) / 100 }))}
                        onBlur={runAnalyze}
                        inputMode="decimal"
                      />
                      <span className="adorn">%</span>
                    </div>
                  </label>

                  <label className="field">
                    <span className="field-label">Operating Margin ≥ <span className="muted">(10%)</span></span>
                    <div className="field-input">
                      <input
                        type="number"
                        step="0.1"
                        value={(thresh.op_margin_min * 100).toString()}
                        onChange={(e) => setThresh(t => ({ ...t, op_margin_min: Number(e.target.value) / 100 }))}
                        onBlur={runAnalyze}
                        inputMode="decimal"
                      />
                      <span className="adorn">%</span>
                    </div>
                  </label>

                  <label className="field">
                    <span className="field-label">Net Debt / Equity ≤ <span className="muted">(1.0x)</span></span>
                    <div className="field-input">
                      <input
                        type="number"
                        step="0.1"
                        value={thresh.nd_eq_max.toString()}
                        onChange={(e) => setThresh(t => ({ ...t, nd_eq_max: Number(e.target.value) }))}
                        onBlur={runAnalyze}
                        inputMode="decimal"
                      />
                      <span className="adorn">x</span>
                    </div>
                  </label>

                  <label className="field">
                    <span className="field-label">Interest Coverage ≥ <span className="muted">(4.0x)</span></span>
                    <div className="field-input">
                      <input
                        type="number"
                        step="0.1"
                        value={thresh.interest_cover_min.toString()}
                        onChange={(e) => setThresh(t => ({ ...t, interest_cover_min: Number(e.target.value) }))}
                        onBlur={runAnalyze}
                        inputMode="decimal"
                      />
                      <span className="adorn">x</span>
                    </div>
                  </label>

                  <label className="field">
                    <span className="field-label">ROE ≥ <span className="muted">(10%)</span></span>
                    <div className="field-input">
                      <input
                        type="number"
                        step="0.1"
                        value={(thresh.roe_min * 100).toString()}
                        onChange={(e) => setThresh(t => ({ ...t, roe_min: Number(e.target.value) / 100 }))}
                        onBlur={runAnalyze}
                        inputMode="decimal"
                      />
                      <span className="adorn">%</span>
                    </div>
                  </label>
                </div>

                <div className="thresh-actions">
                  <button
                    className="rounded-lg border px-3 py-2"
                    onClick={() => {
                      setThresh({ rev_cagr_min: 0.05, op_margin_min: 0.10, nd_eq_max: 1.0, interest_cover_min: 4.0, roe_min: 0.10 });
                      runAnalyze();
                    }}
                    style={{ marginTop: '12px' }} // Add spacing
                  >
                    Reset defaults
                  </button>
                  <button
                    className="rounded-lg bg-blue-600 text-white px-3 py-2"
                    onClick={runAnalyze}
                    style={{ marginTop: '12px' }} // Add spacing
                  >
                    Apply
                  </button>
                </div>
              </Card>
            </aside>

            {/* Sources moved to the very bottom */}
            <section className="lg:col-span-3 stack-lg">
              <Card id="sources">
                <h2 className="section-title">Sources</h2>
                <ul style={{ marginTop: 8, paddingLeft: 18, lineHeight: 1.6 }}>
                  {(data?.sources || []).map((s, i) => (
                    <li key={i}>
                      <a className="hover:underline" href={s.url} target="_blank" rel="noreferrer">
                        {s.title || s.url}
                      </a>
                    </li>
                  ))}
                </ul>
              </Card>
            </section>
          </div>
        )}
      </section>
    </div>
  );
}

// ---------------- Small UI components ---------------- //
function Feature({ title, text }) {
  return (
    <div className="rounded-2xl border bg-white dark:bg-slate-900 dark:border-slate-800 p-5">
      <div className="text-lg font-semibold">{title}</div>
      <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">{text}</p>
    </div>
  );
}

function Card({ children, id, className = "" }) {
  return <section id={id} className={`rounded-2xl border bg-white dark:bg-slate-900 dark:border-slate-800 p-5 shadow-sm ${className}`}>{children}</section>;
}

function Badge({ children, tone = 'gray' }) {
  const tones = { green: 'bg-green-100 text-green-800 border-green-200', red: 'bg-red-100 text-red-800 border-red-200', gray: 'bg-slate-100 text-slate-800 border-slate-200' };
  return <span className={`inline-flex items-center rounded-full border px-3 py-1 text-xs font-medium ${tones[tone]}`}>{children}</span>;
}

function NumField({ label, suffix, value, placeholder, onChange, onBlur, hint }) {
  return (
    <label className="block mt-3">
      <div className="text-sm text-slate-700 dark:text-slate-300">{label} <span className="sub">{hint}</span></div>
      <div className="flex items-center gap-2 mt-1">
        <input
          type="number"
          value={value}
          placeholder={placeholder}
          onChange={(e) => onChange(e.target.value)}
          onBlur={onBlur}
          className="w-full rounded-lg border px-3 py-2"
          step="0.1"
        />
        {suffix && <span className="text-sm text-slate-600 dark:text-slate-400">{suffix}</span>}
      </div>
    </label>
  );
}

function PriceChart({ series = [], width = '100%', height = 200 }) {
  if (!series || series.length < 2) {
    return <div className="chart-empty sub">Price chart unavailable.</div>;
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
        <span className="sub">Change</span>
        <span className={`chart-pct ${pct >= 0 ? 'up' : 'down'}`}>{pct >= 0 ? '+' : ''}{pct.toFixed(2)}%</span>
      </div>
    </div>
  );
}

function KPI({ label, value }) {
  return (
    <div className="rounded-xl border p-4 bg-slate-50 dark:bg-slate-800/50">
      <div className="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">{label}</div>
      <div className="text-xl font-semibold mt-1">{value ?? '—'}</div>
    </div>
  );
}
function ScoreItem({ label, verdict, detail /* value, threshold, unit unused */ }) {
  const tone = verdict === 'green' ? 'green' : verdict === 'red' ? 'red' : 'amber';
  const pillClass = tone === 'green' ? 'pill green' : tone === 'red' ? 'pill red' : 'pill amber';

  return (
    <div className="score-card">
      <div className="score-head">
        <div style={{ fontWeight: 600 }}>{label}</div>
        <span className={pillClass}>{(verdict || 'amber').toUpperCase()}</span>
      </div>
      {detail && <div className="sub" style={{ marginTop: 6 }}>{detail}</div>}
    </div>
  );
}

function Bullets({ title, items = [], tone = 'gray' }) {
  const toneMap = { green: 'border-green-200', amber: 'border-yellow-200', red: 'border-red-200', gray: 'border-slate-200' };
  return (
    <div>
      <h4 className="font-semibold mb-2">{title}</h4>
      {(!items || items.length === 0) && <p className="text-sm text-slate-500 dark:text-slate-400">No items available.</p>}
      <ul className="space-y-2">
        {items.map((it, i) => (
          <li key={i} className={`rounded-xl border ${toneMap[tone]} p-3 bg-slate-50 dark:bg-slate-800/40`}>
            <div className="text-sm">{it.text}</div>
            {it.source && (<a className="text-xs text-blue-700 hover:underline" href={it.source} target="_blank" rel="noreferrer">Source</a>)}
          </li>
        ))}
      </ul>
    </div>
  );
}

function SkeletonCard({ className = "" }) {
  return (
    <div className={`rounded-2xl border bg-white dark:bg-slate-900 dark:border-slate-800 shadow-sm p-5 ${className}`}>
      <div className="animate-pulse space-y-3">
        <div className="h-5 bg-slate-200 dark:bg-slate-800 rounded w-1/3"></div>
        <div className="h-4 bg-slate-200 dark:bg-slate-800 rounded w-full"></div>
        <div className="h-4 bg-slate-200 dark:bg-slate-800 rounded w-5/6"></div>
        <div className="h-4 bg-slate-200 dark:bg-slate-800 rounded w-2/3"></div>
      </div>
    </div>
  );
}

function EmptyState({ onDemo }) {
  return (
    <div className="rounded-2xl border bg-white dark:bg-slate-900 dark:border-slate-800 p-8 shadow-sm text-slate-700 dark:text-slate-300">
      <div className="flex items-start gap-4">
        <div className="text-3xl">🔎</div>
        <div>
          <h3 className="text-lg font-semibold">Search to begin</h3>
          <p className="text-sm mt-1">Enter a company (e.g., <span className="font-medium">NVDA</span>) or an industry (e.g., <span className="font-medium">Robotics</span>), set the years slider, and click Analyze.</p>
          <button onClick={onDemo} className="mt-4 rounded-lg border px-3 py-1.5 text-sm hover:bg-slate-50 dark:hover:bg-slate-800">Run NVDA demo</button>
        </div>
      </div>
    </div>
  );
}

function Logo() {
  return <div className="h-6 w-6 rounded-md bg-gradient-to-br from-blue-500 to-indigo-600 grid place-items-center text-white text-[10px] font-bold">LOGO</div>;
}

function fmtCurrency(v) {
  if (v == null || isNaN(v)) return '—';
  try { return new Intl.NumberFormat(undefined, { style: 'currency', currency: 'USD', maximumFractionDigits: 2 }).format(v); }
  catch { return `$${Number(v).toFixed(2)}`; }
}

function SearchBar({
  value,
  onChange,
  onSubmit,
  suggestions = [],
  showSuggest,
  setShowSuggest,
  loading,
  onPickSuggestion
}) {
  const [active, setActive] = useState(0);
  const listRef = useRef(null);

  // keyboard nav
  const onKeyDown = (e) => {
    if (!showSuggest || suggestions.length === 0) {
      if (e.key === "Enter") onSubmit();
      return;
    }
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActive((i) => (i + 1) % suggestions.length);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActive((i) => (i - 1 + suggestions.length) % suggestions.length);
    } else if (e.key === "Enter") {
      e.preventDefault();
      const s = suggestions[active];
      if (s) onPickSuggestion(s);
    } else if (e.key === "Escape") {
      setShowSuggest(false);
    }
  };

  return (
    <div className="search-wrap flex items-center">
      <span className="search-icon" aria-hidden>
        {/* magnifier */}
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
          <circle cx="11" cy="11" r="7" stroke="currentColor" strokeWidth="2"/>
          <path d="M20 20l-3.5-3.5" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
        </svg>
      </span>

      <input
        value={value}
        onChange={(e) => {
          onChange(e.target.value);
          setShowSuggest(true);
        }}
        onFocus={() => setShowSuggest(true)}
        onKeyDown={onKeyDown}
        placeholder="Search company or industry (e.g., NVDA, ABB, Robotics)…"
        className="search flex-1"
        aria-autocomplete="list"
        aria-expanded={showSuggest}
        aria-controls="suggest-list"
      />

      {loading && <span className="loading-spin" aria-hidden />}

      {value && !loading && (
        <button
          type="button"
          className="clear-btn"
          aria-label="Clear search"
          onMouseDown={(e) => e.preventDefault()}   // keep input focused
          onClick={() => { onChange(""); setShowSuggest(false); }}
          title="Clear"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" aria-hidden="true">
            <path d="M6 6l12 12M18 6L6 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
          </svg>
        </button>
      )}

      {showSuggest && suggestions.length > 0 && (
        <div id="suggest-list" role="listbox" className="suggest" ref={listRef}>
          {suggestions.map((s, i) => (
            <button
              key={`${s.value}-${i}`}
              role="option"
              aria-selected={i === active}
              className="suggest-item"
              onMouseEnter={() => setActive(i)}
              onClick={() => onPickSuggestion(s)}
            >
              <span className="label">{s.label || s.value}</span>
              <span className="type">{s.type === "industry" ? "Industry" : "Company"}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

