"""Collapse the club-staff role titles onto one canonical name per post.

The feed wrote the same post many different ways ("رئيس القطاع", "مدير القطاع",
"المشرف العام", ...). This maps every variant onto a single title.

Grouping rules agreed with the club:
  * رئيس and مدير are the same post; مشرف is a different one.
  * Medical staff stay separate posts (doctor / physio / specialist).
  * Miscellaneous admin titles keep their own wording.

Rows that become identical (same club, same person, same post) are de-duplicated.

    python -m scripts.normalize_club_staff_roles            # dry run
    python -m scripts.normalize_club_staff_roles --apply
"""

from __future__ import annotations

import sys
from collections import Counter

from app import create_app
from app.extensions import db
from app.models import ClubStaff
from scripts.split_coach_roles import normalize_ar

GROUPS: dict[str, list[str]] = {
    "رئيس قطاع الناشئين": [
        "رئيس قطاع الناشئين", "رئيس القطاع", "رئيس قطاع الناشئين و البراعم",
        "مدير قطاع الناشئين", "مدير القطاع", "رئيس قطاع البراعم و الناشئين",
        "رئيس الجهاز", "رئيس قطاع الناشئين و الشباب", "مدير عام القطاع",
        "مدير ادارة الناشئين", "رئيس اللجنة المشرفة علي قطاع الناشئين",
        "مدير الجهاز", "مدير قطاع البراعم",
    ],
    "مشرف القطاع": [
        "مشرف القطاع", "المشرف العام", "مشرف علي القطاع", "مشرف عام علي القطاع",
        "مشرف قطاع الناشئين و البراعم", "مشرف قطاع الناشئين",
        "مشرف عام علي قطاع الناشئين", "مشرف عام على القطاع", "مشرف عام",
        "مشرف البراعم و الناشئين", "مشرف مرحله الناشئين",
        "المشرف العام على قطاع الناشئين",
        "المشرف علي قطاع الناشئين و البراعم و الكرة النسائية",
        "المشرف العام علي قطاعات الكرة العقي",
    ],
    "نائب رئيس القطاع": [
        "نائب رئيس القطاع", "نائب رئيس قطاع الناشئين", "نائب رئيس الجهاز",
        "نواب رئيس القطاع", "نائب رئيس قطاع الناشئين و البراعم",
        "نائب رئيس جهاز البراعم و الناشئين", "مساعد مدير القطاع",
        "مساعد مدير قطاع الناشئين",
        "نائب رئيس قطاع الناشئين و المدير الفني لقطاع البراعم",
        "نائب رئيس القطاع و المدير الفني لقطاع البراعم",
    ],
    "المدير الاداري للقطاع": [
        "مدير اداري", "مدير اداري القطاع", "المدير الاداري",
        "المدير الاداري للقطاع", "مدير اداري قطاع الناشئين", "مدير إداري القطاع",
        "المدير الاداري لقطاع الناشئين", "المدير الإداري",
        "المدير الإداري للقطاع", "المدير الإداري لقطاع الناشئين",
        "المدير الإدارى للقطاع", "مدير اداري قطاع الناشئين و الشباب",
        "مدير اداري القطاع و شئون اللاعبين", "ادراي القطاع",
        "اداري قطاع الناشئين و البراعم",
    ],
    "المدير الفني للقطاع": [
        "مدير فني قطاع الناشئين", "مدير فني القطاع", "مدير فنى القطاع",
        "المدير الفني للقطاع", "المدير الفني لقطاع الناشئين",
        "مديرًا فنيًا للقطاع", "مدرب عام القطاع",
    ],
    "المشرف الفني للقطاع": ["المشرف الفني لفرق الشباب و الناشئين"],
    "مدير حراس المرمى بالقطاع": [
        "مدير قطاع حراس المرمي", "مدير فني مدربين حراس المرمي",
        "مدير فني مدربي حراس المرمي", "مدير فني حراس المرمي للقطاع",
        "مدير فني حراس المرمى", "مدير فنى حراس المرمى", "رئيس جهاز الحراس",
    ],
    "مشرف حراس المرمى": [
        "مشرف مدربي الحراس", "مشرف عام علي مدربين حراس المرمي",
        "مشرف حراس المرمي لقطاع الناشئين و البراعم",
        "مشرف حراس المرمي لقطاع الناشئين", "مشرف حراس المرمي",
        "المشرف العام على حراس المرمى", "مشرفا علي تدريب الحراس للبراعم",
        "مدرب حراس المرمي",
    ],
    "مدير الكرة": ["مدير الكرة", "رئيس جهاز الكرة"],
    "نائب رئيس جهاز الكرة": ["نائب رئيس جهاز الكرة"],
    "مشرف الكرة": ["مشرف علي الكرة"],
    "مسؤول شئون اللاعبين": [
        "مدير شئون اللاعبين", "مسؤول شؤون اللاعبين", "مسئول شئون اللاعبين",
        "شئون لاعبين",
    ],
    "المدير المالي": [
        "مدير مالي", "المشرف المالي", "المدير المالي", "المسؤول المالى والإداري",
    ],
    "عضو مجلس الإدارة": [
        "عضو مجلس الإدارة ورئيس المنظومة الإعلامية",
        "عضو مجلس الادارة و المشرف العام علي قطاع الناشئين و البراعم",
        "عضو مجلس الإدارة والمشرف العام على الكرة", "رئيس مجلس الادارة مهندس",
        "المشرف العام عضو مجلس الادارة",
        "المشرف العام علي قطاع الناشئين و نائب رئيس مجلس الادارة",
        "المشرف العام علي قطاع الناشئين و البراعم و نائب رئيس مجلس الادارة",
    ],
    # Medical posts stay separate.
    "رئيس الجهاز الطبي": ["رئيس الجهاز الطبي"],
    "طبيب القطاع": ["طبيب القطاع"],
    "مشرف العلاج الطبيعي": ["مشرف العلاج الطبيعي"],
    "اخصائي الفريق": ["اخصائي الفريق"],
    "مخطط أحمال": ["مخطط احمال القطاع", "مخطط أحمال القطاع", "مدرب أحمال"],
    "محلل أداء": ["محلل اداء الرياضي للقطاع"],
    # Miscellaneous admin titles keep their own wording (identity mapping).
    "مشرف النشاط الرياضي": ["مشرف النشاط الرياضي"],
    "مدير عام النادي": ["مدير عام النادي"],
    "مدير التسويق بالقطاع": ["مدير التسويق بالقطاع"],
    "مدير رياضي": ["مديرا رياضيا"],
    "المشرف العام علي الالعاب الجماعية": ["المشرف العام علي الالعاب الجماعية"],
}

