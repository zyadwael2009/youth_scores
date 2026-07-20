"""Strip the sector title the القطاعات feed appended to club names.

That competition lists every qualifier as "<club>\\nبطل <sector>" — the club
together with the regional title it won. The import read the whole string as
the club's name, so "انبي" and "انبي بطل القاهرة الكبري" became two clubs, one
of them a duplicate carrying only the القطاعات teams.

Two outcomes per club:

  * the plain club already exists -> the duplicate's teams and staff move onto
    it and the emptied club row is deleted;
  * it does not -> only the name is cleaned, since that row *is* the club.

Moving teams can leave the target club with two squads for one age group and
season. Fusing those means repointing matches, rosters and events, which
scripts.merge_duplicate_teams already does carefully — so this script reports
them and leaves them alone. Run that one afterwards.

    python -m scripts.fix_sector_champion_clubs
    python -m scripts.fix_sector_champion_clubs --apply
"""

from __future__ import annotations

import re
import sys

from app import create_app
from app.extensions import db
from app.models import Club, ClubStaff, Team
from scripts.split_coach_roles import normalize_ar

# The title always starts at the word بطل; the club name is whatever precedes
# it. The feed separates them with a newline, but one row uses a plain space.
TITLE = re.compile(r"\s*بطل\b.*$", re.DOTALL)


def base_name(name: str | None) -> str | None:
    if not name:
        return name
    return TITLE.sub("", name).strip() or None


def main(apply: bool) -> None:
    app = create_app()
    with app.app_context():
        by_name: dict[str, list[Club]] = {}
        for c in Club.query.all():
            by_name.setdefault(normalize_ar(c.name_ar or ""), []).append(c)

        dupes = [c for c in Club.query.order_by(Club.id).all()
                 if c.name_ar and "بطل" in c.name_ar]
        if not dupes:
            print("لا توجد أندية باللقب.")
            return

        merged = renamed = teams_moved = staff_moved = 0
        followups: list[str] = []

        for c in dupes:
            base = base_name(c.name_ar)
            if not base:
                print(f"  ?? #{c.id} لا يمكن استخراج الاسم من {c.name_ar!r}")
                continue

            target = next((t for t in by_name.get(normalize_ar(base), [])
                           if t.id != c.id), None)

            if target is None:
                renamed += 1
                print(f"  تنظيف اسم #{c.id}: {base}")
                if apply:
                    c.name_ar = base
                    c.name_en = base_name(c.name_en)
                continue

            teams = Team.query.filter_by(club_id=c.id).all()
            staff = ClubStaff.query.filter_by(club_id=c.id).all()
            merged += 1
            teams_moved += len(teams)
            staff_moved += len(staff)
            print(f"  دمج #{c.id} «{base}» -> #{target.id}: "
                  f"{len(teams)} فريق، {len(staff)} من الجهاز الإداري")

            # Squads the target already fields for the same age group and season.
            existing = {t.age_group_id
                        for t in Team.query.filter_by(club_id=target.id).all()}
            for t in teams:
                if t.age_group_id in existing:
                    followups.append(
                        f"    #{target.id} «{base}» يحتاج دمج فريقين "
                        f"(مرحلة={t.age_group_id})")
                if apply:
                    t.club_id = target.id
            for s in staff:
                if apply:
                    s.club_id = target.id
            if apply:
                db.session.flush()
                db.session.delete(c)

        print(f"\nأندية ستُدمج   : {merged}")
        print(f"أسماء ستُنظَّف  : {renamed}")
        print(f"فرق ستنتقل     : {teams_moved}")
        print(f"جهاز إداري     : {staff_moved}")
        if followups:
            print("\nبعدها شغّل: python -m scripts.merge_duplicate_teams --apply")
            for f in dict.fromkeys(followups):
                print(f)

        if apply:
            db.session.commit()
            print("\nتم التنفيذ والحفظ.")
        else:
            db.session.rollback()
            print("\nDRY RUN - لم يُكتب شيء. أضف --apply للتنفيذ.")


if __name__ == "__main__":
    main(apply="--apply" in sys.argv)
