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

function Logo() {
  return <div className="h-6 w-6 rounded-md bg-gradient-to-br from-blue-500 to-indigo-600 grid place-items-center text-white text-[10px] font-bold">LOGO</div>;
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
              <Logo />
              <Link to="/" className="brand">Sudut Invest</Link>
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
            <span>© {new Date().getFullYear()} Sudut Invest</span>
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
