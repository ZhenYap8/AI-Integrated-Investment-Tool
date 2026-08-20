import React from 'react';

export default function Feature({ title, text }) {
  return (
    <div className="feature-card">
      <h3 className="feature-card-title">{title}</h3>
      <p className="feature-card-text">{text}</p>
    </div>
  );
}
