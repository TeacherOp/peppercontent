"""AI-assisted editing of a single piece of a report's narrative.

The manager hovers a text box or recommendation, clicks "Edit with AI", and
types an instruction (e.g. "make it more concise", "lead with the revenue
number", "warmer tone"). Claude rewrites just that piece — grounded in the same
report context used to generate it, so it never invents numbers.

This returns a suggestion; it does not persist. The manager reviews the result
in edit mode and saves with the normal Save action.
"""

import json
import os

import config
from .narrative import _context

SYSTEM_PROMPT = (
    "You are an expert editor helping a Customer Success manager refine one piece "
    "of a client report drafted by Pepper Atlas (organic + AI search visibility). "
    "You are given the full report context (the numbers), the specific text being "
    "edited, and the manager's instruction.\n\n"
    "Rules:\n"
    "- Edit ONLY the piece provided; do not rewrite the whole report.\n"
    "- Stay grounded in the supplied numbers — never invent metrics or facts.\n"
    "- Keep a clear, professional, client-ready tone unless told otherwise.\n"
    "- Be concise; match the length to the instruction.\n"
    "- Follow the manager's instruction precisely.\n"
    "- Output the edited content only — no preamble, no explanation, no quotes."
)


def ai_edit(report, field, kind, current, instruction):
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY is not set — AI editing needs a Claude API key."
        )

    import anthropic  # lazy: only needed when actually calling Claude

    client = anthropic.Anthropic(api_key=api_key)
    prompt = _build_prompt(report, field, kind, current, instruction)

    response = client.messages.create(
        model=config.MODEL,
        max_tokens=1200,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )
    text = "".join(block.text for block in response.content if block.type == "text").strip()

    if kind == "recommendation":
        obj = _parse_json(text)
        return {
            "title": str(obj.get("title", "")).strip(),
            "detail": str(obj.get("detail", "")).strip(),
        }
    return {"text": _clean(text)}


def _build_prompt(report, field, kind, current, instruction):
    context = json.dumps(_context(report), indent=2)
    where = _label(field)
    if kind == "recommendation":
        return (
            f"REPORT CONTEXT (the only numbers you may use):\n{context}\n\n"
            f"You are editing one RECOMMENDATION in the report.\n"
            f"Current recommendation:\n\"\"\"\n{current}\n\"\"\"\n\n"
            f"MANAGER'S INSTRUCTION: {instruction}\n\n"
            "Return ONLY a JSON object of the form "
            '{"title": "...", "detail": "..."} — the title is a short action, the '
            "detail is one or two sentences explaining the why and expected impact."
        )
    return (
        f"REPORT CONTEXT (the only numbers you may use):\n{context}\n\n"
        f"You are editing a text box in the \"{where}\" part of the report.\n"
        f"Current text:\n\"\"\"\n{current}\n\"\"\"\n\n"
        f"MANAGER'S INSTRUCTION: {instruction}\n\n"
        "Return ONLY the rewritten text — plain prose, no quotes, no preamble."
    )


_LABELS = {
    "executive_summary": "executive summary",
    "section_insights.organic": "organic search overview",
    "section_insights.ai_visibility": "AI search visibility overview",
    "section_insights.competitive": "competitive overview",
    "section_insights.content": "content health overview",
}


def _label(field):
    return _LABELS.get(field, field or "report")


def _clean(text):
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`").strip()
        if "\n" in text:  # drop a leading language hint line
            first, rest = text.split("\n", 1)
            if len(first) < 12 and " " not in first:
                text = rest.strip()
    if len(text) >= 2 and text[0] in "\"“" and text[-1] in "\"”":
        text = text[1:-1].strip()
    return text


def _parse_json(text):
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise RuntimeError("AI did not return a valid recommendation.")
    return json.loads(text[start:end + 1])
