import React, { useMemo } from 'react';
import Card from '../../components/Card.jsx';
import Badge from '../../components/Badge.jsx';
import PriceChart from '../../components/PriceChart.jsx';
import Scorecard from '../../components/Scorecard.jsx';
import Valuation from '../../components/Valuation.jsx';
import ProsCons from '../../components/ProsCons.jsx';
import NewsHeadlines from '../../components/NewsHeadlines.jsx';

const EXCHANGE_LABELS = {
  US_NASDAQ: 'NASDAQ',
  US_OTHER: 'NYSE/AMEX',
  TSX: 'TSX',
  LSE: 'LSE',
  ASX: 'ASX',
  HKEX: 'HKEX',
  TSE_JP: 'TSE',
  GLOBAL: 'Global',
  INDEX: 'Index',
};

function ScoreSummary({ scorecard = [] }) {
  const greens = scorecard.filter(s => s.verdict === 'green').length;
  const total = scorecard.length;
  if (!total) return null;
  const pct = Math.round((greens / total) * 100);
  const tone = pct >= 70 ? 'green' : pct >= 40 ? 'amber' : 'red';
  return (
    <div className="score-summary">
      <div className={`score-ring score-ring-${tone}`}>
        <span className="score-ring-value">{greens}/{total}</span>
      </div>
      <div>
        <div className="score-summary-label">Quality Score</div>
        <div className="score-summary-detail">{pct}% of metrics pass thresholds</div>
      </div>
    </div>
  );
}

export default function AnalyzerResults({
  resp,
  series = [],
  findings = [],
  headlines = [],
  insightMode = '',
  loading = false,
  period,
  years,
  historyLabel,
  aiLoading = false,
}) {
  const meta = resp?.meta || {};
  const isCompany = meta.queryType === 'company';
  const ticker = meta.ticker || '';
  const exchange = meta.exchange;
  const exchangeLabel = EXCHANGE_LABELS[exchange] || exchange || '';
  const roeChartLabel = meta.roeGranularity === 'quarterly' ? 'ROE (Quarterly)' : 'ROE (Annual)';

  const { pros, cons } = useMemo(() => {
    if (!Array.isArray(findings) || findings.length === 0) {
      return { pros: [], cons: [] };
    }
    const enrich = (f) => ({
      text: f.item,
      factor: f.factor,
      timeframe: f.timeframe,
      materiality: f.materiality,
      outlet: f?.evidence?.[0]?.source,
      sourceUrl: f?.evidence?.[0]?.url,
      snippet: f?.evidence?.[0]?.snippet,
      evidence: f.evidence,
    });
    return {
      pros: findings.filter(f => f?.direction === 'pro').map(enrich),
      cons: findings.filter(f => f?.direction === 'con').map(enrich),
    };
  }, [findings]);

  const fallbackPros = (resp?.pros || []).map(p => ({ text: p.text || p }));
  const fallbackCons = (resp?.cons || []).map(c => ({ text: c.text || c }));
  const risks = (resp?.risks || []).map(r => ({ text: r.text || r }));

  const displayPros = pros.length ? pros : fallbackPros;
  const displayCons = cons.length ? cons : fallbackCons;

  return (
    <div className="results-wrap">
      {/* Hero header */}
      <div className="results-hero">
        <div className="results-hero-main">
          <h2 className="results-title">
            {isCompany ? (meta.companyName || ticker) : (meta.industry || 'Industry Analysis')}
          </h2>
          {isCompany && ticker && (
            <span className="results-ticker">{ticker}</span>
          )}
          {isCompany && exchangeLabel && (
            <Badge tone="gray">{exchangeLabel}</Badge>
          )}
          {!isCompany && (
            <Badge tone="gray">Industry</Badge>
          )}
        </div>
        <div className="results-hero-meta">
          <span>As of {meta.asOf || '—'}</span>
          <span>History: {historyLabel || meta.historyWindow || '—'}</span>
        </div>
      </div>

      {/* Score summary + chart row */}
      <div className="results-grid-2">
        <Card className="score-summary-card">
          <h3 className="section-title">Fundamentals Scorecard</h3>
          <ScoreSummary scorecard={resp?.scorecard || []} />
          <Scorecard
            scorecard={resp?.scorecard || null}
            loading={loading}
            years={years || 5}
          />
        </Card>

        <Card>
          <h3 className="section-title">{roeChartLabel}</h3>
          <PriceChart series={series} height={280} label="ROE" />
        </Card>
      </div>

      {/* Valuation */}
      <Card>
        <h3 className="section-title">Valuation</h3>
        <Valuation valuation={resp?.valuation} ticker={ticker} />
      </Card>

      {/* AI Analysis */}
      <Card>
        <div className="ai-header">
          <h3 className="section-title">Investment Thesis</h3>
          {aiLoading && <span className="ai-loading-badge">Generating…</span>}
          {!aiLoading && insightMode && insightMode !== 'ai' && (
            <span className="ai-loading-badge" style={{ animation: 'none', opacity: 0.85 }}>
              {insightMode === 'news' ? 'News-based' : 'Metrics-based'}
            </span>
          )}
        </div>
        <ProsCons
          pros={displayPros}
          cons={displayCons}
          risks={risks}
          loading={aiLoading}
        />
      </Card>

      {isCompany && (
        <Card>
          <h3 className="section-title">News Headlines</h3>
          <p className="sub" style={{ marginBottom: 8 }}>
            Recent coverage from Reuters, Bloomberg, FT, BBC, CNBC, WSJ &amp; more — used to inform the investment thesis above.
          </p>
          <NewsHeadlines headlines={headlines} mode={insightMode} loading={aiLoading} />
        </Card>
      )}

      {isCompany && (
        <div className="data-provenance" id="data-sources">
          <p className="data-provenance-title">Where this data comes from</p>
          <ul className="data-provenance-list">
            <li>
              <strong>Fundamentals</strong> (scorecard, ROE, valuation) — Yahoo Finance financial statements
            </li>
            <li>
              <strong>News &amp; thesis</strong> — aggregated headlines from major financial press (see list above)
            </li>
          </ul>
          {ticker && (
            <a
              className="data-provenance-link"
              href={`https://finance.yahoo.com/quote/${encodeURIComponent(ticker)}`}
              target="_blank"
              rel="noreferrer"
            >
              View {ticker} on Yahoo Finance
            </a>
          )}
        </div>
      )}
    </div>
  );
}
