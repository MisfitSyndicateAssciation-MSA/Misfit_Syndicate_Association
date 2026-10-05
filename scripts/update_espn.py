import json
import os
import urllib.request
from datetime import datetime, timezone


LEAGUE_ID = "398889101"
SEASON = "2026"


# =========================================================
# ESPN API
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
# We preserve our official MSA names in history.json instead
# of depending on future ESPN name changes.
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
# =========================================================

PLAYER_POSITIONS = {
    1: "QB",
    2: "RB",
    3: "WR",
    4: "TE",
    5: "K",
    16: "D/ST",
}


# =========================================================
# ESPN NFL TEAM IDS
# =========================================================

NFL_TEAMS = {
    0: "FA",
    1: "ATL",
    2: "BUF",
    3: "CHI",
    4: "CIN",
    5: "CLE",
    6: "DAL",
    7: "DEN",
    8: "DET",
    9: "GB",
    10: "TEN",
    11: "IND",
    12: "KC",
    13: "LV",
    14: "LAR",
    15: "MIA",
    16: "MIN",
    17: "NE",
    18: "NO",
    19: "NYG",
    20: "NYJ",
    21: "PHI",
    22: "ARI",
    23: "PIT",
    24: "LAC",
    25: "SF",
    26: "SEA",
    27: "TB",
    28: "WAS",
    29: "CAR",
    30: "JAX",
    33: "BAL",
    34: "HOU",
}


# =========================================================
# FETCH ESPN
# =========================================================

def fetch_espn():

    request = urllib.request.Request(
        ESPN_URL,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
        },
    )

    with urllib.request.urlopen(
        request,
        timeout=30
    ) as response:

        return json.loads(
            response.read().decode("utf-8")
        )


# =========================================================
# SAFE SCORE
# =========================================================

def safe_score(value):

    try:

        return round(
            float(value),
            2
        )

    except (
        TypeError,
        ValueError
    ):

        return 0.0


# =========================================================
# SCORE FOR A SPECIFIC WEEK
#
# This is used by both the live scoreboard and the permanent
# history archive.
# =========================================================

def get_score_for_week(
    matchup_side,
    week
):

    points_by_period = (
        matchup_side.get(
            "pointsByScoringPeriod",
            {}
        )
    )

    week_key = str(week)


    if week_key in points_by_period:

        return safe_score(
            points_by_period[
                week_key
            ]
        )


    total_points = (
        matchup_side.get(
            "totalPoints"
        )
    )


    if total_points is not None:

        return safe_score(
            total_points
        )


    return 0.0


# =========================================================
# CURRENT SCORE HELPER
# =========================================================

def get_current_score(
    matchup_side,
    current_week
):

    return get_score_for_week(
        matchup_side,
        current_week
    )


# =========================================================
# BUILD ROSTERS
# =========================================================

def build_rosters(raw):

    rosters = {}


    for team in raw.get(
        "teams",
        []
    ):

        team_id = team.get("id")

        roster_entries = (
            team.get(
                "roster",
                {}
            ).get(
                "entries",
                []
            )
        )


        players = []


        for entry in roster_entries:

            player_pool_entry = (
                entry.get(
                    "playerPoolEntry",
                    {}
                )
            )


            player = (
                player_pool_entry.get(
                    "player",
                    {}
                )
            )


            player_id = (
                player.get("id")
            )


            player_name = (
                player.get(
                    "fullName",
                    "Unknown Player"
                )
            )


            default_position_id = (
                player.get(
                    "defaultPositionId"
                )
            )


            position = (
                PLAYER_POSITIONS.get(
                    default_position_id,
                    "N/A"
                )
            )


            pro_team_id = (
                player.get(
                    "proTeamId",
                    0
                )
            )


            nfl_team = (
                NFL_TEAMS.get(
                    pro_team_id,
                    "FA"
                )
            )


            lineup_slot_id = (
                entry.get(
                    "lineupSlotId"
                )
            )


            lineup_slot = (
                LINEUP_SLOTS.get(
                    lineup_slot_id,
                    "Bench"
                )
            )


            injury_status = (
                player.get(
                    "injuryStatus",
                    "ACTIVE"
                )
            )


            players.append({

                "playerId":
                    player_id,

                "name":
                    player_name,

                "position":
                    position,

                "nflTeam":
                    nfl_team,

                "lineupSlot":
                    lineup_slot,

                "lineupSlotId":
                    lineup_slot_id,

                "injuryStatus":
                    injury_status,

            })


        rosters[
            str(team_id)
        ] = players


    return rosters


