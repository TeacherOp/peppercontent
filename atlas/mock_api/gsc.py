"""GSC — Search Performance (searchanalytics.query).

Returns clicks / impressions / CTR / position for a single period, both at the
property level and broken out by query and by page.
"""

from . import _gen


def fetch(client, period):
    r = _gen.rng(client["id"], period, "gsc")
    f = _gen.factor(period)
    scale = client["scale"]

    impressions = int(820_000 * scale * f * _gen.jitter(r, 0.04))
    ctr = max(0.012, min(0.075, 0.041 * _gen.jitter(r, 0.06)))
    clicks = int(impressions * ctr)
    position = round(max(3.0, 14.5 / (f ** 0.3) * _gen.jitter(r, 0.05)), 1)

    queries = {
        phrase: _query_row(client, period, phrase, intent)
        for phrase, intent in client["keywords"]
    }
    pages = {
        path: _page_row(client, period, path, title)
        for path, title in client["pages"]
    }

    return {
        "summary": {
            "clicks": clicks,
            "impressions": impressions,
            "ctr": round(ctr, 4),
            "position": position,
        },
        "queries": queries,
        "pages": pages,
    }


def _query_row(client, period, phrase, intent):
    base = _gen.rng(client["id"], "kwbase", phrase)
    pos_base = base.uniform(2, 36)
    volume = int(base.uniform(300, 14_000))

    walk = _gen.rng(client["id"], period, "kw", phrase).uniform(-3.5, 2.5)
    position = round(max(1.0, pos_base + walk), 1)

    f = _gen.factor(period, phase=base.uniform(0, 6))
    ctr = max(0.004, 0.34 / (position ** 0.82))
    impressions = int(volume * f * 0.9)
    clicks = int(impressions * ctr)
    return {
        "intent": intent,
        "volume": volume,
        "position": position,
        "impressions": impressions,
        "clicks": clicks,
        "ctr": round(ctr, 4),
    }


def _page_row(client, period, path, title):
    base = _gen.rng(client["id"], "pagebase", path)
    weight = base.uniform(0.4, 2.2)
    f = _gen.factor(period, phase=base.uniform(0, 6))
    r = _gen.rng(client["id"], period, "page", path)

    clicks = int(2_600 * client["scale"] * weight * f * _gen.jitter(r, 0.08))
    impressions = int(clicks / max(0.01, 0.038 * _gen.jitter(r, 0.1)))
    position = round(max(1.0, base.uniform(2, 22) + r.uniform(-2.5, 2.0)), 1)
    return {
        "title": title,
        "clicks": clicks,
        "impressions": impressions,
        "position": position,
    }
