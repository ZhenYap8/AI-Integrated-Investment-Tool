// ...new file...
// filepath: /Users/zhenweiyap/Documents/Github/AI-Integrated-Investment-Tool/IBFRONT/src/features/FuzzySearchFixing.jsx
// FuzzySearchFixing: provides a small React hook and helper for fuzzy searching ticker lists using Fuse.js

import React, { useEffect, useRef, useState } from 'react';
import Fuse from 'fuse.js';

// NOTE: install fuse.js in the frontend repo: `npm install fuse.js`

/**
 * useFuzzySearch hook
 * @param {Array<Object>} list - array of items (e.g., GLOBAL_TICKERS entries {label, value, ...})
 * @param {Object} opts - optional Fuse.js options and behavior overrides
 * @returns {Object} { query, setQuery, results, search, fuseRef, init }
 */
export function useFuzzySearch(list = [], opts = {}) {
  const {
    keys = ['label', 'value'],
    threshold = 0.35,
    limit = 50,
    ignoreLocation = true,
  } = opts;

  const [query, setQuery] = useState('');
  const [results, setResults] = useState(list || []);
  const fuseRef = useRef(null);

  // initialize or re-init Fuse when list or options change
  useEffect(() => {
    if (Array.isArray(list) && list.length > 0) {
      try {
        fuseRef.current = new Fuse(list, {
          keys,
          threshold,
          ignoreLocation,
          includeScore: true,
        });
        setResults(list.slice(0, limit));
      } catch (e) {
        // fallback: clear fuse and use raw list
        fuseRef.current = null;
        setResults(list.slice(0, limit));
      }
    } else {
      fuseRef.current = null;
      setResults([]);
    }
  }, [list, keys, threshold, limit, ignoreLocation]);

  // perform search whenever query changes
  useEffect(() => {
    const q = (query || '').trim();
    if (!q) {
      setResults(list ? list.slice(0, limit) : []);
      return;
    }

    if (fuseRef.current) {
      try {
        const r = fuseRef.current.search(q, { limit });
        setResults(r.map(rr => rr.item));
        return;
      } catch (e) {
        // fall through to naive filter
      }
    }

    // naive fallback filter
    const low = q.toLowerCase();
    const filtered = (list || []).filter(it => {
      try {
        return (
          (it.label && String(it.label).toLowerCase().includes(low)) ||
          (it.value && String(it.value).toLowerCase().includes(low))
        );
      } catch { return false; }
    }).slice(0, limit);

    setResults(filtered);
  }, [query, list, limit]);

  const search = (q) => setQuery(q || '');

  return { query, setQuery, results, search, fuseRef };
}

/**
 * Non-React fuzzy filter helper for ad-hoc usage
 * @param {Array<Object>} list
 * @param {string} term
 * @param {Object} options
 * @returns {Array<Object>}
 */
export function fuzzyFilter(list = [], term = '', options = {}) {
  const { keys = ['label', 'value'], threshold = 0.35, limit = 50 } = options;
  if (!term) return list.slice(0, limit);
  try {
    const fuse = new Fuse(list, { keys, threshold, includeScore: true, ignoreLocation: true });
    const r = fuse.search(term, { limit });
    return r.map(rr => rr.item);
  } catch (e) {
    const low = term.toLowerCase();
    return (list || []).filter(it => {
      try {
        return (
          (it.label && String(it.label).toLowerCase().includes(low)) ||
          (it.value && String(it.value).toLowerCase().includes(low))
        );
      } catch { return false; }
    }).slice(0, limit);
  }
}

export default useFuzzySearch;
