================================================================================
         COMPLETE DATABASE DESIGN DOCUMENTATION
         Egyptian Youth Competition System - Youthscores.org
================================================================================

TABLE OF CONTENTS
--------------------------------------------------------------------------------
1. Overview
2. Core Design Principles
3. Table Structure (18 Tables)
4. Data Entry Flow
5. Bilingual Support Logic
6. Foreign Key Dropdowns
7. Platform Support (Website + Android)
8. Special Features Supported
9. Relationship Diagram
10. Summary of Nullability Rules
11. Quick Reference: Mandatory Fields by Table


================================================================================
1. OVERVIEW
================================================================================

This document contains the complete database structure for a youth football
competition management system supporting:

- Multiple age groups (2009, 2010, 2011, 2012, 2013)
- Bilingual support (Arabic/English)
- Player transfers mid-season
- Multi-stage tournaments (group stage -> league -> knockout)
- Detailed match statistics (goals, assists, cards, substitutions)
- Penalty shootout tracking
- Administrative staff roles

The system is designed to work for both a website and an Android application
using a single centralized database on PythonAnywhere.


================================================================================
2. CORE DESIGN PRINCIPLES
================================================================================

1. Bilingual Support
   All human-readable fields have _en and _ar versions.

2. Null-Friendly
   All bilingual fields are nullable, with fallback logic (COALESCE).
   If English is missing, Arabic appears. If Arabic is missing, English appears.

3. Auto-Increment IDs
   The system generates all primary keys automatically. Users never type IDs.

4. Platform Agnostic
   Works for both website and Android application via RESTful API.

5. Historical Tracking
   All relationships support start_date and end_date for transfers and role
   changes. end_date = NULL means currently active.


================================================================================
3. TABLE STRUCTURE (18 TABLES)
================================================================================

--------------------------------------------------------------------------------
TABLE 1: Club
Stores public-facing club information.
--------------------------------------------------------------------------------

Field                 Type        Nullable    Bilingual    Description
--------------------- ----------- ----------- ------------ --------------------
id                    Integer     NO (PK)     No           Primary Key
name_en               String      YES         Yes          Club name in English
name_ar               String      YES         Yes          Club name in Arabic
city_en               String      YES         Yes          City in English
city_ar               String      YES         Yes          City in Arabic
logo_url              String      YES         No           Link to club badge
website_url           String      YES         No           Official website
facebook_url          String      YES         No           Facebook page
instagram_url         String      YES         No           Instagram handle
twitter_url           String      YES         No           Twitter/X handle
youtube_url           String      YES         No           YouTube channel
established           Date        YES         No           Foundation year


--------------------------------------------------------------------------------
TABLE 2: Season
Defines the competition calendar.
--------------------------------------------------------------------------------

Field                 Type        Nullable    Bilingual    Description
--------------------- ----------- ----------- ------------ --------------------
id                    Integer     NO (PK)     No           Primary Key
name_en               String      YES         Yes          e.g., "2025-2026"
name_ar               String      YES         Yes          e.g., "۲۰۲٥-۲۰۲٦"
start_date            Date        NO          No           Season start date
end_date              Date        NO          No           Season end date
is_active             Boolean     NO          No           TRUE for current season


--------------------------------------------------------------------------------
TABLE 3: AgeGroup
Defines age categories strictly by birth year.
--------------------------------------------------------------------------------

Field                 Type        Nullable    Bilingual    Description
--------------------- ----------- ----------- ------------ --------------------
id                    Integer     NO (PK)     No           Primary Key
name_en               String      YES         Yes          e.g., "Under-17"
name_ar               String      YES         Yes          e.g., "تحت ١٧ سنة"
oldest_birth_year     Integer     NO          No           Maximum birth year
                                                           allowed (younger
                                                           players can play up)


--------------------------------------------------------------------------------
TABLE 4: Player
Individual player profiles.
ONLY name and birth_year are mandatory. All other fields are optional.
--------------------------------------------------------------------------------

