"""Collapse line breaks and repeated spaces inside stored names.

Long club names were typed across two lines, and clubs that play under a second
name carry both ("بلدية المحلة\\n (اوفرلاب)"). The newline is a typing artefact,
not part of the name: it breaks the layout wherever the name is rendered on one
line, and makes two spellings of one name compare unequal.

Only whitespace changes — every word is kept, nothing is merged or dropped.
Names that differ solely by a line break therefore stay separate rows, which is
correct here: an academy playing under a club's bought name is its own entrant,
not a duplicate of that club.

    python -m scripts.normalize_name_whitespace
    python -m scripts.normalize_name_whitespace --apply
"""

from __future__ import annotations

import re
import sys

from app import create_app
from app.extensions import db
from app.models import Club, Coach, Competition, Player, Team, Venue

# (model, label, columns) — every free-text name the panel or feed displays.
TARGETS = (
    (Club, "نادٍ", ("name_ar", "name_en", "city_ar", "city_en")),
    (Team, "فريق", ("name_ar", "name_en", "short_name_ar", "short_name_en")),
    (Competition, "بطولة", ("name_ar", "name_en", "sector_ar", "sector_en")),
    (Coach, "مدرب", ("full_name_ar", "full_name_en")),
    (Player, "لاعب", ("full_name_ar", "full_name_en")),
    (Venue, "ملعب", ("name_ar", "name_en")),
)

WS = re.compile(r"\s+")


def tidy(v: str | None) -> str | None:
    if not isinstance(v, str):
        return v
    cleaned = WS.sub(" ", v).strip()
    return cleaned or None


def main(apply: bool) -> None:
    app = create_app()
    with app.app_context():
        total = 0
        for model, label, cols in TARGETS:
            hits = 0
            for row in model.query.all():
                for col in cols:
                    before = getattr(row, col, None)
                    after = tidy(before)
                    if before == after:
                        continue
                    hits += 1
                    total += 1
                    print(f"  {label} #{row.id} {col}: {before!r}")
                    print(f"        -> {after!r}")
                    if apply:
                        setattr(row, col, after)
            if hits:
                print(f"  -- {label}: {hits} حقل\n")

        print(f"إجمالي الحقول: {total}")
        if apply:
            db.session.commit()
            print("تم التنفيذ والحفظ.")
        else:
            db.session.rollback()
            print("DRY RUN - لم يُكتب شيء. أضف --apply للتنفيذ.")


if __name__ == "__main__":
    main(apply="--apply" in sys.argv)
