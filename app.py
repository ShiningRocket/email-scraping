"""
Streamlit UI — Company intel, news links, emails, remote-work insights, waiting games.
"""

from __future__ import annotations

import threading

import streamlit as st

from company_intel import full_company_scrape
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
    html, body, [class*="css"] { font-family: 'DM Sans', system-ui, sans-serif; }
    .block-container { padding-top: 1.25rem; max-width: 1000px; }
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


tab_scan, tab_intel, tab_games = st.tabs(["🏢 Scan company & news", "🌍 Remote jobs intel", "🎮 Game arcade"])

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
    st.markdown("## 🌍 Worldwide remote work — roles, future, strategy")
    st.markdown(REMOTE_INSIGHTS_HTML, unsafe_allow_html=True)

with tab_games:
    st.markdown("### 🎮 Play anytime — treasure hunt, quiz, rock-paper-scissors")
    st.caption("Fun for all ages while you wait or take a break.")
    render_waiting_games()