Field                 Type        Nullable    Bilingual    Description
--------------------- ----------- ----------- ------------ --------------------
id                    Integer     NO (PK)     No           Primary Key
full_name_en          String      YES         Yes          Full name in English
full_name_ar          String      YES         Yes          Full name in Arabic
birth_year            Integer     NO          No           Used for age eligibility
full_dob              Date        YES         No           Exact date of birth
nationality_en        String      YES         Yes          Nationality in English
nationality_ar        String      YES         Yes          Nationality in Arabic
position_en           String      YES         Yes          Position in English
position_ar           String      YES         Yes          Position in Arabic
height_cm             Integer     YES         No           Height in centimeters
weight_kg             Integer     YES         No           Weight in kilograms
preferred_foot        String      YES         No           Code: left/right/both
profile_pic_url       String      YES         No           Link to photo
registration_number   String      YES         No           Federation ID


--------------------------------------------------------------------------------
TABLE 5: Coach
Individual coach profiles.
Only name is mandatory. All other fields are optional.
--------------------------------------------------------------------------------

Field                 Type        Nullable    Bilingual    Description
--------------------- ----------- ----------- ------------ --------------------
id                    Integer     NO (PK)     No           Primary Key
full_name_en          String      YES         Yes          Full name in English
full_name_ar          String      YES         Yes          Full name in Arabic
birth_year            Integer     YES         No           Year of birth
nationality_en        String      YES         Yes          Nationality in English
nationality_ar        String      YES         Yes          Nationality in Arabic
profile_pic_url       String      YES         No           Link to photo


--------------------------------------------------------------------------------
TABLE 6: Team
The actual playing squad for a specific club, age group, and season.
(Academy can override the display name here.)
--------------------------------------------------------------------------------

Field                 Type        Nullable    Bilingual    Description
--------------------- ----------- ----------- ------------ --------------------
id                    Integer     NO (PK)     No           Primary Key
club_id               FK-Club     NO          No           Legal owner of team
age_group_id          FK-AgeGroup NO          No           Which age category
season_id             FK-Season   NO          No           Which season
name_en               String      YES         Yes          Override display name
name_ar               String      YES         Yes          Override display name
short_name_en         String      YES         Yes          Short code in English
short_name_ar         String      YES         Yes          Short code in Arabic


--------------------------------------------------------------------------------
TABLE 7: TeamCoach
Historical assignment of coaches to teams.
--------------------------------------------------------------------------------

Field                 Type        Nullable    Bilingual    Description
--------------------- ----------- ----------- ------------ --------------------
id                    Integer     NO (PK)     No           Primary Key
team_id               FK-Team     NO          No           Which team
coach_id              FK-Coach    NO          No           Which coach
role_en               String      YES         Yes          e.g., "Head Coach"
role_ar               String      YES         Yes          e.g., "المدير الفني"
start_date            Date        NO          No           Assignment start date
end_date              Date        YES         No           NULL if currently active


--------------------------------------------------------------------------------
TABLE 8: PlayerTeam
Tracks player registrations and transfers (including mid-season moves).
--------------------------------------------------------------------------------

Field                 Type        Nullable    Bilingual    Description
--------------------- ----------- ----------- ------------ --------------------
id                    Integer     NO (PK)     No           Primary Key
player_id             FK-Player   NO          No           Which player
team_id               FK-Team     NO          No           Which team
shirt_number          Integer     YES         No           Squad number
start_date            Date        NO          No           Registration date
end_date              Date        YES         No           NULL if currently active
status                String      NO          No           Code: active/transferred/
                                                           loaned


--------------------------------------------------------------------------------
TABLE 9: Competition
The tournament umbrella.
--------------------------------------------------------------------------------

Field                 Type        Nullable    Bilingual    Description
--------------------- ----------- ----------- ------------ --------------------
id                    Integer     NO (PK)     No           Primary Key
season_id             FK-Season   NO          No           Which season
age_group_id          FK-AgeGroup YES         No           NULL if open to
                                                           multiple age groups
name_en               String      YES         Yes          Competition name
name_ar               String      YES         Yes          Competition name


--------------------------------------------------------------------------------
TABLE 10: Stage
Different phases of the competition (Group Stage, Knockout, etc.).
--------------------------------------------------------------------------------

Field                 Type        Nullable    Bilingual    Description
--------------------- ----------- ----------- ------------ --------------------
id                    Integer     NO (PK)     No           Primary Key
competition_id        FK-Compet   NO          No           Which competition
name_en               String      YES         Yes          Stage name in English
name_ar               String      YES         Yes          Stage name in Arabic
stage_order           Integer     NO          No           1, 2, 3... (progression)
type                  String      NO          No           Code: group/league/
                                                           knockout


