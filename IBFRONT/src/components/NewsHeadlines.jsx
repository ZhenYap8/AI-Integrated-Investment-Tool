import React from 'react';

function outletClass(outlet = '') {
  const o = outlet.toLowerCase();
  if (o.includes('reuters')) return 'outlet-reuters';
  if (o.includes('bloomberg')) return 'outlet-bloomberg';
  if (o.includes('bbc')) return 'outlet-bbc';
  if (o.includes('financial times') || o === 'ft') return 'outlet-ft';
  if (o.includes('cnbc')) return 'outlet-cnbc';
  if (o.includes('wsj') || o.includes('wall street')) return 'outlet-wsj';
  return 'outlet-default';
}

export default function NewsHeadlines({ headlines = [], mode = '', loading = false }) {
  if (loading) {
    return <p className="sub skeleton-pulse" style={{ padding: '12px 0' }}>Loading headlines…</p>;
  }

  if (!headlines.length) {
    return <p className="sub">No headlines fetched from external sources.</p>;
  }

  const modeLabel = mode === 'ai'
    ? 'Synthesised from the headlines below'
    : mode === 'news'
      ? 'Built from the headlines below (AI unavailable)'
      : '';

  return (
    <div className="news-headlines-wrap">
      {modeLabel && (
        <p className="sub" style={{ marginBottom: 10 }}>{modeLabel}</p>
      )}
      <ul className="news-headlines-list">
        {headlines.map((h, i) => (
          <li key={`${h.url}-${i}`} className="news-headline-item">
            <div className="news-headline-meta">
              <span className={`news-outlet-badge ${outletClass(h.outlet)}`}>{h.outlet || 'News'}</span>
              {h.date && <span className="news-date">{h.date}</span>}
            </div>
            <a className="news-headline-title" href={h.url} target="_blank" rel="noreferrer">
              {h.title}
            </a>
            {h.snippet && h.snippet !== h.title && (
              <p className="news-snippet">{h.snippet}</p>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}
