// src/pages/Docs.jsx
import React from "react";
import Card from "../components/Card.jsx";

export default function Docs() {
  return (
    <div className="stack-lg">
      <Card>
        <h1 className="title">Documentation</h1>
        <p className="lead">Learn how thresholds and metrics are computed and how to interpret the scorecard.</p>
      </Card>
      <Card>
        <h3 className="section-title">Metrics</h3>
        <ul className="list-disc ml-5 text-sm space-y-1">
          <li>Revenue CAGR: Compound annual growth rate over selected years.</li>
          <li>Operating margin: Operating income divided by revenue.</li>
          <li>Net debt / Equity: (Total debt - cash) over equity.</li>
          <li>Interest coverage: EBIT divided by interest expense.</li>
          <li>ROE: Net income divided by equity.</li>
        </ul>
      </Card>
      <Card>
        <h3 className="section-title">Valuation</h3>
        <p className="text-sm">Simple heuristic combining multiples and growth to estimate upside. Treat as a rough guide, not a target price.</p>
      </Card>
      <Card>
        <h3 className="section-title">Endpoints</h3>
        <pre><code>GET /api/suggest?q=...
GET /api/analyze?query=...&period=1d|5d|1mo|3mo|6mo|1y|2y|5y|10y|ytd|max [&years=1|3|5|10]</code></pre>
      </Card>
    </div>
  );
}