--------------------------------------------------------------------------------
TABLE 11: Group
Specific groups within a Stage (e.g., Group A, B, ... up to J).
--------------------------------------------------------------------------------

Field                 Type        Nullable    Bilingual    Description
--------------------- ----------- ----------- ------------ --------------------
id                    Integer     NO (PK)     No           Primary Key
stage_id              FK-Stage    NO          No           Which stage
name_en               String      YES         Yes          e.g., "Group A"
name_ar               String      YES         Yes          e.g., "المجموعة أ"


--------------------------------------------------------------------------------
TABLE 12: Match
The main fixture record - includes referees, scores, and penalty shootouts.
--------------------------------------------------------------------------------

Field                 Type        Nullable    Bilingual    Description
--------------------- ----------- ----------- ------------ --------------------
id                    Integer     NO (PK)     No           Primary Key
stage_id              FK-Stage    NO          No           Which stage
group_id              FK-Group    YES         No           NULL if not group-stage
home_team_id          FK-Team     NO          No           Home team
away_team_id          FK-Team     NO          No           Away team
match_date            DateTime    NO          No           Kickoff date & time
venue_en              String      YES         Yes          Stadium in English
venue_ar              String      YES         Yes          Stadium in Arabic
status                String      NO          No           Code: scheduled/played/
                                                           postponed
home_score            Integer     YES         No           Full-time goals
away_score            Integer     YES         No           Full-time goals
home_penalty_score    Integer     YES         No           NULL if no shootout
away_penalty_score    Integer     YES         No           NULL if no shootout
referee_main          String      YES         No           Main referee name
referee_assistant_1   String      YES         No           Assistant referee 1
referee_assistant_2   String      YES         No           Assistant referee 2
referee_fourth        String      YES         No           Fourth official


--------------------------------------------------------------------------------
TABLE 13: MatchPlayer
Line-up and substitutes for a specific match.
Includes aggregated stats for quick display.
--------------------------------------------------------------------------------

Field                 Type        Nullable    Bilingual    Description
--------------------- ----------- ----------- ------------ --------------------
id                    Integer     NO (PK)     No           Primary Key
match_id              FK-Match    NO          No           Which match
team_id               FK-Team     NO          No           Which team they played for
player_id             FK-Player   NO          No           Which player
jersey_number         Integer     YES         No           Shirt number worn
position              String      YES         No           Code: GK, LB, CB, CM,
                                                           LW, ST
is_starter            Boolean     NO          No           TRUE = starting XI
minutes_played        Integer     NO          No           Total minutes
goals                 Integer     NO          No           Aggregated goals
assists               Integer     NO          No           Aggregated assists
yellow_cards          Integer     NO          No           Aggregated yellow cards
red_cards             Integer     NO          No           Aggregated red cards


--------------------------------------------------------------------------------
TABLE 14: MatchGoal
Minute-by-minute record of every goal and assist.
--------------------------------------------------------------------------------

Field                 Type        Nullable    Bilingual    Description
--------------------- ----------- ----------- ------------ --------------------
id                    Integer     NO (PK)     No           Primary Key
match_id              FK-Match    NO          No           Which match
team_id               FK-Team     NO          No           Scoring team
scorer_id             FK-Player   NO          No           Who scored
assist_id             FK-Player   YES         No           NULL if no assist
minute                Integer     NO          No           Minute of the goal
is_extra_time         Boolean     NO          No           TRUE if in 90+'
is_own_goal           Boolean     NO          No           TRUE if own goal
is_penalty            Boolean     NO          No           TRUE if from penalty


--------------------------------------------------------------------------------
TABLE 15: MatchCard
Yellow and red cards shown during the match.
--------------------------------------------------------------------------------

Field                 Type        Nullable    Bilingual    Description
--------------------- ----------- ----------- ------------ --------------------
id                    Integer     NO (PK)     No           Primary Key
match_id              FK-Match    NO          No           Which match
team_id               FK-Team     NO          No           Which team
player_id             FK-Player   NO          No           Carded player
card_type             String      NO          No           Code: yellow/second_yellow/
                                                           red
minute                Integer     NO          No           Minute card was shown
is_extra_time         Boolean     NO          No           TRUE if in added time


