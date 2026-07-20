"""Merge a stage that was created by mistake back into the one before it.

Competition #10 was entered with an extra "المرحلة 1" sitting between the league
and the knockout. The source feed has no stages at all — each match carries only
a `group` ("3A", "3B", or the final) — so the league is one stage of two groups,
and the extra stage is an artefact of the entry, not of the data.

Moves every match off the doomed stage onto the target, deletes it, and closes
the gap in stage_order so the remaining stages stay 1, 2, 3...

Refuses to run if the doomed stage owns groups of its own, since those would
have to be merged too and that is not a decision this script should make.

    python -m scripts.merge_stage_into_previous 18 17
    python -m scripts.merge_stage_into_previous 18 17 --apply
"""

from __future__ import annotations

import sys

from app import create_app
from app.extensions import db
from app.models import Group, Match, Stage


def main(doomed_id: int, target_id: int, apply: bool) -> None:
    app = create_app()
    with app.app_context():
        doomed = db.session.get(Stage, doomed_id)
        target = db.session.get(Stage, target_id)
        if doomed is None or target is None:
            print("مرحلة غير موجودة")
            return
        if doomed.competition_id != target.competition_id:
            print("المرحلتان في مسابقتين مختلفتين")
            return
        if doomed.id == target.id:
            print("نفس المرحلة")
            return

        own_groups = Group.query.filter_by(stage_id=doomed.id).count()
        if own_groups:
            print(f"المرحلة {doomed.stage_order} لها {own_groups} مجموعة خاصة بها - ادمجها يدويًا أولًا")
            return

        comp = doomed.competition
        matches = Match.query.filter_by(stage_id=doomed.id).all()
        # Matches already point at groups; those groups must live on the target.
        target_groups = {g.id for g in Group.query.filter_by(stage_id=target.id).all()}
        bad = [m for m in matches if m.group_id is not None and m.group_id not in target_groups]

        print(f"المسابقة #{comp.id}: {comp.name_ar} [{comp.sector_ar or '-'}]")
        print(f"  دمج مرحلة {doomed.stage_order} ({doomed.name_ar}) في مرحلة {target.stage_order} ({target.name_ar})")
        print(f"  مباريات ستنتقل: {len(matches)}")
        if bad:
            print(f"  !! {len(bad)} مباراة مجموعتها ليست في المرحلة الهدف - أوقفت التنفيذ")
            return

        after = [s for s in comp.stages if s.stage_order > doomed.stage_order]
        for s in after:
            print(f"  إعادة ترقيم: مرحلة {s.stage_order} ({s.name_ar}) -> {s.stage_order - 1}")

        if not apply:
            db.session.rollback()
            print("\nDRY RUN - لم يُكتب شيء. أضف --apply للتنفيذ.")
            return

        for m in matches:
            m.stage_id = target.id
        db.session.delete(doomed)
        db.session.flush()
        # Shift the tail down one at a time; stage_order is unique per competition.
        for s in sorted(after, key=lambda x: x.stage_order):
            s.stage_order -= 1
        db.session.commit()
        print(f"\nتم: {len(matches)} مباراة نُقلت، ومرحلة #{doomed_id} حُذفت.")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--apply"]
    if len(args) < 2:
        print(__doc__)
        sys.exit(1)
    main(int(args[0]), int(args[1]), apply="--apply" in sys.argv)