# =========================================================
# BUILD COMPLETED WEEK HISTORY
#
# IMPORTANT:
#
# If ESPN says currentWeek = 4, only Weeks 1-3 are eligible
# for permanent history.
#
# Week 4 remains live and is NOT archived.
# =========================================================

def build_history(
    raw,
    current_week
):

    weeks = []


    for week in range(
        1,
        current_week
    ):

        week_matchups = []


        for matchup in raw.get(
            "schedule",
            []
        ):

            if (
                matchup.get(
                    "matchupPeriodId"
                )
                != week
            ):

                continue


            away = matchup.get(
                "away",
                {}
            )

            home = matchup.get(
                "home",
                {}
            )


            away_team_id = (
                away.get(
                    "teamId"
                )
            )

            home_team_id = (
                home.get(
                    "teamId"
                )
            )


            if (
                away_team_id is None
                or
                home_team_id is None
            ):

                continue


            away_score = (
                get_score_for_week(
                    away,
                    week
                )
            )


            home_score = (
                get_score_for_week(
                    home,
                    week
                )
            )


            if away_score > home_score:

                winner_team_id = (
                    away_team_id
                )

                loser_team_id = (
                    home_team_id
                )

            elif home_score > away_score:

                winner_team_id = (
                    home_team_id
                )

                loser_team_id = (
                    away_team_id
                )

            else:

                winner_team_id = None
                loser_team_id = None


            week_matchups.append({

                "awayTeamId":
                    away_team_id,

                "awayTeamName":
                    TEAM_NAMES.get(
                        away_team_id,
                        f"Team {away_team_id}"
                    ),

                "awayScore":
                    away_score,

                "homeTeamId":
                    home_team_id,

                "homeTeamName":
                    TEAM_NAMES.get(
                        home_team_id,
                        f"Team {home_team_id}"
                    ),

                "homeScore":
                    home_score,

                "winnerTeamId":
                    winner_team_id,

                "loserTeamId":
                    loser_team_id,

                "margin":
                    round(
                        abs(
                            away_score -
                            home_score
                        ),
                        2
                    ),

            })


        # -------------------------------------------------
        # We expect five matchups in the 10-team MSA.
        #
        # If ESPN does not give us a complete week, we do
        # not pretend that week is safely archived.
        # -------------------------------------------------

        if len(
            week_matchups
        ) != 5:

            print(
                f"HISTORY WARNING: "
                f"Week {week} returned "
                f"{len(week_matchups)} matchups. "
                f"Skipping permanent archive for that week."
            )

            continue


        # -------------------------------------------------
        # WEEK STATISTICS
        # -------------------------------------------------

        team_scores = []


        for matchup in week_matchups:

            team_scores.append({

                "teamId":
                    matchup[
                        "awayTeamId"
                    ],

                "teamName":
                    matchup[
                        "awayTeamName"
                    ],

                "score":
                    matchup[
                        "awayScore"
                    ],

            })


            team_scores.append({

                "teamId":
                    matchup[
                        "homeTeamId"
                    ],

                "teamName":
                    matchup[
                        "homeTeamName"
                    ],

                "score":
                    matchup[
                        "homeScore"
                    ],

            })


        highest =
            max(
                team_scores,
                key=lambda item:
                    item["score"]
            )


        lowest =
            min(
                team_scores,
                key=lambda item:
                    item["score"]
            )


        closest_game =
            min(
                week_matchups,
                key=lambda item:
                    item["margin"]
            )


        biggest_blowout =
            max(
                week_matchups,
                key=lambda item:
                    item["margin"]
            )


        weeks.append({

            "week":
                week,

            "matchups":
                week_matchups,

            "highestScore": {

                "teamId":
                    highest[
                        "teamId"
                    ],

                "teamName":
                    highest[
                        "teamName"
                    ],

                "score":
                    highest[
                        "score"
                    ],

            },

            "lowestScore": {

                "teamId":
                    lowest[
                        "teamId"
                    ],

                "teamName":
                    lowest[
                        "teamName"
                    ],

                "score":
                    lowest[
                        "score"
                    ],

            },

            "closestGame": {

                "awayTeamId":
                    closest_game[
                        "awayTeamId"
                    ],

                "homeTeamId":
                    closest_game[
                        "homeTeamId"
                    ],

                "margin":
                    closest_game[
                        "margin"
                    ],

            },

            "biggestBlowout": {

                "awayTeamId":
                    biggest_blowout[
                        "awayTeamId"
                    ],

                "homeTeamId":
                    biggest_blowout[
                        "homeTeamId"
                    ],

                "margin":
                    biggest_blowout[
                        "margin"
                    ],

            },

        })


    return {

        "leagueId":
            raw.get("id"),

        "season":
            raw.get("seasonId"),

        "completedThroughWeek":
            max(
                0,
                current_week - 1
            ),

        "weeks":
            weeks,

    }


