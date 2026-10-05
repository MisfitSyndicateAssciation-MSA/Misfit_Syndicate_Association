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
# FETCH ESPN DATA FOR A SPECIFIC COMPLETED WEEK
# =========================================================

def fetch_espn_week(week):

    week_url = (
        f"https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/"
        f"seasons/{SEASON}/segments/0/leagues/{LEAGUE_ID}"
        "?view=mBoxscore"
        "&view=mRoster"
        f"&scoringPeriodId={week}"
    )

    request = urllib.request.Request(
        week_url,
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
# HISTORICAL PLAYER SCORE
#
# statSourceId 0 = actual fantasy points.
# statSourceId 1 = projection, which is intentionally ignored.
# =========================================================

def get_actual_player_score_for_week(
    player,
    week
):

    actual_scores = []

    for stat in player.get(
        "stats",
        []
    ):

        if (
            stat.get("scoringPeriodId") == week
            and
            stat.get("statSourceId") == 0
        ):

            actual_scores.append(
                safe_score(
                    stat.get(
                        "appliedTotal",
                        0
                    )
                )
            )

    if not actual_scores:
        return 0.0

    return max(
        actual_scores
    )


# =========================================================
# BENCHWARMER OF THE WEEK
#
# ESPN lineupSlotId 20 = Bench.
# ESPN lineupSlotId 21 = IR, which is excluded.
# =========================================================

def build_benchwarmer_for_week(
    week_raw,
    week
):

    candidates = []

    for team in week_raw.get(
        "teams",
        []
    ):

        team_id = team.get(
            "id"
        )

        entries = (
            team.get(
                "roster",
                {}
            ).get(
                "entries",
                []
            )
        )

        for entry in entries:

            lineup_slot_id = (
                entry.get(
                    "lineupSlotId"
                )
            )

            if lineup_slot_id != 20:
                continue

            player = (
                entry.get(
                    "playerPoolEntry",
                    {}
                ).get(
                    "player",
                    {}
                )
            )

            player_id = (
                player.get(
                    "id"
                )
            )

            if player_id is None:
                player_id = (
                    entry.get(
                        "playerId"
                    )
                )

            points = (
                get_actual_player_score_for_week(
                    player,
                    week
                )
            )

            candidates.append({

                "teamId":
                    team_id,

                "teamName":
                    TEAM_NAMES.get(
                        team_id,
                        f"Team {team_id}"
                    ),

                "playerId":
                    player_id,

                "playerName":
                    player.get(
                        "fullName",
                        "Unknown Player"
                    ),

                "position":
                    PLAYER_POSITIONS.get(
                        player.get(
                            "defaultPositionId"
                        ),
                        "N/A"
                    ),

                "nflTeam":
                    NFL_TEAMS.get(
                        player.get(
                            "proTeamId",
                            0
                        ),
                        "FA"
                    ),

                "points":
                    points,

                "lineupSlotId":
                    lineup_slot_id,

                "lineupSlot":
                    "Bench",

            })

    if not candidates:
        return None

    return max(
        candidates,
        key=lambda item: (
            item["points"],
            item["playerName"],
        )
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
# ESPN exposes weekly points in pointsByScoringPeriod.
#
# totalPoints remains as a fallback.
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

        team_id = team.get(
            "id"
        )

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
                player.get(
                    "id"
                )
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
# BUILD COMPLETED-WEEK HISTORY
#
# IMPORTANT:
#
# If ESPN reports currentWeek = 4, this function only
# archives Weeks 1, 2 and 3.
#
# The active/current week is NEVER written into permanent
# history.
# =========================================================

def build_history(
    raw,
    current_week,
    weekly_raw=None
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


            if (
                away_score >
                home_score
            ):

                winner_team_id = (
                    away_team_id
                )

                loser_team_id = (
                    home_team_id
                )


            elif (
                home_score >
                away_score
            ):

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
        # MSA has 10 teams, therefore five matchups.
        #
        # If ESPN returns an incomplete completed week,
        # don't archive partial history.
        # -------------------------------------------------

        if (
            len(
                week_matchups
            )
            != 5
        ):

            print(
                f"HISTORY WARNING: "
                f"Week {week} returned "
                f"{len(week_matchups)} matchups. "
                f"Skipping permanent archive for that week."
            )

            continue


        # -------------------------------------------------
        # COLLECT ALL 10 TEAM SCORES
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


        # -------------------------------------------------
        # WEEKLY SUPERLATIVES
        # -------------------------------------------------

        highest = max(
            team_scores,
            key=lambda item:
                item["score"]
        )


        lowest = min(
            team_scores,
            key=lambda item:
                item["score"]
        )


        closest_game = min(
            week_matchups,
            key=lambda item:
                item["margin"]
        )


        biggest_blowout = max(
            week_matchups,
            key=lambda item:
                item["margin"]
        )


        # -------------------------------------------------
        # MSA WEEKLY AWARDS - PHASE 2
        # -------------------------------------------------

        # Reconstruct standings ENTERING this week using only
        # completed matchups from earlier weeks.
        entering_records = {
            team_id: {
                "teamId": team_id,
                "teamName": team_name,
                "wins": 0,
                "losses": 0,
                "ties": 0,
                "pointsFor": 0.0,
            }
            for team_id, team_name in TEAM_NAMES.items()
        }

        for prior_week_data in weeks:

            for prior_matchup in prior_week_data["matchups"]:

                away_id = prior_matchup["awayTeamId"]
                home_id = prior_matchup["homeTeamId"]

                entering_records[away_id]["pointsFor"] += (
                    prior_matchup["awayScore"]
                )

                entering_records[home_id]["pointsFor"] += (
                    prior_matchup["homeScore"]
                )

                winner_id = prior_matchup["winnerTeamId"]
                loser_id = prior_matchup["loserTeamId"]

                if winner_id is None:

                    entering_records[away_id]["ties"] += 1
                    entering_records[home_id]["ties"] += 1

                else:

                    entering_records[winner_id]["wins"] += 1
                    entering_records[loser_id]["losses"] += 1

        entering_standings = sorted(
            entering_records.values(),
            key=lambda team: (
                -team["wins"],
                team["losses"],
                -team["pointsFor"],
                team["teamId"],
            )
        )

        entering_rank = {
            team["teamId"]: rank
            for rank, team in enumerate(
                entering_standings,
                start=1
            )
        }

        # Week 1 has no prior standings, so Giant Killer
        # begins in Week 2.
        giant_killer = None

        if week > 1:

            upset_candidates = []

            for matchup in week_matchups:

                winner_id = matchup["winnerTeamId"]
                loser_id = matchup["loserTeamId"]

                if (
                    winner_id is None
                    or loser_id is None
                ):
                    continue

                winner_rank = entering_rank[winner_id]
                loser_rank = entering_rank[loser_id]

                # An upset only counts when the winner entered
                # the week ranked lower than the team it beat.
                rank_gap = winner_rank - loser_rank

                if rank_gap <= 0:
                    continue

                upset_candidates.append({
                    "teamId": winner_id,
                    "teamName": TEAM_NAMES.get(
                        winner_id,
                        f"Team {winner_id}"
                    ),
                    "opponentId": loser_id,
                    "opponentName": TEAM_NAMES.get(
                        loser_id,
                        f"Team {loser_id}"
                    ),
                    "enteringRank": winner_rank,
                    "opponentEnteringRank": loser_rank,
                    "rankGap": rank_gap,
                    "margin": matchup["margin"],
                })

            if upset_candidates:

                giant_killer = max(
                    upset_candidates,
                    key=lambda item: (
                        item["rankGap"],
                        item["margin"],
                    )
                )

        # Stock Rising measures the largest scoring improvement
        # against a team's recent completed-week average.
        stock_rising = None

        if week > 1:

            stock_candidates = []

            for team_score in team_scores:

                team_id = team_score["teamId"]
                recent_scores = []

                # Use up to the previous two completed weeks.
                for prior_week_data in weeks[-2:]:

                    for prior_matchup in prior_week_data["matchups"]:

                        if prior_matchup["awayTeamId"] == team_id:
                            recent_scores.append(
                                prior_matchup["awayScore"]
                            )
                            break

                        if prior_matchup["homeTeamId"] == team_id:
                            recent_scores.append(
                                prior_matchup["homeScore"]
                            )
                            break

                if not recent_scores:
                    continue

                previous_average = (
                    sum(recent_scores) /
                    len(recent_scores)
                )

                improvement = (
                    team_score["score"] -
                    previous_average
                )

                stock_candidates.append({
                    "teamId": team_id,
                    "teamName": team_score["teamName"],
                    "score": team_score["score"],
                    "previousAverage": round(
                        previous_average,
                        2
                    ),
                    "improvement": round(
                        improvement,
                        2
                    ),
                    "weeksCompared": len(recent_scores),
                })

            positive_stock = [
                item
                for item in stock_candidates
                if item["improvement"] > 0
            ]

            if positive_stock:

                stock_rising = max(
                    positive_stock,
                    key=lambda item: (
                        item["improvement"],
                        item["score"],
                    )
                )


        # -------------------------------------------------
        # MSA WEEKLY AWARDS - PHASE 1
        # -------------------------------------------------

        def team_name_for_id(matchup, team_id):
            if team_id == matchup["awayTeamId"]:
                return matchup["awayTeamName"]
            if team_id == matchup["homeTeamId"]:
                return matchup["homeTeamName"]
            return None

        execution_winner_id = biggest_blowout["winnerTeamId"]
        execution_loser_id = biggest_blowout["loserTeamId"]

        photo_finish_winner_id = closest_game["winnerTeamId"]
        photo_finish_loser_id = closest_game["loserTeamId"]

        awards = {
            "kingOfTheWeek": {
                "teamId": highest["teamId"],
                "teamName": highest["teamName"],
                "score": highest["score"],
            },

            "frozenMisfit": {
                "teamId": lowest["teamId"],
                "teamName": lowest["teamName"],
                "score": lowest["score"],
            },

            "theExecution": {
                "teamId": execution_winner_id,
                "teamName": team_name_for_id(
                    biggest_blowout,
                    execution_winner_id
                ),
                "opponentId": execution_loser_id,
                "opponentName": team_name_for_id(
                    biggest_blowout,
                    execution_loser_id
                ),
                "margin": biggest_blowout["margin"],
            },

            "photoFinish": {
                "winnerTeamId": photo_finish_winner_id,
                "winnerTeamName": team_name_for_id(
                    closest_game,
                    photo_finish_winner_id
                ),
                "loserTeamId": photo_finish_loser_id,
                "loserTeamName": team_name_for_id(
                    closest_game,
                    photo_finish_loser_id
                ),
                "margin": closest_game["margin"],
            },

            "shouldHaveStayedHome": {
                "teamId": execution_loser_id,
                "teamName": team_name_for_id(
                    biggest_blowout,
                    execution_loser_id
                ),
                "opponentId": execution_winner_id,
                "opponentName": team_name_for_id(
                    biggest_blowout,
                    execution_winner_id
                ),
                "margin": biggest_blowout["margin"],
            },

            "giantKiller":
                giant_killer,

            "stockRising":
                stock_rising,

            "benchwarmerOfTheWeek":
                (
                    build_benchwarmer_for_week(
                        weekly_raw.get(
                            week,
                            {}
                        ),
                        week
                    )
                    if weekly_raw
                    else None
                ),
        }


        # -------------------------------------------------
        # SAVE COMPLETED WEEK
        # -------------------------------------------------

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

                "awayTeamName":
                    closest_game[
                        "awayTeamName"
                    ],

                "homeTeamId":
                    closest_game[
                        "homeTeamId"
                    ],

                "homeTeamName":
                    closest_game[
                        "homeTeamName"
                    ],

                "awayScore":
                    closest_game[
                        "awayScore"
                    ],

                "homeScore":
                    closest_game[
                        "homeScore"
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

                "awayTeamName":
                    biggest_blowout[
                        "awayTeamName"
                    ],

                "homeTeamId":
                    biggest_blowout[
                        "homeTeamId"
                    ],

                "homeTeamName":
                    biggest_blowout[
                        "homeTeamName"
                    ],

                "awayScore":
                    biggest_blowout[
                        "awayScore"
                    ],

                "homeScore":
                    biggest_blowout[
                        "homeScore"
                    ],

                "margin":
                    biggest_blowout[
                        "margin"
                    ],

            },

            "awards":
                awards,

        })


    return {

        "leagueId":
            raw.get(
                "id"
            ),

        "season":
            raw.get(
                "seasonId"
            ),

        "completedThroughWeek":
            (
                max(
                    week_data["week"]
                    for week_data in weeks
                )
                if weeks
                else 0
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
                team.get(
                    "id"
                ),

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
                    team.get(
                        "id"
                    ),
                    "Unknown"
                ),

            "logo":
                team.get(
                    "logo"
                ),

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
                    2
                ),

            "pointsAgainst":
                round(
                    record.get(
                        "pointsAgainst",
                        0
                    ),
                    2
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
                    1
                ),

            "waiverRank":
                team.get(
                    "waiverRank"
                ),

        })


    teams.sort(
        key=lambda team: (
            -team[
                "wins"
            ],
            team[
                "losses"
            ],
            -team[
                "pointsFor"
            ],
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
        )
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
                    2
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
                    2
                ),

        })


    # -----------------------------------------------------
    # ROSTERS
    # -----------------------------------------------------

    rosters = (
        build_rosters(
            raw
        )
    )


    # -----------------------------------------------------
    # FINAL LIVE JSON
    # -----------------------------------------------------

    return {

        "leagueId":
            raw.get(
                "id"
            ),

        "season":
            raw.get(
                "seasonId"
            ),

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
            ) as file:

                existing = (
                    json.load(
                        file
                    )
                )

        except (
            json.JSONDecodeError,
            OSError
        ):

            existing = None


    new_compare = dict(
        data
    )


    if isinstance(
        existing,
        dict
    ):

        existing_compare = dict(
            existing
        )

    else:

        existing_compare = None


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
    ) as file:

        json.dump(
            data,
            file,
            indent=2,
            ensure_ascii=False
        )


    print(
        f"SUCCESS: Updated "
        f"{output_file}"
    )


    return True


