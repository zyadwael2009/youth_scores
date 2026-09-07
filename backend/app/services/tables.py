"""Assemble standings for a competition out of the database."""

from __future__ import annotations

from sqlalchemy.orm import joinedload

from app.models import Competition, CompetitionTeam, Group, GroupTeam, Match, Stage, Team
from app.services.standings import Standing, calculate


def competition_matches(competition_id: int) -> list[Match]:
    return (
        Match.query.join(Stage)
        .filter(Stage.competition_id == competition_id)
        .filter(Match.deleted_at.is_(None))
        .options(joinedload(Match.stage))
        .all()
    )


def competition_teams(competition_id: int) -> list[Team]:
    return (
        Team.query.join(CompetitionTeam)
        .filter(CompetitionTeam.competition_id == competition_id)
        .order_by(CompetitionTeam.id)
        .all()
    )


def deductions_of(competition_id: int) -> dict[int, int]:
    """Points docked from each team in this competition, by team id."""
    return {
        ct.team_id: ct.point_deduction
        for ct in CompetitionTeam.query.filter_by(competition_id=competition_id).all()
        if ct.point_deduction
    }


def groups_of(competition_id: int) -> list[Group]:
    # Order by the admin's sort_order (then id) — not name, where «المجموعة 10»
    # would sort before «المجموعة 2» — so the standings follow the admin's
    # up/down arrangement, matching the public group lists.
    return (
        Group.query.join(Stage)
        .filter(Stage.competition_id == competition_id)
        .order_by(Group.sort_order, Group.id)
        .all()
    )


def standings_by_group(
    competition_id: int,
    *,
    teams: list[Team] | None = None,
    matches: list[Match] | None = None,
    groups: list[Group] | None = None,
    group_team_ids: dict[int, set[int]] | None = None,
    deductions: dict[int, int] | None = None,
) -> list[dict]:
    """One table per group, or a single unnamed table when there are no groups.

    Teams are partitioned by their group, while their matches against everyone
    else still count -- unless the group's stage declares that it starts from
    zero (`carries_points = False`), in which case only that stage's matches do.

    All inputs may be passed in pre-loaded: the competition page already fetches
    the teams, matches, groups, group memberships and deductions, so it hands them
    over rather than have this re-run the same five queries (and the per-group
    GroupTeam fan-out) a second time. Anything omitted is queried as before.
    """
    teams = teams if teams is not None else competition_teams(competition_id)
    matches = matches if matches is not None else competition_matches(competition_id)
    groups = groups if groups is not None else groups_of(competition_id)
    docked = deductions if deductions is not None else deductions_of(competition_id)

    if not groups:
        return [{"group": None,
                 "standings": calculate(matches, teams, deductions=docked)}]

    out = []
    grouped: set[int] = set()
    for g in groups:
        ids = (
            group_team_ids.get(g.id, set())
            if group_team_ids is not None
            else {gt.team_id for gt in GroupTeam.query.filter_by(group_id=g.id).all()}
        )
        if not ids:
            continue
        grouped |= ids
        stage = g.stage
        stage_filter = None if (stage is None or stage.carries_points) else stage.id
        out.append(
            {"group": g,
             "standings": calculate(matches, teams, team_ids=ids,
                                    stage_filter=stage_filter, deductions=docked)}
        )

    # A competition can have groups and still leave some teams out of them.
    ungrouped = {t.id for t in teams} - grouped
    if ungrouped:
        out.append(
            {"group": None, "standings": calculate(matches, teams, team_ids=ungrouped,
                                                   deductions=docked)}
        )
    return out
