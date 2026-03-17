# Company scanner — emails, company snapshot, news links + games

Python + Streamlit. Enter a **company URL** for:

- **Emails** — contact / careers pages (same as before)  
- **Company snapshot** — site title, meta description, text snippet from home/about  
- **News / blog links** — tries `/news`, `/blog`, `/press`, etc., and lists article-style links  

While the scan runs, **mini-games** keep the wait fun (treasure dig, quiz, rock-paper-scissors).  
A second tab has **worldwide remote job trends** (popular roles, future outlook, strategy).

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

Tabs: **Scan company & news** · **Remote jobs intel** · **Game arcade**

## What it finds

- `mailto:` links and visible emails on HTML pages  
- Company name/tagline/snippet from public pages  
- News-style links from index pages (not full article scraping)  

It does **not** bypass logins, CAPTCHAs, or heavy JavaScript-only sites.

## Legal / ethical use

Use only on sites you’re permitted to scrape. Comply with terms of service and applicable laws. This tool is for legitimate business or recruiting research.
