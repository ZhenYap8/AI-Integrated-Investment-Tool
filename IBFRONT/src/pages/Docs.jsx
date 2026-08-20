import React from 'react';
import Card from '../components/Card.jsx';

export default function Docs() {
  return (
    <div className="stack-lg">
      <Card>
        <span className="eyebrow">Documentation</span>
        <h1 className="title">Metrics &amp; methodology</h1>
        <p className="lead">
          How thresholds are applied and how to interpret the scorecard and valuation outputs.
        </p>
      </Card>
      <Card>
        <h3 className="section-title">Metrics</h3>
        <ul className="prose-list">
          <li>Revenue CAGR: Compound annual growth rate over the selected period.</li>
          <li>Operating margin: Operating income divided by revenue.</li>
          <li>Net debt / Equity: (Total debt − cash) over equity.</li>
          <li>Interest coverage: EBIT divided by interest expense.</li>
          <li>ROE: Net income divided by equity.</li>
        </ul>
      </Card>
      <Card>
        <h3 className="section-title">Valuation</h3>
        <p className="sub">
          A simple heuristic combining multiples and growth to estimate upside.
          Treat as a rough guide, not a target price.
        </p>
      </Card>
    </div>
  );
}
