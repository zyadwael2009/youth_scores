"""Move a role from a team's technical staff to the club's youth-sector staff.

Some imported roles are club-level posts (رئيس قطاع الناشئين, مدير الكرة, ...)
that were attached to every team of the club as if they were coaches. This
lifts them to ClubStaff, where they belong, and removes the TeamCoach rows.

A person holding the post across several teams of one club collapses into a
single ClubStaff row.

    python -m scripts.move_role_to_club_staff "رئيس قطاع الناشئين"
    python -m scripts.move_role_to_club_staff "رئيس قطاع الناشئين" --apply
"""

from __future__ import annotations

import sys

from app import create_app
from app.extensions import db
from app.models import ClubStaff, TeamCoach


def main(role: str, apply: bool) -> None:
    app = create_app()
    with app.app_context():
        rows = TeamCoach.query.filter_by(role_ar=role).all()
        if not rows:
            print(f"no team_coach rows with role {role!r}")
            return

        # (club_id, coach_id) -> the TeamCoach rows contributing to it
        grouped: dict[tuple[int, int], list[TeamCoach]] = {}
        for r in rows:
            club_id = r.team.club_id
            grouped.setdefault((club_id, r.coach_id), []).append(r)

        created = skipped = removed = 0
        print(f"role                 : {role}")
        print(f"team_coach rows      : {len(rows)}")
        print(f"distinct club+person : {len(grouped)}\n")

        for (club_id, coach_id), src_rows in grouped.items():
            existing = ClubStaff.query.filter_by(
                club_id=club_id, coach_id=coach_id, role_ar=role
            ).first()
            name = src_rows[0].coach.full_name_ar or src_rows[0].coach.full_name_en
            teams = ", ".join(str(r.team_id) for r in src_rows)
            if existing:
                skipped += 1
                print(f"  = club {club_id}: {name}  (already club staff; teams {teams})")
            else:
                created += 1
                print(f"  + club {club_id}: {name}  (from teams {teams})")
                if apply:
                    db.session.add(ClubStaff(
                        club_id=club_id, coach_id=coach_id, role_ar=role,
                        start_date=src_rows[0].start_date,
                        end_date=src_rows[0].end_date,
                    ))
            removed += len(src_rows)
            if apply:
                for r in src_rows:
                    db.session.delete(r)

        print(f"\nclub_staff to create : {created}")
        print(f"already present      : {skipped}")
        print(f"team_coach to remove : {removed}")

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
    main(args[0], apply="--apply" in sys.argv)
