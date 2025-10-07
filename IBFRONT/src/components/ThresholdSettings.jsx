import React from 'react';

const ThresholdSettings = ({ 
  thresholds, 
  setThresholds, 
  onApply, 
  onReset 
}) => {
  const handleChange = (key, value) => {
    setThresholds(prev => ({
      ...prev,
      [key]: parseFloat(value) || 0
    }));
  };

  return (
    <div className="thresh-grid">
      <div className="field">
        <label className="field-label">
          Revenue Growth <span className="muted">(CAGR)</span>
        </label>
        <div className="field-input">
          <input
            type="number"
            step="0.01"
            min="0"
            max="1"
            value={thresholds.rev_cagr_min}
            onChange={(e) => handleChange('rev_cagr_min', e.target.value)}
          />
          <div className="adorn">%</div>
        </div>
      </div>

      <div className="field">
        <label className="field-label">
          Operating Margin <span className="muted">(min)</span>
        </label>
        <div className="field-input">
          <input
            type="number"
            step="0.01"
            min="0"
            max="1"
            value={thresholds.op_margin_min}
            onChange={(e) => handleChange('op_margin_min', e.target.value)}
          />
          <div className="adorn">%</div>
        </div>
      </div>

      <div className="field">
        <label className="field-label">
          Net Debt/Equity <span className="muted">(max)</span>
        </label>
        <div className="field-input">
          <input
            type="number"
            step="0.1"
            min="0"
            max="10"
            value={thresholds.nd_eq_max}
            onChange={(e) => handleChange('nd_eq_max', e.target.value)}
          />
          <div className="adorn">x</div>
        </div>
      </div>

      <div className="field">
        <label className="field-label">
          Interest Coverage <span className="muted">(min)</span>
        </label>
        <div className="field-input">
          <input
            type="number"
            step="0.1"
            min="0"
            max="50"
            value={thresholds.interest_cover_min}
            onChange={(e) => handleChange('interest_cover_min', e.target.value)}
          />
          <div className="adorn">x</div>
        </div>
      </div>

      <div className="field">
        <label className="field-label">
          ROE <span className="muted">(min)</span>
        </label>
        <div className="field-input">
          <input
            type="number"
            step="0.01"
            min="0"
            max="1"
            value={thresholds.roe_min}
            onChange={(e) => handleChange('roe_min', e.target.value)}
          />
          <div className="adorn">%</div>
        </div>
      </div>

      <div className="thresh-actions">
        <button
          className="px-3 py-2 rounded-lg bg-blue-600 text-white text-sm font-medium hover:bg-blue-700"
          onClick={onApply}
        >
          Apply
        </button>
        <button
          className="px-3 py-2 rounded-lg border border-gray-300 text-gray-700 text-sm font-medium hover:bg-gray-50"
          onClick={onReset}
        >
          Reset
        </button>
      </div>
    </div>
  );
};

export default ThresholdSettings;