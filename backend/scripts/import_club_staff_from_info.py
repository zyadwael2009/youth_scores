"""Import club youth-sector staff from the feed's team `information` field.

The source JSON keeps a club's youth-sector officials in each team's
`information` field, one person per line. The original migration had nowhere to
put it (teams have no `information` column), so it was dropped -- which is why
"مسؤولو قطاع الناشئين" is empty for most clubs.

Three line formats appear, and all are handled:

    المشرف علي قطاع الناشئين ك / عاطف حنفي     role, marker, name
    رئيس قطاع الناشئين كابتن حماده البحر        role, marker, name (no slash)
    د. حاتم حسن – عضو مجلس الإدارة              name, dash, role

The same club shows up under several age groups with the same officials, so
entries are de-duplicated per (club, person, role).

    python -m scripts.import_club_staff_from_info            # dry run
    python -m scripts.import_club_staff_from_info --apply
"""

from __future__ import annotations

import json
import re
import sys
import urllib.request
from collections import Counter, defaultdict

from app import create_app
from app.extensions import db
from app.models import Club, ClubStaff, Coach
from scripts.split_coach_roles import normalize_ar

CONFIG_URL = "https://youth-scores-data.vercel.app/api/config"

DASH = r"[–—]"
# Honorific that introduces a person, in either direction.
MARKER = (
    r"(?:الكابتن|الكابتين|كابتن|الدكتور|دكتور|ك\s*[/.]|د\s*[/.]|م\s*[/.]"
    r"|أ\s*[/.]|ا\s*[/.]|\bك\b|/)"
)
# Personal titles that precede a name and are not part of it.
LEADING_TITLE = re.compile(
    r"^(?:الكابتن|الكابتين|كابتن|الدكتور|دكتور|العميد|الحاج|الاستاذ|الأستاذ"
    r"|المهندس|الشيخ|[كدمأا]\s*[/.])\s*[:：]?\s*"
)
MARKER_RE = re.compile(MARKER)


def fetch(url: str):
    with urllib.request.urlopen(url, timeout=90) as r:
        return json.loads(r.read().decode("utf-8"))


# Words that begin a job title; used to find where a name ends and a role starts
# when the line has no separator at all ("كابتن ياسر رجب رئيس قطاع الناشئين").
ROLE_KW = (
    r"(?:ال)?(?:رئيس|نواب|نائب|مدير|مشرف|طبيب|إدار|ادار|مدرب|محلل|مخطط|"
    r"مسؤول|مسئول|عضو|اخصائي|أخصائي|معد|مساعد|شئون|شؤون|امين|أمين|كابتن)"
)
ROLE_START = re.compile(rf"(?:^|\s)({ROLE_KW}.*)$")
# Lines that are not a person at all.
SKIP_LINE = re.compile(r"^(?:برعاية|ويشرف)")


def _split_on_role_word(text: str) -> tuple[str, str] | None:
    m = ROLE_START.search(text)
    if not m:
        return None
    return text[: m.start()].strip(), m.group(1).strip()


def parse_line(line: str) -> tuple[str, str] | None:
    """Return (name, role) for one line of the information field."""
    s = re.sub(r"\s+", " ", (line or "").strip())
    if len(s) < 4 or SKIP_LINE.match(s):
        return None

    name = role = ""
    if re.search(DASH, s):
        # "<name> – <role>"
        left, right = re.split(DASH, s, maxsplit=1)
        name = LEADING_TITLE.sub("", left.strip()).strip()
        role = right.strip()
    else:
        m = MARKER_RE.search(s)
        if m and m.start() > 0:
            # "<role> <marker> <name>"
            role = s[: m.start()].strip()
            name = s[m.end():].strip()
        else:
            # "<marker>? <name> <role>" - no separator; find the role word.
            rest = LEADING_TITLE.sub("", s).strip() if m else s
            split = _split_on_role_word(rest)
            if not split:
                return None
            name, role = split

    # Titles can also sit in front of the name after a role-word split.
    name = LEADING_TITLE.sub("", name.strip()).strip()
    name = re.sub(r"\s+", " ", name).strip(" .-–—:")
    role = re.sub(r"\s+", " ", role).strip(" .-–—:")
    # A "name" that is itself a job title means the line had no person in it.
    if not name or not role or len(name) < 3 or ROLE_START.match(name):
        return None
    return name, role


