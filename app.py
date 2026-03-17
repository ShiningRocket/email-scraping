"""
Streamlit UI — Company intel, news links, emails, remote-work insights, waiting games.
"""

from __future__ import annotations

import threading

import streamlit as st

from arcade_games import render_arcade, render_external_game_links
from company_intel import full_company_scrape
from remote_intel_scraper import fetch_remote_intel
from remote_insights import REMOTE_INSIGHTS_HTML
from scraping_games import render_waiting_games

try:
    from streamlit_autorefresh import st_autorefresh
except ImportError:
    st_autorefresh = None  # type: ignore

st.set_page_config(
    page_title="Company & email scanner",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="collapsed",
)

CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,600;0,9..40,700&family=JetBrains+Mono:wght@400;500&display=swap');
    /* Do NOT use [class*="css"] — it matches Streamlit Emotion classes and breaks tab layout (clipped tabs). */
    .stApp, .stApp p, .stApp label, .stApp input, .stApp textarea {
        font-family: 'DM Sans', system-ui, sans-serif;
    }
    .block-container {
        padding-top: 1.75rem;
        padding-bottom: 3rem;
        max-width: 1000px;
    }
    /* Main column must scroll — overflow:visible on stMain breaks scrolling and clips bottom content */
    [data-testid="stMain"] {
        overflow-y: auto !important;
        overflow-x: hidden !important;
        -webkit-overflow-scrolling: touch;
    }

    /* Tab bar: prevent labels being clipped (overflow / height issues) */
    [data-testid="stTabs"] {
        overflow: visible !important;
        margin-top: 0.5rem;
        padding-top: 0.5rem;
    }
    [data-testid="stTabs"] > div {
        overflow: visible !important;
    }
    [data-testid="stTabs"] [role="tablist"] {
        overflow: visible !important;
        min-height: 3rem !important;
        align-items: stretch !important;
        flex-wrap: wrap !important;
        gap: 0.25rem !important;
        padding-bottom: 0.25rem !important;
    }
    [data-testid="stTabs"] button[role="tab"],
    [data-testid="stTabs"] [data-baseweb="tab"] {
        min-height: 2.75rem !important;
        padding: 0.65rem 1rem !important;
        line-height: 1.35 !important;
        white-space: nowrap !important;
        overflow: visible !important;
    }
    /* First row inside stTabs = tab labels row */
    [data-testid="stTabs"] > div:first-child {
        min-height: 3.25rem !important;
        overflow: visible !important;
        align-items: center !important;
    }
    .hero {
        background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 50%, #134e4a 100%);
        border-radius: 20px; padding: 2rem 2rem; margin-bottom: 1.25rem;
        box-shadow: 0 25px 50px -12px rgba(15, 23, 42, 0.4);
        border: 1px solid rgba(255,255,255,0.08);
    }
    .hero h1 { color: #f8fafc !important; font-weight: 700; font-size: 1.85rem !important; margin-bottom: 0.35rem !important; border: none !important; }
    .hero p { color: #94a3b8 !important; font-size: 1rem; margin: 0 !important; max-width: 560px; }
    .stTextInput > div > div > input { border-radius: 12px !important; border: 1px solid #e2e8f0 !important; padding: 0.65rem 1rem !important; }
    .stButton > button[kind="primary"] {
        border-radius: 12px !important; font-weight: 600 !important;
        background: linear-gradient(135deg, #0d9488, #0f766e) !important; color: white !important; border: none !important;
    }
    .email-card {
        background: linear-gradient(180deg, #fff 0%, #f8fafc 100%);
        border: 1px solid #e2e8f0; border-radius: 14px; padding: 1rem 1.25rem; margin-bottom: 0.75rem;
    }
    .email-addr { font-family: 'JetBrains Mono', monospace; font-size: 1rem; font-weight: 500; color: #0f172a; word-break: break-all; }
    .meta { color: #64748b; font-size: 0.82rem; margin-top: 0.35rem; }
    .badge { display: inline-block; background: #ccfbf1; color: #0f766e; padding: 0.15rem 0.5rem; border-radius: 6px; font-size: 0.72rem; font-weight: 600; margin-right: 0.25rem; }
    .company-box {
        background: #f0fdfa; border: 1px solid #99f6e4; border-radius: 16px; padding: 1.25rem; margin-bottom: 1rem;
    }
    .footer-note { color: #94a3b8; font-size: 0.78rem; margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #e2e8f0; }

    /* Tab panels: scroll if needed + grow to full content (no flex clipping) */
    [data-testid="stTabs"] {
        flex: 0 1 auto !important;
    }
    [data-testid="stTabs"] [role="tabpanel"],
    [data-testid="stTabs"] [data-baseweb="tab-panel"] {
        padding-top: 2.25rem !important;
        padding-bottom: 3rem !important;
        overflow-y: auto !important;
        overflow-x: hidden !important;
        max-height: none !important;
        height: auto !important;
        min-height: min-content !important;
    }
    [data-testid="stTabs"] [role="tabpanel"] > div,
    [data-testid="stTabs"] [data-baseweb="tab-panel"] > div {
        padding-top: 0.35rem !important;
        overflow: visible !important;
        max-height: none !important;
    }

    /* Remote jobs intel — always light card = readable in dark & light theme */
    .remote-insights-panel {
        background: linear-gradient(180deg, #ffffff 0%, #f1f5f9 100%);
        color: #0f172a;
        padding: 1.5rem 1.5rem 2rem 1.5rem;
        border-radius: 18px;
        border: 1px solid #cbd5e1;
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.18);
        margin: 0.25rem 0 1rem 0;
        line-height: 1.65;
    }
    .remote-insights-title {
        color: #020617 !important;
        font-size: clamp(1.25rem, 2.5vw, 1.75rem);
        font-weight: 800;
        line-height: 1.35;
        margin: 0 0 1.35rem 0 !important;
        padding: 0.35rem 0 1rem 0 !important;
        border-bottom: 3px solid #0284c7;
        letter-spacing: -0.02em;
    }
    .remote-insights-h3 {
        color: #0c4a6e !important;
        font-size: 1.15rem !important;
        font-weight: 700 !important;
        margin: 1.35rem 0 0.65rem 0 !important;
        padding: 0.5rem 0.75rem !important;
        background: #e0f2fe !important;
        border-radius: 10px;
        border-left: 5px solid #0284c7;
    }
    .remote-insights-p,
    .remote-insights-list li {
        color: #1e293b !important;
        font-size: 1rem;
    }
    .remote-insights-list {
        color: #1e293b;
        padding-left: 1.35rem;
    }
    .remote-insights-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.95rem;
        margin-top: 0.5rem;
        background: #fff;
        border: 1px solid #94a3b8;
        border-radius: 10px;
        overflow: hidden;
    }
    .remote-insights-table th {
        background: #0c4a6e !important;
        color: #f8fafc !important;
        padding: 12px 10px;
        text-align: left;
        font-weight: 700;
    }
    .remote-insights-table td {
        padding: 10px;
        border-bottom: 1px solid #cbd5e1;
        color: #0f172a !important;
        background: #f8fafc;
    }
    .remote-insights-table tr:last-child td { border-bottom: none; }
    .remote-insights-table tr:nth-child(even) td { background: #fff; }
    .remote-insights-foot {
        font-size: 0.88rem;
        color: #475569 !important;
        margin-top: 1.25rem !important;
        padding-top: 0.75rem;
        border-top: 1px solid #cbd5e1;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

if "scrape_holder" not in st.session_state:
    st.session_state.scrape_holder = None
if "scrape_job_active" not in st.session_state:
    st.session_state.scrape_job_active = False
if "last_scan" not in st.session_state:
    st.session_state.last_scan = None


def _start_background_scrape(url: str, deep: bool) -> None:
    holder: dict = {"done": False, "result": None, "err": None}

    def work() -> None:
        try:
            holder["result"] = full_company_scrape(url.strip(), deep=deep)
        except Exception as e:
            holder["err"] = str(e)
        holder["done"] = True

    st.session_state.scrape_holder = holder
    st.session_state.scrape_job_active = True
    t = threading.Thread(target=work, daemon=True)
    t.start()


def _render_scan_results(data: dict) -> None:
    if not data.get("ok"):
        st.error(data.get("error") or "Scan failed.")
        return

    comp = data.get("company") or {}
    name = comp.get("site_name") or data.get("base_url", "Company")
    st.markdown(
        f"""
        <div class="company-box">
            <h3 style="margin:0 0 0.5rem 0;color:#115e59;">🏢 {name}</h3>
            <p style="margin:0;color:#475569;font-size:0.95rem;"><strong>Tagline / meta:</strong> {comp.get("tagline") or "—"}</p>
            <p style="margin:0.75rem 0 0 0;color:#334155;font-size:0.9rem;line-height:1.5;">{comp.get("snippet") or "No long snippet from homepage/about (page may be script-heavy)."}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    news = data.get("news") or []
    if news:
        st.subheader("📰 Recent news & blog links")
        for n in news[:15]:
            st.markdown(f"- [{n['title']}]({n['url']})")
        st.caption(f"Sourced from index pages on **{data.get('base_url')}** (titles as found on site).")

    for w in data.get("warnings") or []:
        if "No emails" in w or "No news" in w:
            st.caption(f"ℹ️ {w}")
        else:
            st.caption(f"⚠️ {w}")

    emails = data.get("emails") or []
    if emails:
        st.subheader("✉️ Emails")
        st.success(f"**{len(emails)}** address(es)")
        for r in emails:
            rel = r["relevance"]
            badge = ""
            if rel >= 3:
                badge = '<span class="badge">Hiring / careers</span>'
            elif "mailto" in r["how"].lower():
                badge = '<span class="badge">mailto</span>'
            st.markdown(
                f"""<div class="email-card"><div class="email-addr">{r["email"]}</div>{badge}
                <div class="meta">📄 {r["found_on"]}<br>🔍 {r["how"]}</div></div>""",
                unsafe_allow_html=True,
            )
        st.text_area(
            "Copy all emails",
            value="\n".join(r["email"] for r in emails),
            height=min(140, 40 + len(emails) * 26),
            label_visibility="collapsed",
        )
    else:
        st.info("No public emails found on scanned pages.")


# Spacer so tab labels sit below any header chrome (avoids top clipping)
st.markdown(
    '<div class="app-tabs-lead" style="height:16px;min-height:16px;" aria-hidden="true"></div>',
    unsafe_allow_html=True,
)
tab_scan, tab_intel, tab_games = st.tabs(
    ["🏢 Scan company & news", "🌍 Remote jobs intel", "🎮 Game arcade"]
)

with tab_scan:
    st.markdown(
        """
        <div class="hero">
            <h1>Company snapshot + current news + emails</h1>
            <p>One scan: public emails, company description, and news/blog links. Play mini-games while the crawler works.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    url = st.text_input(
        "Company or job site URL",
        placeholder="https://company.com",
        label_visibility="collapsed",
        key="url_main",
    )
    c1, c2, c3 = st.columns([1, 0.28, 0.32])
    with c1:
        go = st.button("🚀 Full scan (emails + company + news)", type="primary", use_container_width=True)
    with c2:
        deep = st.checkbox("Deep", value=True, help="More pages for emails")
    with c3:
        if st_autorefresh:
            st.caption("Auto-refresh while scanning")
        else:
            st.caption("pip install streamlit-autorefresh")

    if go:
        if not url or not url.strip():
            st.warning("Enter a URL first.")
        elif not st.session_state.scrape_job_active:
            _start_background_scrape(url, deep)
            st.rerun()

    # Background job: poll + games
    if st.session_state.scrape_job_active and st.session_state.scrape_holder:
        h = st.session_state.scrape_holder
        if not h.get("done"):
            if st_autorefresh:
                st_autorefresh(interval=1600, key="scrape_poll")
            st.markdown("### ⏳ Scanning…")
            st.progress(0.65, text="Fetching careers, contact, news, and blog pages — hang tight!")
            render_waiting_games()
            if not st_autorefresh:
                if st.button("🔄 Check if finished"):
                    st.rerun()
            st.stop()
        # Finished this run — show once, then persist in session for later visits
        st.session_state.scrape_job_active = False
        st.session_state.scrape_holder = None
        if h.get("err"):
            st.error(h["err"])
            st.stop()
        st.session_state.last_scan = h["result"]
        st.balloons()
        st.success("Scan complete — company, news links, and emails below.")
        _render_scan_results(h["result"])
        if st.button("Clear results", key="clear_fresh_scan"):
            st.session_state.last_scan = None
            st.rerun()
        st.stop()

    if st.session_state.last_scan and not st.session_state.scrape_job_active:
        _render_scan_results(st.session_state.last_scan)
        if st.button("Clear results"):
            st.session_state.last_scan = None
            st.rerun()

    st.markdown(
        '<div class="footer-note"><strong>Responsible use:</strong> Respect robots.txt, terms of service, and privacy laws. '
        "News items are links found on the site’s public index pages, not guaranteed “latest” if the site loads via JavaScript only.</div>",
        unsafe_allow_html=True,
    )

with tab_intel:
    st.markdown("### 🌍 Remote jobs intel — **live from the internet**")
    st.caption(
        "Data is pulled from public sources: **Remotive** API, **RemoteOK** API, "
        "**Hacker News** (Algolia), **Reddit** r/remotework, **Google News** RSS. "
        "Respect each site’s terms; use for research only."
    )
    if st.button("🔄 Refresh from internet", key="intel_refresh", type="primary"):
        with st.spinner("Fetching latest remote-work signals…"):
            st.session_state["intel_data"] = fetch_remote_intel()
        st.rerun()
    if "intel_data" not in st.session_state:
        with st.spinner("Loading live snapshot (first visit)…"):
            st.session_state["intel_data"] = fetch_remote_intel()

    d = st.session_state["intel_data"]
    st.success(f"**Snapshot time:** {d.get('fetched_at', '—')}")
    errs = [e for e in (d.get("errors") or []) if e]
    if errs:
        with st.expander("Source status", expanded=False):
            for e in errs:
                st.caption(f"ℹ️ {e}")

    has_live = bool(
        d.get("categories") or d.get("tags") or d.get("hn_stories")
        or d.get("reddit_posts") or d.get("news_headlines")
    )
    if not has_live:
        st.warning("Live sources returned little or no data (network, rate limits, or blocks). Showing reference content below.")
        st.markdown(REMOTE_INSIGHTS_HTML, unsafe_allow_html=True)
    else:
        if d.get("categories"):
            st.subheader("📊 Job categories (live listing mix)")
            st.caption("How many current **Remotive** remote jobs sit in each category (recent API snapshot).")
            st.dataframe(
                [{"Category": r["name"], "Listings": r["count"]} for r in d["categories"]],
                use_container_width=True,
                hide_index=True,
            )
        if d.get("tags"):
            st.subheader("🔥 Skills & tags (RemoteOK listings)")
            st.dataframe(
                [{"Tag / skill": r["name"], "Mentions": r["count"]} for r in d["tags"][:20]],
                use_container_width=True,
                hide_index=True,
            )

        st.subheader("💬 What the web is discussing")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Hacker News** — stories matching remote work / jobs")
            for s in d.get("hn_stories") or []:
                st.markdown(f"- [{s['title']}]({s['url']})")
            if not d.get("hn_stories"):
                st.caption("No stories returned.")
        with c2:
            st.markdown("**Reddit** r/remotework — hot posts")
            for s in d.get("reddit_posts") or []:
                st.markdown(f"- [{s['title']}]({s['url']})")
            if not d.get("reddit_posts"):
                st.caption("Reddit may rate-limit; try Refresh later.")

        st.markdown("**News headlines** — Google News RSS (*remote jobs worldwide*)")
        for s in d.get("news_headlines") or []:
            st.markdown(f"- [{s['title']}]({s['url']})")
        if not d.get("news_headlines"):
            st.caption("No RSS items parsed.")

        with st.expander("📌 Extra: reference strategy & role types (offline guide)", expanded=False):
            st.markdown(REMOTE_INSIGHTS_HTML, unsafe_allow_html=True)

with tab_games:
    st.markdown("### 🎮 Arcade + more games online")
    st.caption(
        "**Snake** · **Fruit catch** · **Tap targets** — runs in your browser. "
        "Below: links to big game sites (open in a new tab)."
    )
    render_arcade(height=520)
    render_external_game_links()
    st.markdown(
        '<div class="page-bottom-spacer" style="min-height:100px;height:100px;width:100%;" aria-hidden="true"></div>',
        unsafe_allow_html=True,
    )
