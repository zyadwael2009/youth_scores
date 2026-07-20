"""Re-attach groups to the stage they actually belong to.

These competitions run a full single round-robin first, then split the table
into an "الاوائل" group and a placings group that play each other again. The
JSON import hung both groups off stage 1 — the round-robin — because that is
where it was creating groups; stage 2 was left with no groups at all and its
matches with no `group_id`.

The fix moves each group onto the next stage and stamps that stage's matches
with their group. It refuses to touch a competition unless the shape proves the
reading is right:

  * the source stage has groups but not one match assigned to a group,
  * the next stage has no groups of its own,
  * every match in the next stage is between two members of the same group.

That last check is what makes the match->group assignment unambiguous. A source
stage left with no groups is also retyped `group` -> `league`, since a single
table is what it now is.

    python -m scripts.move_groups_to_next_stage            # scan, list candidates
    python -m scripts.move_groups_to_next_stage 1 2 3 4 5 6
    python -m scripts.move_groups_to_next_stage 1 2 3 4 5 6 --apply
"""

from __future__ import annotations

import sys

from app import create_app
from app.extensions import db
from app.models import Competition, Group, GroupTeam, Match, Stage


class Rejected(Exception):
    """The competition does not match the shape this script repairs."""


def plan(comp: Competition):
    """Return (source_stage, target_stage, groups, {match: group_id}).

    Raises Rejected with a reason when the competition is not a candidate.
    """
    stages = sorted(comp.stages, key=lambda s: s.stage_order)
    if len(stages) < 2:
        raise Rejected("مرحلة واحدة فقط")

    src = next((s for s in stages if s.groups), None)
    if src is None:
        raise Rejected("لا توجد مجموعات")

    grouped = Match.query.filter(
        Match.stage_id == src.id, Match.group_id.isnot(None)
    ).count()
    if grouped:
        raise Rejected(f"المرحلة {src.stage_order} بها {grouped} مباراة موزّعة على مجموعات بالفعل")

    after = [s for s in stages if s.stage_order > src.stage_order]
    if not after:
        raise Rejected(f"لا توجد مرحلة بعد المرحلة {src.stage_order}")
    dst = after[0]
    if dst.groups:
        raise Rejected(f"المرحلة {dst.stage_order} لها مجموعاتها الخاصة")

    member: dict[int, int] = {}
    for g in src.groups:
        for gt in GroupTeam.query.filter_by(group_id=g.id).all():
            member[gt.team_id] = g.id

    assign: dict[int, int] = {}
    stray = []
    for m in Match.query.filter_by(stage_id=dst.id).all():
        gh, ga = member.get(m.home_team_id), member.get(m.away_team_id)
        if gh is None or ga is None:
            stray.append((m, "فريق خارج المجموعات"))
        elif gh != ga:
            stray.append((m, "الفريقان في مجموعتين مختلفتين"))
        else:
            assign[m.id] = gh
    if stray:
        raise Rejected(
            f"{len(stray)} مباراة في المرحلة {dst.stage_order} لا تنتمي لمجموعة واحدة "
            f"(أول واحدة: مباراة #{stray[0][0].id} - {stray[0][1]})"
        )
    if not assign:
        raise Rejected(f"المرحلة {dst.stage_order} بلا مباريات")

    return src, dst, list(src.groups), assign


def report(comp: Competition, src: Stage, dst: Stage, groups: list[Group], assign: dict) -> None:
    print(f"\nالمسابقة #{comp.id}: {comp.name_ar} [{comp.sector_ar or '-'}]")
    print(f"  من مرحلة {src.stage_order} ({src.name_ar})  ->  مرحلة {dst.stage_order} ({dst.name_ar})")
    for g in groups:
        n_teams = GroupTeam.query.filter_by(group_id=g.id).count()
        n_matches = sum(1 for gid in assign.values() if gid == g.id)
        print(f"    · {g.name_ar}: {n_teams} فريق، {n_matches} مباراة")
    if src.type == "group":
        print(f"  نوع المرحلة {src.stage_order}: group -> league")


def main(ids: list[int], apply: bool) -> None:
    app = create_app()
    with app.app_context():
        if not ids:
            print("مسح كل المسابقات بحثًا عن الحالة:\n")
            for comp in Competition.query.order_by(Competition.id).all():
                try:
                    src, dst, groups, assign = plan(comp)
                except Rejected:
                    continue
                print(f"  #{comp.id:<3} {comp.name_ar} [{comp.sector_ar or '-'}] "
                      f"- {len(groups)} مجموعة، {len(assign)} مباراة")
            print("\nمرّر أرقام المسابقات لعرض التفاصيل، ثم --apply للتنفيذ.")
            return

        total_groups = total_matches = 0
        for cid in ids:
            comp = db.session.get(Competition, cid)
            if comp is None:
                print(f"\n!! لا توجد مسابقة #{cid}")
                continue
            try:
                src, dst, groups, assign = plan(comp)
            except Rejected as e:
                print(f"\n!! تخطّي #{cid} {comp.name_ar}: {e}")
                continue

            report(comp, src, dst, groups, assign)
            total_groups += len(groups)
            total_matches += len(assign)

            if apply:
                for g in groups:
                    g.stage_id = dst.id
                for mid, gid in assign.items():
                    db.session.get(Match, mid).group_id = gid
                if src.type == "group":
                    src.type = "league"

        print(f"\nالإجمالي: {total_groups} مجموعة، {total_matches} مباراة")
        if apply:
            db.session.commit()
            print("تم التنفيذ والحفظ.")
        else:
            db.session.rollback()
            print("DRY RUN - لم يُكتب شيء. أضف --apply للتنفيذ.")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--apply"]
    main([int(a) for a in args], apply="--apply" in sys.argv)
