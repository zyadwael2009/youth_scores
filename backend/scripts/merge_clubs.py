"""Merge one club into another — they are the same club under two names.

The import occasionally created a second Club row for a club that already
existed (e.g. "المقاولون" as a bare short form of "المقاولون العرب"), so its
teams, staff and history are split across two ids. This folds the *source*
club into the *target* and deletes the source.

Teams move by repointing `teams.club_id`. When the target already has a team in
the *same* age group, the two are the same squad and are merged team-for-team
(matches, roster, staff and competition/group entries repointed, exact repeats
dropped) — the (club_id, age_group_id) uniqueness leaves no other option.
Club staff move the same way, dropping an exact (coach, role) repeat.

    python -m scripts.merge_clubs --from 141 --to 20            # dry run
    python -m scripts.merge_clubs --from 141 --to 20 --apply

Clubs may be given by id (--from/--to) or by exact Arabic name
(--from-name/--to-name).
"""

from __future__ import annotations

import sys

from app import create_app
from app.extensions import db
from app.models import (
    Club,
    ClubStaff,
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


class Counts:
    def __init__(self) -> None:
        self.moved = 0
        self.dropped = 0


def _merge_team_into(keep: Team, drop: Team, apply: bool, c: Counts) -> None:
    """Fold team `drop` into `keep` (same club, same age group)."""
    for m in Match.query.filter_by(home_team_id=drop.id).all():
        c.moved += 1
        if apply:
            m.home_team_id = keep.id
    for m in Match.query.filter_by(away_team_id=drop.id).all():
        c.moved += 1
        if apply:
            m.away_team_id = keep.id
    for model in SIMPLE_TEAM_FKS:
        for row in model.query.filter_by(team_id=drop.id).all():
            c.moved += 1
            if apply:
                row.team_id = keep.id
    for ct in CompetitionTeam.query.filter_by(team_id=drop.id).all():
        twin = CompetitionTeam.query.filter_by(
            competition_id=ct.competition_id, team_id=keep.id).first()
        c.dropped += twin is not None
        c.moved += twin is None
        if apply:
            db.session.delete(ct) if twin else setattr(ct, "team_id", keep.id)
    for gt in GroupTeam.query.filter_by(team_id=drop.id).all():
        twin = GroupTeam.query.filter_by(
            group_id=gt.group_id, team_id=keep.id).first()
        c.dropped += twin is not None
        c.moved += twin is None
        if apply:
            db.session.delete(gt) if twin else setattr(gt, "team_id", keep.id)
    for tc in TeamCoach.query.filter_by(team_id=drop.id).all():
        twin = TeamCoach.query.filter_by(
            team_id=keep.id, coach_id=tc.coach_id, role_ar=tc.role_ar).first()
        c.dropped += twin is not None
        c.moved += twin is None
        if apply:
            db.session.delete(tc) if twin else setattr(tc, "team_id", keep.id)
    for pt in PlayerTeam.query.filter_by(team_id=drop.id).all():
        twin = PlayerTeam.query.filter_by(
            team_id=keep.id, player_id=pt.player_id).first()
        c.dropped += twin is not None
        c.moved += twin is None
        if apply:
            db.session.delete(pt) if twin else setattr(pt, "team_id", keep.id)
    if apply:
        db.session.flush()
        db.session.delete(drop)


def _resolve(from_id, to_id, from_name, to_name) -> tuple[Club, Club] | None:
    def one(cid, name, label):
        if cid is not None:
            return db.session.get(Club, cid)
        if name is not None:
            return Club.query.filter_by(name_ar=name).one_or_none()
        print(f"مطلوب --{label} أو --{label}-name")
        return None
    src = one(from_id, from_name, "from")
    tgt = one(to_id, to_name, "to")
    if src is None or tgt is None:
        print("لم يُعثر على أحد الناديين.")
        return None
    if src.id == tgt.id:
        print("المصدر والهدف نفس النادي.")
        return None
    return src, tgt


def main(from_id, to_id, from_name, to_name, apply: bool) -> None:
    app = create_app()
    with app.app_context():
        pair = _resolve(from_id, to_id, from_name, to_name)
        if pair is None:
            return
        src, tgt = pair
        print(f"source: club {src.id}  {src.name_ar!r} ({src.name_en!r})")
        print(f"target: club {tgt.id}  {tgt.name_ar!r} ({tgt.name_en!r})\n")

        c = Counts()
        tgt_teams = {t.age_group_id: t for t in tgt.teams}
        for t in list(src.teams):
            twin = tgt_teams.get(t.age_group_id)
            if twin is None:
                print(f"  move team {t.id} (age_group {t.age_group_id}) -> club {tgt.id}")
                c.moved += 1
                if apply:
                    # Reassign through the relationship so `t` leaves src.teams;
                    # setting club_id alone leaves it parented to src, and the
                    # later delete(src) would then NULL the FK.
                    t.club = tgt
            else:
                print(f"  merge team {t.id} -> {twin.id} (age_group {t.age_group_id})")
                _merge_team_into(twin, t, apply, c)

        for st in list(src.staff):
            twin = ClubStaff.query.filter_by(
                club_id=tgt.id, coach_id=st.coach_id, role_ar=st.role_ar).first()
            if twin is not None:
                print(f"  drop duplicate staff (coach {st.coach_id}, {st.role_ar})")
                c.dropped += 1
                if apply:
                    db.session.delete(st)
            else:
                print(f"  move staff (coach {st.coach_id}, {st.role_ar}) -> club {tgt.id}")
                c.moved += 1
                if apply:
                    # Same reason as teams — and club.staff is delete-orphan, so
                    # reassigning the parent is what keeps it from being deleted
                    # along with src.
                    st.club = tgt

        if apply:
            db.session.flush()
            db.session.delete(src)

        print(f"\nrows repointed : {c.moved}")
        print(f"rows dropped   : {c.dropped}")
        print(f"club deleted   : {src.id} {src.name_ar!r}")

        if apply:
            db.session.commit()
            print("\nAPPLIED and committed.")
        else:
            db.session.rollback()
            print("\nDRY RUN - nothing written. Re-run with --apply to commit.")


def _arg(flag: str, argv: list[str]):
    return argv[argv.index(flag) + 1] if flag in argv and argv.index(flag) + 1 < len(argv) else None


if __name__ == "__main__":
    argv = sys.argv[1:]
    fi, ti = _arg("--from", argv), _arg("--to", argv)
    main(from_id=int(fi) if fi else None,
         to_id=int(ti) if ti else None,
         from_name=_arg("--from-name", argv),
         to_name=_arg("--to-name", argv),
         apply="--apply" in argv)
