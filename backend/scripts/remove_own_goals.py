"""Remove own-goal rows the old import created as bogus "هدف عكسي" players.

The source writes an own goal into the beneficiary team's scorer list as the
literal "هدف عكسي" (own goal) with no player named. The old import turned that
into a player of that name on the team and credited him the goal. Since the real
scorer is unknowable, these are removed entirely: the goal row and the fake
player (with his roster row and any stray references). The scoreline is
unaffected — it comes from home_score/away_score, not the goal rows.

`migrate_json` now drops own goals on import, so this only cleans up data already
stored.

    python -m scripts.remove_own_goals            # dry run
    python -m scripts.remove_own_goals --apply
"""
from __future__ import annotations

import sys

from app import create_app
from app.extensions import db
from app.models import (
    MatchCard, MatchGoal, MatchPlayer, MatchSubstitution, Player, PlayerTeam,
)

from scripts.migrate_json import is_own_goal


def main(apply: bool) -> None:
    app = create_app()
    with app.app_context():
        fakes = [p for p in Player.query.all()
                 if is_own_goal(p.full_name_ar or p.full_name_en or "")]
        print(f"own-goal 'players' found: {len(fakes)}")

        goals_removed = 0
        for p in fakes:
            g_as_scorer = MatchGoal.query.filter_by(scorer_id=p.id).all()
            g_as_assist = MatchGoal.query.filter_by(assist_id=p.id).all()
            cards = MatchCard.query.filter_by(player_id=p.id).count()
            lineup = MatchPlayer.query.filter_by(player_id=p.id).count()
            subs = MatchSubstitution.query.filter(
                (MatchSubstitution.player_in_id == p.id)
                | (MatchSubstitution.player_out_id == p.id)
            ).count()
            pts = PlayerTeam.query.filter_by(player_id=p.id).count()
            print(f"  #{p.id} {p.full_name_ar!r}: goals={len(g_as_scorer)} "
                  f"assist_of={len(g_as_assist)} cards={cards} lineup={lineup} "
                  f"subs={subs} roster={pts}")
            goals_removed += len(g_as_scorer)

            if apply:
                for g in g_as_scorer:
                    db.session.delete(g)
                # An own-goal name should never be a real assist; if it somehow
                # is, drop the link rather than the whole goal.
                for g in g_as_assist:
                    g.assist_id = None
                MatchCard.query.filter_by(player_id=p.id).delete()
                MatchPlayer.query.filter_by(player_id=p.id).delete()
                MatchSubstitution.query.filter(
                    (MatchSubstitution.player_in_id == p.id)
                    | (MatchSubstitution.player_out_id == p.id)
                ).delete()
                PlayerTeam.query.filter_by(player_id=p.id).delete()
                db.session.delete(p)

        print(f"\nplayers to remove: {len(fakes)}   own-goal rows to remove: {goals_removed}")
        if apply:
            db.session.commit()
            print("APPLIED — own-goal players and goals removed.")
        else:
            db.session.rollback()
            print("DRY RUN — nothing written. Add --apply to remove.")


if __name__ == "__main__":
    main(apply="--apply" in sys.argv[1:])
