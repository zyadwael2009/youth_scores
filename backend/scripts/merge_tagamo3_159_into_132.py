"""One-shot: fold club 159 ("م.ش التجمع الاول") into club 132 ("التجمع الاول").

Source 159 is merged into target 132 and then deleted, reusing the audited
logic in ``scripts.merge_clubs`` (teams repoint by age group; matches, roster,
staff and competition/group rows follow; exact duplicates are dropped).

Safety rails added on top of the generic script:
  * stdout is forced to UTF-8 so it never crashes on a Windows cp1252 console
    (``railway run`` executes locally, so this runs on your machine).
  * the two clubs are verified BY NAME (compared against exact codepoints)
    before anything is touched — if the live DB's ids don't line up with the
    expected names, it aborts and writes nothing.

Usage (run against the LIVE database via Railway):

    railway run python -m scripts.merge_tagamo3_159_into_132            # dry run
    railway run python -m scripts.merge_tagamo3_159_into_132 --apply    # commit
"""

from __future__ import annotations

import sys

# Force UTF-8 so printing Arabic names never dies on a Windows cp1252 console.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from app import create_app
from app.extensions import db
from app.models import Club
import scripts.merge_clubs as merge_clubs

SOURCE_ID = 159
TARGET_ID = 132

# Expected names, built from codepoints to avoid any file-encoding ambiguity.
# 132: "التجمع الاول"
EXPECTED_TARGET = "".join(map(chr, (
    0x627, 0x644, 0x62a, 0x62c, 0x645, 0x639, 0x20,
    0x627, 0x644, 0x627, 0x648, 0x644,
)))
# 159: "م.ش التجمع الاول"
EXPECTED_SOURCE = "".join(map(chr, (
    0x645, 0x2e, 0x634, 0x20,
    0x627, 0x644, 0x62a, 0x62c, 0x645, 0x639, 0x20,
    0x627, 0x644, 0x627, 0x648, 0x644,
)))


def _guard() -> bool:
    """Confirm the live ids still carry the names we expect. No writes."""
    app = create_app()
    with app.app_context():
        src = db.session.get(Club, SOURCE_ID)
        tgt = db.session.get(Club, TARGET_ID)
        ok = True
        for club, cid, expected, label in (
            (src, SOURCE_ID, EXPECTED_SOURCE, "source"),
            (tgt, TARGET_ID, EXPECTED_TARGET, "target"),
        ):
            if club is None:
                print(f"ABORT: {label} club id {cid} not found in this database.")
                ok = False
            elif club.name_ar != expected:
                print(f"ABORT: {label} club id {cid} is {club.name_ar!r}, "
                      f"expected {expected!r}. Refusing to touch the wrong club.")
                ok = False
        if ok:
            print(f"guard OK: {SOURCE_ID}={src.name_ar!r} -> {TARGET_ID}={tgt.name_ar!r}\n")
        db.session.rollback()
        return ok


if __name__ == "__main__":
    apply = "--apply" in sys.argv[1:]
    if not _guard():
        sys.exit(1)
    merge_clubs.main(from_id=SOURCE_ID, to_id=TARGET_ID,
                     from_name=None, to_name=None, apply=apply)
