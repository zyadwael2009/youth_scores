"""Report how ready each competition is for stage-scoped standings.

Today's table is built from a group's members plus *every* match in the
competition -- stages are ignored entirely -- so all competitions currently
compute correctly no matter which stage their groups and matches sit in.

That stops being true the moment a stage can say "start from zero"
(`carries_points`), because then the group's stage decides which matches count.
This checks the two things that will matter then:

  * a group's matches must live in the group's own stage
  * every enrolled team should belong to a group

    python -m scripts.check_competition_structure
    python -m scripts.check_competition_structure --all   # include ready ones
"""

from __future__ import annotations

import sys
from collections import Counter

from app import create_app
from app.extensions import db
from app.models import (
    AgeGroup,
    Competition,
    CompetitionTeam,
    Group,
    GroupTeam,
    Match,
    Stage,
)
from scripts.split_coach_roles import normalize_ar


def check(c: Competition) -> list[str]:
    """Return a list of problems found in one competition."""
    problems: list[str] = []
    stages = Stage.query.filter_by(competition_id=c.id).order_by(Stage.stage_order).all()
    if not stages:
        return ["لا توجد مراحل على الإطلاق"]

    enrolled = {ct.team_id for ct in CompetitionTeam.query.filter_by(competition_id=c.id).all()}
    all_grouped: set[int] = set()

    for s in stages:
        groups = Group.query.filter_by(stage_id=s.id).all()
        matches = Match.query.filter_by(stage_id=s.id).all()
        gnames = {normalize_ar(g.name_ar or g.name_en or "") for g in groups}
        for g in groups:
            all_grouped |= {gt.team_id for gt in GroupTeam.query.filter_by(group_id=g.id).all()}

        if s.type == "knockout":
            continue

        all_matches = Match.query.join(Stage).filter(Stage.competition_id == c.id).all()
        for g in groups:
            ids = {gt.team_id for gt in GroupTeam.query.filter_by(group_id=g.id).all()}
            if not ids:
                problems.append(f"مرحلة {s.stage_order}: مجموعة '{g.name_ar}' بلا فرق")
                continue
            here = sum(1 for m in matches
                       if m.home_team_id in ids and m.away_team_id in ids)
            anywhere = sum(1 for m in all_matches
                           if m.home_team_id in ids and m.away_team_id in ids)
            if anywhere == 0:
                problems.append(
                    f"مرحلة {s.stage_order}: مجموعة '{g.name_ar}' ({len(ids)} فريق) بلا مباريات إطلاقًا")
            elif here != anywhere:
                problems.append(
                    f"مرحلة {s.stage_order}: مجموعة '{g.name_ar}' لها {anywhere} مباراة، "
                    f"منها {here} فقط في نفس المرحلة ({anywhere - here} في مرحلة أخرى)")

    ungrouped = enrolled - all_grouped
    if all_grouped and ungrouped:
        problems.append(f"{len(ungrouped)} فريق مسجّل في البطولة وغير موزّع على أي مجموعة")
    return problems


def main(show_all: bool) -> None:
    app = create_app()
    with app.app_context():
        comps = Competition.query.order_by(Competition.id).all()
        bad = 0
        for c in comps:
            ag = db.session.get(AgeGroup, c.age_group_id) if c.age_group_id else None
            problems = check(c)
            if problems:
                bad += 1
            if problems or show_all:
                head = (f"#{c.id} {c.name_ar} [{c.sector_ar or '-'}] "
                        f"مواليد {ag.name_ar if ag else '—'}")
                print(f"\n{head}")
                if problems:
                    for p in problems:
                        print(f"   ⚠️  {p}")
                else:
                    print("   ✅ سليمة")
        print(f"\n{'='*60}")
        print(f"إجمالي المسابقات: {len(comps)}   بها ملاحظات: {bad}   سليمة: {len(comps)-bad}")


if __name__ == "__main__":
    main(show_all="--all" in sys.argv)
