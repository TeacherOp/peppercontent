"""GA4 — Web Analytics (properties.runReport).

Sessions, users, engagement, conversions and revenue for a single period,
broken out by default channel grouping.
"""

from . import _gen

CHANNELS = [
    ("Organic Search", 0.46),
    ("Direct", 0.22),
    ("Referral", 0.10),
    ("Paid Search", 0.11),
    ("Social", 0.07),
    ("Email", 0.04),
]


def fetch(client, period):
    r = _gen.rng(client["id"], period, "ga4")
    f = _gen.factor(period)
    scale = client["scale"]
    aov = client.get("aov", 120)

    total = int(62_000 * scale * f * _gen.jitter(r, 0.04))
    base_cvr = max(0.008, 0.021 * _gen.jitter(r, 0.08))

    channels = {}
    for name, weight in CHANNELS:
        cr = _gen.rng(client["id"], period, "ch", name)
        sessions = int(total * weight * _gen.jitter(cr, 0.08))
        intent_lift = 1.35 if name in ("Email", "Paid Search") else 1.0
        conversions = int(sessions * base_cvr * intent_lift * _gen.jitter(cr, 0.1))
        revenue = round(conversions * aov * _gen.jitter(cr, 0.1), 2)
        channels[name] = {
            "sessions": sessions,
            "conversions": conversions,
            "revenue": revenue,
        }

    sessions = sum(c["sessions"] for c in channels.values())
    conversions = sum(c["conversions"] for c in channels.values())
    revenue = round(sum(c["revenue"] for c in channels.values()), 2)
    users = int(sessions * 0.78)
    engagement = round(max(0.40, min(0.86, 0.61 * _gen.jitter(r, 0.05))), 4)

    return {
        "summary": {
            "sessions": sessions,
            "totalUsers": users,
            "engagementRate": engagement,
            "conversions": conversions,
            "revenue": revenue,
        },
        "channels": channels,
    }