# =========================================================
# MAIN
# =========================================================

def main():

    print(
        "Fetching MSA data from ESPN..."
    )


    raw = (
        fetch_espn()
    )

    current_week = raw.get(
        "scoringPeriodId",
        raw.get(
            "status",
            {}
        ).get(
            "currentMatchupPeriod",
            1
        )
    )

    weekly_raw = {}

    for completed_week in range(
        1,
        current_week
    ):

        print(
            f"Fetching historical roster data "
            f"for Week {completed_week}..."
        )

        weekly_raw[
            completed_week
        ] = fetch_espn_week(
            completed_week
        )



    clean = (
        build_clean_data(
            raw
        )
    )


    history = (
        build_history(
            raw,
            clean[
                "currentWeek"
            ],
            weekly_raw
        )
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
        f"Week: "
        f"{clean['currentWeek']}"
    )


    print(
        f"Teams: "
        f"{len(clean['standings'])}"
    )


    print(
        f"Current Matchups: "
        f"{len(clean['matchups'])}"
    )


    print(
        f"Rosters: "
        f"{len(clean['rosters'])}"
    )


    total_players = sum(
        len(
            roster
        )
        for roster
        in clean[
            "rosters"
        ].values()
    )


    print(
        f"Rostered Players: "
        f"{total_players}"
    )


    # -----------------------------------------------------
    # CURRENT LIVE SCORE DEBUG
    # -----------------------------------------------------

    print(
        "Current matchup scores:"
    )


    for matchup in clean[
        "matchups"
    ]:

        print(
            f"Team "
            f"{matchup['awayTeamId']}: "
            f"{matchup['awayScore']} "
            f"vs "
            f"Team "
            f"{matchup['homeTeamId']}: "
            f"{matchup['homeScore']}"
        )


    # -----------------------------------------------------
    # HISTORY DEBUG
    # -----------------------------------------------------

    print(
        "Completed weeks eligible for history:"
    )


    if history[
        "weeks"
    ]:

        for week_data in history[
            "weeks"
        ]:

            print(
                f"Week "
                f"{week_data['week']}: "
                f"{len(week_data['matchups'])} "
                f"final matchups archived"
            )


            print(
                f"  Highest: "
                f"{week_data['highestScore']['teamName']} "
                f"({week_data['highestScore']['score']})"
            )


            print(
                f"  Lowest: "
                f"{week_data['lowestScore']['teamName']} "
                f"({week_data['lowestScore']['score']})"
            )


            print(
                f"  Closest game margin: "
                f"{week_data['closestGame']['margin']}"
            )


            print(
                f"  Biggest blowout margin: "
                f"{week_data['biggestBlowout']['margin']}"
            )


    else:

        print(
            "No completed weeks archived."
        )


    print(
        f"History completed through Week "
        f"{history['completedThroughWeek']}"
    )


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    main()