def team_name(t: dict) -> str:
    n = t.get("name")
    if isinstance(n, str):
        return n
    return (n or {}).get("ar") or (n or {}).get("en") or ""


def main(apply: bool) -> None:
    app = create_app()
    with app.app_context():
        # club lookup by normalised name
        clubs: dict[str, Club] = {}
        for c in Club.query.all():
            for nm in (c.name_ar, c.name_en):
                if nm:
                    clubs.setdefault(normalize_ar(nm), c)

        data = fetch(fetch(CONFIG_URL)["latestDataUrl"])
        feeds: list[str] = []
        for s in data.get("seasons") or []:
            for c in s.get("competitions") or []:
                for a in c.get("ages") or []:
                    u = a.get("matchesurl")
                    u = [u] if isinstance(u, str) else (u or [])
                    feeds.extend([x for x in u if x])
        feeds = list(dict.fromkeys(feeds))

        # (club_id, normalised person) -> {display name, roles}
        found: dict[tuple[int, str], dict] = defaultdict(lambda: {"name": "", "roles": set()})
        roles = Counter()
        unmatched: Counter = Counter()
        lines_seen = lines_parsed = 0

        for url in feeds:
            try:
                feed = fetch(url)
            except Exception as e:  # noqa: BLE001
                print(f"  !! {url}: {e}")
                continue
            for t in feed.get("teams") or []:
                info = (t.get("information") or "").strip()
                if not info:
                    continue
                club = clubs.get(normalize_ar(team_name(t)))
                if club is None:
                    unmatched[team_name(t)] += 1
                    continue
                for line in re.split(r"[\r\n]+", info):
                    if not line.strip():
                        continue
                    lines_seen += 1
                    parsed = parse_line(line)
                    if not parsed:
                        continue
                    lines_parsed += 1
                    name, role = parsed
                    key = (club.id, normalize_ar(name))
                    found[key]["name"] = name
                    found[key]["roles"].add(role)
                    roles[role] += 1

        created = skipped = 0
        for (club_id, _norm), rec in found.items():
            for role in sorted(rec["roles"]):
                exists = any(
                    normalize_ar(s.coach.full_name_ar or "") == _norm and s.role_ar == role
                    for s in ClubStaff.query.filter_by(club_id=club_id).all()
                )
                if exists:
                    skipped += 1
                    continue
                created += 1
                if apply:
                    coach = None
                    for s in ClubStaff.query.filter_by(club_id=club_id).all():
                        if normalize_ar(s.coach.full_name_ar or "") == _norm:
                            coach = s.coach
                            break
                    if coach is None:
                        coach = Coach(full_name_ar=rec["name"])
                        db.session.add(coach)
                        db.session.flush()
                    db.session.add(ClubStaff(club_id=club_id, coach_id=coach.id, role_ar=role))

        print(f"feeds scanned        : {len(feeds)}")
        print(f"information lines    : {lines_seen}  (parsed {lines_parsed})")
        print(f"clubs matched        : {len({k[0] for k in found})}")
        print(f"people found         : {len(found)}")
        print(f"club_staff to create : {created}")
        print(f"already present      : {skipped}")
        print(f"distinct roles       : {len(roles)}")
        print("\n--- roles ---")
        for r, n in roles.most_common():
            print(f"  {n:>4}  {r}")
        if unmatched:
            print(f"\n--- teams with info but no matching club ({len(unmatched)}) ---")
            for nm, n in unmatched.most_common(15):
                print(f"  {n:>3}  {nm}")

        if apply:
            db.session.commit()
            print("\nAPPLIED and committed.")
        else:
            db.session.rollback()
            print("\nDRY RUN - nothing written. Re-run with --apply to commit.")


if __name__ == "__main__":
    main(apply="--apply" in sys.argv)
