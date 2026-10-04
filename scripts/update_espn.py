import json
import os
import urllib.request
from datetime import datetime, timezone


LEAGUE_ID = "398889101"
SEASON = "2026"


ESPN_URL = (
    f"https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/"
    f"seasons/{SEASON}/segments/0/leagues/{LEAGUE_ID}"
    "?view=mTeam"
    "&view=mStandings"
    "&view=mMatchup"
    "&view=mBoxscore"
    "&view=mLiveScoring"
    "&view=mRoster"
)


# Commissioner-approved MSA owner names.
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


# ESPN lineup slot IDs.
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


# ESPN default position IDs.
PLAYER_POSITIONS = {
    1: "QB",
    2: "RB",
    3: "WR",
    4: "TE",
    5: "K",
    16: "D/ST",
}


# NFL pro team IDs used by ESPN.
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


def build_rosters(raw):

    rosters = {}


    for team in raw.get("teams", []):

        team_id = team.get("id")

        roster_entries = (
            team.get("roster", {})
            .get("entries", [])
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


            player_id = player.get("id")

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
                "playerId": player_id,
                "name": player_name,
                "position": position,
                "nflTeam": nfl_team,
                "lineupSlot": lineup_slot,
                "lineupSlotId": lineup_slot_id,
                "injuryStatus": injury_status,
            })


        rosters[str(team_id)] = players


    return rosters


def build_clean_data(raw):

    teams = []


    for team in raw.get("teams", []):

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
            "rank": position,
            **team,
        })


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
                round(
                    away.get(
                        "totalPoints",
                        0
                    ),
                    2,
                ),

            "homeScore":
                round(
                    home.get(
                        "totalPoints",
                        0
                    ),
                    2,
                ),

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


    rosters = build_rosters(raw)


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


def main():

    print(
        "Fetching MSA data from ESPN..."
    )


    raw = fetch_espn()


    clean = build_clean_data(
        raw
    )


    os.makedirs(
        "data",
        exist_ok=True
    )


    output_file = (
        "data/league.json"
    )


    with open(
        output_file,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            clean,
            f,
            indent=2,
            ensure_ascii=False
        )


    print(
        f"SUCCESS: Created {output_file}"
    )

    print(
        f"Week: {clean['currentWeek']}"
    )

    print(
        f"Teams: {len(clean['standings'])}"
    )

    print(
        f"Matchups: {len(clean['matchups'])}"
    )

    print(
        f"Rosters: {len(clean['rosters'])}"
    )


    total_players = sum(
        len(roster)
        for roster
        in clean["rosters"].values()
    )


    print(
        f"Rostered Players: {total_players}"
    )


if __name__ == "__main__":

    main()
