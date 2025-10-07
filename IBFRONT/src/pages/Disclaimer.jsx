// src/pages/Disclaimer.jsx
import React from "react";
import Card from "../components/Card.jsx";

export default function Disclaimer() {
  return (
    <div className="stack-lg">
      <Card>
        <h1 className="title">Disclaimer</h1>
        <p className="lead">This application is for informational and educational purposes only and does not constitute investment advice. Do your own research.</p>
      </Card>
      <Card>
        <h3 className="section-title">Risks</h3>
        <ul className="list-disc ml-5 text-sm space-y-1">
          <li>Financial data can be delayed, incomplete, or inaccurate.</li>
          <li>Models and thresholds are simplified heuristics.</li>
          <li>Past performance is not indicative of future results.</li>
        </ul>
      </Card>
    </div>
  );
}
