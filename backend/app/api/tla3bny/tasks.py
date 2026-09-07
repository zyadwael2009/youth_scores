"""Periodic maintenance tasks for tla3bny, triggered by an external scheduler.

Secret-gated by the admin key (X-Admin-Key header) — the same master key the platform
already uses for automation — so only the scheduler (Railway cron / a GitHub Action /
an uptime cron) can run them. Idempotent, so a repeated or missed run is harmless.
"""
from flask import jsonify

from app.services import tla3bny_reminders
from app.services.auth import has_master_key

from . import tla3bny_bp
from ._helpers import _forbid


@tla3bny_bp.post("/tasks/lineup-reminders")
def t3_task_lineup_reminders():
    """Send "submit your lineup" reminders for matches whose deadline is approaching.
    Point a scheduler at this hourly."""
    if not has_master_key():
        return _forbid()
    return jsonify({"status": "ok", **tla3bny_reminders.send_due_lineup_reminders()})
