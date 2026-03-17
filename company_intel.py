"""
Company snapshot + recent news-style links from corporate sites.
"""

from __future__ import annotations

import re
import time
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from email_scraper import USER_AGENT, _normalize_base, _same_domain

NEWS_PATHS = (
    "/news",
    "/newsroom",
    "/press",
    "/press-releases",
    "/blog",
    "/blogs",
    "/media",
    "/insights",
    "/stories",
    "/updates",
    "/company/news",
)

SKIP_TITLE = re.compile(
    r"^(home|read more|learn more|click here|menu|login|sign in|subscribe)$",
    re.I,
)


def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.9"})
    return s


def scrape_company_snapshot(session: requests.Session, base: str, timeout: int = 12) -> dict:
    """Homepage + /about style summary."""
    out = {
        "site_name": "",
        "tagline": "",
        "snippet": "",
        "pages_used": [],
    }
    for path in ("", "/about", "/about-us", "/company"):
        url = urljoin(base + "/", path.lstrip("/")) if path else base
        try:
            r = session.get(url, timeout=timeout, allow_redirects=True)
            if r.status_code != 200 or "text/html" not in r.headers.get("Content-Type", ""):
                continue
            soup = BeautifulSoup(r.text, "html.parser")
            out["pages_used"].append(r.url)

            og = soup.find("meta", property="og:title")
            if og and og.get("content") and not out["site_name"]:
                out["site_name"] = og["content"].strip()[:200]
            if soup.title and not out["site_name"]:
                out["site_name"] = (soup.title.string or "").strip()[:200]

            desc = soup.find("meta", attrs={"name": re.compile(r"^description$", re.I)})
            if desc and desc.get("content"):
                out["tagline"] = desc["content"].strip()[:500]

            if not out["snippet"]:
                for sel in ("main p", "article p", "#content p", ".content p", "p"):
                    for p in soup.select(sel)[:8]:
                        t = p.get_text(" ", strip=True)
                        if 80 <= len(t) <= 1200:
                            out["snippet"] = t[:600]
                            break
                    if out["snippet"]:
                        break
            time.sleep(0.2)
        except requests.RequestException:
            continue
    return out


def _title_ok(text: str) -> bool:
    t = text.strip()
    if len(t) < 12 or len(t) > 180:
        return False
    if SKIP_TITLE.match(t):
        return False
    return True


def scrape_news_links(
    session: requests.Session,
    base: str,
    *,
    timeout: int = 12,
    max_items: int = 20,
    delay: float = 0.25,
) -> list[dict]:
    """Collect headline + URL from news/blog/press index pages."""
    seen: set[str] = set()
    items: list[dict] = []

    for path in NEWS_PATHS:
        if len(items) >= max_items:
            break
        url = urljoin(base + "/", path.lstrip("/"))
        try:
            r = session.get(url, timeout=timeout, allow_redirects=True)
            if r.status_code != 200 or "text/html" not in r.headers.get("Content-Type", ""):
                time.sleep(delay)
                continue
            soup = BeautifulSoup(r.text, "html.parser")
            base_page = r.url

            candidates: list[tuple[str, str]] = []

            for a in soup.find_all("a", href=True):
                href = a["href"].split("#")[0]
                if not href or href.startswith(("javascript:", "mailto:", "tel:")):
                    continue
                full = urljoin(base_page, href)
                if not _same_domain(base, full):
                    continue
                title = re.sub(r"\s+", " ", (a.get_text() or "").strip())
                if not _title_ok(title):
                    continue
                low = full.lower()
                if low in seen:
                    continue
                # Prefer paths that look like articles
                path_part = urlparse(full).path.lower()
                if any(
                    x in path_part
                    for x in ("/news/", "/blog/", "/press/", "/article/", "/post/", "/story/", "/202", "/20")
                ) or len(path_part.split("/")) >= 3:
                    candidates.append((title[:180], full))

            for title, full in candidates:
                if full.lower() in seen:
                    continue
                seen.add(full.lower())
                items.append({"title": title, "url": full, "index_page": base_page})
                if len(items) >= max_items:
                    break

            time.sleep(delay)
        except requests.RequestException:
            time.sleep(delay)
            continue

    return items


def full_company_scrape(
    start_url: str,
    *,
    max_email_pages: int = 14,
    deep: bool = True,
) -> dict:
    """Emails + company snapshot + news links."""
    from email_scraper import scrape_emails

    warnings: list[str] = []
    try:
        base = _normalize_base(start_url)
    except ValueError as e:
        return {
            "ok": False,
            "error": str(e),
            "emails": [],
            "warnings": [str(e)],
            "company": {},
            "news": [],
        }

    max_pages = 18 if deep else 8
    emails, w_email = scrape_emails(start_url, max_pages=max_pages)
    warnings.extend(w_email)

    session = _session()
    company = scrape_company_snapshot(session, base)
    news = scrape_news_links(session, base)

    if not news:
        warnings.append("No news/blog index found (try a site with /news or /blog).")

    return {
        "ok": True,
        "base_url": base,
        "emails": emails,
        "warnings": warnings,
        "company": company,
        "news": news,
    }