LOOKUP = {normalize_ar(v): canon for canon, vs in GROUPS.items() for v in vs}


def main(apply: bool) -> None:
    app = create_app()
    with app.app_context():
        rows = ClubStaff.query.all()
        changed = Counter()
        unmapped = Counter()
        seen: set[tuple[int, int, str]] = set()
        dupes = 0

        for s in rows:
            canon = LOOKUP.get(normalize_ar(s.role_ar or ""))
            if canon is None:
                unmapped[s.role_ar] += 1
                continue
            if canon != s.role_ar:
                changed[f"{s.role_ar}  ->  {canon}"] += 1
            key = (s.club_id, s.coach_id, canon)
            if key in seen:
                dupes += 1
                if apply:
                    db.session.delete(s)
                continue
            seen.add(key)
            if apply:
                s.role_ar = canon

        print(f"club_staff rows      : {len(rows)}")
        print(f"titles rewritten     : {sum(changed.values())}")
        print(f"duplicate rows dropped: {dupes}")
        print(f"unmapped titles      : {len(unmapped)}")
        for t, n in unmapped.most_common():
            print(f"   {n:>3}  {t}")
        print(f"\nfinal distinct posts : {len({k[2] for k in seen})}")

        if apply:
            db.session.commit()
            print("\nAPPLIED and committed.")
        else:
            db.session.rollback()
            print("\nDRY RUN - nothing written. Re-run with --apply to commit.")


if __name__ == "__main__":
    main(apply="--apply" in sys.argv)
