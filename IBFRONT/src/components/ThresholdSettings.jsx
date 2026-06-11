import React from 'react';
import Card from './Card.jsx';
import NumField from './NumField.jsx';

const DEFAULT_THRESH = { rev_cagr_min: 5, op_margin_min: 10, nd_eq_max: 1.0, interest_cover_min: 4.0, roe_min: 10 };

const ThresholdSettings = ({ thresholds, setThresholds, onApply, onReset, loading = false, query = '' }) => {
  return (
    <Card>
      <h3 className="section-title">Thresholds</h3>
      <p className="text-sm text-slate-500 mb-4">
        Configure thresholds that will be used for scorecard evaluation.
      </p>
      <div className="thresh-grid">
        <NumField label="Revenue CAGR min" value={thresholds.rev_cagr_min} onChange={(v)=>setThresholds(t=>({...t, rev_cagr_min:v}))} suffix="%" hint="1-10y" />
        <NumField label="Operating margin min" value={thresholds.op_margin_min} onChange={(v)=>setThresholds(t=>({...t, op_margin_min:v}))} suffix="%" />
        <NumField label="Net debt / Equity max" value={thresholds.nd_eq_max} onChange={(v)=>setThresholds(t=>({...t, nd_eq_max:v}))} suffix="x" />
        <NumField label="Interest coverage min" value={thresholds.interest_cover_min} onChange={(v)=>setThresholds(t=>({...t, interest_cover_min:v}))} suffix="x" />
        <NumField label="ROE min" value={thresholds.roe_min} onChange={(v)=>setThresholds(t=>({...t, roe_min:v}))} suffix="%" />
      </div>
      <div className="thresh-actions" style={{ marginTop: 8 }}>
        <button className="btn-range" onClick={onApply} disabled={loading || !query}>Apply Thresholds</button>
        <button
          className="btn-range"
          onClick={() => {
            if (typeof setThresholds === 'function') {
              setThresholds(DEFAULT_THRESH);
            }
            if (typeof onReset === 'function') {
              try { onReset(); } catch (e) { /* ignore onReset errors */ }
            }
          }}
          style={{ marginLeft: 8 }}
        >
          Reset
        </button>
      </div>
    </Card>
  );
};

export default ThresholdSettings;