--------------------------------------------------------------------------------
TABLE 16: MatchSubstitution
Substitution events (who came on and who went off).
--------------------------------------------------------------------------------

Field                 Type        Nullable    Bilingual    Description
--------------------- ----------- ----------- ------------ --------------------
id                    Integer     NO (PK)     No           Primary Key
match_id              FK-Match    NO          No           Which match
team_id               FK-Team     NO          No           Which team
player_out_id         FK-Player   NO          No           Player leaving the pitch
player_in_id          FK-Player   NO          No           Player entering the pitch
minute                Integer     NO          No           Minute of substitution
is_extra_time         Boolean     NO          No           TRUE if in added time


--------------------------------------------------------------------------------
TABLE 17: MatchPenaltyShootout
Records every single penalty kick taken during a knockout match shootout.
--------------------------------------------------------------------------------

Field                 Type        Nullable    Bilingual    Description
--------------------- ----------- ----------- ------------ --------------------
id                    Integer     NO (PK)     No           Primary Key
match_id              FK-Match    NO          No           Which knockout match
team_id               FK-Team     NO          No           Which team is taking kick
player_id             FK-Player   NO          No           The player taking the kick
kick_order            Integer     NO          No           Sequence number (1,2,3...)
result                String      NO          No           Code: scored/missed/
                                                           saved/off_target
is_winning_kick       Boolean     NO          No           TRUE for decisive kick


--------------------------------------------------------------------------------
TABLE 18: ClubStaff
Administrative and technical leadership roles within a club's youth sector.
--------------------------------------------------------------------------------

Field                 Type        Nullable    Bilingual    Description
--------------------- ----------- ----------- ------------ --------------------
id                    Integer     NO (PK)     No           Primary Key
club_id               FK-Club     NO          No           Which club
coach_id              FK-Coach    NO          No           Person holding the role
role_en               String      YES         Yes          Role title in English
role_ar               String      YES         Yes          Role title in Arabic
start_date            Date        YES         No           When role started
end_date              Date        YES         No           NULL if currently active


================================================================================
4. DATA ENTRY FLOW
================================================================================

RECOMMENDED DATA CREATION ORDER:

Step 1: Independent Tables (no dependencies)
        - Club
        - Season
        - AgeGroup
        - Player
        - Coach

Step 2: Dependent Core Tables
        - Team (depends on Club, Season, AgeGroup)
        - ClubStaff (depends on Club, Coach)

Step 3: Competition Structure
        - Competition (depends on Season)
        - Stage (depends on Competition)
        - Group (depends on Stage)

Step 4: Matches & Events
        - Match (depends on Stage, Group, Teams)
        - MatchPlayer (depends on Match, Team, Player)
        - MatchGoal (depends on Match, Team, Player)
        - MatchCard (depends on Match, Team, Player)
        - MatchSubstitution (depends on Match, Team, Player)
        - MatchPenaltyShootout (depends on Match, Team, Player)


MATCH REGISTRATION WORKFLOW (Step-by-Step):

1. Ensure all participating players exist in the Player table
   (Create minimal records with just name and birth_year if needed)

2. Create the match fixture in the Match table
   (Stage, Group, Teams, Date, Venue, Referees)

3. Insert starting XI and substitutes in MatchPlayer table
   (11 starters + substitutes for each team)

4. Record goals in MatchGoal table
   (Scorer, assist, minute, type: penalty/own-goal)

5. Record cards in MatchCard table
   (Player, card type, minute)

6. Record substitutions in MatchSubstitution table
   (Player out, player in, minute)

7. Record penalty shootout in MatchPenaltyShootout table
   (Each kick: player, result, order, winning kick flag)

8. Update Match table with final scores and penalty shootout summary


================================================================================
5. BILINGUAL SUPPORT LOGIC
================================================================================

DISPLAY RULE (Backend Implementation):

IF requested_language = 'en' THEN
    display = COALESCE(field_en, field_ar)
    
IF requested_language = 'ar' THEN
    display = COALESCE(field_ar, field_en)

FIELD CONSTRAINTS:

- All _en and _ar text fields are NULL allowed
- No NOT NULL constraints on bilingual fields
- Allows data entry in one language while leaving the other empty


EXAMPLES:

Example 1: Player has English name only
    full_name_en = "Ahmed Mohamed"
    full_name_ar = NULL
    English interface shows: "Ahmed Mohamed"
    Arabic interface shows: "Ahmed Mohamed" (fallback from English)

