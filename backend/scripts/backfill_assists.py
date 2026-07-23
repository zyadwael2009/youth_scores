"""Backfill assists the old import dropped, and goals it under-listed.

Two source quirks lost data on import, both now handled by
`migrate_json.resolve_events`:

  * a self-assist collision made the importer discard an assist instead of
    carrying it to the next goal by someone else, and
  * a lone scorer named once though the scoreline (and a second assister) show
    he scored again left that extra assist with no goal to attach to.

This re-derives each imported match's goals and assists from the source and
corrects the stored rows: it reassigns assists, and creates the goal a lone
scorer was under-credited for (with the assister, creating that player if the
dropped assist meant he was never stored). Scores, scorers on existing goals,
cards, subs and line-ups are left untouched.

It is deliberately conservative. A match side is only rewritten when it still
looks exactly as import (or the earlier assist-only backfill) left it: the stored
goals match the source list one-for-one, and the stored assists match one of
those accepted states. Otherwise the side was hand-edited and is skipped and
reported, so no manual correction is ever clobbered.

    python -m scripts.backfill_assists            # dry run — shows what would change
    python -m scripts.backfill_assists --apply    # write the corrections
"""
from __future__ import annotations

import sys

from app import create_app
from app.extensions import db
from app.models import AgeGroup, Match, MatchGoal, Player, PlayerTeam, Season, Team

from scripts.migrate_json import (
    CONFIG_URL, as_int, as_list, fetch, greedy_pairing, norm, resolve_events,
    split_scorers,
)


def old_pairing(goal_names: list[str], flat_assists: list[str]) -> list[str | None]:
    """The pre-fix behaviour, used only to prove a side is untouched."""
    out: list[str | None] = []
    i = 0
    for name in goal_names:
        a = None
        if i < len(flat_assists) and norm(flat_assists[i]) != norm(name):
            a = flat_assists[i]
        out.append(a)
        i += 1
    return out


def build_source_map() -> dict[str, dict[str, list]]:
    """source_ref -> {'home': [...scorers], 'away': [...scorers]}.

    Rebuilds the exact source_ref the importer stored (code|age|sector|idx|mid),
    so a stored match can be looked up without re-matching teams or dates.
    """
    cfg = fetch(CONFIG_URL)
    data = fetch(cfg["latestDataUrl"])
    out: dict[str, dict[str, list]] = {}
    for s in data.get("seasons") or []:
        for c in s.get("competitions") or []:
            code = c.get("competition_id")
            for a in c.get("ages") or []:
                age = str(a.get("age")).strip()
                sec = a.get("sector")
                if isinstance(sec, dict):
                    sec_ar, sec_en = as_list(sec.get("ar")), as_list(sec.get("en"))
                elif isinstance(sec, list):
                    sec_ar = sec_en = [str(x) for x in sec]
                else:
                    sec_ar = sec_en = []
                urls = a.get("matchesurl")
                urls = [urls] if isinstance(urls, str) else (urls or [])
                for i, url in enumerate(urls):
                    if not url:
                        continue
                    sector_key = norm((sec_ar[i] if i < len(sec_ar) else None)
                                      or (sec_en[i] if i < len(sec_en) else None) or "")
                    try:
                        feed = fetch(url)
                    except Exception as e:  # noqa: BLE001
                        print(f"  ! could not fetch {url}: {e}")
                        continue
                    for idx, m in enumerate(feed.get("matches") or []):
                        mid = str(m.get("match_id") or "").strip()
                        src = f"{code}|{age}|{sector_key}|{idx:04d}|{mid}"
                        out[src] = {
                            "home": as_list(m.get("home_scorers")),
                            "away": as_list(m.get("away_scorers")),
                            "home_score": m.get("home_score"),
                            "away_score": m.get("away_score"),
                        }
    return out


def player_on_team(name: str, team_id: int):
    """Existing player of this name registered to the team, or None."""
    key = norm(name)
    for pt in PlayerTeam.query.filter_by(team_id=team_id).all():
        p = pt.player
        if norm(p.full_name_ar) == key or norm(p.full_name_en) == key:
            return p
    return None


def get_or_create_player(name: str, team: Team, season: Season) -> Player:
    """Find the named player on the team, or create him — same as the importer.

    Only reached when padding recovers a goal whose assister was dropped on
    import and so was never created (he only assisted, never scored).
    """
    p = player_on_team(name, team.id)
    if p is not None:
        return p
    ag = db.session.get(AgeGroup, team.age_group_id) if team.age_group_id else None
    p = Player(
        full_name_ar=name.strip(),
        birth_year=ag.oldest_birth_year if ag else None,
        birth_year_verified=False,
    )
    db.session.add(p)
    db.session.flush()
    db.session.add(PlayerTeam(
        player_id=p.id, team_id=team.id,
        start_date=season.start_date if season else None, status="active",
    ))
    return p


