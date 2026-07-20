"""Merge team rows that are really one squad entered in several competitions.

The import created one Team per competition entry, so a club whose 2010 side
played both "منطقة القاهرة المرحلة الثانية" and "تصفية الصعود" ended up with two
teams -- and therefore two rosters and two coaching staffs for one squad.

Only rows whose competitions do NOT overlap are merged. When two rows sit in the
*same* competition they are separate phases with separate tables (the 2011 group
stage + second phase), and merging them would fuse two standings rows into one;
those are reported and left alone.

    python -m scripts.merge_duplicate_teams            # dry run
    python -m scripts.merge_duplicate_teams --apply
"""

from __future__ import annotations

import sys

import sqlalchemy as sa

from app import create_app
from app.extensions import db
from app.models import (
    CompetitionTeam,
    GroupTeam,
    Match,
    MatchCard,
    MatchGoal,
    MatchPenaltyShootout,
    MatchPlayer,
    MatchSubstitution,
    PlayerTeam,
    Team,
    TeamCoach,
)

# Tables that simply point at a team and need repointing.
SIMPLE_TEAM_FKS = (MatchPlayer, MatchGoal, MatchCard, MatchSubstitution,
                   MatchPenaltyShootout)


def comps_of(team_id: int) -> set[int]:
    return {ct.competition_id
            for ct in CompetitionTeam.query.filter_by(team_id=team_id).all()}


def main(apply: bool, allow_same_competition: bool = False) -> None:
    app = create_app()
    with app.app_context():
        groups = (db.session.query(Team.club_id, Team.age_group_id)
                  .group_by(Team.club_id, Team.age_group_id)
                  .having(sa.func.count(Team.id) > 1).all())

        merged = skipped = rows_moved = rows_dropped = 0
        for g in groups:
            teams = Team.query.filter_by(
                club_id=g.club_id, age_group_id=g.age_group_id
            ).order_by(Team.id).all()
            sets = [comps_of(t.id) for t in teams]
            if set.intersection(*sets) and not allow_same_competition:
                skipped += 1
                print(f"  SKIP {teams[0].club.name_ar} / {teams[0].age_group.name_ar}"
                      f" - same competition, separate phases")
                continue
            # Two rows in one competition are only safe to merge when they sit in
            # different groups: each group keeps its own table, and the merged
            # team ends up a member of both.
            if set.intersection(*sets):
                gsets = [{gt.group_id for gt in GroupTeam.query.filter_by(team_id=t.id).all()}
                         for t in teams]
                if set.intersection(*gsets) or any(not s for s in gsets):
                    skipped += 1
                    print(f"  SKIP {teams[0].club.name_ar} / {teams[0].age_group.name_ar}"
                          f" - same competition AND same/blank group")
                    continue

            keep, drop = teams[0], teams[1:]
            print(f"  merge {teams[0].club.name_ar} / {teams[0].age_group.name_ar}: "
                  f"keep {keep.id} <- {[t.id for t in drop]}")
            for d in drop:
                merged += 1
                # Matches
                for m in Match.query.filter_by(home_team_id=d.id).all():
                    rows_moved += 1
                    if apply:
                        m.home_team_id = keep.id
                for m in Match.query.filter_by(away_team_id=d.id).all():
                    rows_moved += 1
                    if apply:
                        m.away_team_id = keep.id
                for model in SIMPLE_TEAM_FKS:
                    for row in model.query.filter_by(team_id=d.id).all():
                        rows_moved += 1
                        if apply:
                            row.team_id = keep.id
                # Competition + group entries (unique per competition/group)
                for ct in CompetitionTeam.query.filter_by(team_id=d.id).all():
                    twin = CompetitionTeam.query.filter_by(
                        competition_id=ct.competition_id, team_id=keep.id).first()
                    rows_dropped, rows_moved = (
                        (rows_dropped + 1, rows_moved) if twin else (rows_dropped, rows_moved + 1))
                    if apply:
                        db.session.delete(ct) if twin else setattr(ct, "team_id", keep.id)
                for gt in GroupTeam.query.filter_by(team_id=d.id).all():
                    twin = GroupTeam.query.filter_by(
                        group_id=gt.group_id, team_id=keep.id).first()
                    rows_dropped, rows_moved = (
                        (rows_dropped + 1, rows_moved) if twin else (rows_dropped, rows_moved + 1))
                    if apply:
                        db.session.delete(gt) if twin else setattr(gt, "team_id", keep.id)
                # Staff and roster: union, dropping exact repeats
                for tc in TeamCoach.query.filter_by(team_id=d.id).all():
                    twin = TeamCoach.query.filter_by(
                        team_id=keep.id, coach_id=tc.coach_id, role_ar=tc.role_ar).first()
                    rows_dropped, rows_moved = (
                        (rows_dropped + 1, rows_moved) if twin else (rows_dropped, rows_moved + 1))
                    if apply:
                        db.session.delete(tc) if twin else setattr(tc, "team_id", keep.id)
                for pt in PlayerTeam.query.filter_by(team_id=d.id).all():
                    twin = PlayerTeam.query.filter_by(
                        team_id=keep.id, player_id=pt.player_id).first()
                    rows_dropped, rows_moved = (
                        (rows_dropped + 1, rows_moved) if twin else (rows_dropped, rows_moved + 1))
                    if apply:
                        db.session.delete(pt) if twin else setattr(pt, "team_id", keep.id)
                if apply:
                    db.session.flush()
                    db.session.delete(d)

        print(f"\ngroups merged  : {merged}")
        print(f"groups skipped : {skipped}  (same competition - separate phases)")
        print(f"rows repointed : {rows_moved}")
        print(f"rows dropped   : {rows_dropped}")

        if apply:
            db.session.commit()
            print("\nAPPLIED and committed.")
        else:
            db.session.rollback()
            print("\nDRY RUN - nothing written. Re-run with --apply to commit.")


if __name__ == "__main__":
    main(apply="--apply" in sys.argv,
         allow_same_competition="--same-competition" in sys.argv)
