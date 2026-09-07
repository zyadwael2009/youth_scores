"""iCalendar (.ics) feeds for tla3bny fixtures.

Two public reads: one match ("add to calendar") and a whole team's fixtures (a
subscribable webcal feed — a parent subscribes once and their kid's matches keep
updating). Times are written as floating local time (the audience is all in one
timezone), so a calendar shows the kickoff exactly as the site does.
"""
from datetime import datetime, time, timedelta, timezone

from flask import Response
from sqlalchemy import or_

from app.models import Tla3bnyMatch, Tla3bnyTeam

from . import tla3bny_bp


def _esc(s: str | None) -> str:
    """Escape the ICS text special characters."""
    return (
        (s or "")
        .replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\n", "\\n")
    )


def _fold(line: str) -> str:
    """Fold a content line to the 75-octet RFC-5545 limit, UTF-8 safe (Arabic is
    multibyte). Continuation lines begin with a single space."""
    if len(line.encode("utf-8")) <= 75:
        return line
    parts: list[str] = []
    cur = ""
    for ch in line:
        candidate = cur + ch
        if len(candidate.encode("utf-8")) > 73:
            parts.append(cur)
            cur = " " + ch
        else:
            cur = candidate
    parts.append(cur)
    return "\r\n".join(parts)


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _parse_time(value: str | None) -> time | None:
    if not value:
        return None
    try:
        hh, mm = value.strip().split(":")[:2]
        h, m = int(hh), int(mm)
        if 0 <= h <= 23 and 0 <= m <= 59:
            return time(h, m)
    except (ValueError, AttributeError):
        pass
    return None


def _vevent(match: Tla3bnyMatch) -> list[str]:
    """The VEVENT lines for one dated match (empty list if it has no date)."""
    if not match.date:
        return []
    home = match.home_team.display_name() if match.home_team else "?"
    away = match.away_team.display_name() if match.away_team else "?"
    comp = match.competition.name if match.competition else ""
    summary = f"{home} × {away}" + (f" — {comp}" if comp else "")

    lines = [
        "BEGIN:VEVENT",
        f"UID:t3-match-{match.id}@youthscores",
        f"DTSTAMP:{_utc_stamp()}",
    ]
    t = _parse_time(match.time)
    if t is not None:
        start = datetime.combine(match.date, t)
        end = start + timedelta(minutes=90)
        lines.append(f"DTSTART:{start.strftime('%Y%m%dT%H%M%S')}")
        lines.append(f"DTEND:{end.strftime('%Y%m%dT%H%M%S')}")
    else:
        # No kickoff time recorded → an all-day event (DTEND is the exclusive next day).
        lines.append(f"DTSTART;VALUE=DATE:{match.date.strftime('%Y%m%d')}")
        lines.append(f"DTEND;VALUE=DATE:{(match.date + timedelta(days=1)).strftime('%Y%m%d')}")

    lines.append(f"SUMMARY:{_esc(summary)}")
    if match.venue:
        lines.append(f"LOCATION:{_esc(match.venue)}")
    if match.round:
        lines.append(f"DESCRIPTION:{_esc(match.round)}")
    lines.append("END:VEVENT")
    return lines


def _calendar(name: str, matches: list[Tla3bnyMatch]) -> str:
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//youthscores//tla3bny//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{_esc(name)}",
    ]
    for m in matches:
        lines.extend(_vevent(m))
    lines.append("END:VCALENDAR")
    return "\r\n".join(_fold(ln) for ln in lines) + "\r\n"


def _ics_response(name: str, matches: list[Tla3bnyMatch], filename: str) -> Response:
    body = _calendar(name, matches)
    return Response(
        body,
        mimetype="text/calendar",
        headers={
            "Content-Type": "text/calendar; charset=utf-8",
            "Content-Disposition": f'inline; filename="{filename}"',
            "Cache-Control": "public, max-age=300",
        },
    )


@tla3bny_bp.get("/matches/<int:match_id>/calendar.ics")
def match_calendar(match_id: int):
    """A single match as a downloadable .ics ("add to calendar")."""
    match = Tla3bnyMatch.query.get_or_404(match_id)
    if not match.date:
        return Response("match has no date", status=404)
    name = match.competition.name if match.competition else "tla3bny"
    return _ics_response(name, [match], f"match-{match_id}.ics")


@tla3bny_bp.get("/teams/<int:team_id>/fixtures.ics")
def team_fixtures_calendar(team_id: int):
    """A team's dated fixtures as a subscribable feed (webcal). Updates as the
    organizer schedules/edits matches."""
    team = Tla3bnyTeam.query.get_or_404(team_id)
    matches = (
        Tla3bnyMatch.query.filter(
            or_(Tla3bnyMatch.home_team_id == team_id,
                Tla3bnyMatch.away_team_id == team_id),
            Tla3bnyMatch.date.isnot(None),
        )
        .order_by(Tla3bnyMatch.date.asc())
        .limit(300)
        .all()
    )
    return _ics_response(team.display_name(), matches, f"team-{team_id}-fixtures.ics")
