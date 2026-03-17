"""
Streamlit UI — Company / hiring / contact email discovery.
"""

import streamlit as st

from email_scraper import scrape_emails

st.set_page_config(
    page_title="Email Finder",
    page_icon="✉️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,600;0,9..40,700;1,9..40,400&family=JetBrains+Mono:wght@400;500&display=swap');

    html, body, [class*="css"] {
        font-family: 'DM Sans', system-ui, sans-serif;
    }

    .block-container {
        padding-top: 2rem;
        max-width: 920px;
    }

    .hero {
        background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 45%, #0c4a6e 100%);
        border-radius: 20px;
        padding: 2.5rem 2rem;
        margin-bottom: 2rem;
        box-shadow: 0 25px 50px -12px rgba(15, 23, 42, 0.45);
        border: 1px solid rgba(255,255,255,0.08);
    }

    .hero h1 {
        color: #f8fafc !important;
        font-weight: 700;
        font-size: 2.1rem !important;
        letter-spacing: -0.02em;
        margin-bottom: 0.5rem !important;
        border: none !important;
    }

    .hero p {
        color: #94a3b8 !important;
        font-size: 1.05rem;
        margin: 0 !important;
        max-width: 520px;
    }

    .stTextInput > div > div > input {
        border-radius: 12px !important;
        border: 1px solid #e2e8f0 !important;
        padding: 0.75rem 1rem !important;
        font-size: 1rem !important;
    }

    div[data-testid="stVerticalBlock"] > div:has(> .stButton) {
        margin-top: 0.5rem;
    }

    .stButton > button {
        border-radius: 12px !important;
        font-weight: 600 !important;
        padding: 0.65rem 1.5rem !important;
        background: linear-gradient(135deg, #0284c7, #0369a1) !important;
        color: white !important;
        border: none !important;
        width: 100%;
    }

    .stButton > button:hover {
        box-shadow: 0 10px 25px -5px rgba(2, 132, 199, 0.45);
    }

    .email-card {
        background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 1.25rem 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 4px 6px -1px rgba(15, 23, 42, 0.06);
    }

    .email-addr {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.05rem;
        font-weight: 500;
        color: #0f172a;
        word-break: break-all;
    }

    .meta {
        color: #64748b;
        font-size: 0.875rem;
        margin-top: 0.5rem;
    }

    .badge {
        display: inline-block;
        background: #e0f2fe;
        color: #0369a1;
        padding: 0.2rem 0.6rem;
        border-radius: 8px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-right: 0.35rem;
    }

    .footer-note {
        color: #94a3b8;
        font-size: 0.8rem;
        margin-top: 2.5rem;
        padding: 1rem;
        border-top: 1px solid #e2e8f0;
    }
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

col_main, _ = st.columns([1, 0.02])
with col_main:
    st.markdown(
        """
        <div class="hero">
            <h1>✉️ Email discovery</h1>
            <p>Paste a company or job posting site URL. We scan contact, careers, and related pages for public emails.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    url = st.text_input(
        "Website URL",
        placeholder="https://company.com or acme.io",
        label_visibility="collapsed",
        key="url_input",
    )

    c1, c2 = st.columns([1, 0.35])
    with c1:
        run = st.button("Find emails", type="primary", use_container_width=True)
    with c2:
        deep = st.checkbox("Deep scan", value=True, help="Follow more internal links (slower)")

    if run:
        if not url or not url.strip():
            st.warning("Please enter a URL.")
        else:
            max_pages = 18 if deep else 8
            with st.spinner("Scanning pages…"):
                results, warnings = scrape_emails(url.strip(), max_pages=max_pages)

            for w in warnings:
                if "No emails" in w or "empty" in w.lower():
                    st.info(w)
                else:
                    st.caption(f"⚠ {w}")

            if results:
                st.success(f"Found **{len(results)}** unique address(es)")
                for r in results:
                    rel = r["relevance"]
                    badge = ""
                    if rel >= 3:
                        badge = '<span class="badge">Hiring / careers</span>'
                    elif "mailto" in r["how"].lower():
                        badge = '<span class="badge">mailto</span>'
                    st.markdown(
                        f"""
                        <div class="email-card">
                            <div class="email-addr">{r["email"]}</div>
                            {badge}
                            <div class="meta">📄 {r["found_on"]}<br>🔍 {r["how"]}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                st.subheader("Copy all")
                st.text_area(
                    "Emails (one per line)",
                    value="\n".join(r["email"] for r in results),
                    height=min(120, 36 + len(results) * 28),
                    label_visibility="collapsed",
                )

    st.markdown(
        """
        <div class="footer-note">
        <strong>Responsible use:</strong> Only scrape sites you’re allowed to access. Respect robots.txt, terms of service, and privacy laws (GDPR, CAN-SPAM). 
        Use findings for legitimate outreach only.
        </div>
        """,
        unsafe_allow_html=True,
    )
