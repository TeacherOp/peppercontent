"""Deterministic helpers shared by the mock sources.

Everything is seeded so a given (client, period) always produces the same
numbers. That makes the previous period of one report equal to the current
period of the report before it — deltas stay internally consistent.
"""

import calendar
import hashlib
import math
import random

ENGINES = ["chatgpt", "perplexity", "google_aio", "copilot", "claude"]
_BASE_INDEX = 2025 * 12  # January 2025, the trend anchor.


def rng(*parts):
    """A deterministic Random seeded from the given parts."""
    key = "|".join(str(p) for p in parts)
    seed = int(hashlib.sha256(key.encode()).hexdigest(), 16) & 0xFFFFFFFF
    return random.Random(seed)


def period_index(period):
    year, month = (int(x) for x in period.split("-"))
    return year * 12 + (month - 1)


def shift_period(period, months):
    """Return the YYYY-MM that is ``months`` before ``period``."""
    idx = period_index(period) - months
    year, month = divmod(idx, 12)
    return f"{year:04d}-{month + 1:02d}"


def factor(period, phase=0.0):
    """A smooth growth-plus-seasonality multiplier (~0.9-1.3)."""
    i = period_index(period) - _BASE_INDEX
    trend = 1.0 + 0.012 * i
    seasonal = 1.0 + 0.06 * math.sin((i + phase) / 12.0 * 2 * math.pi)
    return max(0.3, trend * seasonal)


def jitter(r, spread=0.05):
    return 1.0 + r.uniform(-spread, spread)


def months_since_anchor(period):
    return period_index(period) - _BASE_INDEX


def period_label(period):
    year, month = (int(x) for x in period.split("-"))
    return f"{calendar.month_name[month]} {year}"


def period_dates(period):
    year, month = (int(x) for x in period.split("-"))
    last = calendar.monthrange(year, month)[1]
    return f"{year:04d}-{month:02d}-01", f"{year:04d}-{month:02d}-{last:02d}"


def slugify(text):
    out = "".join(c.lower() if c.isalnum() else "-" for c in text)
    while "--" in out:
        out = out.replace("--", "-")
    return out.strip("-")
