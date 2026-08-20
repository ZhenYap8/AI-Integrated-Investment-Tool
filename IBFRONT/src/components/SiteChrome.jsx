import React, { useEffect, useState } from 'react';
import { Link, NavLink, useLocation } from 'react-router-dom';
import '../styles/theme.css';

function Nav({ to, children }) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}
    >
      {children}
    </NavLink>
  );
}

function useDarkMode() {
  const [dark, setDark] = useState(
    () => typeof window !== 'undefined'
      && window.matchMedia
      && window.matchMedia('(prefers-color-scheme: dark)').matches,
  );
  useEffect(() => {
    document.documentElement.classList.toggle('dark-mode', dark);
  }, [dark]);
  return [dark, setDark];
}

function usePageTitle(location) {
  useEffect(() => {
    const map = {
      '/': 'Sudut Invest',
      '/analyze': 'Analyse · Sudut Invest',
      '/screen': 'Screener · Sudut Invest',
      '/about': 'About · Sudut Invest',
      '/docs': 'Docs · Sudut Invest',
      '/disclaimer': 'Disclaimer · Sudut Invest',
    };
    document.title = map[location.pathname] || 'Sudut Invest';
  }, [location]);
}

function Logo({ src = '/sudutinvest.png', alt = 'Sudut Invest' }) {
  const fallback = <div className="brand-mark" aria-hidden="true">SI</div>;

  if (!src) return fallback;

  return (
    <img
      src={src}
      alt={alt}
      width={36}
      height={36}
      loading="lazy"
      className="site-logo"
      onError={(e) => { e.currentTarget.replaceWith(fallback); }}
    />
  );
}

export default function SiteChrome({ children }) {
  const [dark, setDark] = useDarkMode();
  const location = useLocation();
  usePageTitle(location);

  return (
    <div className={dark ? 'dark-mode' : ''}>
      <div className="layout">
        <nav className="navbar" aria-label="Main">
          <div className="navbar-content">
            <div className="navbar-left">
              <Link to="/" className="brand-link" aria-label="Sudut Invest home">
                <Logo />
                <span className="brand">Sudut Invest</span>
              </Link>
            </div>
            <div className="navbar-right">
              <Nav to="/analyze">Analyse</Nav>
              <Nav to="/screen">Screener</Nav>
              <Nav to="/docs">Docs</Nav>
              <Nav to="/about">About</Nav>
              <button
                type="button"
                onClick={() => setDark(!dark)}
                className="toggle-theme"
                aria-label={dark ? 'Switch to light mode' : 'Switch to dark mode'}
              >
                {dark ? 'Light' : 'Dark'}
              </button>
            </div>
          </div>
        </nav>

        <main className="main-content">{children}</main>

        <footer className="footer">
          <div className="footer-content">
            <span className="footer-brand">© {new Date().getFullYear()} Sudut Invest</span>
            <div className="footer-links">
              <Link to="/disclaimer">Disclaimer</Link>
              <span aria-hidden="true"> · </span>
              <Link to="/docs">Documentation</Link>
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
}
