import React from 'react';
import { Link } from 'react-router-dom';
import Card from '../components/Card.jsx';
import Feature from '../components/Feature.jsx';

export default function Home() {
  return (
    <div className="stack-lg">
      <Card className="hero-card">
        <span className="eyebrow">Equity research platform</span>
        <h1 className="title">Fundamental screening &amp; company analysis</h1>
        <p className="lead">
          Screen US index constituents by quality score, compare peers within each sector,
          and run deep-dive analysis with scorecards, valuation, and AI-assisted thesis.
        </p>
        <div className="hero-actions">
          <Link to="/screen" className="btn-range btn-primary">Open screener</Link>
          <Link to="/analyze" className="btn-range btn-secondary">Analyse a company</Link>
        </div>
      </Card>

      <div className="kpis">
        <Feature
          title="Global coverage"
          text="US, LSE, TSX, ASX, HKEX, TSE and more — search by ticker or company name."
        />
        <Feature
          title="Sector screener"
          text="Rank companies within their industry using interpretable quality scores from Yahoo Finance fundamentals."
        />
        <Feature
          title="Actionable metrics"
          text="Growth, margins, leverage, interest coverage, and ROE with clear pass/fail scorecards."
        />
      </div>

      <Card>
        <h3 className="section-title">How it works</h3>
        <ol className="steps-list">
          <li>Pick a sector in the screener, or search a ticker directly (e.g. NVDA, BP.L).</li>
          <li>Set your thresholds and analysis period to match your investment criteria.</li>
          <li>Review the scorecard, valuation range, ROE trend, and AI investment thesis.</li>
        </ol>
      </Card>
    </div>
  );
}
