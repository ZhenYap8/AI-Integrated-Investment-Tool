import React, { useState, useEffect } from 'react';
import Badge from './Badge.jsx';
import { api, fetchJSON } from '../lib/api.js';

const Valuation = ({ valuation, ticker }) => {
  const [valuationData, setValuationData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (valuation && valuation.table && valuation.table.length > 0) {
      setValuationData(valuation);
      return;
    }
    if (ticker) {
      fetchValuation(ticker);
    }
  }, [valuation, ticker]);

  const fetchValuation = async (tickerSymbol) => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchJSON(api('/api/valuation'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ticker: tickerSymbol, metrics: {}, overrides: {} }),
      });
      if (data.valuation) {
        setValuationData(data.valuation);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="sub" style={{ padding: '1rem', textAlign: 'center' }}>Loading valuation…</div>;
  }

  if (error) {
    return <div className="sub" style={{ padding: '1rem', color: 'var(--error, #dc2626)' }}>Error: {error}</div>;
  }

  if (!valuationData) {
    return <div className="sub" style={{ padding: '1rem' }}>No valuation data available.</div>;
  }

  const { upsidePct, table = [] } = valuationData;

  if (!table || table.length === 0) {
    return <div className="sub" style={{ padding: '1rem' }}>No valuation metrics available.</div>;
  }

  return (
    <>
      {typeof upsidePct === 'number' && (
        <Badge tone={upsidePct >= 0 ? 'green' : 'red'}>
          Upside {upsidePct >= 0 ? '+' : ''}{upsidePct.toFixed(1)}%
        </Badge>
      )}
      <div className="overflow-x-auto" style={{ marginTop: typeof upsidePct === 'number' ? '12px' : '0' }}>
        <table className="table">
          <thead>
            <tr>
              <th style={{ textAlign: 'left' }}>Metric</th>
              <th style={{ textAlign: 'right' }}>Value</th>
              <th style={{ textAlign: 'left' }}>Notes</th>
            </tr>
          </thead>
          <tbody>
            {table.map((row, idx) => (
              <tr key={idx}>
                <td style={{ fontWeight: 600 }}>{row.metric || '—'}</td>
                <td className="num" style={{ textAlign: 'right' }}>
                  {row.value != null ? row.value : '—'}
                </td>
                <td style={{ color: 'var(--muted)' }}>{row.note || ''}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
};

export default Valuation;
