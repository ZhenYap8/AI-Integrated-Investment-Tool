// src/pages/Home.jsx
import React from "react";
import { Link } from "react-router-dom";
import Card from "../components/Card.jsx";
import Feature from "../components/Feature.jsx";

export default function Home() {
  return (
    <div className="stack-lg">
      <Card>
        <h1 className="title">AI-assisted investment analyser</h1>
        <p className="lead">Search a company or industry, view fundamentals, scorecard, and a simple valuation with ROE trends.</p>
        <div className="mt-3">
          <Link to="/analyze" className="btn-range">Get started</Link>
        </div>
      </Card>

      <div className="kpis">
        <Feature title="Screen quickly" text="Use suggestions to find tickers and industries, then analyse in one click." />
        <Feature title="Actionable metrics" text="Growth, margins, leverage, interest coverage, and ROE summarized." />
      </div>

      <Card>
        <h3 className="section-title">How it works</h3>
        <ol className="list-decimal ml-5 space-y-1 text-sm">
          <li>Type a ticker (e.g., NVDA for Nvidia) or industry (e.g., Robotics).</li>
          <li>Adjude the thresholds and years according to your interests.</li>
          <li>Run and review scorecard, valuation, and ROE trend.</li>
        </ol>
      </Card>
    </div>
  );
}
