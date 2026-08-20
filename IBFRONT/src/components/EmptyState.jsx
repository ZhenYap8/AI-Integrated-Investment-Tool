import React from 'react';
import Card from './Card.jsx';

export default function EmptyState({ title = 'Nothing here', text = '', action }) {
  return (
    <Card>
      <div className="empty-state">
        <h3 className="section-title">{title}</h3>
        {text && <p className="sub">{text}</p>}
        {action && <div className="empty-state-action">{action}</div>}
      </div>
    </Card>
  );
}
