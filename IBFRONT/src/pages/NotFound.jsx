// src/pages/NotFound.jsx
import React from "react";
import { Link } from "react-router-dom";
import EmptyState from "../components/EmptyState.jsx";

export default function NotFound() {
  return (
    <EmptyState
      title="Page not found"
      text="The page you are looking for does not exist."
      action={<Link to="/" className="btn-range">Go home</Link>}
    />
  );
}
