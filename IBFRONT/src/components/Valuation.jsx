import React, { useState, useEffect } from 'react';
import Badge from './Badge.jsx';

const Valuation = ({ valuation, ticker }) => {
  const [valuationData, setValuationData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    // If valuation is already provided from analyzer, use it
    if (valuation && valuation.table && valuation.table.length > 0) {
      console.log('[Valuation] Using valuation from analyzer response');
      setValuationData(valuation);
      return;
    }

    // Otherwise, fetch from dedicated valuation endpoint if ticker is available
    if (ticker) {
      fetchValuation(ticker);
    }
  }, [valuation, ticker]);

  const fetchValuation = async (tickerSymbol) => {
    setLoading(true);
    setError(null);
    
    try {
      console.log('[Valuation] Fetching valuation for ticker:', tickerSymbol);
      
      const response = await fetch('http://localhost:8000/api/valuation', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ticker: tickerSymbol,
          metrics: {},
          overrides: {}
        }),
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch valuation: ${response.statusText}`);
      }

      const data = await response.json();
      console.log('[Valuation] Received data:', data);
      
      if (data.valuation) {
        setValuationData(data.valuation);
      }
    } catch (err) {
      console.error('[Valuation] Error fetching valuation:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Show loading state
  if (loading) {
    return (
      <div style={{ padding: '1rem', textAlign: 'center', color: 'var(--muted)' }}>
        Loading valuation data...
      </div>
    );
  }

  // Show error state
  if (error) {
    return (
      <div style={{ padding: '1rem', color: 'var(--error)' }}>
        Error loading valuation: {error}
      </div>
    );
  }

  // If no valuation data available
  if (!valuationData) {
    return (
      <div style={{ padding: '1rem', color: 'var(--muted)' }}>
        No valuation data available.
      </div>
    );
  }

  const { upsidePct, table = [] } = valuationData;

  // If table is empty
  if (!table || table.length === 0) {
    return (
      <div style={{ padding: '1rem', color: 'var(--muted)' }}>
        No valuation metrics available.
      </div>
    );
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
                <td style={{ color: 'var(--muted)' }}>
                  {row.note || ''}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
};

export default Valuation;
