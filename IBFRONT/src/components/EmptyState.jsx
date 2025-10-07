// src/components/EmptyState.jsx
import React from "react";
import Card from "./Card.jsx";

export default function EmptyState({ title = "Nothing here", text = "", action }) {
  return (
    <Card>
      <div className="empty">
        <h3 className="section-title" style={{ marginBottom: 6 }}>{title}</h3>
        {text && <p className="sub">{text}</p>}
        {action}
      </div>
    </Card>
  );
}
