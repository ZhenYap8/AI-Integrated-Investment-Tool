// src/components/SiteChrome.jsx
import React, { useEffect, useState } from "react";
import { Link, NavLink, useLocation } from "react-router-dom";
import "../styles/theme.css";

function Nav({ to, children }) {
  return (
    <NavLink to={to} className={({ isActive }) => (isActive ? "nav-link active" : "nav-link")}>{children}</NavLink>
  );
}

function useDarkMode() {
  const [dark, setDark] = useState(() => (typeof window !== 'undefined' && window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches));
  useEffect(() => { document.documentElement.classList.toggle("dark-mode", dark); }, [dark]);
  return [dark, setDark];
}

function usePageTitle(location) {
  useEffect(() => {
    const map = {
      "/": "Sudut Invest",
      "/analyze": "Analyse • Sudut Invest",
      "/about": "About •  Sudut Invest",
      "/docs": "Docs • Sudut Invest",
      "/disclaimer": "Disclaimer • Sudut Invest",
    };
    document.title = map[location.pathname] || "Sudut Invest";
  }, [location]);
}

function Logo({ src = "/sudutinvest.png", alt = "Sudut Invest", size = 100 }) { // increased default size from 24 to 40
  const fallback = (
    <div
      className="rounded-md bg-gradient-to-br from-blue-500 to-indigo-600 grid place-items-center text-white font-bold select-none"
      style={{ width: size, height: size, fontSize: Math.max(12, size * 0.34) }}
      aria-label={alt}
    >
      SI
    </div>
  );
  if (!src) return fallback;
  return (
    <img
      src={src}
      alt={alt}
      width={size}
      height={size}
      loading="lazy"
      onError={(e) => { e.currentTarget.replaceWith(fallback); }}
      style={{ width: size, height: size, objectFit: 'contain', display: 'block' }}
    />
  );
}

export default function SiteChrome({ children }) {
  const [dark, setDark] = useDarkMode();
  const location = useLocation();
  usePageTitle(location);

  return (
    <div className={dark ? "dark-mode" : ""}>
      <div className="layout">
        <nav className="navbar">
          <div className="navbar-content">
            <div className="navbar-left">
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Logo />
                <Link to="/" className="brand" style={{ margin: 0, lineHeight: 1 }}>Sudut Invest</Link>
              </div>
            </div>
            <div className="navbar-right">
              <Nav to="/analyze">Analyse</Nav>
              <Nav to="/docs">Docs</Nav>
              <Nav to="/about">About</Nav>
              <Nav to="/disclaimer">Disclaimer</Nav>
              <button onClick={() => setDark(!dark)} className="toggle-theme">{dark ? "Light" : "Dark"}</button>
            </div>
          </div>
        </nav>

        <main className="main-content">{children}</main>

        <footer className="footer">
          <div className="footer-content">
            <span style={{ fontSize: '12px', fontWeight: 600, letterSpacing: '0.3px' }}>© {new Date().getFullYear()} Sudut Invest</span>
            <div className="footer-links">
              <Link to="/disclaimer">Not investment advice</Link>
              <a href="#sources">Sources</a>
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
}
