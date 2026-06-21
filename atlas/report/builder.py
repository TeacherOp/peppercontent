"""Assemble a full client report from the mock sources.

Pulls the current and comparison periods for each source, computes deltas, and
hands a compact summary to the narrative layer for the written insights.
"""

import config
from .. import clients as clients_mod
from ..mock_api import _gen, gsc, ga4, semrush, semrush_ai, cms
from . import metrics
from .narrative import generate_narrative


def build_report(client_id, period, cadence="Monthly"):
    client = clients_mod.get_client(client_id)
    if client is None:
        raise ValueError(f"Unknown client: {client_id}")

    months_back = config.CADENCES.get(cadence, 1)
    prev = _gen.shift_period(period, months_back)

    organic = _organic(client, period, prev)
    traffic = _traffic(client, period, prev)
    competitive = _competitive(client, period, prev)
    ai_visibility = _ai_visibility(client, period, prev)
    content = _content(client, period)

    report = {
        "client": {
            "name": client["name"],
            "domain": client["domain"],
            "industry": client["industry"],
            "market": client["market"].upper(),
        },
        "period": {
            "label": _gen.period_label(period),
            "compare_label": _gen.period_label(prev),
            "cadence": cadence,
            "start": _gen.period_dates(period)[0],
            "end": _gen.period_dates(period)[1],
        },
        "organic": organic,
        "traffic": traffic,
        "competitive": competitive,
        "ai_visibility": ai_visibility,
        "content": content,
    }

    report["narrative"] = generate_narrative(report)
    return report


# --- Organic search (GSC) ------------------------------------------------

def _organic(client, period, prev):
    cur = gsc.fetch(client, period)
    old = gsc.fetch(client, prev)

    summary = {
        "clicks": metrics.delta(cur["summary"]["clicks"], old["summary"]["clicks"]),
        "impressions": metrics.delta(cur["summary"]["impressions"], old["summary"]["impressions"]),
        "ctr": metrics.delta(cur["summary"]["ctr"], old["summary"]["ctr"]),
        "position": metrics.delta(cur["summary"]["position"], old["summary"]["position"], lower_is_better=True),
    }

    queries = []
    for phrase, row in cur["queries"].items():
        prev_row = old["queries"].get(phrase, row)
        queries.append({
            "phrase": phrase,
            "intent": row["intent"],
            "clicks": row["clicks"],
            "clicks_change": _pct(row["clicks"], prev_row["clicks"]),
            "position": row["position"],
            "position_delta": round(prev_row["position"] - row["position"], 1),
        })
    top_queries = sorted(queries, key=lambda q: q["clicks"], reverse=True)[:8]
    movers = sorted(queries, key=lambda q: q["position_delta"], reverse=True)
    gained = [q for q in movers if q["position_delta"] > 0.1][:5]
    lost = [q for q in reversed(movers) if q["position_delta"] < -0.1][:5]

    pages = []
    for path, row in cur["pages"].items():
        prev_row = old["pages"].get(path, row)
        pages.append({
            "path": path,
            "title": row["title"],
            "clicks": row["clicks"],
            "clicks_change": _pct(row["clicks"], prev_row["clicks"]),
            "position": row["position"],
        })
    top_pages = sorted(pages, key=lambda p: p["clicks"], reverse=True)[:6]

    return {
        "summary": summary,
        "top_queries": top_queries,
        "top_pages": top_pages,
        "gained": gained,
        "lost": lost,
    }


# --- Traffic & conversions (GA4) -----------------------------------------

def _traffic(client, period, prev):
    cur = ga4.fetch(client, period)
    old = ga4.fetch(client, prev)
    s, o = cur["summary"], old["summary"]

    summary = {
        "sessions": metrics.delta(s["sessions"], o["sessions"]),
        "totalUsers": metrics.delta(s["totalUsers"], o["totalUsers"]),
        "engagementRate": metrics.delta(s["engagementRate"], o["engagementRate"]),
        "conversions": metrics.delta(s["conversions"], o["conversions"]),
        "revenue": metrics.delta(s["revenue"], o["revenue"]),
    }

    channels = []
    for name, row in cur["channels"].items():
        prev_row = old["channels"].get(name, row)
        channels.append({
            "name": name,
            "sessions": row["sessions"],
            "sessions_change": _pct(row["sessions"], prev_row["sessions"]),
            "conversions": row["conversions"],
            "revenue": row["revenue"],
        })
    channels.sort(key=lambda c: c["sessions"], reverse=True)

    return {"summary": summary, "channels": channels}


