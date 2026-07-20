"""Import the 2025-2026 season from the legacy JSON feed.

    python -m scripts.migrate_json            # import (re-runnable)
    python -m scripts.migrate_json --reset    # wipe the season first
    python -m scripts.migrate_json --report   # what the source data looks like

The feed nests competition -> age -> sector, and each sector is a separate file
of teams and matches. Team ids inside those files are file-local ("t001" is a
different club in every one), so clubs are identified by name instead.

What the source cannot give us, and what we do about it:

  * No birth years.  Inferred from the age group of the team the player appeared
    for, flagged birth_year_verified = False. Wrong for anyone playing up.
  * No goal minutes. Left NULL.
  * No player identity. A name is only unique within a team, so the same person
    at two clubs becomes two Player rows. Merging them would need real identity
    data we do not have; splitting is the recoverable mistake.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
import urllib.request
from collections import Counter, defaultdict
from datetime import date, datetime

from app import create_app
from app.extensions import db
from app.models import (
    Ad,
    AgeGroup,
    AppVersion,
    Club,
    Coach,
    Competition,
    CompetitionTeam,
    Group,
    GroupTeam,
    Match,
    MatchCard,
    MatchGoal,
    News,
    Player,
    PlayerTeam,
    Season,
    Stage,
    Team,
    TeamCoach,
    Venue,
)

CONFIG_URL = "https://youth-scores-data.vercel.app/api/config"

# The feed's status vocabulary is not the schema's.
STATUS_MAP = {
    "completed": "completed",
    "upcoming": "scheduled",
    "delayed": "postponed",
    "": "scheduled",
    "none": "scheduled",
}

ASSIST_DELIMITERS = {"صناعة الاهداف", "assists"}

# "لا يوجد بيانات" ("no data available") is written into the scorer list where a
# goal is known but the scorer is not. It is not a person: imported literally it
# became the competition's leading scorer.
PLACEHOLDER_NAMES = {"لا يوجد بيانات", "لايوجد بيانات", "غير معروف", "unknown", "n/a"}


def is_placeholder(name: str) -> bool:
    return norm(name).lower() in {norm(p).lower() for p in PLACEHOLDER_NAMES}

# "محمد رضا (2)" -> the player scored twice.
MULTIPLIER_RE = re.compile(r"^(.*?)\s*[\(\[]\s*[x×]?\s*(\d+)\s*[\)\]]$")

# "نزول\n احمد خالد\n و خروج\n يحيي" -> on: احمد خالد, off: يحيي
SUB_RE = re.compile(r"نزول\s*(.+?)\s*و\s*خروج\s*(.+)", re.S)


# ── text ──────────────────────────────────────────────────────────────────────

def norm(s: str | None) -> str:
    """Fold the spelling variants that make one club look like several.

    Arabic here is user-typed, so أ/إ/آ and ه/ة alternate freely for the same
    name. Diacritics and tatweel are dropped, and Arabic-Indic digits folded to
    ASCII. Deliberately conservative: it does not touch ي/ى, which can
    distinguish real names.
    """
    if not s:
        return ""
    s = unicodedata.normalize("NFKC", str(s)).strip()
    s = re.sub(r"[ً-ٰٟـ]", "", s)  # harakat + tatweel
    s = s.translate(str.maketrans("أإآٱ", "اااا"))
    s = s.translate(str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789"))
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def pick(v, lang: str) -> str | None:
    """The feed writes a localised value as either a bare string or {ar, en}."""
    if v is None:
        return None
    if isinstance(v, dict):
        return (v.get(lang) or "").strip() or None
    s = str(v).strip()
    return s or None


def as_list(v) -> list[str]:
    if not v:
        return []
    if isinstance(v, list):
        return [str(x).strip() for x in v if x is not None and str(x).strip()]
    s = str(v).strip()
    return [s] if s else []


def as_int(v) -> int | None:
    if v is None or v == "":
        return None
    try:
        return int(str(v).strip())
    except ValueError:
        return None


def fetch(url: str):
    with urllib.request.urlopen(url, timeout=90) as r:
        return json.loads(r.read().decode("utf-8"))


def split_scorers(entries: list[str]) -> tuple[list[tuple[str, int]], list[tuple[str, int]]]:
    """Split one team's scorer list into goals and assists at the delimiter."""
    goals: list[tuple[str, int]] = []
    assists: list[tuple[str, int]] = []
    target = goals
    for raw in entries:
        s = raw.strip()
        if not s:
            continue
        if norm(s) in {norm(d) for d in ASSIST_DELIMITERS}:
            target = assists
            continue
        m = MULTIPLIER_RE.match(s)
        if m:
            name, count = m.group(1).strip(), int(m.group(2))
        else:
            name, count = s, 1
        if name and not is_placeholder(name):
            target.append((name, max(1, count)))
    return goals, assists


