"""
warmup_engine.py
────────────────
Domain warm-up email sender powered by the Resend API.

Usage:
    python warmup_engine.py

The engine reads configuration from warmup_config.py, loads seed
recipients from seed_emails.csv, and persists daily progress in
warmup_state.json so it can safely resume after interruptions.
"""

from __future__ import annotations

import csv
import itertools
import json
import logging
import os
import random
import sys
import time
from datetime import date, datetime
from pathlib import Path
from typing import Any

import resend
from dotenv import load_dotenv

from content_templates import TEMPLATES
from warmup_config import (
    DEFAULT_MAX_VOLUME,
    FROM_EMAIL,
    LOG_FILE,
    MAX_DELAY_SECONDS,
    MIN_DELAY_SECONDS,
    SEED_CSV,
    STATE_FILE,
    WARMUP_SCHEDULE,
)

# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------
_BASE_DIR = Path(__file__).resolve().parent


class EmailWarmupEngine:
    """Orchestrates domain warm-up sends via the Resend API.

    Responsibilities
    ─────────────────
    • Load & validate the Resend API key from the environment.
    • Track warm-up progress (current day, emails sent) in a JSON state
      file so the engine is crash-safe and idempotent across runs.
    • Read seed recipients from a CSV file.
    • Generate randomised, realistic email content.
    • Pace outbound sends with a randomised delay window.
    """

    # ── Initialisation ────────────────────────────────────────────────

    def __init__(self) -> None:
        """Initialise the engine: load env, configure logging, set up
        the Resend client."""
        load_dotenv(dotenv_path=_BASE_DIR / ".env")

        self._configure_logging()
        self.logger.info("Initialising Email Warmup Engine …")

        api_key = os.getenv("RESEND_API_KEY")
        if not api_key:
            self.logger.critical(
                "RESEND_API_KEY not found in environment. "
                "Add it to your .env file and try again."
            )
            sys.exit(1)

        resend.api_key = api_key
        self.logger.info("Resend API key loaded successfully.")

    # ── Logging ───────────────────────────────────────────────────────

    def _configure_logging(self) -> None:
        """Set up a logger that writes to both a file and the console."""
        self.logger = logging.getLogger("warmup_engine")
        self.logger.setLevel(logging.DEBUG)

        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # File handler – append mode so history is preserved across runs.
        file_handler = logging.FileHandler(
            _BASE_DIR / LOG_FILE, encoding="utf-8"
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)

        # Console handler – INFO and above only to keep stdout clean.
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    # ── State Management ──────────────────────────────────────────────

    def _load_state(self) -> dict[str, Any]:
        """Load persisted state from the JSON file.

        Returns a fresh Day-1 state if the file does not exist yet.
        """
        state_path = _BASE_DIR / STATE_FILE
        if state_path.exists():
            with open(state_path, "r", encoding="utf-8") as fh:
                state: dict[str, Any] = json.load(fh)
            self.logger.info(
                "State loaded — Day %s, %s emails sent today, "
                "%s total lifetime sends.",
                state["current_day"],
                state["emails_sent_today"],
                state["total_emails_sent"],
            )
            return state

        self.logger.info("No state file found. Starting fresh at Day 1.")
        return {
            "current_day": 1,
            "emails_sent_today": 0,
            "last_run_date": str(date.today()),
            "total_emails_sent": 0,
        }

    def _save_state(self, state: dict[str, Any]) -> None:
        """Persist the current state to disk (atomic-safe on most OS)."""
        state_path = _BASE_DIR / STATE_FILE
        with open(state_path, "w", encoding="utf-8") as fh:
            json.dump(state, fh, indent=2)
        self.logger.debug("State saved to %s.", STATE_FILE)

    def _advance_day_if_needed(self, state: dict[str, Any]) -> dict[str, Any]:
        """If today's date is newer than *last_run_date*, advance the
        warm-up day counter and reset the daily send tally."""
        today = str(date.today())
        if state["last_run_date"] != today:
            state["current_day"] += 1
            state["emails_sent_today"] = 0
            state["last_run_date"] = today
            self.logger.info(
                "New calendar day detected. Advanced to warm-up Day %s.",
                state["current_day"],
            )
        return state

    # ── Volume Calculation ────────────────────────────────────────────

    @staticmethod
    def _get_daily_volume(current_day: int) -> int:
        """Return the target send volume for *current_day*.

        Falls back to DEFAULT_MAX_VOLUME for days beyond the explicit
        WARMUP_SCHEDULE.
        """
        return WARMUP_SCHEDULE.get(current_day, DEFAULT_MAX_VOLUME)

    # ── Data Ingestion ────────────────────────────────────────────────

    def _load_seed_emails(self) -> list[dict[str, str]]:
        """Parse the seed CSV and return a list of recipient dicts.

        Expected CSV columns: ``email``, ``name``.
        """
        csv_path = _BASE_DIR / SEED_CSV
        if not csv_path.exists():
            self.logger.critical(
                "Seed CSV not found at %s. Create the file and try again.",
                csv_path,
            )
            sys.exit(1)

        recipients: list[dict[str, str]] = []
        with open(csv_path, "r", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                email = row.get("email", "").strip()
                name = row.get("name", "").strip()
                if email:
                    recipients.append({"email": email, "name": name})

        if not recipients:
            self.logger.critical(
                "Seed CSV is empty or malformed. "
                "Ensure it has 'email' and 'name' columns."
            )
            sys.exit(1)

        self.logger.info("Loaded %d seed recipients.", len(recipients))
        return recipients

    # ── Content Generation ────────────────────────────────────────────

    def _generate_content(self) -> tuple[str, str]:
        """Return a randomly selected (subject, body) pair."""
        subject, body = random.choice(TEMPLATES)
        self.logger.debug("Selected template — subject: '%s'", subject)
        return subject, body

    # ── Email Dispatch ────────────────────────────────────────────────

    def _send_email(
        self, recipient: dict[str, str], subject: str, body: str
    ) -> bool:
        """Send a single email via the Resend API.

        Returns True on success, False on failure. All errors are logged
        but never re-raised, so the run loop continues uninterrupted.
        """
        to_address = recipient["email"]
        try:
            params: resend.Emails.SendParams = {
                "from": FROM_EMAIL,
                "to": [to_address],
                "subject": subject,
                "text": body,
            }
            response = resend.Emails.send(params)
            self.logger.info(
                "✓ Email sent to %s  |  Resend ID: %s",
                to_address,
                response.get("id", "N/A") if isinstance(response, dict) else response,
            )
            return True

        except resend.exceptions.ResendError as exc:
            self.logger.error(
                "✗ Resend API error sending to %s: %s", to_address, exc
            )
            return False
        except (ConnectionError, TimeoutError) as exc:
            self.logger.error(
                "✗ Network error sending to %s: %s", to_address, exc
            )
            return False
        except Exception as exc:  # noqa: BLE001
            self.logger.error(
                "✗ Unexpected error sending to %s: %s", to_address, exc
            )
            return False

    # ── Pacing ────────────────────────────────────────────────────────

    def _random_delay(self) -> None:
        """Sleep for a random duration between MIN_DELAY and MAX_DELAY
        to mimic manual sending cadence."""
        delay = random.randint(MIN_DELAY_SECONDS, MAX_DELAY_SECONDS)
        minutes, seconds = divmod(delay, 60)
        self.logger.info(
            "Pacing delay: sleeping for %dm %ds …", minutes, seconds
        )
        time.sleep(delay)

    # ── Main Orchestrator ─────────────────────────────────────────────

    def run(self) -> None:
        """Execute a single warm-up session.

        Flow
        ────
        1. Load (or initialise) state.
        2. Advance the day counter if a new calendar day.
        3. Calculate remaining sends for today.
        4. Loop: pick recipient → generate content → send → delay → save.
        5. Log a run summary.
        """
        state = self._load_state()
        state = self._advance_day_if_needed(state)

        daily_target = self._get_daily_volume(state["current_day"])
        remaining = daily_target - state["emails_sent_today"]

        self.logger.info(
            "Day %s  |  Target: %d  |  Already sent: %d  |  Remaining: %d",
            state["current_day"],
            daily_target,
            state["emails_sent_today"],
            remaining,
        )

        if remaining <= 0:
            self.logger.info(
                "Daily target already met. Nothing to send. "
                "Run again tomorrow for Day %d.",
                state["current_day"] + 1,
            )
            return

        recipients = self._load_seed_emails()
        recipient_cycle = itertools.cycle(recipients)

        success_count = 0
        error_count = 0

        for i in range(1, remaining + 1):
            recipient = next(recipient_cycle)
            subject, body = self._generate_content()

            self.logger.info(
                "── Send %d/%d  →  %s", i, remaining, recipient["email"]
            )

            if self._send_email(recipient, subject, body):
                success_count += 1
                state["emails_sent_today"] += 1
                state["total_emails_sent"] += 1
            else:
                error_count += 1

            # Persist after every attempt so progress is never lost.
            self._save_state(state)

            # Apply pacing delay between sends (skip after the last one).
            if i < remaining:
                self._random_delay()

        # ── Run Summary ───────────────────────────────────────────────
        self.logger.info("═" * 50)
        self.logger.info("Run complete for Day %s.", state["current_day"])
        self.logger.info("  Successful sends : %d", success_count)
        self.logger.info("  Failed sends     : %d", error_count)
        self.logger.info("  Lifetime total   : %d", state["total_emails_sent"])
        self.logger.info("═" * 50)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    engine = EmailWarmupEngine()
    engine.run()
