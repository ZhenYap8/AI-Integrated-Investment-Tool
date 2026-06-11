import React from "react";

export default function Badge({ children, tone = 'gray' }) {
  return <span className={`badge ${tone}`}>{children}</span>;
}
