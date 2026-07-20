"""Merge coach records that are the same person written differently.

"عبدالوهاب أشرف" and "عبد الوهاب اشرف" are one man; the spacing and the hamza
differ. Names are compared after dropping diacritics, unifying alef/ya forms and
removing every space, so those collapse onto one key.

Merging is deliberately scoped to people who already share a club (club staff)
or a team (technical staff). Two men called "محمد نبيل" at different clubs are
different men, and a global merge would fuse them.

    python -m scripts.merge_similar_people            # dry run
    python -m scripts.merge_similar_people --apply
"""

from __future__ import annotations

import re
import sys
from collections import defaultdict

from app import create_app
from app.extensions import db
from app.models import ClubStaff, Coach, TeamCoach
from scripts.split_coach_roles import normalize_ar


def squash(name: str) -> str:
    """Normalised, space-free key for comparing two spellings of a name."""
    return re.sub(r"\s+", "", normalize_ar(name or ""))


def _pick_canonical(coaches: list[Coach]) -> Coach:
    """Keep the richest record: most fields filled, then the longest name."""
    def score(c: Coach):
        filled = sum(bool(v) for v in (c.full_name_en, c.birth_year,
                                       c.nationality_ar, c.profile_pic_url))
        return (filled, len(c.full_name_ar or ""), -c.id)
    return max(coaches, key=score)


def collect_groups() -> list[list[Coach]]:
    """Groups of Coach rows that share a scope and a squashed name."""
    scoped: dict[tuple[str, int, str], set[int]] = defaultdict(set)
    for s in ClubStaff.query.all():
        scoped[("club", s.club_id, squash(s.coach.full_name_ar or ""))].add(s.coach_id)
    for t in TeamCoach.query.all():
        scoped[("team", t.team_id, squash(t.coach.full_name_ar or ""))].add(t.coach_id)

    # Union coach ids that co-occur in any scope.
    parent: dict[int, int] = {}

    def find(x: int) -> int:
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for (_kind, _sid, key), ids in scoped.items():
        if not key or len(ids) < 2:
            continue
        ids_list = sorted(ids)
        for other in ids_list[1:]:
            union(ids_list[0], other)

    groups: dict[int, list[int]] = defaultdict(list)
    for cid in list(parent):
        groups[find(cid)].append(cid)

    out = []
    for members in groups.values():
        if len(members) < 2:
            continue
        out.append([db.session.get(Coach, i) for i in sorted(members)])
    return out


def main(apply: bool) -> None:
    app = create_app()
    with app.app_context():
        groups = collect_groups()
        merged = rows_repointed = rows_dropped = 0

        for coaches in groups:
            coaches = [c for c in coaches if c]
            if len(coaches) < 2:
                continue
            keep = _pick_canonical(coaches)
            drop = [c for c in coaches if c.id != keep.id]
            merged += len(drop)
            names = " | ".join(f"{c.full_name_ar}(#{c.id})" for c in coaches)
            print(f"  keep #{keep.id} {keep.full_name_ar}   <-   {names}")

            for c in drop:
                for s in ClubStaff.query.filter_by(coach_id=c.id).all():
                    twin = ClubStaff.query.filter_by(
                        club_id=s.club_id, coach_id=keep.id, role_ar=s.role_ar
                    ).first()
                    if twin:
                        rows_dropped += 1
                        if apply:
                            db.session.delete(s)
                    else:
                        rows_repointed += 1
                        if apply:
                            s.coach_id = keep.id
                for t in TeamCoach.query.filter_by(coach_id=c.id).all():
                    twin = TeamCoach.query.filter_by(
                        team_id=t.team_id, coach_id=keep.id, role_ar=t.role_ar
                    ).first()
                    if twin:
                        rows_dropped += 1
                        if apply:
                            db.session.delete(t)
                    else:
                        rows_repointed += 1
                        if apply:
                            t.coach_id = keep.id
                if apply:
                    db.session.flush()
                    db.session.delete(c)

        print(f"\ngroups found       : {len(groups)}")
        print(f"coach rows merged  : {merged}")
        print(f"staff rows moved   : {rows_repointed}")
        print(f"staff rows dropped : {rows_dropped}")

        if apply:
            db.session.commit()
            print("\nAPPLIED and committed.")
        else:
            db.session.rollback()
            print("\nDRY RUN - nothing written. Re-run with --apply to commit.")


if __name__ == "__main__":
    main(apply="--apply" in sys.argv)
