"""Central configuration for the Atlas Report Builder."""

# Claude model used for narrative generation.
# Pinned to the latest Sonnet per project convention.
MODEL = "claude-sonnet-4-5-20250929"
MAX_TOKENS = 4000

# Most-recent reporting period available in the demo dataset (YYYY-MM).
# The picker offers this month and the five preceding it.
LATEST_PERIOD = "2025-10"
PERIOD_CHOICES = 6

# Reporting cadences and how many months back each compares against.
CADENCES = {
    "Weekly": 1,
    "Monthly": 1,
    "Quarterly": 3,
}

# A page is a refresh candidate when it hasn't been touched in this many days
# and still pulls meaningful organic traffic.
STALE_DAYS = 180
REFRESH_MIN_TRAFFIC = 700
