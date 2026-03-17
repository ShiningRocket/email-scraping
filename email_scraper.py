"""
Email discovery from company / job posting websites.
Fetches pages and extracts mailto links + visible email patterns.
"""

from __future__ import annotations

import re
import time
from collections import defaultdict
from html import unescape
from typing import NamedTuple
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

# Polite client identity
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

# Paths often containing hiring / contact emails
PRIORITY_PATHS = (
    "",
    "/contact",
    "/contact-us",
    "/about",
    "/about-us",
    "/careers",
    "/jobs",
    "/hiring",
    "/team",
    "/people",
    "/recruitment",
    "/apply",
    "/work-with-us",
)

# Broader regex; we filter false positives below
EMAIL_PATTERN = re.compile(
    r"[a-zA-Z0-9][a-zA-Z0-9._%+\-]*@[a-zA-Z0-9][a-zA-Z0-9.\-]*\.[a-zA-Z]{2,}",
    re.IGNORECASE,
)

INVALID_TLDS = frozenset(
    {
        "png", "jpg", "jpeg", "gif", "webp", "svg", "css", "js",
        "pdf", "zip", "exe", "dll", "woff", "woff2", "ttf", "eot",
    }
)

ROLE_HINTS = (
    "career", "job", "hire", "recruit", "talent", "hr@", "people@",
    "apply", "resume", "cv@", "staffing", "recruiting",
)


class EmailHit(NamedTuple):
    email: str
    source_url: str
    context: str  # mailto | page_text | link_text


def _normalize_base(url: str) -> str:
    url = url.strip()
    if not url:
        raise ValueError("URL is empty")
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    parsed = urlparse(url)
    if not parsed.netloc:
        raise ValueError("Invalid URL")
    scheme = parsed.scheme or "https"
    return f"{scheme}://{parsed.netloc}"


def _same_domain(base: str, link: str) -> bool:
    try:
        b = urlparse(base).netloc.lower().lstrip("www.")
        l = urlparse(link).netloc.lower().lstrip("www.")
        return l == b or l.endswith("." + b)
    except Exception:
        return False


def _clean_email(raw: str) -> str | None:
    raw = unescape(raw.strip().rstrip(".,;:)\"'"))
    m = EMAIL_PATTERN.search(raw)
    if not m:
        return None
    e = m.group(0).lower()
    parts = e.rsplit(".", 1)
    if len(parts) == 2 and parts[1] in INVALID_TLDS:
        return None
    if e.startswith("mailto:"):
        e = e[7:]
    if "@" not in e or e.count("@") != 1:
        return None
    local, domain = e.split("@", 1)
    if len(local) < 2 or len(domain) < 3:
        return None
    return e


def _extract_from_text(html: str, source_url: str) -> list[EmailHit]:
    soup = BeautifulSoup(html, "html.parser")
    hits: list[EmailHit] = []

    for a in soup.find_all("a", href=True):
        href = a.get("href", "")
        if href.lower().startswith("mailto:"):
            body = href[7:].split("?", 1)[0]
            e = _clean_email(body)
            if e:
                label = (a.get_text() or "").strip()[:80]
                hits.append(EmailHit(e, source_url, f"mailto ({label})" if label else "mailto"))

    text = soup.get_text(" ", strip=True)
    for m in EMAIL_PATTERN.finditer(text):
        e = _clean_email(m.group(0))
        if e:
            hits.append(EmailHit(e, source_url, "page content"))

    return hits


def _score_email(email: str, context: str) -> float:
    local, _, domain = email.partition("@")
    ctx = (context + " " + email).lower()
    score = 0.0
    for hint in ROLE_HINTS:
        if hint in ctx or hint in local:
            score += 2.0
    if any(x in local for x in ("jobs", "careers", "hiring", "recruit", "hr", "talent")):
        score += 3.0
    if any(x in local for x in ("hello", "info", "contact", "support", "sales")):
        score += 1.0
    return score


def scrape_emails(
    start_url: str,
    *,
    timeout: int = 15,
    delay_sec: float = 0.35,
    max_pages: int = 12,
) -> tuple[list[dict], list[str]]:
    """
    Returns (list of unique email dicts with metadata, list of error/warning strings).
    """
    warnings: list[str] = []
    try:
        base = _normalize_base(start_url)
    except ValueError as e:
        return [], [str(e)]

    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.9"})

    seen_urls: set[str] = set()
    all_hits: list[EmailHit] = []
    to_fetch: list[str] = []

    for path in PRIORITY_PATHS:
        u = urljoin(base + "/", path.lstrip("/")) if path else base
        if u not in to_fetch:
            to_fetch.append(u)

    pages_fetched = 0
    idx = 0

    while idx < len(to_fetch) and pages_fetched < max_pages:
        url = to_fetch[idx]
        idx += 1
        if url in seen_urls:
            continue
        if not _same_domain(base, url):
            continue
        seen_urls.add(url)

        try:
            r = session.get(url, timeout=timeout, allow_redirects=True)
            r.raise_for_status()
            ctype = r.headers.get("Content-Type", "")
            if "text/html" not in ctype and "application/xhtml" not in ctype:
                continue
            all_hits.extend(_extract_from_text(r.text, r.url))
            pages_fetched += 1

            # Discover same-domain contact/career links from first page only (save requests)
            if pages_fetched == 1:
                soup = BeautifulSoup(r.text, "html.parser")
                keywords = (
                    "contact", "career", "job", "hire", "about", "team",
                    "recruit", "apply", "work",
                )
                for a in soup.find_all("a", href=True):
                    href = a["href"]
                    full = urljoin(r.url, href)
                    if not _same_domain(base, full):
                        continue
                    text = (a.get_text() or "") + " " + href
                    low = text.lower()
                    if any(k in low for k in keywords) and full not in to_fetch and full not in seen_urls:
                        if len(to_fetch) < 25:
                            to_fetch.append(full.split("#")[0])

        except requests.RequestException as e:
            warnings.append(f"{url}: {e!s}")
        time.sleep(delay_sec)

    # Dedupe: aggregate relevance, keep primary source (highest single-context score)
    grouped: dict[str, list[EmailHit]] = defaultdict(list)
    for hit in all_hits:
        grouped[hit.email].append(hit)

    scores: dict[str, float] = {}
    best_hit: dict[str, EmailHit] = {}
    for email, hits in grouped.items():
        scores[email] = sum(_score_email(email, h.context) for h in hits)
        best_hit[email] = max(hits, key=lambda h: _score_email(email, h.context))

    def sort_key(e: str) -> tuple:
        s = scores[e]
        hiring = 1 if any(h in e for h in ("career", "job", "hire", "recruit", "hr", "talent")) else 0
        return (-hiring, -s, e)

    ordered = sorted(grouped.keys(), key=sort_key)
    results = [
        {
            "email": e,
            "found_on": best_hit[e].source_url,
            "how": best_hit[e].context,
            "relevance": round(scores[e], 1),
        }
        for e in ordered
    ]

    if not results and not warnings:
        warnings.append("No emails found. Try a direct careers or contact page URL.")
    return results, warnings
