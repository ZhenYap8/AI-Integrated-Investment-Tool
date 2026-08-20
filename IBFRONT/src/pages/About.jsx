import React from 'react';
import Card from '../components/Card.jsx';

export default function About() {
  return (
    <div className="stack-lg">
      <Card>
        <span className="eyebrow">About</span>
        <h1 className="title">Sudut Invest</h1>
        <p className="lead">
          A lightweight analytics platform for exploring companies through fundamental data,
          financial scorecards, and simple valuation models — designed to make financial insights
          accessible, fast, and interpretable.
        </p>
      </Card>
      <Card>
        <h3 className="section-title">Tech stack</h3>
        <ul className="prose-list">
          <li>Frontend: React + Vite</li>
          <li>Backend: FastAPI</li>
          <li>Data: Yahoo Finance and company financial statements</li>
        </ul>
      </Card>
    </div>
  );
}