# =========================================================
# BUILD CLEAN LIVE DATA
# =========================================================

def build_clean_data(raw):

    teams = []


    # -----------------------------------------------------
    # TEAMS / STANDINGS
    # -----------------------------------------------------

    for team in raw.get(
        "teams",
        []
    ):

        record = (
            team.get(
                "record",
                {}
            ).get(
                "overall",
                {}
            )
        )


        teams.append({

            "id":
                team.get("id"),

            "name":
                team.get(
                    "name",
                    ""
                ).strip(),

            "abbrev":
                team.get(
                    "abbrev",
                    ""
                ).strip(),

            "owner":
                OWNER_OVERRIDES.get(
                    team.get("id"),
                    "Unknown"
                ),

            "logo":
                team.get("logo"),

            "wins":
                record.get(
                    "wins",
                    0
                ),

            "losses":
                record.get(
                    "losses",
                    0
                ),

            "ties":
                record.get(
                    "ties",
                    0
                ),

            "pointsFor":
                round(
                    record.get(
                        "pointsFor",
                        team.get(
                            "points",
                            0
                        )
                    ),
                    2,
                ),

            "pointsAgainst":
                round(
                    record.get(
                        "pointsAgainst",
                        0
                    ),
                    2,
                ),

            "streakType":
                record.get(
                    "streakType",
                    "NONE"
                ),

            "streakLength":
                record.get(
                    "streakLength",
                    0
                ),

            "playoffPct":
                round(
                    team.get(
                        "currentSimulationResults",
                        {}
                    ).get(
                        "playoffPct",
                        0
                    ) * 100,
                    1,
                ),

            "waiverRank":
                team.get(
                    "waiverRank"
                ),

        })


    teams.sort(
        key=lambda t: (
            -t["wins"],
            t["losses"],
            -t["pointsFor"],
        )
    )


    standings = []


    for position, team in enumerate(
        teams,
        start=1
    ):

        standings.append({

            "rank":
                position,

            **team,

        })


    # -----------------------------------------------------
    # CURRENT WEEK
    # -----------------------------------------------------

    current_week = raw.get(
        "scoringPeriodId",
        raw.get(
            "status",
            {}
        ).get(
            "currentMatchupPeriod",
            1
        ),
    )


    # -----------------------------------------------------
    # CURRENT MATCHUPS
    # -----------------------------------------------------

    matchups = []


    for matchup in raw.get(
        "schedule",
        []
    ):

        if (
            matchup.get(
                "matchupPeriodId"
            )
            != current_week
        ):

            continue


        away = matchup.get(
            "away",
            {}
        )

        home = matchup.get(
            "home",
            {}
        )


        away_score = (
            get_current_score(
                away,
                current_week
            )
        )

        home_score = (
            get_current_score(
                home,
                current_week
            )
        )


        matchups.append({

            "week":
                current_week,

            "awayTeamId":
                away.get(
                    "teamId"
                ),

            "homeTeamId":
                home.get(
                    "teamId"
                ),

            "awayScore":
                away_score,

            "homeScore":
                home_score,

            "awayProjection":
                round(
                    away.get(
                        "totalProjectedPointsLive",
                        away.get(
                            "totalProjectedPoints",
                            0
                        )
                    ),
                    2,
                ),

            "homeProjection":
                round(
                    home.get(
                        "totalProjectedPointsLive",
                        home.get(
                            "totalProjectedPoints",
                            0
                        )
                    ),
                    2,
                ),

        })


    # -----------------------------------------------------
    # ROSTERS
    # -----------------------------------------------------

    rosters = (
        build_rosters(raw)
    )


    # -----------------------------------------------------
    # FINAL LIVE JSON
    # -----------------------------------------------------

    return {

        "leagueId":
            raw.get("id"),

        "season":
            raw.get("seasonId"),

        "currentWeek":
            current_week,

        "updatedAt":
            datetime.now(
                timezone.utc
            ).isoformat(),

        "standings":
            standings,

        "matchups":
            matchups,

        "rosters":
            rosters,

    }


