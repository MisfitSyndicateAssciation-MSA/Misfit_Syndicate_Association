import json
import os
import urllib.request
from datetime import datetime, timezone


LEAGUE_ID = "398889101"
SEASON = "2026"


# =========================================================
# ESPN API
#
# Includes the views used by the MSA website for:
# - standings
# - live/current matchup scores
# - projections
# - rosters
# - completed matchup history
# =========================================================

ESPN_URL = (
    f"https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/"
    f"seasons/{SEASON}/segments/0/leagues/{LEAGUE_ID}"
    "?view=mTeam"
    "&view=mStandings"
    "&view=mMatchup"
    "&view=mMatchupScore"
    "&view=mScoreboard"
    "&view=mBoxscore"
    "&view=mLiveScoring"
    "&view=mRoster"
)


# =========================================================
# OFFICIAL MSA OWNERS
#
# We use our official owner names instead of relying on
# ESPN's member/account names.
# =========================================================

OWNER_OVERRIDES = {
    1: "Steve Perez",
    3: "Mark Torres",
    4: "Colin Brazee",
    5: "Jeri Armijo",
    6: "Sai Kappagantula",
    8: "Adam Hadlock",
    9: "Dion Will",
    10: "AJ Jackson",
    11: "Juan Loredo",
    12: "Steven Fisher",
}


# =========================================================
# OFFICIAL MSA TEAM NAMES
#
# History uses these names so a future ESPN team-name
# change does not rewrite old MSA history.
# =========================================================

TEAM_NAMES = {
    1: "Big Papi Queso",
    3: "Team Ramrod",
    4: "Nabershood Cookout",
    5: "Pitts Creek",
    6: "Double Dookie Dawgs",
    8: "Big Pickens Energy",
    9: "Apukalypse Now, Skattebo Later",
    10: "Db.EAtERs",
    11: "Red Zone Redbirds",
    12: "Ladiboyz",
}


# =========================================================
# ESPN LINEUP SLOT IDS
# =========================================================

LINEUP_SLOTS = {
    0: "QB",
    2: "RB",
    4: "WR",
    6: "TE",
    16: "D/ST",
    17: "K",
    20: "Bench",
    21: "IR",
    23: "FLEX",
}


# =========================================================
# ESPN PLAYER POSITION IDS
