const SESSION_KEY = 'analyzer-session';

export function loadAnalyzerSession() {
  try {
    const raw = sessionStorage.getItem(SESSION_KEY);
    if (!raw) return null;
    const data = JSON.parse(raw);
    if (!data || typeof data !== 'object') return null;
    return data;
  } catch {
    return null;
  }
}

export function saveAnalyzerSession(session) {
  try {
    sessionStorage.setItem(SESSION_KEY, JSON.stringify({
      ...session,
      savedAt: Date.now(),
    }));
  } catch {
    // ignore quota / private mode
  }
}

export function clearAnalyzerSession() {
  try {
    sessionStorage.removeItem(SESSION_KEY);
  } catch {}
}

/** True when cached results match the requested ticker + period */
export function sessionMatches(session, query, period) {
  if (!session?.resp || !query) return false;
  const q = String(query).trim().toUpperCase();
  const cachedQ = String(session.query || '').trim().toUpperCase();
  const ticker = String(session.resp?.meta?.ticker || '').trim().toUpperCase();
  const sameQuery = cachedQ === q || ticker === q;
  const samePeriod = (session.period || '5y') === (period || '5y');
  return sameQuery && samePeriod;
}
