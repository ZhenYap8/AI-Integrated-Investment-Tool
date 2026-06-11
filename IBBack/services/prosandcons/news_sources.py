"""
Multi-source financial news aggregation for AI context.

Sources (no API key required):
  - Yahoo Finance (via yfinance)
  - Google News RSS (general + tier-1 financial press)

Optional (set NEWS_API_KEY in .env):
  - NewsAPI.org (Reuters, BBC, Bloomberg*, etc.)

*Availability depends on NewsAPI plan.
"""
from __future__ import annotations

import datetime as dt
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from urllib.parse import quote, urlparse

try:
    import requests
except Exception:
    requests = None

try:
    import trafilatura
except Exception:
    trafilatura = None

from .config import NEWS_API_KEY, NEWS_ABSTRACT_LIMIT, NEWS_TOTAL_LIMIT

# Known outlet labels by domain fragment
OUTLET_BY_DOMAIN: Dict[str, str] = {
    "reuters.com": "Reuters",
    "ft.com": "Financial Times",
    "bloomberg.com": "Bloomberg",
    "bbc.co.uk": "BBC",
    "bbc.com": "BBC",
    "cnbc.com": "CNBC",
    "wsj.com": "Wall Street Journal",
    "finance.yahoo.com": "Yahoo Finance",
    "yahoo.com": "Yahoo Finance",
    "marketwatch.com": "MarketWatch",
    "barrons.com": "Barron's",
    "investing.com": "Investing.com",
    "seekingalpha.com": "Seeking Alpha",
    "fool.com": "Motley Fool",
    "theguardian.com": "The Guardian",
    "nytimes.com": "New York Times",
    "apnews.com": "AP News",
    "businessinsider.com": "Business Insider",
    "forbes.com": "Forbes",
    "thestreet.com": "The Street",
    "techcrunch.com": "TechCrunch",
}

TIER1_SITE_QUERY = (
    "site:reuters.com OR site:ft.com OR site:bloomberg.com OR site:bbc.com "
    "OR site:bbc.co.uk OR site:cnbc.com OR site:wsj.com OR site:apnews.com"
)

_USER_AGENT = (
    "Mozilla/5.0 (compatible; InvestmentAgent/1.0; +https://github.com/local)"
)
_ABSTRACT_MAX = 600


@dataclass
class NewsArticle:
    title: str
    url: str
    date: str = ""
    outlet: str = "Unknown"
    feed: str = "unknown"
    snippet: str = ""

    def normalized_title(self) -> str:
        t = re.sub(r"\s+", " ", (self.title or "").lower()).strip()
        return re.sub(r"[^a-z0-9 ]", "", t)


def _outlet_from_url(url: str, fallback: str = "Unknown") -> str:
    try:
        host = urlparse(url).netloc.lower().replace("www.", "")
        for fragment, label in OUTLET_BY_DOMAIN.items():
            if fragment in host:
                return label
        return host.split(".")[0].capitalize() if host else fallback
    except Exception:
        return fallback


def _fetch_abstract(url: str, title: str = "") -> str:
    if not url or "news.google.com" in url:
        return title[:_ABSTRACT_MAX] if title else "(headline only — open link for full article)"
    if trafilatura is None:
        return title[:_ABSTRACT_MAX] if title else "(abstract unavailable)"
    try:
        if requests:
            resp = requests.get(
                url, timeout=8, headers={"User-Agent": _USER_AGENT},
                allow_redirects=True,
            )
            if resp.ok and resp.text:
                text = trafilatura.extract(resp.text, include_comments=False, include_formatting=False) or ""
                text = re.sub(r"\s+", " ", text).strip()
                if len(text) > 80:
                    return text[:_ABSTRACT_MAX]
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            text = trafilatura.extract(downloaded, include_comments=False, include_formatting=False) or ""
            text = re.sub(r"\s+", " ", text).strip()
            if text:
                return text[:_ABSTRACT_MAX]
    except Exception:
        pass
    return title[:_ABSTRACT_MAX] if title else "(abstract unavailable)"


def _parse_rss(xml_bytes: bytes, feed_name: str, default_outlet: str = "") -> List[NewsArticle]:
    articles: List[NewsArticle] = []
    if not xml_bytes:
        return articles
    try:
        root = ET.fromstring(xml_bytes)
        for item in root.findall(".//item"):
            title_el = item.find("title")
            link_el = item.find("link")
            pub_el = item.find("pubDate")
            source_el = item.find("source")

            title = (title_el.text or "").strip() if title_el is not None else ""
            url = (link_el.text or "").strip() if link_el is not None else ""
            if not title or not url:
                continue

            outlet = default_outlet
            if source_el is not None and source_el.text:
                outlet = source_el.text.strip()
            elif source_el is not None and source_el.get("url"):
                outlet = _outlet_from_url(source_el.get("url"), outlet or "Unknown")

            date_str = ""
            if pub_el is not None and pub_el.text:
                try:
                    from email.utils import parsedate_to_datetime
                    date_str = parsedate_to_datetime(pub_el.text).date().isoformat()
                except Exception:
                    date_str = dt.date.today().isoformat()

            articles.append(NewsArticle(
                title=title[:220],
                url=url,
                date=date_str or dt.date.today().isoformat(),
                outlet=outlet or _outlet_from_url(url),
                feed=feed_name,
            ))
    except Exception:
        pass
    return articles


def _google_news_rss(query: str, feed_name: str, limit: int = 8) -> List[NewsArticle]:
    if requests is None:
        return []
    try:
        url = f"https://news.google.com/rss/search?q={quote(query)}&hl=en-US&gl=US&ceid=US:en"
        resp = requests.get(url, timeout=12, headers={"User-Agent": _USER_AGENT})
        resp.raise_for_status()
        items = _parse_rss(resp.content, feed_name)
        return items[:limit]
    except Exception:
        return []


