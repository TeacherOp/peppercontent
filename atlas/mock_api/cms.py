"""CMS — WordPress / Webflow / Contentful (read published content).

A single ``fetch`` covers all three; the documented read endpoints differ in
shape but return the same fields we care about for reporting: title, URL,
publish date and last-modified date. Staleness is measured relative to the
selected period's end date.
"""

from . import _gen


def fetch(client, period):
    # How far the selected period sits before the latest one — older reports
    # see fresher content, so shift modification ages accordingly.
    months_back = max(0, _gen.months_since_anchor("2025-10") - _gen.months_since_anchor(period))
    age_offset = months_back * 30

    items = []
    for i, title in enumerate(client["articles"]):
        b = _gen.rng(client["id"], "article", i)
        published = int(b.uniform(60, 1200)) - age_offset
        published = max(20, published)
        if b.random() > 0.5:
            modified = int(published * b.uniform(0.15, 0.9))
        else:
            modified = published
        modified = max(5, modified - age_offset) if modified != published else published
        items.append({
            "title": title,
            "url": f"https://{client['domain']}/blog/{_gen.slugify(title)}",
            "published_days_ago": published,
            "modified_days_ago": modified,
            "monthly_traffic": int(b.uniform(40, 5400)),
        })

    extra = int(_gen.rng(client["id"], "cmscount").uniform(48, 230))
    return {
        "platform": client["cms"],
        "items": items,
        "total_published": len(items) + extra,
    }
