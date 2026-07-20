"""Controlled vocabularies for the coded string columns."""

# Match.status
# Deviates from the design doc, which said scheduled/played/postponed:
# "completed" is what the existing JSON feed and both clients already use,
# and "live" is needed for in-progress score updates.
MATCH_STATUS = ("scheduled", "live", "completed", "postponed", "cancelled")
MATCH_STATUS_COMPLETED = "completed"

# Stage.type
STAGE_TYPE = ("group", "league", "knockout")
STAGE_TYPE_KNOCKOUT = "knockout"

# PlayerTeam.status
PLAYER_TEAM_STATUS = ("active", "transferred", "loaned")

# MatchCard.card_type
CARD_TYPE = ("yellow", "second_yellow", "red")

# MatchPenaltyShootout.result
PENALTY_RESULT = ("scored", "missed", "saved", "off_target")

# Player.preferred_foot
PREFERRED_FOOT = ("left", "right", "both")

# MatchPlayer.position
POSITION = ("GK", "RB", "LB", "CB", "CDM", "CM", "CAM", "RM", "LM", "RW", "LW", "ST", "CF")

# AdminUser.role
ADMIN_ROLE = ("superadmin", "editor", "clerk")

# TeamCoach.role_ar — the default seniority order for a team's technical staff.
# Free text is still allowed; anything not listed sorts after these. A manual
# reorder (TeamCoach.sort_order) takes precedence over this.
COACH_ROLE_ORDER = (
    "المدير الفني",
    "مدرب",
    "مساعد مدرب",
    "مدرب حراس مرمي",
    "محلل اداء",
    "المعد النفسي",
    "اداري",
    "طبيب",
    "اخصائي اصابات",
    "علاج طبيعي",
    "مدلك",
    "مدرب الاحمال",
    "اخصائي",
    "عامل مهمات",
)
# Existing rows use variant wordings for roles already in the list above; rank
# them with their canonical equivalent instead of dumping them at the end.
COACH_ROLE_ALIASES = {
    "مدرب الحراس": "مدرب حراس مرمي",
    "مسئول المهمات": "عامل مهمات",
    "طبيب عظام": "طبيب",
    "محلل الاداء": "محلل اداء",
    "اخصائي الاصابات": "اخصائي اصابات",
}

COACH_ROLE_RANK = {role: i for i, role in enumerate(COACH_ROLE_ORDER)}
COACH_ROLE_RANK.update(
    {alias: COACH_ROLE_RANK[canonical] for alias, canonical in COACH_ROLE_ALIASES.items()}
)
UNRANKED_COACH_ROLE = len(COACH_ROLE_ORDER)


# ClubStaff.role_ar — the club's youth-sector posts, most senior first. Same
# rules as the coach order: free text is allowed and sorts last, and a manual
# reorder (ClubStaff.sort_order) wins over this.
CLUB_STAFF_ROLE_ORDER = (
    "عضو مجلس الإدارة",
    "رئيس قطاع الناشئين",
    "نائب رئيس القطاع",
    "مشرف القطاع",
    "المدير الفني للقطاع",
    "المشرف الفني للقطاع",
    "المدير الاداري للقطاع",
    "مدير الكرة",
    "نائب رئيس جهاز الكرة",
    "مشرف الكرة",
    "مدير حراس المرمى بالقطاع",
    "مشرف حراس المرمى",
    "رئيس الجهاز الطبي",
    "طبيب القطاع",
    "مشرف العلاج الطبيعي",
    "اخصائي الفريق",
    "مخطط أحمال",
    "محلل أداء",
    "مسؤول شئون اللاعبين",
    "المدير المالي",
    "مدير عام النادي",
    "مدير رياضي",
    "مشرف النشاط الرياضي",
    "مدير التسويق بالقطاع",
    "المشرف العام علي الالعاب الجماعية",
)
CLUB_STAFF_ROLE_RANK = {role: i for i, role in enumerate(CLUB_STAFF_ROLE_ORDER)}
UNRANKED_CLUB_STAFF_ROLE = len(CLUB_STAFF_ROLE_ORDER)
