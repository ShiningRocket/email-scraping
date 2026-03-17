# Email address discovery (company / careers / contact)

Python app with a Streamlit UI. Enter a **company or job-site URL**; the tool fetches the homepage and common paths (`/contact`, `/careers`, `/jobs`, etc.) and follows same-domain links that look like contact or hiring pages.

## Setup

```bash
cd emailaddress-scraping
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

## Run

```bash
streamlit run app.py
```

Opens a browser UI. Paste a URL like `https://example.com` or `jobs.example.com`.

## What it finds

- `mailto:` links  
- Email-like text in HTML pages  
- Prioritizes paths and contexts that suggest hiring / HR / careers  

It does **not** bypass logins, CAPTCHAs, or JavaScript-only content. Many job boards hide emails on purpose.

## Legal / ethical use

Use only on sites you’re permitted to scrape. Comply with terms of service and applicable laws. This tool is for legitimate business or recruiting research.