def main(apply: bool) -> None:
    app = create_app()
    with app.app_context():
        print("fetching source feed…")
        src_map = build_source_map()
        print(f"source matches: {len(src_map)}\n")

        season = Season.query.filter_by(is_active=True).first() or Season.query.first()

        reassigned = 0       # existing goals whose assist changed
        created = 0          # goals created to recover an unlisted scorer's goal
        sides_fixed = 0
        skipped: list[str] = []

        matches = Match.query.filter(Match.source_ref.isnot(None)).all()
        for match in matches:
            src = src_map.get(match.source_ref)
            if src is None:
                continue
            for side, team_id in (("home", match.home_team_id), ("away", match.away_team_id)):
                goals, assists = split_scorers(src[side])
                declared = as_int(src[f"{side}_score"])

                # The goals the old import created (no padding).
                listed: list[str] = []
                for name, count in goals:
                    listed.extend([name] * count)
                flat_assists: list[str] = []
                for name, count in assists:
                    flat_assists.extend([name] * count)

                # The corrected result, with the lone-scorer padding.
                new_names, new_vec = resolve_events(goals, assists, declared)

                # Assist states that count as "untouched" on the unpadded goals:
                # the original import, or the earlier greedy backfill.
                old_vec = old_pairing(listed, flat_assists)
                prev_vec = greedy_pairing(listed, flat_assists)

                # Cheap skip: on a pristine side where the fix changes nothing, no
                # need to touch the database at all.
                if new_names == listed and new_vec == prev_vec:
                    continue

                db_goals = (MatchGoal.query
                            .filter_by(match_id=match.id, team_id=team_id)
                            .order_by(MatchGoal.id).all())
                label = f"{match.source_ref} [{side}]"
                db_scorers = [norm((g.scorer.full_name_ar or g.scorer.full_name_en) if g.scorer else "")
                              for g in db_goals]
                db_assists = [norm((g.assist.full_name_ar or g.assist.full_name_en) if g.assist else "")
                              for g in db_goals]

                # Already at the corrected (possibly padded) state — a re-run.
                if (len(db_goals) == len(new_names)
                        and db_scorers == [norm(n) for n in new_names]
                        and db_assists == [norm(x or "") for x in new_vec]):
                    continue

                # Otherwise it must still be exactly what import (or the greedy
                # backfill) left: same scorers on the unpadded goals, and assists
                # matching one accepted state. Anything else is a hand edit.
                if not (len(db_goals) == len(listed)
                        and db_scorers == [norm(n) for n in listed]
                        and db_assists in ([norm(x or "") for x in old_vec],
                                           [norm(x or "") for x in prev_vec])):
                    skipped.append(f"{label}: stored goals/assists differ from source — hand-edited?")
                    continue

                team = db.session.get(Team, team_id)
                side_re = side_new = 0
                # Reconcile the existing goals' assists.
                for k, g in enumerate(db_goals):
                    want = new_vec[k]
                    want_id = get_or_create_player(want, team, season).id if want else None
                    if g.assist_id != want_id:
                        g.assist_id = want_id
                        side_re += 1
                # Create the goals the source under-listed (padding), all by the
                # sole scorer, carrying the assists that had nowhere to go before.
                for k in range(len(listed), len(new_names)):
                    scorer = get_or_create_player(new_names[k], team, season)
                    want = new_vec[k]
                    assist_id = get_or_create_player(want, team, season).id if want else None
                    db.session.add(MatchGoal(
                        match_id=match.id, team_id=team_id,
                        scorer_id=scorer.id, assist_id=assist_id, minute=None,
                    ))
                    side_new += 1

                if side_re or side_new:
                    sides_fixed += 1
                    reassigned += side_re
                    created += side_new
                    extra = f", +{side_new} goal(s)" if side_new else ""
                    print(f"  ✓ {label}: {side_re} re-assisted{extra} "
                          f"({match.match_date:%Y-%m-%d})")

        print(f"\nsides corrected: {sides_fixed}   goals re-assisted: {reassigned}   "
              f"goals created: {created}")
        if skipped:
            print(f"\nskipped (not touched): {len(skipped)}")
            for s in skipped[:20]:
                print(f"  - {s}")
            if len(skipped) > 20:
                print(f"  … and {len(skipped) - 20} more")

        if apply:
            db.session.commit()
            print("\nAPPLIED — assists corrected.")
        else:
            db.session.rollback()
            print("\nDRY RUN — nothing written. Add --apply to save.")


if __name__ == "__main__":
    main(apply="--apply" in sys.argv[1:])