Example 2: Player has Arabic name only
    full_name_en = NULL
    full_name_ar = "أحمد محمد"
    English interface shows: "أحمد محمد" (fallback from Arabic)
    Arabic interface shows: "أحمد محمد"

Example 3: Player has both names
    full_name_en = "Ahmed Mohamed"
    full_name_ar = "أحمد محمد"
    English interface shows: "Ahmed Mohamed"
    Arabic interface shows: "أحمد محمد"


================================================================================
6. FOREIGN KEY DROPDOWNS
================================================================================

All foreign key fields will appear as searchable dropdowns (typeahead) to users.

Dropdown Display Rule: Show the bilingual name (with fallback) to the user,
                      store the ID in the database.

Table                    Dropdown Fields (Foreign Keys)
-----------------------  -------------------------------------------
Team                     club_id, age_group_id, season_id
TeamCoach                team_id, coach_id
PlayerTeam               player_id, team_id
Match                    stage_id, group_id, home_team_id, away_team_id
MatchPlayer              match_id, team_id, player_id
MatchGoal                match_id, team_id, scorer_id, assist_id
MatchCard                match_id, team_id, player_id
MatchSubstitution        match_id, team_id, player_out_id, player_in_id
MatchPenaltyShootout     match_id, team_id, player_id
ClubStaff                club_id, coach_id


CHAINED DROPDOWNS (Dependent Filtering):

To prevent errors, dropdowns should be filtered based on previous selections:

Parent Selection              Child Dropdown (Filtered)
----------------------------  ----------------------------------------------
Select a Season               Team dropdown shows only teams in that season
Select a Club                 Team dropdown shows only teams for that club
Select a Match                Team dropdown shows only Home/Away teams
Select a Match + Team         Player dropdown shows only players registered
                              to that team for that match (MatchPlayer)
Select a Stage                Group dropdown shows only groups in that stage


"QUICK ADD" FOR MISSING PLAYERS:

If a player does NOT appear in the dropdown:
1. Clerk clicks "+" button next to the dropdown
2. Popup form appears with: full_name_ar (required) + birth_year (required)
3. Clerk saves the minimal player record
4. System creates the player with a new auto-generated ID
5. Dropdown refreshes and the new player appears
6. Clerk selects the player and continues


================================================================================
7. PLATFORM SUPPORT (WEBSITE + ANDROID APPLICATION)
================================================================================

ARCHITECTURE:

- Single Database: One central database on PythonAnywhere
- API-First: RESTful API delivers JSON to both platforms
- Language Handling: Backend applies bilingual fallback before sending JSON
- Auto-Increment IDs: System generates all IDs automatically


API RESPONSE EXAMPLE (Player Profile):

{
  "id": 45,
  "full_name": "Ahmed Mohamed",
  "birth_year": 2010,
  "nationality": "Egyptian",
  "position": "Midfielder",
  "profile_pic_url": "https://..."
}

Note: Only the resolved language name appears in the API response.
      The Android app never receives raw IDs - just the resolved name.


DATA ENTRY:

Option A (Recommended): Data entry only on Website (desktop admin panel)
Option B: Data entry on both Website and Android app

Both options use the same API endpoints:
POST /api/matches/102/goals/
Payload: { "scorer_id": 45, "minute": 15, "assist_id": null }


================================================================================
8. SPECIAL FEATURES SUPPORTED
================================================================================

1. ACADEMY BUYING CLUB NAME
   - Override Team.name_en and Team.name_ar fields
   - Club remains legal owner via club_id foreign key

2. YOUNGER PLAYERS PLAYING UP
   - AgeGroup.oldest_birth_year defines eligibility
   - Player can register for older age group
   - Application validates: Player.birth_year >= AgeGroup.oldest_birth_year

3. MULTI-STAGE COMPETITIONS
   - Up to 10 groups in first stage via Group table
   - Top teams progress to next Stage
   - Supports: Group Stage -> League -> Knockout progression

4. PLAYER TRANSFERS MID-SEASON
   - PlayerTeam table tracks start_date and end_date
   - Close old record with end_date
   - Open new record with new start_date for new team

