// src/components/Card.jsx
import React from "react";
export default function Card(props) {
  const { className, children, ...rest } = props;
  return (
    <div className={`card ${className || ''}`} {...rest}>
      {children}
    </div>
  );
}