def fetch_yahoo_news(ticker_obj, limit: int = 6) -> List[NewsArticle]:
    articles: List[NewsArticle] = []
    news = getattr(ticker_obj, "news", None) or []
    for n in news[:limit]:
        title = (n.get("title") or "")[:220]
        url = n.get("link") or ""
        if not title or not url:
            continue
        ts = n.get("providerPublishTime")
        date_str = dt.datetime.utcfromtimestamp(ts).date().isoformat() if ts else dt.date.today().isoformat()
        publisher = n.get("publisher") or _outlet_from_url(url, "Yahoo Finance")
        articles.append(NewsArticle(
            title=title,
            url=url,
            date=date_str,
            outlet=publisher,
            feed="yahoo",
        ))
    return articles


def fetch_newsapi(query: str, limit: int = 8) -> List[NewsArticle]:
    if not NEWS_API_KEY or requests is None:
        return []
    try:
        resp = requests.get(
            "https://newsapi.org/v2/everything",
            params={
                "q": query,
                "language": "en",
                "sortBy": "publishedAt",
                "pageSize": min(limit, 20),
                "apiKey": NEWS_API_KEY,
            },
            timeout=12,
        )
        resp.raise_for_status()
        data = resp.json()
        articles: List[NewsArticle] = []
        for item in data.get("articles") or []:
            title = (item.get("title") or "")[:220]
            url = item.get("url") or ""
            if not title or not url:
                continue
            pub = (item.get("publishedAt") or "")[:10]
            source_name = (item.get("source") or {}).get("name") or _outlet_from_url(url)
            desc = (item.get("description") or "")[:_ABSTRACT_MAX]
            articles.append(NewsArticle(
                title=title,
                url=url,
                date=pub or dt.date.today().isoformat(),
                outlet=source_name,
                feed="newsapi",
                snippet=desc,
            ))
        return articles[:limit]
    except Exception:
        return []


def _dedupe_and_rank(articles: List[NewsArticle], limit: int) -> List[NewsArticle]:
    seen_titles: Set[str] = set()
    seen_urls: Set[str] = set()
    outlet_counts: Dict[str, int] = {}
    result: List[NewsArticle] = []

    # Pass 1: prefer tier-1 outlets, diverse sources
    tier1_keywords = {"reuters", "bloomberg", "financial times", "bbc", "cnbc", "wall street journal", "ap news"}

    def sort_key(a: NewsArticle):
        outlet_l = a.outlet.lower()
        tier = 0 if any(k in outlet_l for k in tier1_keywords) else 1
        feed_rank = {"tier1": 0, "newsapi": 1, "yahoo": 2, "google": 3}.get(a.feed, 4)
        return (tier, feed_rank)

    sorted_articles = sorted(articles, key=sort_key)

    for a in sorted_articles:
        nt = a.normalized_title()
        if nt in seen_titles or a.url in seen_urls:
            continue
        if outlet_counts.get(a.outlet, 0) >= 3:
            continue
        seen_titles.add(nt)
        seen_urls.add(a.url)
        outlet_counts[a.outlet] = outlet_counts.get(a.outlet, 0) + 1
        result.append(a)
        if len(result) >= limit:
            break
    return result


def aggregate_news(
    ticker: str,
    company_name: str,
    ticker_obj=None,
    *,
    total_limit: Optional[int] = None,
    abstract_limit: Optional[int] = None,
) -> List[NewsArticle]:
    """
    Aggregate news from Yahoo, Google News (incl. FT/Reuters/Bloomberg/BBC via site search),
    and optional NewsAPI.
    """
    total_limit = total_limit or NEWS_TOTAL_LIMIT
    abstract_limit = abstract_limit or NEWS_ABSTRACT_LIMIT

    name = company_name or ticker
    query_base = f'"{name}" OR {ticker} stock'
    tier1_query = f"{name} {ticker} ({TIER1_SITE_QUERY})"

    collected: List[NewsArticle] = []

    if ticker_obj is not None:
        collected.extend(fetch_yahoo_news(ticker_obj, limit=8))

    collected.extend(_google_news_rss(tier1_query, "tier1", limit=10))
    collected.extend(_google_news_rss(query_base, "google", limit=8))
    collected.extend(fetch_newsapi(f"{name} {ticker}", limit=6))

    ranked = _dedupe_and_rank(collected, total_limit)

    for i, article in enumerate(ranked):
        if i < abstract_limit and not article.snippet:
            article.snippet = _fetch_abstract(article.url, article.title)

    return ranked


def format_news_for_context(articles: List[NewsArticle]) -> List[str]:
    """Format articles as context lines for the LLM."""
    lines: List[str] = []
    if not articles:
        return lines

    outlets = sorted({a.outlet for a in articles if a.outlet})
    lines.append(f"News sources in context: {', '.join(outlets[:12])}")

    lines.append("Recent headlines (multi-source):")
    for a in articles:
        lines.append(f"- [{a.outlet}] {a.date} | {a.title} | {a.url}")

    lines.append("News abstracts (use these URLs as evidence):")
    for a in articles:
        snippet = a.snippet or a.title
        lines.append(
            f"- [{a.outlet}] {a.title}\n"
            f"  URL: {a.url}\n"
            f"  Date: {a.date}\n"
            f"  Abstract: {snippet[:_ABSTRACT_MAX]}"
        )
    return lines


__all__ = [
    "NewsArticle",
    "aggregate_news",
    "fetch_yahoo_news",
    "format_news_for_context",
]
