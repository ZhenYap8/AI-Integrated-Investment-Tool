import React from 'react';

function fmtCurrency(v) {
  if (v == null || isNaN(v)) return '—';
  try { 
    return new Intl.NumberFormat(undefined, { 
      style: 'currency', 
      currency: 'USD', 
      maximumFractionDigits: 2 
    }).format(v); 
  } catch { 
    return `$${Number(v).toFixed(2)}`; 
  }
}

const ValuationKPIs = ({ valuation }) => {
  if (!valuation) return null;

  return (
    <div className="kpis" style={{ marginTop: 12 }}>
      <div className="kpi">
        <div className="label">Current Price</div>
        <div className="value">{fmtCurrency(valuation?.currentPrice)}</div>
      </div>
      <div className="kpi">
        <div className="label">Fair Value (est.)</div>
        <div className="value">{fmtCurrency(valuation?.fairValue)}</div>
      </div>
    </div>
  );
};

export default ValuationKPIs;
