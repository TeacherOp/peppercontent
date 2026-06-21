"""Claude-generated narrative for the report.

This is the part that replaces the slow, manual half of report-building: the CS
manager no longer writes the "what happened and why" prose — Claude drafts it
from the structured deltas, and the manager reviews/edits.

Claude is required (per product decision). If ANTHROPIC_API_KEY is missing the
build fails loudly rather than shipping a chart-only report.
"""

import json
import os

import config

SYSTEM_PROMPT = (
    "You are a senior Customer Success analyst at Pepper, an AI-native organic "
    "and AI-search visibility platform. You write recurring performance reports "
    "for clients. Your tone is clear, specific, and executive-ready: lead with "
    "outcomes, quantify movements, and explain the likely 'why'. You never invent "
    "numbers — you only interpret the figures provided. Plain text only, no markdown."
)


def generate_narrative(report):
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY is not set. This app runs in Claude-required mode — "
            "add your key to a .env file (see .env.example) and try again."
        )

    # Imported lazily so the rest of the app (and tests) don't need the SDK present.
    import anthropic

    client = anthropic.Anthropic(api_key=api_key)
    context = _context(report)
    user_prompt = _build_prompt(context)

    response = client.messages.create(
        model=config.MODEL,
        max_tokens=config.MAX_TOKENS,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )
    text = "".join(block.text for block in response.content if block.type == "text")
    return _parse(text)


def _build_prompt(context):
    return (
        "Here is the structured performance data for this client and reporting "
        "period. Each metric shows current vs previous and the percent change.\n\n"
        f"{json.dumps(context, indent=2)}\n\n"
        "Write the report narrative. Respond with ONLY a JSON object, no prose "
        "around it, matching exactly this schema:\n"
        "{\n"
        '  "executive_summary": "2-4 sentences a client exec reads first",\n'
        '  "highlights": [{"title": "short label", "detail": "one sentence with a number"}],\n'
        '  "section_insights": {\n'
        '    "organic": "2-3 sentences on organic search performance",\n'
        '    "ai_visibility": "2-3 sentences on AI search visibility — Pepper\'s focus",\n'
        '    "competitive": "2-3 sentences on competitive position",\n'
        '    "content": "2-3 sentences on content health and refresh opportunities"\n'
        "  },\n"
        '  "recommendations": [{"title": "action", "detail": "why and expected impact", "priority": "High|Medium|Low"}]\n'
        "}\n"
        "Provide 3-4 highlights and 3-5 recommendations. Prioritise the AI "
        "visibility story where it's notable."
    )


def _context(report):
    """A compact, number-only view of the report for the model."""
    return {
        "client": report["client"],
        "period": {"current": report["period"]["label"], "compare": report["period"]["compare_label"]},
        "organic_summary": _summary(report["organic"]["summary"]),
        "top_gaining_keywords": [
            {"phrase": q["phrase"], "position_improvement": q["position_delta"]}
            for q in report["organic"]["gained"]
        ],
        "declining_keywords": [
            {"phrase": q["phrase"], "position_drop": q["position_delta"]}
            for q in report["organic"]["lost"]
        ],
        "traffic_summary": _summary(report["traffic"]["summary"]),
        "channels": [
            {"name": c["name"], "sessions": c["sessions"], "sessions_change_pct": c["sessions_change"]}
            for c in report["traffic"]["channels"]
        ],
        "competitive_summary": _summary(report["competitive"]["summary"]),
        "competitors": [
            {"name": c["name"], "visibility": c["visibility"], "is_client": c["is_you"]}
            for c in report["competitive"]["competitors"]
        ],
        "ai_visibility_summary": _summary(report["ai_visibility"]["summary"]),
        "ai_sentiment": report["ai_visibility"]["sentiment"],
        "ai_engines": [
            {"engine": e["engine"], "visibility_score": e["visibility_score"], "change_pct": e["vs_change"]}
            for e in report["ai_visibility"]["engines"]
        ],
        "ai_competing_brands": report["ai_visibility"]["competing_brands"],
        "content": report["content"],
    }


def _summary(summary):
    return {
        key: {"current": d["current"], "previous": d["previous"], "change_pct": d["change_pct"]}
        for key, d in summary.items()
    }


def _parse(text):
    """Pull the JSON object out of the model response, tolerating fences."""
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        raise RuntimeError("Claude did not return a JSON narrative. Raw output:\n" + text[:500])
    try:
        return json.loads(text[start:end + 1])
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Could not parse Claude's narrative JSON: {exc}")