# ── importer ──────────────────────────────────────────────────────────────────

class Importer:
    def __init__(self, season_name: str = "2025-2026"):
        self.season_name = season_name
        self.season: Season | None = None
        self.clubs: dict[str, Club] = {}
        self.age_groups: dict[str, AgeGroup] = {}
        self.teams: dict[tuple[int, int], Team] = {}
        self.players: dict[tuple[int, str], Player] = {}
        self.coaches: dict[str, Coach] = {}
        self.stats = defaultdict(int)
        self.warnings: list[str] = []

    # -- lookups, all get-or-create so the script can be re-run --

    def get_season(self) -> Season:
        if self.season is not None:
            return self.season
        s = Season.query.filter_by(name_en=self.season_name).first()
        if not s:
            y = int(self.season_name.split("-")[0])
            s = Season(
                name_en=self.season_name,
                name_ar=self.season_name,
                start_date=date(y, 8, 1),
                end_date=date(y + 1, 6, 30),
                is_active=True,
            )
            db.session.add(s)
            db.session.flush()
            self.stats["seasons"] += 1
        # Held so a registration date can be stamped without threading the
        # season through every call — a team no longer carries one.
        self.season = s
        return s

    def get_age_group(self, age: str) -> AgeGroup:
        age = str(age).strip()
        if age in self.age_groups:
            return self.age_groups[age]
        ag = AgeGroup.query.filter_by(name_en=age).first()
        if not ag:
            ag = AgeGroup(name_en=age, name_ar=age, oldest_birth_year=int(age))
            db.session.add(ag)
            db.session.flush()
            self.stats["age_groups"] += 1
        self.age_groups[age] = ag
        return ag

    @staticmethod
    def split_name(v):
        """Split a feed team name into (club, the name the side plays under).

        The feed writes the club on the first line and, where a side plays under
        other branding — an academy, a sponsor — that name on the next. The club
        is the identity: players are registered with the federation under it, so
        it is what the Club row is made from. The second line becomes the team's
        own name, shown beneath the club wherever the team appears.

        A name on one line has no second part, which is the ordinary case.
        """
        if not v:
            return v, None
        parts = [p.strip() for p in re.split(r"[\r\n]+", str(v)) if p.strip()]
        if not parts:
            return None, None
        alias = " ".join(parts[1:]).strip()
        # The older files wrap the second name in brackets ("(اوفرلاب)"); the
        # brackets are punctuation around it, not part of the name.
        if len(alias) > 2 and alias[0] in "([" and alias[-1] in ")]":
            alias = alias[1:-1].strip()
        return parts[0], alias or None

    def get_club(self, name_ar, name_en, city_ar, city_en, logo) -> Club:
        key = norm(name_ar) or norm(name_en)
        if key in self.clubs:
            c = self.clubs[key]
            # Later files may carry fields an earlier one lacked.
            c.name_en = c.name_en or name_en
            c.city_ar = c.city_ar or city_ar
            c.city_en = c.city_en or city_en
            c.logo_url = c.logo_url or logo
            return c
        c = Club(
            name_ar=name_ar, name_en=name_en, city_ar=city_ar, city_en=city_en,
            logo_url=logo,
        )
        db.session.add(c)
        db.session.flush()
        self.clubs[key] = c
        self.stats["clubs"] += 1
        return c

    def get_team(
        self, club: Club, ag: AgeGroup, season: Season, source_ref: str, **extra
    ) -> Team:
        # Keyed by the feed entry, not the club: a club that appears twice in one
        # competition (two phases) is two teams that share a Club. Keying by club
        # would merge them and double-count every match in the standings.
        if source_ref in self.teams:
            return self.teams[source_ref]
        t = Team.query.filter_by(source_ref=source_ref).first()
        if not t:
            t = Team(
                club_id=club.id, age_group_id=ag.id,
                source_ref=source_ref, **extra,
            )
            db.session.add(t)
            db.session.flush()
            self.stats["teams"] += 1
        self.teams[source_ref] = t
        return t

    def get_player(self, name: str, team: Team, ag: AgeGroup) -> Player:
        key = (team.id, norm(name))
        if key in self.players:
            return self.players[key]
        p = Player(
            full_name_ar=name.strip(),
            # No birth year anywhere in the source; assume the player is native
            # to the age group he appeared in and flag it for review.
            birth_year=ag.oldest_birth_year,
            birth_year_verified=False,
        )
        db.session.add(p)
        db.session.flush()
        db.session.add(
            PlayerTeam(
                player_id=p.id, team_id=team.id,
                start_date=self.get_season().start_date, status="active",
            )
        )
        self.players[key] = p
        self.stats["players"] += 1
        return p

    def get_coach(self, name: str) -> Coach:
        key = norm(name)
        if key in self.coaches:
            return self.coaches[key]
        c = Coach(full_name_ar=name.strip())
        db.session.add(c)
        db.session.flush()
        self.coaches[key] = c
        self.stats["coaches"] += 1
        return c

    # -- feed walking --

    def feed_urls(self, data) -> list[dict]:
        """Flatten seasons -> competitions -> ages -> sectors into one job list."""
        jobs = []
        for s in data.get("seasons") or []:
            if str(s.get("season", "")).strip() != self.season_name:
                continue
            for c in s.get("competitions") or []:
                ages = c.get("ages")
                if not ages:
                    self.warnings.append(
                        f"competition {c.get('competition_id')} "
                        f"({pick(c.get('name'), 'ar')}) has no ages — skipped"
                    )
                    continue
                for a in ages:
                    urls = a.get("matchesurl")
                    urls = [urls] if isinstance(urls, str) else (urls or [])
                    sec = a.get("sector")
                    # sector is {ar:[...], en:[...]} in some files, [..] in others
                    if isinstance(sec, dict):
                        sec_ar, sec_en = as_list(sec.get("ar")), as_list(sec.get("en"))
                    elif isinstance(sec, list):
                        sec_ar = sec_en = [str(x) for x in sec]
                    else:
                        sec_ar = sec_en = []
                    for i, url in enumerate(urls):
                        if not url:
                            continue
                        jobs.append({
                            "code": c.get("competition_id"),
                            "name_ar": pick(c.get("name"), "ar"),
                            "name_en": pick(c.get("name"), "en"),
                            "age": str(a.get("age")).strip(),
                            "sector_ar": sec_ar[i] if i < len(sec_ar) else None,
                            "sector_en": sec_en[i] if i < len(sec_en) else None,
                            "url": url,
                        })
        return jobs

    def warm_cache(self, season: Season):
        """Load what is already stored into the dedup caches.

        The caches key on the normalised name, which is not what is stored, so a
        second run cannot find an existing club with a plain query and would
        insert every club a second time.
        """
        for c in Club.query.all():
            key = norm(c.name_ar) or norm(c.name_en)
            if key:
                self.clubs[key] = c
        for c in Coach.query.all():
            key = norm(c.full_name_ar) or norm(c.full_name_en)
            if key:
                self.coaches[key] = c
        for a in AgeGroup.query.all():
            if a.name_en:
                self.age_groups[a.name_en] = a
        # Teams are no longer per-season, so the whole set is the cache.
        for t in Team.query.all():
            if t.source_ref:
                self.teams[t.source_ref] = t
        for pt in PlayerTeam.query.join(Team).all():
            key = (pt.team_id, norm(pt.player.full_name_ar))
            self.players.setdefault(key, pt.player)
        if self.clubs or self.players:
            print(
                f"cache warmed: {len(self.clubs)} clubs, {len(self.teams)} teams, "
                f"{len(self.players)} players already present\n"
            )

    def run(self, reset: bool = False):
        cfg = fetch(CONFIG_URL)
        data = fetch(cfg["latestDataUrl"])
        season = self.get_season()

        if reset:
            self.wipe(season)
        self.warm_cache(season)

        jobs = self.feed_urls(data)
        print(f"{len(jobs)} competition feeds to import\n")

        for j in jobs:
            label = f"{j['code']} {j['age']}" + (f" [{j['sector_ar']}]" if j["sector_ar"] else "")
            try:
                feed = fetch(j["url"])
            except Exception as e:
                self.warnings.append(f"{label}: download failed — {e}")
                print(f"  FAIL {label}: {e}")
                continue
            n = self.import_feed(j, feed, season)
            db.session.commit()
            print(f"  ok   {label:34} teams={n[0]:3} matches={n[1]:4}")

        self.import_content(data)
        db.session.commit()

    def wipe(self, season: Season):
        """Delete this season's imported rows, children first."""
        comp_ids = [c.id for c in Competition.query.filter_by(season_id=season.id)]
        stage_ids = [s.id for s in Stage.query.filter(Stage.competition_id.in_(comp_ids))] if comp_ids else []
        match_ids = [m.id for m in Match.query.filter(Match.stage_id.in_(stage_ids))] if stage_ids else []
        # A team is not owned by a season; the ones to clear are those entered
        # in this season's competitions.
        team_ids = [ct.team_id for ct in
                    CompetitionTeam.query.filter(CompetitionTeam.competition_id.in_(comp_ids))
                    ] if comp_ids else []

        for model, col, ids in (
            (MatchGoal, MatchGoal.match_id, match_ids),
            (MatchCard, MatchCard.match_id, match_ids),
            (Match, Match.id, match_ids),
            (GroupTeam, GroupTeam.team_id, team_ids),
            (CompetitionTeam, CompetitionTeam.team_id, team_ids),
            (PlayerTeam, PlayerTeam.team_id, team_ids),
            (TeamCoach, TeamCoach.team_id, team_ids),
        ):
            if ids:
                model.query.filter(col.in_(ids)).delete(synchronize_session=False)
        if stage_ids:
            Group.query.filter(Group.stage_id.in_(stage_ids)).delete(synchronize_session=False)
            Stage.query.filter(Stage.id.in_(stage_ids)).delete(synchronize_session=False)
        if comp_ids:
            Competition.query.filter(Competition.id.in_(comp_ids)).delete(synchronize_session=False)
        if team_ids:
            Team.query.filter(Team.id.in_(team_ids)).delete(synchronize_session=False)
        # Players are only ever created by this importer.
        Player.query.delete(synchronize_session=False)
        db.session.commit()
        print("wiped existing season data\n")

    def import_feed(self, job: dict, feed: dict, season: Season) -> tuple[int, int]:
        ag = self.get_age_group(job["age"])
        sector_key = norm(job["sector_ar"] or job["sector_en"] or "")

        comp = Competition.query.filter_by(
            season_id=season.id, code=job["code"],
            age_group_id=ag.id, sector_key=sector_key,
        ).first()
        if not comp:
            comp = Competition(
                season_id=season.id, code=job["code"], age_group_id=ag.id,
                name_ar=job["name_ar"], name_en=job["name_en"],
                sector_ar=job["sector_ar"], sector_en=job["sector_en"],
                sector_key=sector_key,
            )
            db.session.add(comp)
            db.session.flush()
            self.stats["competitions"] += 1

        # -- teams (feed ids are file-local, so map them to real Team rows) --
        local: dict[str, Team] = {}
        team_group: dict[str, tuple[str | None, str | None]] = {}
        for t in feed.get("teams") or []:
            tid = str(t.get("team_id") or "").strip()
            if not tid:
                continue
            name_ar, name_en = pick(t.get("name"), "ar"), pick(t.get("name"), "en")
            if not (name_ar or name_en):
                self.warnings.append(f"{job['code']}/{job['age']}: team {tid} has no name — skipped")
                continue
            club_ar, alias_ar = self.split_name(name_ar)
            club_en, alias_en = self.split_name(name_en)
            club = self.get_club(
                club_ar, club_en, pick(t.get("city"), "ar"), pick(t.get("city"), "en"),
                t.get("logo"),
            )
            team = self.get_team(club, ag, season, source_ref=f"{comp.id}|{tid}",
                                 name_ar=alias_ar, name_en=alias_en)
            # get_team only applies these when it creates the row, so a name the
            # feed gains later would otherwise never land on an existing team.
            team.name_ar = team.name_ar or alias_ar
            team.name_en = team.name_en or alias_en
            local[tid] = team
            # The deduction is a penalty in this competition, so it belongs on
            # the entry. It may appear on only the later of two feed rows, hence
            # the update on an entry that already exists.
            pd = as_int(t.get("point_deduction")) or 0
            entry = CompetitionTeam.query.filter_by(
                competition_id=comp.id, team_id=team.id
            ).first()
            if entry is None:
                db.session.add(CompetitionTeam(competition_id=comp.id, team_id=team.id,
                                               point_deduction=pd))
            elif pd:
                entry.point_deduction = pd

            g = t.get("group")
            if g:
                team_group[tid] = (pick(g, "ar"), pick(g, "en")) if isinstance(g, dict) else (str(g), str(g))

            for cname in as_list((t.get("players") or {}).get("coach")) + as_list(t.get("coach")):
                if is_placeholder(cname):
                    continue
                coach = self.get_coach(cname)
                exists = TeamCoach.query.filter_by(team_id=team.id, coach_id=coach.id).first()
                if not exists:
                    db.session.add(TeamCoach(
                        team_id=team.id, coach_id=coach.id,
                        role_ar="المدير الفني", role_en="Head Coach",
                        start_date=season.start_date,
                    ))
        db.session.flush()

        # -- stages --
        # Most matches carry no stage at all, and some files pair those with a
        # couple of "knockout" ones. Those unstaged matches are the league, so
        # they need a non-knockout stage of their own: filed under knockout they
        # would be dropped from every table.
        raw = [str(m.get("stage") or "").strip() for m in (feed.get("matches") or [])]
        raw = ["" if s.lower() in ("", "none") else s for s in raw]

        ordered: list[str] = []
        if any(s == "" for s in raw) or not raw:
            ordered.append("")  # the default league stage
        ordered += sorted({s for s in raw if s and s.lower() != "knockout"})
        if any(s.lower() == "knockout" for s in raw):
            ordered.append("knockout")

        stage_map: dict[str, Stage] = {}
        has_groups = bool(team_group)
        for i, s in enumerate(ordered, start=1):
            is_ko = s.lower() == "knockout"
            st = Stage.query.filter_by(competition_id=comp.id, stage_order=i).first()
            if not st:
                st = Stage(
                    competition_id=comp.id, stage_order=i,
                    type="knockout" if is_ko else ("group" if has_groups else "league"),
                    name_ar="خروج المغلوب" if is_ko else (f"المرحلة {s}" if s else "الدوري"),
                    name_en="Knockout" if is_ko else (f"Stage {s}" if s else "League"),
                )
                db.session.add(st)
                db.session.flush()
                self.stats["stages"] += 1
            stage_map[s] = st
        # Groups and unstaged matches hang off the first non-knockout stage.
        default_stage = next(
            (st for s, st in stage_map.items() if s.lower() != "knockout"),
            stage_map[ordered[0]],
        )
        db.session.flush()

        # -- groups: the team-level vocabulary, which is what standings use --
        group_map: dict[str, Group] = {}
        for tid, (g_ar, g_en) in team_group.items():
            key = norm(g_ar or g_en)
            if key not in group_map:
                g = Group.query.filter_by(stage_id=default_stage.id, name_ar=g_ar).first()
                if not g:
                    g = Group(stage_id=default_stage.id, name_ar=g_ar, name_en=g_en)
                    db.session.add(g)
                    db.session.flush()
                    self.stats["groups"] += 1
                group_map[key] = g
            team = local.get(tid)
            if team and not GroupTeam.query.filter_by(
                group_id=group_map[key].id, team_id=team.id
            ).first():
                db.session.add(GroupTeam(group_id=group_map[key].id, team_id=team.id))
        db.session.flush()

        # -- matches --
        # match_id is not unique inside a feed: the source reuses the same id for
        # genuinely different fixtures, so the row's position is part of the key.
        # Without it those matches would collide and be dropped on import.
        seen_ids: Counter[str] = Counter()
        for m in feed.get("matches") or []:
            seen_ids[str(m.get("match_id") or "").strip()] += 1
        for mid, n in seen_ids.items():
            if n > 1 and mid:
                self.warnings.append(
                    f"{job['code']}/{job['age']}: match_id {mid!r} used by {n} different "
                    f"matches in the source — imported, but the id needs fixing upstream"
                )

        n_matches = 0
        for idx, m in enumerate(feed.get("matches") or []):
            mid = str(m.get("match_id") or "").strip()
            src = f"{job['code']}|{job['age']}|{sector_key}|{idx:04d}|{mid}"
            if Match.query.filter_by(source_ref=src).first():
                continue

            home, away = local.get(str(m.get("home_team_id"))), local.get(str(m.get("away_team_id")))
            if not home or not away:
                self.warnings.append(
                    f"{job['code']}/{job['age']}: match {mid} references an unknown team — skipped"
                )
                continue
            if home.id == away.id:
                self.warnings.append(f"{job['code']}/{job['age']}: match {mid} has one team twice — skipped")
                continue

            dt = self.parse_dt(m.get("date"), m.get("time"))
            if not dt:
                self.warnings.append(f"{job['code']}/{job['age']}: match {mid} has no usable date — skipped")
                continue

            raw_stage = str(m.get("stage") or "").strip()
            if raw_stage.lower() in ("", "none"):
                raw_stage = ""
            stage = stage_map.get(raw_stage, default_stage)
            raw_group = m.get("group")
            g_label = pick(raw_group, "ar") if isinstance(raw_group, dict) else (str(raw_group).strip() if raw_group else None)
            # Only link when the match-level label names a real team group.
            linked = group_map.get(norm(g_label)) if g_label else None

            match = Match(
                stage_id=stage.id,
                group_id=linked.id if linked else None,
                home_team_id=home.id, away_team_id=away.id,
                match_date=dt,
                week=str(m.get("week")).strip() if m.get("week") else None,
                round_label_ar=g_label, round_label_en=g_label,
                venue_ar=pick(m.get("venue"), "ar"), venue_en=pick(m.get("venue"), "en"),
                status=STATUS_MAP.get(str(m.get("status") or "").strip().lower(), "scheduled"),
                home_score=as_int(m.get("home_score")), away_score=as_int(m.get("away_score")),
                home_penalty_score=as_int(m.get("home_penalty")),
                away_penalty_score=as_int(m.get("away_penalty")),
                note_ar=str(m.get("note")).strip() if m.get("note") else None,
                source_ref=src or None,
            )
            db.session.add(match)
            db.session.flush()
            n_matches += 1
            self.stats["matches"] += 1

            for side, team in (("home", home), ("away", away)):
                scored = self.import_events(m, side, team, match, ag)
                declared = as_int(m.get(f"{side}_score"))
                # More named scorers than goals means the source contradicts
                # itself — the scoreline and the scorer list disagree.
                if declared is not None and scored > declared:
                    self.warnings.append(
                        f"{job['code']}/{job['age']}: match {mid} lists {scored} {side} "
                        f"scorers but {side}_score is {declared} — source disagrees with itself"
                    )
                    self.stats["score_mismatch"] += 1

        db.session.flush()
        return len(local), n_matches

    def import_events(self, m: dict, side: str, team: Team, match: Match, ag: AgeGroup) -> int:
        goals, assists = split_scorers(as_list(m.get(f"{side}_scorers")))

        # Assists are a flat list with no link to a specific goal, so they are
        # paired positionally with this team's goals — the only mapping the
        # source supports.
        flat_assists: list[str] = []
        for name, count in assists:
            flat_assists.extend([name] * count)

        i = 0
        for name, count in goals:
            for _ in range(count):
                scorer = self.get_player(name, team, ag)
                assist_player = None
                if i < len(flat_assists):
                    a_name = flat_assists[i]
                    if norm(a_name) != norm(name):  # never self-assist
                        assist_player = self.get_player(a_name, team, ag)
                db.session.add(MatchGoal(
                    match_id=match.id, team_id=team.id,
                    scorer_id=scorer.id,
                    assist_id=assist_player.id if assist_player else None,
                    minute=None,  # not in the source
                ))
                self.stats["goals"] += 1
                i += 1
        scored = sum(c for _, c in goals)

        for field, card_type in ((f"{side}_yc", "yellow"), (f"{side}_rc", "red")):
            for name in as_list(m.get(field)):
                if is_placeholder(name):
                    continue
                p = self.get_player(name, team, ag)
                db.session.add(MatchCard(
                    match_id=match.id, team_id=team.id, player_id=p.id,
                    card_type=card_type, minute=None,
                ))
                self.stats["cards"] += 1
        return scored

    @staticmethod
    def parse_dt(d, t) -> datetime | None:
        d = str(d or "").strip()
        if not d:
            return None
        t = str(t or "").strip() or "00:00"
        for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(f"{d} {t}", fmt)
            except ValueError:
                continue
        try:
            return datetime.strptime(d, "%Y-%m-%d")
        except ValueError:
            return None

    def import_content(self, data: dict):
        for v in data.get("venues") or []:
            name_ar = pick(v.get("name"), "ar")
            if not name_ar or Venue.query.filter_by(name_ar=name_ar).first():
                continue
            db.session.add(Venue(
                name_ar=name_ar, name_en=pick(v.get("name"), "en"), url=v.get("url"),
            ))
            self.stats["venues"] += 1

        for n in data.get("news") or []:
            d = str(n.get("date") or "").strip()
            try:
                nd = datetime.strptime(d, "%Y-%m-%d").date()
            except ValueError:
                continue
            title_ar = pick(n.get("title"), "ar")
            if News.query.filter_by(date=nd, title_ar=title_ar).first():
                continue
            db.session.add(News(
                date=nd, title_ar=title_ar, title_en=pick(n.get("title"), "en"),
                details_ar=pick(n.get("details"), "ar"),
                details_en=pick(n.get("details"), "en"),
                image_url=n.get("image"),
                images=[u for u in as_list(n.get("images")) if u.startswith("http")] or None,
            ))
            self.stats["news"] += 1

        for a in data.get("Ads") or []:
            name = str(a.get("name") or "").strip()
            if not name or Ad.query.filter_by(name=name).first():
                continue
            exp = None
            if a.get("expire_date"):
                try:
                    exp = datetime.strptime(str(a["expire_date"]).strip(), "%Y-%m-%d").date()
                except ValueError:
                    pass
            db.session.add(Ad(
                name=name, image=a.get("image"), youtube_video=a.get("youtube_video"),
                facebook_link=a.get("facebook_link"), mobile_number=a.get("mobile_number"),
                whatsapp_number=a.get("whatsapp_number"), location=a.get("location"),
                location_url=a.get("location_url"), expire_date=exp,
            ))
            self.stats["ads"] += 1

        av = data.get("app_version") or {}
        if av and not AppVersion.query.filter_by(platform="android").first():
            db.session.add(AppVersion(
                platform="android",
                version_code=str(av.get("version_code") or "1"),
                version_name=str(av.get("version_name") or "1.0.0"),
            ))


