"""Move a group into its own stage, for phases that restart from zero.

The 2011 second phase was imported as just another group alongside the first
round's groups, all inside one stage. Its six qualifiers replay each other from
scratch, so it needs to be a stage of its own flagged `carries_points = False`;
only then does the table stop counting their first-round matches.

Moves the group, and every match played between its members, onto a new stage.

    python -m scripts.split_stage_from_group 18 "المرحلة التانية"
    python -m scripts.split_stage_from_group 18 "المرحلة التانية" --apply
"""

from __future__ import annotations

import sys

from app import create_app
from app.extensions import db
from app.models import Competition, Group, GroupTeam, Match, Stage
from scripts.split_coach_roles import normalize_ar


def main(competition_id: int, group_name: str, apply: bool) -> None:
    app = create_app()
    with app.app_context():
        comp = db.session.get(Competition, competition_id)
        if comp is None:
            print(f"لا توجد مسابقة #{competition_id}")
            return

        target = None
        for g in Group.query.join(Stage).filter(Stage.competition_id == competition_id).all():
            if normalize_ar(g.name_ar or "") == normalize_ar(group_name):
                target = g
                break
        if target is None:
            print(f"لم أجد مجموعة باسم {group_name!r} في المسابقة")
            return

        old_stage = target.stage
        ids = {gt.team_id for gt in GroupTeam.query.filter_by(group_id=target.id).all()}
        moving = [m for m in Match.query.filter_by(stage_id=old_stage.id).all()
                  if m.home_team_id in ids and m.away_team_id in ids]
        next_order = max(s.stage_order for s in comp.stages) + 1

        print(f"المسابقة  : #{comp.id} {comp.name_ar} [{comp.sector_ar or '-'}]")
        print(f"المجموعة  : {target.name_ar}  ({len(ids)} فريق)")
        print(f"من مرحلة  : {old_stage.stage_order} ({old_stage.name_ar})")
        print(f"إلى مرحلة : {next_order} جديدة، carries_points = False")
        print(f"مباريات ستنتقل: {len(moving)}")

        if not apply:
            db.session.rollback()
            print("\nDRY RUN - لم يُكتب شيء. أضف --apply للتنفيذ.")
            return

        new_stage = Stage(
            competition_id=comp.id,
            name_ar=target.name_ar,
            name_en=target.name_en,
            stage_order=next_order,
            type=old_stage.type,
            carries_points=False,
        )
        db.session.add(new_stage)
        db.session.flush()
        target.stage_id = new_stage.id
        for m in moving:
            m.stage_id = new_stage.id
        db.session.commit()
        print(f"\nتم: مرحلة #{new_stage.id} أُنشئت ونُقل إليها {len(moving)} مباراة.")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--apply"]
    if len(args) < 2:
        print(__doc__)
        sys.exit(1)
    main(int(args[0]), args[1], apply="--apply" in sys.argv)
