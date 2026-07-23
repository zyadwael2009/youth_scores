from app.models.auth import AdminUser
from app.models.competition import (
    Competition,
    CompetitionTeam,
    Group,
    GroupTeam,
    Stage,
)
from app.models.content import Ad, AppVersion, News, Venue
from app.models.core import AgeGroup, Club, Coach, Player, Season
from app.models.match import (
    Match,
    MatchCard,
    MatchGoal,
    MatchPenaltyShootout,
    MatchPlayer,
    MatchSubstitution,
)
from app.models.team import ClubStaff, PlayerTeam, Team, TeamCoach
from app.models.tla3bny import (
    Tla3bnyAgeCategory,
    Tla3bnyLineup,
    Tla3bnyLineupSlot,
    Tla3bnyMatch,
    Tla3bnyMatchEvent,
    Tla3bnyPlayer,
    Tla3bnyPlayerFile,
    Tla3bnyUser,
)

__all__ = [
    # core
    "Club",
    "Season",
    "AgeGroup",
    "Player",
    "Coach",
    # team
    "Team",
    "TeamCoach",
    "PlayerTeam",
    "ClubStaff",
    # competition
    "Competition",
    "CompetitionTeam",
    "Stage",
    "Group",
    "GroupTeam",
    # match
    "Match",
    "MatchPlayer",
    "MatchGoal",
    "MatchCard",
    "MatchSubstitution",
    "MatchPenaltyShootout",
    # content
    "Venue",
    "News",
    "Ad",
    "AppVersion",
    # auth
    "AdminUser",
    # tla3bny (LeagueHub subdomain)
    "Tla3bnyUser",
    "Tla3bnyAgeCategory",
    "Tla3bnyPlayer",
    "Tla3bnyPlayerFile",
    "Tla3bnyMatch",
    "Tla3bnyMatchEvent",
    "Tla3bnyLineup",
    "Tla3bnyLineupSlot",
]
