"""Configuration for the Telegram bot."""

import os

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise RuntimeError("TELEGRAM_TOKEN environment variable not set")

LANDING_URL = os.getenv("LANDING_URL", "https://example.com")