# =========================================================
# WRITE JSON ONLY WHEN CONTENT CHANGES
# =========================================================

def write_json_if_changed(
    output_file,
    data,
    ignore_updated_at=False
):

    existing = None


    if os.path.exists(
        output_file
    ):

        try:

            with open(
                output_file,
                "r",
                encoding="utf-8"
            ) as f:

                existing = json.load(f)

        except (
            json.JSONDecodeError,
            OSError
        ):

            existing = None


    new_compare = dict(data)

    existing_compare = (
        dict(existing)
        if isinstance(
            existing,
            dict
        )
        else None
    )


    if ignore_updated_at:

        new_compare.pop(
            "updatedAt",
            None
        )

        if (
            existing_compare
            is not None
        ):

            existing_compare.pop(
                "updatedAt",
                None
            )


    changed = (
        existing_compare
        != new_compare
    )


    if not changed:

        print(
            f"NO CHANGES: "
            f"{output_file} is already current."
        )

        return False


    if ignore_updated_at:

        data["updatedAt"] = (
            datetime.now(
                timezone.utc
            ).isoformat()
        )


    with open(
        output_file,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            data,
            f,
            indent=2,
            ensure_ascii=False
        )


    print(
        f"SUCCESS: Updated {output_file}"
    )


    return True


# =========================================================
# MAIN
# =========================================================

def main():

    print(
        "Fetching MSA data from ESPN..."
    )


    raw = fetch_espn()


    clean = build_clean_data(
        raw
    )


    history = build_history(
        raw,
        clean[
            "currentWeek"
        ]
    )


    os.makedirs(
        "data",
        exist_ok=True
    )


    league_output_file = (
        "data/league.json"
    )


    history_output_file = (
        "data/history.json"
    )


    # -----------------------------------------------------
    # LIVE LEAGUE DATA
    # -----------------------------------------------------

    write_json_if_changed(
        league_output_file,
        clean,
        ignore_updated_at=True
    )


    # -----------------------------------------------------
    # PERMANENT COMPLETED-WEEK HISTORY
    # -----------------------------------------------------

    write_json_if_changed(
        history_output_file,
        history
    )


    # -----------------------------------------------------
    # DEBUG / VERIFICATION
    # -----------------------------------------------------

    print(
        f"Week: {clean['currentWeek']}"
    )


    print(
        f"Teams: {len(clean['standings'])}"
    )


    print(
        f"Current Matchups: {len(clean['matchups'])}"
    )


    print(
        f"Rosters: {len(clean['rosters'])}"
    )


    total_players = sum(
        len(roster)
        for roster
        in clean[
            "rosters"
        ].values()
    )


    print(
        f"Rostered Players: {total_players}"
    )


    print(
        "Current matchup scores:"
    )


    for matchup in clean[
        "matchups"
    ]:

        print(
            f"Team {matchup['awayTeamId']}: "
            f"{matchup['awayScore']} "
            f"vs "
            f"Team {matchup['homeTeamId']}: "
            f"{matchup['homeScore']}"
        )


    print(
        "Completed weeks eligible for history:"
    )


    if history["weeks"]:

        for week_data in history[
            "weeks"
        ]:

            print(
                f"Week {week_data['week']}: "
                f"{len(week_data['matchups'])} "
                f"final matchups archived"
            )

    else:

        print(
            "No completed weeks archived."
        )


    print(
        f"History completed through Week "
        f"{history['completedThroughWeek']}"
    )


if __name__ == "__main__":

    main()
