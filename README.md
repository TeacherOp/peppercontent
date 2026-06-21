# Pepper Atlas — Report Builder

A working prototype that turns the 4+ hours/week CS managers spend hand-building
client reports into a few minutes of **review and approve**.

It pulls the documented data sources, computes period-over-period changes, and
uses **Claude** (`claude-sonnet-4-5`) to draft the narrative and
recommendations — then renders a clean, client-ready report (HTML, exportable to
PDF) that leads with **AI search visibility**, Pepper Atlas's differentiator.

See [`docs/PRD.md`](docs/PRD.md) for the product spec, UX flow, and the
evaluation design (how we'd prove it saves the 4 hours).

## What it does

1. Pick a **client + reporting period + cadence**.
2. Atlas pulls every source (GSC, GA4, Semrush, Semrush AI, and the CMS) for the
   current and comparison periods.
3. It computes **period-over-period deltas** for every metric.
4. **Claude drafts** the executive summary, per-section insights, and
   prioritised recommendations — grounded only in the numbers.
5. You get a rendered report to **review → edit → approve → send**.

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env        # then add your ANTHROPIC_API_KEY
python app.py               # http://127.0.0.1:5001
```

The app runs in **Claude-required mode**: a valid `ANTHROPIC_API_KEY` must be set
(it powers the narrative). Without one, the report build fails with a clear
message instead of shipping a chart-only report.

## Deployment (Docker / Coolify)

The repo ships a `Dockerfile` that runs the app under gunicorn.

```bash
docker build -t atlas .
docker run -p 8000:8000 -e ANTHROPIC_API_KEY=sk-ant-... -v atlas-data:/app/data atlas
# → http://localhost:8000
```

On **Coolify** (build from the Dockerfile):

- **Port:** `8000` (the container exposes and binds to it).
- **Environment:** set `ANTHROPIC_API_KEY` (required).
- **Persistent storage:** mount a volume at **`/app/data`** so saved reports
  survive redeploys (the JSON store lives there).
- **Health check path:** `/health` (returns `{"status":"ok"}`).

The image uses a single gunicorn worker with threads and a 120s timeout — one
writer keeps the file-based JSON store consistent, and the long timeout covers
the multi-second Claude calls.

## Data

The 7 sources are treated as **black-box APIs** (per the brief — no real calls).
`atlas/mock_api/` returns realistic, internally-consistent synthetic data for
**3 demo clients** (a B2B SaaS, a DTC skincare brand, and an online legal
service). Generation is deterministic and seeded by `(client, period)`, so the
previous period of one report equals the current period of the report before it —
deltas stay consistent across reports. In production, each `mock_api` module is
swapped for the real source connector; nothing else changes.

## Architecture

```
app.py                     Flask routes + Jinja formatting filters
config.py                  model id, periods, cadences, staleness thresholds
atlas/
  clients.py               the 3 demo clients (stable identity: keywords, pages, …)
  mock_api/                black-box source layer — fetch(client, period)
    _gen.py                deterministic seeded helpers
    gsc.py ga4.py          GSC + GA4
    semrush.py             organic SEO + competitors + backlinks
    semrush_ai.py          AI search visibility (the differentiator)
    cms.py                 WordPress / Webflow / Contentful content inventory
  report/
    metrics.py             period-over-period delta math
    builder.py             pulls sources, computes deltas, assembles the report
    narrative.py           Claude call → executive summary, insights, recs
templates/                 base / index (form) / report
static/                    styles + Chart.js charts
docs/PRD.md                product requirements + eval design
```

The mock layer returns **raw single-period data** (like a real API); the report
layer is what pulls two periods and computes the deltas — faithful to how a CS
manager actually works.
