import React from 'react';
import Card from '../../components/Card.jsx';
import SearchBar from '../../components/SearchBar.jsx';
import ThresholdSettings from '../../components/ThresholdSettings.jsx';

export default function PreAnalyzer({
  query, setQuery, runAnalyze, suggestions = [], showSuggest, setShowSuggest, loading = false, onPickSuggestion,
  period, onPeriodChange, HISTORY_PRESETS = [],
  thresholds, setThresholds, onApply, onReset
}) {
  const periodLabel = (p) => (p === 'max' ? 'All' : (p || '').toUpperCase());

  return (
    <div className="stack-lg">
      <Card>
        <h2 className="section-title">Analyze Companies or Industries</h2>
        <p className="sub" style={{ marginBottom: 12 }}>
          US, European, Asian &amp; Canadian listings supported — search by ticker or name.
        </p>
        <SearchBar
          value={query}
          onChange={setQuery}
          onSubmit={() => runAnalyze()}
          suggestions={suggestions}
          showSuggest={showSuggest}
          setShowSuggest={setShowSuggest}
          loading={loading}
          onPickSuggestion={onPickSuggestion}
        />
        <div style={{ marginTop: 8 }}>
          <span className="sub" style={{ display: 'block', marginBottom: 6 }}>
            History window — 6M/1Y use quarterly ROE; 3Y+ use annual filings
          </span>
          <div className="segmented">
            {HISTORY_PRESETS.map(p => (
              <button
                key={p}
                className={`btn-range ${period === p ? 'active' : ''}`}
                aria-pressed={period === p}
                onClick={() => onPeriodChange(p)}
                disabled={loading}
              >{periodLabel(p)}</button>
            ))}
            <button className="btn-range" onClick={() => runAnalyze()} disabled={loading || !query}>Run</button>
          </div>
        </div>
      </Card>

      <ThresholdSettings
        thresholds={thresholds}
        setThresholds={setThresholds}
        onApply={onApply}
        onReset={onReset}
        loading={loading}
        query={query}
      />
    </div>
  );
}
