import React from 'react';

const AnalysisResults = ({ data, loading, error }) => {
  if (loading) {
    return (
      <div className="text-center py-8">
        <div className="loading-spin mx-auto mb-4" />
        <p className="text-gray-600">Analyzing financial data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">Error: {error}</p>
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="stack-lg">
      {/* Scorecard */}
      <section>
        <h2 className="section-title">Financial Scorecard</h2>
        <div className="score-grid">
          {data.scorecard?.map((item, i) => (
            <div key={i} className="score-card">
              <div className="score-head">
                <span>{item.label}</span>
                <span className={`pill ${item.verdict}`}>
                  {item.verdict}
                </span>
              </div>
              <p className="text-sm text-gray-600 mt-2">{item.detail}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Pros/Cons */}
      <section>
        <h2 className="section-title">Investment Thesis</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h3 className="font-semibold text-green-700 mb-3">Pros</h3>
            <ul className="space-y-2">
              {data.pros?.map((item, i) => (
                <li key={i} className="flex items-start gap-2">
                  <span className="text-green-500 mt-1">+</span>
                  <span className="text-sm">{item.text}</span>
                </li>
              ))}
            </ul>
          </div>
          
          <div>
            <h3 className="font-semibold text-red-700 mb-3">Cons</h3>
            <ul className="space-y-2">
              {data.cons?.map((item, i) => (
                <li key={i} className="flex items-start gap-2">
                  <span className="text-red-500 mt-1">-</span>
                  <span className="text-sm">{item.text}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </section>

      {/* Risks */}
      <section>
        <h2 className="section-title">Key Risks</h2>
        <ul className="space-y-2">
          {data.risks?.map((item, i) => (
            <li key={i} className="flex items-start gap-2">
              <span className="text-amber-500 mt-1">⚠</span>
              <span className="text-sm">{item.text}</span>
            </li>
          ))}
        </ul>
      </section>

      {/* Sources */}
      {data.sources?.length > 0 && (
        <section>
          <h2 className="section-title">Sources</h2>
          <div className="text-sm space-y-1">
            {data.sources.map((source, i) => (
              <div key={i}>
                <a 
                  href={source.url} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:underline"
                >
                  {source.title}
                </a>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
};

export default AnalysisResults;