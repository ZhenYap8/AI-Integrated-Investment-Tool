import React from 'react';
import ScoreItem from './ScoreItem';

/**
 * Scorecard Component
 * Displays scorecard items with verdicts from the API response.
 */
const Scorecard = ({ 
  scorecard = null,
  loading = false,
  years = 5
}) => {
  // If loading or no scorecard, show skeleton
  if (loading || !scorecard || scorecard.length === 0) {
    const skeletonItems = [
      { id: 'rev_cagr', label: `Revenue CAGR (${years}y)`, verdict: 'loading', detail: 'No data' },
      { id: 'op_margin', label: 'Operating Margin', verdict: 'loading', detail: 'No data' },
      { id: 'nd_eq', label: 'Net Debt / Equity', verdict: 'loading', detail: 'No data' },
      { id: 'interest_cover', label: 'Interest Coverage', verdict: 'loading', detail: 'No data' },
      { id: 'roe', label: 'Return on Equity (ROE)', verdict: 'loading', detail: 'No data' }
    ];
    
    return (
      <div className="score-grid">
        {skeletonItems.map((item) => (
          <ScoreItem key={item.id} {...item} loading={true} />
        ))}
      </div>
    );
  }

  // Display scorecard items from API
  return (
    <div className="score-grid">
      {scorecard.map((item) => (
        <ScoreItem 
          key={item.id} 
          label={item.label} 
          verdict={item.verdict}
          detail={item.detail}
          value={item.value} 
          threshold={item.threshold} 
          unit={item.unit}
          loading={false}
        />
      ))}
    </div>
  );
};

export default Scorecard;
