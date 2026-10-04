import json
import os
import urllib.request
from datetime import datetime, timezone

LEAGUE_ID = "398889101"
SEASON = "2026"

ESPN_URL = (
    f"https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/"
    f"seasons/{SEASON}/segments/0/leagues/{LEAGUE_ID}"
    "?view=mTeam&view=mStandings&view=mMatchup"
)

# Names we want displayed on the MSA website.
# ESPN currently associates Pitts Creek with a different account name,
# so the commissioner-approved owner name is preserved here.
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


def fetch_espn():
    request = urllib.request.Request(
        ESPN_URL,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
        },
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def build_clean_data(raw):
    teams = []

    for team in raw.get("teams", []):
        record = team.get("record", {}).get("overall", {})

        teams.append({
            "id": team.get("id"),
            "name": team.get("name", "").strip(),
            "abbrev": team.get("abbrev", "").strip(),
            "owner": OWNER_OVERRIDES.get(team.get("id"), "Unknown"),
            "logo": team.get("logo"),
            "wins": record.get("wins", 0),
            "losses": record.get("losses", 0),
            "ties": record.get("ties", 0),
            "pointsFor": round(record.get("pointsFor", team.get("points", 0)), 2),
            "pointsAgainst": round(record.get("pointsAgainst", 0), 2),
            "streakType": record.get("streakType", "NONE"),
            "streakLength": record.get("streakLength", 0),
            "playoffPct": round(
                team.get("currentSimulationResults", {}).get("playoffPct", 0) * 100,
                1,
            ),
            "waiverRank": team.get("waiverRank"),
        })

    teams.sort(
        key=lambda t: (
            -t["wins"],
            t["losses"],
            -t["pointsFor"],
        )
    )

    standings = []

    for position, team in enumerate(teams, start=1):
        standings.append({
            "rank": position,
            **team,
        })

    current_week = raw.get(
        "scoringPeriodId",
        raw.get("status", {}).get("currentMatchupPeriod", 1),
    )

    matchups = []

    for matchup in raw.get("schedule", []):
        if matchup.get("matchupPeriodId") != current_week:
            continue

        away = matchup.get("away", {})
        home = matchup.get("home", {})

        matchups.append({
            "week": current_week,
            "awayTeamId": away.get("teamId"),
            "homeTeamId": home.get("teamId"),
            "awayScore": away.get("totalPoints", 0),
            "homeScore": home.get("totalPoints", 0),
            "awayProjection": round(
                away.get(
                    "totalProjectedPointsLive",
                    away.get("totalProjectedPoints", 0),
                ),
                2,
            ),
            "homeProjection": round(
                home.get(
                    "totalProjectedPointsLive",
                    home.get("totalProjectedPoints", 0),
                ),
                2,
            ),
        })

    return {
        "leagueId": raw.get("id"),
        "season": raw.get("seasonId"),
        "currentWeek": current_week,
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "standings": standings,
        "matchups": matchups,
    }


def main():
    print("Fetching MSA data from ESPN...")

    raw = fetch_espn()
    clean = build_clean_data(raw)

    os.makedirs("data", exist_ok=True)

    output_file = "data/league.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(clean, f, indent=2, ensure_ascii=False)

    print(f"SUCCESS: Created {output_file}")
    print(f"Week: {clean['currentWeek']}")
    print(f"Teams: {len(clean['standings'])}")
    print(f"Matchups: {len(clean['matchups'])}")


if __name__ == "__main__":
    main()
