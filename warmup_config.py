"""
warmup_config.py
────────────────
Centralized configuration constants for the Email Warmup Engine.

Edit FROM_EMAIL to match your verified Resend domain before running.
"""

# ---------------------------------------------------------------------------
# Warm-up schedule: maps Day → number of emails to send that day.
# After the last explicit day the engine falls back to DEFAULT_MAX_VOLUME.
# ---------------------------------------------------------------------------
WARMUP_SCHEDULE: dict[int, int] = {
    1: 5,
    2: 10,
    3: 10,
    4: 20,
    5: 20,
    6: 30,
    7: 50,
}

# ---------------------------------------------------------------------------
# Pacing – randomized delay window between individual sends (in seconds).
# 180 s = 3 min, 420 s = 7 min
# ---------------------------------------------------------------------------
MIN_DELAY_SECONDS: int = 180
MAX_DELAY_SECONDS: int = 420

# ---------------------------------------------------------------------------
# File paths
# ---------------------------------------------------------------------------
STATE_FILE: str = "warmup_state.json"
SEED_CSV: str = "seed_emails.csv"
LOG_FILE: str = "warmup.log"

# ---------------------------------------------------------------------------
# Sender identity – update this to your verified Resend domain
# ---------------------------------------------------------------------------
FROM_EMAIL: str = "abdulmuiz@vectralautomation.tech"

# ---------------------------------------------------------------------------
# Fallback daily volume for days beyond the explicit schedule
# ---------------------------------------------------------------------------
DEFAULT_MAX_VOLUME: int = 100
