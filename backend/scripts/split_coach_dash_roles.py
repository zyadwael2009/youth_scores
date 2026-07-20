"""Split coach names written as "<title> <name> – <role>".

A second format found in the feed, the reverse of the "<role> ك/ <name>" one
handled by split_coach_roles.py:

    الكابتن عادل ماضي – مدرب الفريق
    إسلام عنتر — المدير الفني

One field can also hold several people, each introduced by a title marker:

    ك. سامح حسن– المدير الفني للفريق ك. مخلص ابو المجد– المدرب العام ك. ...

Those are expanded into one Coach + TeamCoach row per person, all attached to
the team(s) the original row belonged to.

    python -m scripts.split_coach_dash_roles            # dry run
    python -m scripts.split_coach_dash_roles --apply
"""

from __future__ import annotations

import re
import sys
from collections import Counter

from app import create_app
from app.extensions import db
from app.models import ClubStaff, Coach, TeamCoach
from scripts.split_coach_roles import canonical_role

DASH = r"[–—\-]"
# Markers that introduce a person; also used to split a multi-person field.
TITLE = r"(?:الكابتن|الكابتين|كابتن|الدكتور|دكتور|ك\s*\.|د\s*\.|ك/|د/)"
TITLE_SPLIT = re.compile(TITLE)
LEADING_TITLE = re.compile(rf"^{TITLE}\s*")
ENTRY = re.compile(rf"^(?P<name>[^–—\-]+?)\s*{DASH}\s*(?P<role>.+)$")


def parse_entries(raw: str) -> list[tuple[str, str]]:
    """Return [(name, canonical_role), ...] found in one field."""
    text = re.sub(r"\s+", " ", (raw or "").strip())
    if not re.search(DASH, text):
        return []

    # Several people in one field -> split on the title markers.
    chunks = [c for c in TITLE_SPLIT.split(text) if c and c.strip()]
    if len(chunks) < 2:
        chunks = [text]

    out: list[tuple[str, str]] = []
    for chunk in chunks:
        chunk = LEADING_TITLE.sub("", chunk.strip()).strip()
        m = ENTRY.match(chunk)
        if not m:
            continue
        name = re.sub(r"\s+", " ", m.group("name")).strip()
        role = canonical_role(m.group("role"))
        if name and role:
            out.append((name, role))
    return out


def main(apply: bool) -> None:
    app = create_app()
    with app.app_context():
        roles = Counter()
        touched = created = 0
        samples: list[str] = []

        for c in list(Coach.query.all()):
            entries = parse_entries(c.full_name_ar or "")
            if not entries:
                continue
            touched += 1
            tc_rows = TeamCoach.query.filter_by(coach_id=c.id).all()
            cs_rows = ClubStaff.query.filter_by(coach_id=c.id).all()

            if len(samples) < 40:
                samples.append(f"  {c.full_name_ar}")
                for n, r in entries:
                    samples.append(f"     -> {r}  |  {n}")

            first_name, first_role = entries[0]
            for n, r in entries:
                roles[r] += 1

            if not apply:
                created += (len(entries) - 1) * max(len(tc_rows), 1)
                continue

            # First person reuses the existing Coach row.
            c.full_name_ar = first_name
            for r in tc_rows:
                r.role_ar = first_role
            for r in cs_rows:
                r.role_ar = first_role

            # The rest become their own Coach, mirrored onto the same teams.
            for name, role in entries[1:]:
                extra = Coach(full_name_ar=name)
                db.session.add(extra)
                db.session.flush()
                for src in tc_rows:
                    db.session.add(TeamCoach(
                        team_id=src.team_id, coach_id=extra.id, role_ar=role,
                        start_date=src.start_date, end_date=src.end_date,
                    ))
                    created += 1
                for src in cs_rows:
                    db.session.add(ClubStaff(
                        club_id=src.club_id, coach_id=extra.id, role_ar=role,
                        start_date=src.start_date, end_date=src.end_date,
                    ))
                    created += 1

        print(f"fields matched        : {touched}")
        print(f"people found          : {sum(roles.values())}")
        print(f"new staff rows to add : {created}")
        print(f"distinct roles        : {len(roles)}")
        print("\n--- roles ---")
        for r, n in roles.most_common():
            print(f"  {n:>4}  {r}")
        print("\n--- parsed ---")
        print("\n".join(samples))

        if apply:
            db.session.commit()
            print("\nAPPLIED and committed.")
        else:
            db.session.rollback()
            print("\nDRY RUN - nothing written. Re-run with --apply to commit.")


if __name__ == "__main__":
    main(apply="--apply" in sys.argv)
