import json
import urllib.request


LEAGUE_ID = "398889101"
SEASON = "2026"


def fetch_espn():
    url = (
        f"https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/"
        f"seasons/{SEASON}/segments/0/leagues/{LEAGUE_ID}"
        "?view=mTeam"
        "&view=mStandings"
        "&view=mMatchup"
        "&view=mMatchupScore"
        "&view=mScoreboard"
        "&view=mSettings"
    )

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0"
        }
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def pretty(value):
    return json.dumps(
        value,
        indent=2,
        sort_keys=True,
        default=str
    )


def main():

    print("")
    print("=" * 70)
    print("MSA PLAYOFF DIAGNOSTIC")
    print("=" * 70)

    print("")
    print("Fetching ESPN playoff information...")

    raw = fetch_espn()

    print("SUCCESS: ESPN data received.")

    # ---------------------------------------------------------
    # TOP-LEVEL ESPN KEYS
    # ---------------------------------------------------------

    print("")
    print("=" * 70)
    print("TOP LEVEL ESPN KEYS")
    print("=" * 70)

    print(sorted(raw.keys()))

    # ---------------------------------------------------------
    # LEAGUE STATUS
    # ---------------------------------------------------------

    print("")
    print("=" * 70)
    print("LEAGUE STATUS")
    print("=" * 70)

    print(pretty(raw.get("status")))

    # ---------------------------------------------------------
    # LEAGUE SETTINGS
    # ---------------------------------------------------------

    print("")
    print("=" * 70)
    print("LEAGUE SETTINGS")
    print("=" * 70)

    settings = raw.get("settings", {})

    print(pretty(settings))

    # ---------------------------------------------------------
    # IMPORTANT SCHEDULE / PLAYOFF SETTINGS
    # ---------------------------------------------------------

    print("")
    print("=" * 70)
    print("SCHEDULE + PLAYOFF SETTINGS")
    print("=" * 70)

    schedule_settings = settings.get("scheduleSettings", {})

    print(pretty(schedule_settings))

    # ---------------------------------------------------------
    # TEAM PLAYOFF INFORMATION
    # ---------------------------------------------------------

    print("")
    print("=" * 70)
    print("TEAM PLAYOFF / SEED INFORMATION")
    print("=" * 70)

    teams = raw.get("teams", [])

    for team in teams:

        team_id = team.get("id")

        location = team.get("location", "")
        nickname = team.get("nickname", "")

        name = f"{location} {nickname}".strip()

        record = team.get("record", {}).get("overall", {})

        simulation = team.get(
            "currentSimulationResults",
            {}
        )

        print("")
        print("-" * 60)

        print(f"TEAM ID: {team_id}")
        print(f"ESPN NAME: {name}")

        print(
            "RECORD:",
            record.get("wins"),
            "-",
            record.get("losses"),
            "-",
            record.get("ties")
        )

        print(
            "PLAYOFF SEED:",
            team.get("playoffSeed")
        )

        print(
            "RANK CALCULATED FINAL:",
            team.get("rankCalculatedFinal")
        )

        print(
            "RANK FINAL:",
            team.get("rankFinal")
        )

        print(
            "SIMULATION RESULTS:"
        )

        print(pretty(simulation))

    # ---------------------------------------------------------
    # SCHEDULE / BRACKET INFORMATION
    # ---------------------------------------------------------

    print("")
    print("=" * 70)
    print("PLAYOFF TIER SUMMARY")
    print("=" * 70)

    schedule = raw.get("schedule", [])

    tier_counts = {}

    for matchup in schedule:

        tier = matchup.get("playoffTierType")

        key = str(tier)

        tier_counts[key] = tier_counts.get(key, 0) + 1

    print(pretty(tier_counts))

    # ---------------------------------------------------------
    # POSSIBLE POSTSEASON MATCHUPS
    # ---------------------------------------------------------

    print("")
    print("=" * 70)
    print("POSTSEASON / BRACKET MATCHUPS")
    print("=" * 70)

    postseason_found = False

    for matchup in schedule:

        matchup_period = matchup.get(
            "matchupPeriodId",
            0
        )

        playoff_tier = matchup.get(
            "playoffTierType"
        )

        # Show anything ESPN identifies as playoff-related,
        # plus later matchup periods that may contain bracket data.
        if (
            playoff_tier is not None
            or matchup_period >= 15
        ):

            postseason_found = True

            print("")
            print("-" * 60)

            diagnostic = {
                "id": matchup.get("id"),
                "matchupPeriodId": matchup_period,
                "playoffTierType": playoff_tier,
                "winner": matchup.get("winner"),
                "homeTeamId": matchup.get("home", {}).get(
                    "teamId"
                ),
                "awayTeamId": matchup.get("away", {}).get(
                    "teamId"
                ),
                "homeTotalPoints": matchup.get(
                    "home",
                    {}
                ).get("totalPoints"),
                "awayTotalPoints": matchup.get(
                    "away",
                    {}
                ).get("totalPoints"),
            }

            print(pretty(diagnostic))

    if not postseason_found:
        print("")
        print(
            "No postseason-specific schedule entries "
            "were returned yet."
        )

    print("")
    print("=" * 70)
    print("END PLAYOFF DIAGNOSTIC")
    print("=" * 70)
    print("")


if __name__ == "__main__":
    main()