def report():
    """What the imported data actually looks like, warts included."""
    import sqlalchemy as sa

    def scalar(q):
        return db.session.execute(sa.text(q)).scalar()

    print("=" * 62)
    print("DATA QUALITY REPORT")
    print("=" * 62)

    total = scalar("select count(*) from matches")
    done = scalar("select count(*) from matches where status='completed'")
    print(f"\nMatches: {total} ({done} completed)")

    sl = scalar("select coalesce(sum(home_score+away_score),0) from matches where status='completed'")
    rec = scalar("""select count(*) from match_goals g join matches m on m.id=g.match_id
                    where m.status='completed'""")
    print(f"\nGoals in scorelines : {sl}")
    print(f"Goals with a scorer : {rec}  ({100*rec/sl:.0f}%)")
    print(f"Goals with no name  : {sl-rec}  <- standings are right, top-scorer tables are incomplete")

    noscorer = scalar("""select count(*) from matches m where m.status='completed'
        and m.home_score+m.away_score > 0
        and not exists (select 1 from match_goals g where g.match_id=m.id)""")
    print(f"\nCompleted matches with goals but no scorers recorded: {noscorer}")

    mism = scalar("""select count(*) from (
        select m.id from matches m join match_goals g on g.match_id=m.id
        where m.status='completed' group by m.id
        having count(g.id) > m.home_score+m.away_score)""")
    print(f"Matches where the scorer list exceeds the score:      {mism}  <- fix at source")

    print(f"\nPlayers: {scalar('select count(*) from players')}")
    print(f"  birth year inferred, needs review: {scalar('select count(*) from players where birth_year_verified=0')}")
    dupe = scalar("""select count(*) from (select full_name_ar from players
        group by full_name_ar having count(*) > 1)""")
    print(f"  names held by more than one player row: {dupe}")
    print("     (same name at two clubs = two rows; merging needs real identity data)")

    print(f"\nClubs: {scalar('select count(*) from clubs')}")
    print(f"  without an English name: {scalar('select count(*) from clubs where name_en is null')}")
    print(f"  without a logo:         {scalar('select count(*) from clubs where logo_url is null')}")

    print(f"\nCards recorded: {scalar('select count(*) from match_cards')}  (the feed carries almost none)")
    print(f"Coaches: {scalar('select count(*) from coaches')}")
    print("=" * 62)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--reset", action="store_true", help="wipe the season before importing")
    ap.add_argument("--report", action="store_true", help="describe imported data, do not import")
    ap.add_argument("--season", default="2025-2026")
    args = ap.parse_args()

    app = create_app()
    with app.app_context():
        if args.report:
            return report()

        imp = Importer(args.season)
        imp.run(reset=args.reset)

        print("\n" + "=" * 58)
        print("IMPORTED")
        for k in ("seasons", "age_groups", "competitions", "stages", "groups",
                  "clubs", "teams", "coaches", "players", "matches", "goals",
                  "cards", "venues", "news", "ads"):
            if imp.stats[k]:
                print(f"  {k:14} {imp.stats[k]:6}")
        if imp.warnings:
            print(f"\nWARNINGS ({len(imp.warnings)}):")
            for w in imp.warnings[:25]:
                print("  -", w)
            if len(imp.warnings) > 25:
                print(f"  ... and {len(imp.warnings) - 25} more")
        print("=" * 58)


if __name__ == "__main__":
    sys.exit(main())
