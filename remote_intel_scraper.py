"""
Live remote-job market signals from public APIs (no API keys).
Sources: Remotive, RemoteOK, Hacker News (Algolia), Reddit r/remotework.
"""

from __future__ import annotations

import re
import time
from collections import Counter
from datetime import datetime, timezone
from typing import Any
from xml.etree import ElementTree as ET

import requests

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": USER_AGENT,
    "Accept": "application/json, text/xml, application/rss+xml, */*",
})


def _get(url: str, timeout: int = 18) -> requests.Response | None:
    try:
        r = SESSION.get(url, timeout=timeout)
        r.raise_for_status()
        return r
    except requests.RequestException:
        return None


def fetch_remotive_categories(max_jobs: int = 120) -> list[tuple[str, int]]:
    """Job counts by category from Remotive public API."""
    r = _get("https://remotive.com/api/remote-jobs")
    if not r:
        return []
    try:
        data = r.json()
    except Exception:
        return []
    jobs = data.get("jobs") or []
    cats = [j.get("category") or "Other" for j in jobs[:max_jobs]]
    counts = Counter(cats)
    return counts.most_common(15)


def fetch_remoteok_tags(max_jobs: int = 80) -> list[tuple[str, int]]:
    """Skill/tag frequency from RemoteOK public API."""
    r = _get("https://remoteok.com/api")
    if not r:
        return []
    try:
        rows = r.json()
    except Exception:
        return []
    if not isinstance(rows, list):
        return []
    tags: list[str] = []
    n = 0
    for row in rows:
        if not isinstance(row, dict) or "position" not in row:
            continue
        if n >= max_jobs:
            break
        n += 1
        t = row.get("tags")
        if isinstance(t, str):
            for part in re.split(r"[,;]", t):
                p = part.strip().lower()
                if 2 <= len(p) <= 40:
                    tags.append(p)
        elif isinstance(t, list):
            for p in t:
                if isinstance(p, str) and 2 <= len(p) <= 40:
                    tags.append(p.strip().lower())
    return Counter(tags).most_common(20)


def fetch_hn_remote_stories(limit: int = 10) -> list[dict[str, str]]:
    """Recent Hacker News stories matching remote work."""
    url = (
        "https://hn.algolia.com/api/v1/search?tags=story&query=remote+work+OR+remote+job"
        f"&hitsPerPage={limit}"
    )
    r = _get(url)
    if not r:
        return []
    try:
        hits = r.json().get("hits") or []
    except Exception:
        return []
    out = []
    for h in hits:
        title = h.get("title") or h.get("story_title") or ""
        oid = h.get("objectID") or h.get("story_id")
        if not title or len(title) < 15:
            continue
        link = f"https://news.ycombinator.com/item?id={oid}" if oid else ""
        out.append({"title": title[:200], "url": link})
    return out[:limit]


def fetch_reddit_remotework(limit: int = 8) -> list[dict[str, str]]:
    """Hot posts from r/remotework (public JSON)."""
    for base in (
        "https://www.reddit.com/r/remotework/hot.json?limit=15",
        "https://old.reddit.com/r/remotework/hot.json?limit=15",
    ):
        r = _get(base, timeout=20)
        if r:
            break
    else:
        return []
    try:
        data = r.json()
    except Exception:
        return []
    out = []
    for c in (data.get("data") or {}).get("children") or []:
        p = (c.get("data") or {})
        title = p.get("title") or ""
        if not title or title.startswith("[") and "]" in title[:4]:
            continue
        url = "https://reddit.com" + (p.get("permalink") or "")
        out.append({"title": title[:220], "url": url})
        if len(out) >= limit:
            break
    return out


def fetch_remote_work_rss_headlines(limit: int = 6) -> list[dict[str, str]]:
    """Google News RSS for 'remote jobs' (lightweight headlines)."""
    q = "remote+jobs+worldwide"
    url = f"https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en"
    r = _get(url, timeout=15)
    if not r:
        return []
    try:
        root = ET.fromstring(r.content)
    except ET.ParseError:
        return []
    out = []
    for it in root.findall(".//item"):
        title_el = it.find("title")
        link_el = it.find("link")
        title = (title_el.text or "").strip() if title_el is not None else ""
        href = (link_el.text or "").strip() if link_el is not None else ""
        if len(title) < 12 or title.lower().startswith("google news"):
            continue
        out.append({"title": title[:240], "url": href or "#"})
        if len(out) >= limit:
            break
    return out


def fetch_remote_intel() -> dict[str, Any]:
    """
    Aggregate live signals. Returns keys: ok, fetched_at, categories, tags,
    hn_stories, reddit_posts, news_headlines, errors (list of str).
    """
    errors: list[str] = []
    out: dict[str, Any] = {
        "ok": True,
        "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "categories": [],
        "tags": [],
        "hn_stories": [],
        "reddit_posts": [],
        "news_headlines": [],
        "errors": errors,
    }

    time.sleep(0.15)
    cats = fetch_remotive_categories()
    if not cats:
        errors.append("Remotive categories unavailable.")
    out["categories"] = [{"name": n, "count": c} for n, c in cats]

    time.sleep(0.2)
    tags = fetch_remoteok_tags()
    if not tags:
        errors.append("RemoteOK tags unavailable.")
    out["tags"] = [{"name": n, "count": c} for n, c in tags]

    time.sleep(0.15)
    out["hn_stories"] = fetch_hn_remote_stories()
    if not out["hn_stories"]:
        errors.append("Hacker News search returned nothing.")

    time.sleep(0.25)
    out["reddit_posts"] = fetch_reddit_remotework()
    if not out["reddit_posts"]:
        errors.append("Reddit r/remotework unavailable (rate limit or block).")

    time.sleep(0.15)
    out["news_headlines"] = fetch_remote_work_rss_headlines()
    if not out["news_headlines"]:
        errors.append("Google News RSS unavailable.")

    out["ok"] = bool(
        out["categories"] or out["tags"] or out["hn_stories"] or out["reddit_posts"]
    )
    return out
