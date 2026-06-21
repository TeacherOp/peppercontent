"""Period-over-period math shared across report sections."""


def delta(current, previous, lower_is_better=False):
    """Compare two numbers and label the movement.

    Returns the raw values, percent change, a direction, and whether the move
    counts as an improvement (position/avg-position are lower-is-better).
    """
    current = float(current)
    previous = float(previous)

    if previous == 0:
        change = 0.0
    else:
        change = (current - previous) / previous * 100.0

    if abs(change) < 0.05:
        direction = "flat"
        improved = None
    else:
        rising = change > 0
        direction = "up" if rising else "down"
        improved = rising != lower_is_better

    return {
        "current": _round(current),
        "previous": _round(previous),
        "change_pct": round(change, 1),
        "direction": direction,
        "improved": improved,
    }


def _round(value):
    return round(value, 2) if abs(value) < 100 else round(value)
