"""Move club-staff entries back onto the team they came from.

Some lines in a team's `information` field describe the team, not the club
("مشرف الفريق"). They were imported as ClubStaff; this puts them on the team's
technical staff instead.

The originating team is recovered by re-reading the feed: each feed team entry
has an id ("t007") that our Team rows carry in `source_ref` as
"<competition>|<feed_team_id>", so club + that suffix identifies the team.

    python -m scripts.move_club_staff_to_team "مشرف الفريق" "المشرف على الفريق"
    python -m scripts.move_club_staff_to_team "مشرف الفريق" --apply
"""

from __future__ import annotations

import re
import sys
from collections import defaultdict

from sqlalchemy import or_

from app import create_app
from app.extensions import db
from app.models import Club, ClubStaff, Team, TeamCoach
from scripts.import_club_staff_from_info import CONFIG_URL, fetch, parse_line, team_name
from scripts.split_coach_roles import normalize_ar


def _active_season_start():
    """When a coaching spell is taken to have started.

    A team is not tied to a season, so this comes from the active season rather
    than from the team itself.
    """
    from app.models import Season
    s = (Season.query.order_by(Season.is_active.desc(), Season.start_date.desc())
         .first())
    return s.start_date if s else None


def main(roles: list[str], apply: bool) -> None:
    wanted = {normalize_ar(r) for r in roles}
    app = create_app()
    with app.app_context():
        clubs: dict[str, Club] = {}
        for c in Club.query.all():
            for nm in (c.name_ar, c.name_en):
                if nm:
                    clubs.setdefault(normalize_ar(nm), c)

        data = fetch(fetch(CONFIG_URL)["latestDataUrl"])
        feeds: list[str] = []
        for s in data.get("seasons") or []:
            for c in s.get("competitions") or []:
                for a in c.get("ages") or []:
                    u = a.get("matchesurl")
                    u = [u] if isinstance(u, str) else (u or [])
                    feeds.extend([x for x in u if x])

        # (club_id, person) -> feed team ids that mentioned them
        origin: dict[tuple[int, str], set[str]] = defaultdict(set)
        for url in dict.fromkeys(feeds):
            try:
                feed = fetch(url)
            except Exception:  # noqa: BLE001
                continue
            for t in feed.get("teams") or []:
                info = (t.get("information") or "").strip()
                if not info:
                    continue
                club = clubs.get(normalize_ar(team_name(t)))
                if club is None:
                    continue
                for line in re.split(r"[\r\n]+", info):
                    parsed = parse_line(line)
                    if not parsed:
                        continue
                    name, role = parsed
                    if normalize_ar(role) in wanted:
                        origin[(club.id, normalize_ar(name))].add(str(t.get("team_id") or ""))

        moved = unresolved = 0
        for s in list(ClubStaff.query.all()):
            if normalize_ar(s.role_ar or "") not in wanted:
                continue
            person = normalize_ar(s.coach.full_name_ar or "")
            feed_ids = origin.get((s.club_id, person), set())
            teams = []
            for fid in feed_ids:
                if not fid:
                    continue
                # A squad's source_ref now accumulates every feed id it carried,
                # each terminated by a space ("12|t7 18|t2 "); the first pattern
                # matches an id in any position, the second a legacy lone id.
                teams += Team.query.filter(
                    Team.club_id == s.club_id,
                    or_(
                        Team.source_ref.like(f"%|{fid} %"),
                        Team.source_ref.like(f"%|{fid}"),
                    ),
                ).all()
            teams = list({t.id: t for t in teams}.values())
            if not teams:
                unresolved += 1
                print(f"  ?? club={s.club_id} {s.coach.full_name_ar} ({s.role_ar}) - team not resolved")
                continue
            for t in teams:
                print(f"  -> team {t.id} | {s.role_ar} | {s.coach.full_name_ar}")
                moved += 1
                if apply:
                    db.session.add(TeamCoach(
                        team_id=t.id, coach_id=s.coach_id, role_ar=s.role_ar,
                        start_date=_active_season_start(),
                    ))
            if apply:
                db.session.delete(s)

        print(f"\nteam_coach rows to add : {moved}")
        print(f"unresolved             : {unresolved}")
        if apply:
            db.session.commit()
            print("\nAPPLIED and committed.")
        else:
            db.session.rollback()
            print("\nDRY RUN - nothing written. Re-run with --apply to commit.")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--apply"]
    if not args:
        print(__doc__)
        sys.exit(1)
    main(args, apply="--apply" in sys.argv)
