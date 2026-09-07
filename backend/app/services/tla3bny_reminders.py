"""The periodic "submit your lineup" reminder.

A scheduler hits POST /api/tla3bny/tasks/lineup-reminders (secret-gated) every hour;
this pings the staff of any team that hasn't posted a lineup for a match whose lineup
deadline is approaching. Idempotent — one reminder per match, so it's safe to run
repeatedly and a missed run just catches up on the next.

Match times are local (the audience is one timezone), so "now" is compared in that
timezone (Africa/Cairo by default, overridable via TLA3BNY_TIMEZONE).
"""
from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from flask import current_app

from app.extensions import db
from app.models import Tla3bnyLineup, Tla3bnyLineupSlot, Tla3bnyMatch, Tla3bnyTeam
from app.services import notifications

# Send the reminder within this window before the lineup deadline.
REMINDER_LEAD = timedelta(hours=3)
DEFAULT_DEADLINE_MINUTES = 60
DEFAULT_TZ = "Africa/Cairo"


def _now_local() -> datetime:
    tz = current_app.config.get("TLA3BNY_TIMEZONE") or DEFAULT_TZ
    return datetime.now(ZoneInfo(tz)).replace(tzinfo=None)


def _team_has_lineup(match_id: int, team_id: int) -> bool:
    """True once a team has posted a lineup with at least one player for this match."""
    return db.session.query(Tla3bnyLineupSlot.id).join(
        Tla3bnyLineup, Tla3bnyLineupSlot.lineup_id == Tla3bnyLineup.id
    ).filter(
        Tla3bnyLineup.match_id == match_id,
        Tla3bnyLineup.team_id == team_id,
        Tla3bnyLineupSlot.player_id.isnot(None),
    ).first() is not None


def send_due_lineup_reminders(now_local: datetime | None = None) -> dict:
    """Ping the staff of any team without a submitted lineup for a match whose deadline
    is inside the reminder window. Guarded by ``lineup_reminder_sent_at`` so a team is
    reminded at most once per match."""
    now = now_local or _now_local()
    candidates = (
        Tla3bnyMatch.query.filter(
            Tla3bnyMatch.status == "scheduled",
            Tla3bnyMatch.date.isnot(None),
            Tla3bnyMatch.time.isnot(None),
            Tla3bnyMatch.lineup_reminder_sent_at.is_(None),
            Tla3bnyMatch.date >= (now.date() - timedelta(days=1)),
            Tla3bnyMatch.date <= (now.date() + timedelta(days=2)),
        ).all()
    )

    reminded_matches = 0
    reminded_teams = 0
    for m in candidates:
        kickoff = m.match_date  # naive local (date + HH:MM)
        if kickoff is None or kickoff <= now:
            continue
        rules = m.rules
        lead_min = (rules.lineup_deadline_minutes if rules and rules.lineup_deadline_minutes
                    else DEFAULT_DEADLINE_MINUTES)
        deadline = kickoff - timedelta(minutes=lead_min)
        # Only in the lead window before the deadline — not too early, not after it.
        if not (deadline - REMINDER_LEAD <= now <= deadline):
            continue

        home = db.session.get(Tla3bnyTeam, m.home_team_id)
        away = db.session.get(Tla3bnyTeam, m.away_team_id)
        names = {
            m.home_team_id: home.display_name() if home else "فريق",
            m.away_team_id: away.display_name() if away else "فريق",
        }
        for tid in (m.home_team_id, m.away_team_id):
            if tid and not _team_has_lineup(m.id, tid):
                opp = m.away_team_id if tid == m.home_team_id else m.home_team_id
                notifications.notify_tla3bny_lineup_due(
                    m, tid, names.get(tid, "فريق"), names.get(opp, "الخصم"))
                reminded_teams += 1
        # Mark reminded once we're in-window (even if both teams already submitted), so
        # the match isn't rescanned every run.
        m.lineup_reminder_sent_at = now
        reminded_matches += 1

    db.session.commit()
    return {"matches": reminded_matches, "teams": reminded_teams}