5. KNOCKOUT MATCH PENALTY SHOOTOUTS
   - Match.home_penalty_score and away_penalty_score for summary
   - MatchPenaltyShootout for individual kick details
   - Tracks scorer, result, order, and winning kick


================================================================================
9. RELATIONSHIP DIAGRAM
================================================================================

Club ─────┬── Team ──────┬── Match (home/away)
          │              ├── TeamCoach ── Coach
          │              ├── PlayerTeam ── Player
          │              ├── MatchPlayer ── Player
          │              └── MatchGoal ── Player (scorer/assist)
          │
          ├── ClubStaff ── Coach
          │
AgeGroup ─┘
Season ───┘

Competition ── Stage ──┬── Group ──┬── Match
                       │           │
                       └── Match ──┘

Match ─────┬── MatchPlayer
           ├── MatchGoal
           ├── MatchCard
           ├── MatchSubstitution
           └── MatchPenaltyShootout


TABLE RELATIONSHIPS SUMMARY:

Club (1) ──── (n) Team
Club (1) ──── (n) ClubStaff
Coach (1) ─── (n) ClubStaff
Coach (1) ─── (n) TeamCoach
Team (1) ──── (n) TeamCoach
Team (1) ──── (n) PlayerTeam
Player (1) ── (n) PlayerTeam
Team (1) ──── (n) Match (as home_team_id)
Team (1) ──── (n) Match (as away_team_id)
Match (1) ─── (n) MatchPlayer
Match (1) ─── (n) MatchGoal
Match (1) ─── (n) MatchCard
Match (1) ─── (n) MatchSubstitution
Match (1) ─── (n) MatchPenaltyShootout
Player (1) ── (n) MatchPlayer
Player (1) ── (n) MatchGoal (as scorer_id)
Player (1) ── (n) MatchGoal (as assist_id)
Player (1) ── (n) MatchCard
Player (1) ── (n) MatchSubstitution (as player_out_id)
Player (1) ── (n) MatchSubstitution (as player_in_id)
Player (1) ── (n) MatchPenaltyShootout


================================================================================
10. SUMMARY OF NULLABILITY RULES
================================================================================

Element                                   Rule
----------------------------------------  ------------------------------------
Bilingual Text Fields (_en / _ar)         All are NULL allowed
IDs and Foreign Keys                      NOT NULL
Birth Year (Player)                       NOT NULL
Dates (start_date, match_date, etc.)      NOT NULL for mandatory events
Scores (home_score, away_score)           NULL until match is played
Penalty Scores                            NULL if no shootout
end_date (TeamCoach, PlayerTeam)          NULL if currently active
end_date (ClubStaff)                      NULL if currently active
Boolean Flags (is_starter, etc.)          NOT NULL (have default values)


DATA ENTRY PRIORITY:

1. Enter Arabic names first (since you are in Egypt)
2. Enter birth years (required for age eligibility)
3. Enter English names later as a bonus
4. The system will never show a blank field due to COALESCE fallback


================================================================================
11. QUICK REFERENCE: MANDATORY FIELDS BY TABLE
================================================================================

Table                    Required Fields (NOT NULL)
-----------------------  -----------------------------------------------
Club                     id
Season                   id, start_date, end_date, is_active
AgeGroup                 id, oldest_birth_year
Player                   id, birth_year
Coach                    id
Team                     id, club_id, age_group_id, season_id
TeamCoach                id, team_id, coach_id, start_date
PlayerTeam               id, player_id, team_id, start_date, status
Competition              id, season_id
Stage                    id, competition_id, stage_order, type
Group                    id, stage_id
Match                    id, stage_id, home_team_id, away_team_id,
                         match_date, status
MatchPlayer              id, match_id, team_id, player_id, is_starter,
                         minutes_played, goals, assists, yellow_cards,
                         red_cards
MatchGoal                id, match_id, team_id, scorer_id, minute,
                         is_extra_time, is_own_goal, is_penalty
MatchCard                id, match_id, team_id, player_id, card_type,
                         minute, is_extra_time
MatchSubstitution        id, match_id, team_id, player_out_id,
                         player_in_id, minute, is_extra_time
MatchPenaltyShootout     id, match_id, team_id, player_id, kick_order,
                         result, is_winning_kick
ClubStaff                id, club_id, coach_id


================================================================================
END OF DOCUMENTATION
================================================================================

Document prepared for Youthscores.org
Egyptian Youth Competition Management System