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
        <p className="lead">Search companies across US, European, and Asian exchanges — view fundamentals, scorecard, valuation, and AI-powered investment thesis.</p>
        <div className="mt-3">
          <Link to="/analyze" className="btn-range">Get started</Link>
        </div>
      </Card>

      <div className="kpis">
        <Feature title="Global coverage" text="US, LSE, TSX, ASX, HKEX, TSE and more — search by ticker or company name." />
        <Feature title="Actionable metrics" text="Growth, margins, leverage, interest coverage, and ROE with pass/fail scorecard." />
      </div>

      <Card>
        <h3 className="section-title">How it works</h3>
        <ol className="list-decimal ml-5 space-y-1 text-sm">
          <li>Type a ticker (e.g., NVDA, BP.L, SHOP.TO) or industry (e.g., Robotics).</li>
          <li>Adjust the thresholds and period according to your criteria.</li>
          <li>Run and review scorecard, valuation, ROE trend, and AI thesis.</li>
        </ol>
      </Card>
    </div>
  );
}