# --- Competitive (Semrush) -----------------------------------------------

def _competitive(client, period, prev):
    cur = semrush.fetch(client, period)
    old = semrush.fetch(client, prev)
    s, o = cur["summary"], old["summary"]

    summary = {
        "organic_keywords": metrics.delta(s["organic_keywords"], o["organic_keywords"]),
        "traffic": metrics.delta(s["traffic"], o["traffic"]),
        "ascore": metrics.delta(s["ascore"], o["ascore"]),
        "backlinks": metrics.delta(s["backlinks"], o["backlinks"]),
        "ref_domains": metrics.delta(s["ref_domains"], o["ref_domains"]),
    }

    competitors = []
    you = {"name": client["name"], "visibility": round(s["traffic"] / 110_000, 3),
           "visibility_change": _pct(s["traffic"], o["traffic"]), "ascore": s["ascore"], "is_you": True}
    competitors.append(you)
    for name, row in cur["competitors"].items():
        prev_row = old["competitors"].get(name, row)
        competitors.append({
            "name": name,
            "visibility": row["visibility"],
            "visibility_change": _pct(row["visibility"], prev_row["visibility"]),
            "ascore": row["ascore"],
            "is_you": False,
        })
    competitors.sort(key=lambda c: c["visibility"], reverse=True)

    return {"summary": summary, "competitors": competitors}


# --- AI search visibility (Semrush AI) -----------------------------------

def _ai_visibility(client, period, prev):
    cur = semrush_ai.fetch(client, period)
    old = semrush_ai.fetch(client, prev)
    s, o = cur["summary"], old["summary"]

    summary = {
        "visibility_score": metrics.delta(s["visibility_score"], o["visibility_score"]),
        "share_of_voice": metrics.delta(s["share_of_voice"], o["share_of_voice"]),
        "mention_rate": metrics.delta(s["mention_rate"], o["mention_rate"]),
        "avg_position": metrics.delta(s["avg_position"], o["avg_position"], lower_is_better=True),
    }

    engines = []
    for name, row in cur["engines"].items():
        prev_row = old["engines"].get(name, row)
        engines.append({
            "engine": _engine_label(name),
            "visibility_score": row["visibility_score"],
            "vs_change": _pct(row["visibility_score"], prev_row["visibility_score"]),
            "share_of_voice": row["share_of_voice"],
            "mention_rate": row["mention_rate"],
            "avg_position": row["avg_position"],
        })
    engines.sort(key=lambda e: e["visibility_score"], reverse=True)

    competing = [{"name": n, "share_of_voice": v["share_of_voice"], "top_engine": _engine_label(v["top_engine"])}
                 for n, v in cur["competing_brands"].items()]
    competing.sort(key=lambda c: c["share_of_voice"], reverse=True)

    cited = []
    for path, row in cur["cited_pages"].items():
        prev_row = old["cited_pages"].get(path, row)
        cited.append({
            "title": row["title"],
            "citations": row["citations"],
            "citations_change": _pct(row["citations"], prev_row["citations"]),
            "avg_position": row["avg_position"],
        })
    cited.sort(key=lambda c: c["citations"], reverse=True)

    return {
        "summary": summary,
        "sentiment": s["sentiment"],
        "engines": engines,
        "competing_brands": competing[:4],
        "cited_pages": cited[:5],
        "prompts": cur["prompts"][:6],
    }


# --- Content health (CMS) ------------------------------------------------

def _content(client, period):
    data = cms.fetch(client, period)
    items = data["items"]
    recent = [i for i in items if i["published_days_ago"] <= 30]
    stale = [i for i in items if i["modified_days_ago"] > config.STALE_DAYS]
    refresh = sorted(
        [i for i in stale if i["monthly_traffic"] >= config.REFRESH_MIN_TRAFFIC],
        key=lambda i: i["monthly_traffic"],
        reverse=True,
    )[:5]

    return {
        "platform": data["platform"].title(),
        "total_published": data["total_published"],
        "tracked": len(items),
        "published_recent": len(recent),
        "stale_count": len(stale),
        "refresh_candidates": refresh,
    }


# --- helpers -------------------------------------------------------------

def _pct(current, previous):
    if not previous:
        return 0.0
    return round((current - previous) / previous * 100.0, 1)


_ENGINE_LABELS = {
    "chatgpt": "ChatGPT",
    "perplexity": "Perplexity",
    "google_aio": "Google AI Overviews",
    "copilot": "Copilot",
    "claude": "Claude",
}


def _engine_label(name):
    return _ENGINE_LABELS.get(name, name)
