"""Semrush AI — AI Search Visibility (ai_visibility_overview,
ai_prompt_mentions, ai_citation_tracking).

The differentiator section: how visible the brand is across ChatGPT,
Perplexity, Google AI Overviews, Copilot and Claude — with per-engine numbers,
competing brands, cited pages, and per-prompt drill-down.
"""

from . import _gen


def fetch(client, period):
    r = _gen.rng(client["id"], period, "semrush_ai")
    f = _gen.factor(period)
    months = _gen.months_since_anchor(period)

    # AI visibility is newer and trending up faster than classic organic.
    vis_base = (28 + 1.6 * months) * (client["scale"] ** 0.25)
    visibility_score = round(max(4.0, min(92.0, vis_base * _gen.jitter(r, 0.06))), 1)
    share_of_voice = round(max(0.02, min(0.55, (visibility_score / 240) * _gen.jitter(r, 0.06))), 3)
    total_prompts = int(420 * client["scale"] + r.uniform(40, 120))
    mention_rate = round(max(0.05, min(0.8, visibility_score / 130 * _gen.jitter(r, 0.05))), 3)
    total_mentions = int(total_prompts * mention_rate * r.uniform(1.1, 1.8))
    avg_position = round(max(1.1, 4.2 - 0.05 * months) * _gen.jitter(r, 0.05), 1)

    pos = round(max(0.18, min(0.62, 0.34 * _gen.jitter(r, 0.1))), 2)
    neg = round(max(0.01, min(0.18, 0.06 * _gen.jitter(r, 0.25))), 2)
    sentiment = {"positive": pos, "neutral": round(1 - pos - neg, 2), "negative": neg}

    engines = {}
    for engine in _gen.ENGINES:
        er = _gen.rng(client["id"], period, "engine", engine)
        eb = _gen.rng(client["id"], "enginebase", engine)
        bias = eb.uniform(0.6, 1.4)
        engines[engine] = {
            "visibility_score": round(max(2.0, min(95.0, visibility_score * bias * _gen.jitter(er, 0.08))), 1),
            "share_of_voice": round(max(0.01, share_of_voice * bias * _gen.jitter(er, 0.08)), 3),
            "mention_rate": round(max(0.02, min(0.9, mention_rate * bias * _gen.jitter(er, 0.08))), 3),
            "avg_position": round(max(1.0, avg_position * eb.uniform(0.8, 1.3)), 1),
        }

    competing = {}
    for name in client["competitors"]:
        cb = _gen.rng(client["id"], "aicompbase", name)
        cr = _gen.rng(client["id"], period, "aicomp", name)
        competing[name] = {
            "share_of_voice": round(max(0.03, min(0.6, cb.uniform(0.06, 0.34) * f * _gen.jitter(cr, 0.06))), 3),
            "top_engine": cb.choice(_gen.ENGINES),
        }

    cited_pages = _cited_pages(client, period)
    prompts = _prompts(client, period, mention_rate)

    return {
        "summary": {
            "visibility_score": visibility_score,
            "share_of_voice": share_of_voice,
            "mention_rate": mention_rate,
            "avg_position": avg_position,
            "total_prompts": total_prompts,
            "total_mentions": total_mentions,
            "sentiment": sentiment,
        },
        "engines": engines,
        "competing_brands": competing,
        "cited_pages": cited_pages,
        "prompts": prompts,
    }


def _cited_pages(client, period):
    out = {}
    for path, title in client["pages"][:6]:
        base = _gen.rng(client["id"], "citebase", path)
        r = _gen.rng(client["id"], period, "cite", path)
        f = _gen.factor(period, phase=base.uniform(0, 6))
        out[path] = {
            "title": title,
            "citations": int(max(0, base.uniform(2, 40) * f * _gen.jitter(r, 0.15))),
            "avg_position": round(base.uniform(1.0, 4.5), 1),
        }
    return out


def _prompts(client, period, mention_rate):
    rows = []
    for i, prompt in enumerate(client["ai_prompts"]):
        r = _gen.rng(client["id"], period, "prompt", i)
        engine = r.choice(_gen.ENGINES)
        mentioned = r.random() < min(0.85, mention_rate + 0.25)
        sentiment = r.choices(
            ["positive", "neutral", "negative"], weights=[0.45, 0.45, 0.10]
        )[0]
        competitors = r.sample(client["competitors"], k=min(2, len(client["competitors"]))) if r.random() < 0.7 else []
        if mentioned:
            excerpt = (
                f"...{client['brand']} is often recommended here, described as "
                f"{'a strong, well-rounded choice' if sentiment == 'positive' else 'one option to consider'}..."
            )
            position = r.randint(1, 5)
        else:
            excerpt = f"...the response named {', '.join(competitors) or 'several alternatives'} but did not mention {client['brand']}..."
            position = None
        rows.append({
            "prompt": prompt,
            "engine": engine,
            "mentioned": mentioned,
            "position": position,
            "sentiment": sentiment,
            "excerpt": excerpt,
            "competitors": competitors,
        })
    return rows
