"""Semrush — Third-party SEO (domain_organic, domain_organic_pages,
backlinks_overview, competitor visibility).

Period-level totals plus per-keyword rank, top traffic pages, and a competitor
set with visibility scores.
"""

from . import _gen


def fetch(client, period):
    r = _gen.rng(client["id"], period, "semrush")
    f = _gen.factor(period)
    scale = client["scale"]
    months = _gen.months_since_anchor(period)

    organic_keywords = int(4_200 * scale * f * _gen.jitter(r, 0.03))
    traffic = int(48_000 * scale * f * _gen.jitter(r, 0.05))
    traffic_cost = round(traffic * client.get("cpc_base", 2.4) * _gen.jitter(r, 0.05), 2)
    ascore = int(max(18, min(78, (50 * scale ** 0.18) * (1 + 0.004 * months) * _gen.jitter(r, 0.02))))
    backlinks = int(118_000 * scale * f * _gen.jitter(r, 0.02))
    ref_domains = int(2_300 * scale * f * _gen.jitter(r, 0.02))

    keywords = {
        phrase: _kw_row(client, period, phrase, intent)
        for phrase, intent in client["keywords"]
    }
    competitors = {
        name: _comp_row(client, period, name)
        for name in client["competitors"]
    }

    return {
        "summary": {
            "organic_keywords": organic_keywords,
            "traffic": traffic,
            "traffic_cost": traffic_cost,
            "ascore": ascore,
            "backlinks": backlinks,
            "ref_domains": ref_domains,
        },
        "keywords": keywords,
        "competitors": competitors,
    }


def _kw_row(client, period, phrase, intent):
    base = _gen.rng(client["id"], "kwbase", phrase)
    pos_base = base.uniform(2, 36)
    walk = _gen.rng(client["id"], period, "kw", phrase).uniform(-3.5, 2.5)
    position = int(max(1, round(pos_base + walk)))
    volume = int(base.uniform(300, 14_000))
    cpc = round(base.uniform(0.4, 12.0), 2)
    return {
        "position": position,
        "volume": volume,
        "cpc": cpc,
        "intent": intent,
    }


def _comp_row(client, period, name):
    base = _gen.rng(client["id"], "compbase", name)
    r = _gen.rng(client["id"], period, "comp", name)
    f = _gen.factor(period, phase=base.uniform(0, 6))
    visibility = round(max(0.05, min(0.95, base.uniform(0.18, 0.62) * f * _gen.jitter(r, 0.05))), 3)
    ascore = int(base.uniform(45, 80))
    return {"visibility": visibility, "ascore": ascore}
