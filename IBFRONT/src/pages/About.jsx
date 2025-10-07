// src/pages/About.jsx
import React from "react";
import Card from "../components/Card.jsx";

export default function About() {
  return (
    <div className="stack-lg">
      <Card>
        <h1 className="title">About</h1>
        <p className="lead">Sudut Invest is a lightweight tool to explore companies and industries using fundamentals, scorecards, and simple valuation heuristics.</p>
      </Card>
      <Card>
        <h3 className="section-title">Tech stack</h3>
        <ul className="list-disc ml-5 text-sm space-y-1">
          <li>Frontend: React + Vite</li>
          <li>Backend: FastAPI</li>
          <li>Data: yfinance and company statements</li>
        </ul>
      </Card>
    </div>
  );
}
