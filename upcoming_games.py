import elo_model
import scraper

def add_season_to_db(cur, conn):
    last_season = cur.execute("SELECT * FROM Seasons").fetchall()[-1]
    year = last_season[1].split("-")
    next_year = year[1] + "-" + str(int(year[1])+1)
    length = 18
    cur.execute("""INSERT OR IGNORE INTO Seasons (season, length)
                VALUES (?, ?)""", (next_year, length))
    conn.commit()

def update_pre_season_elo(cur, conn):
    """
    Update the elo score for each team with their preseason elo.

    Parameters
    ----------
    cur: database cursor
    conn: database connection
    """
    teams = cur.execute("SELECT id, elo FROM Teams").fetchall()
    for team in teams:
        elo = elo_model.pre_season_elo(team[1])
        cur.execute("UPDATE Teams SET elo = ? WHERE id = ?", (elo,team[0]))
    conn.commit()

def assign_home_away(game):
    """
    Assign the home and away team to `game`.
    """
    if game["game_location"] == '@' or game["game_location"] == 'N':
        game["home"] = "loser"
        game["away"] = "winner"
    elif game["game_location"] == '':
        game["home"] = "winner"
        game["away"] = "loser"

def set_pregame_spread(games, cur):
    """
    Sets pregame spread for upcoming games.

    Parameters
    ----------
    games: 
    """
    neutral_dest = 'None'
    for game in games:
        assign_home_away(game)
        if game["home"] == "loser":
            home_team = game["loser"]
            away_team = game["winner"]
        else:
            home_team = game["winner"]
            away_team = game["loser"]

        home_elo = cur.execute("SELECT elo FROM Teams WHERE name = ?", (home_team,)).fetchone()[0]
        away_elo = cur.execute("SELECT elo FROM Teams WHERE name = ?", (away_team,)).fetchone()[0]

        # TODO account for playoffs and implement neutral dest
        pregame_elo_shift = elo_model.elo_team_adjustment(home_team, away_team, False, neutral_dest, cur)
        home_elo = home_elo + pregame_elo_shift
        away_elo = away_elo - pregame_elo_shift
        game["home_elo"] = home_elo
        game["away_elo"] = away_elo

        home_spread = (away_elo - home_elo)/25
        away_spread = home_spread * -1
        game["home_spread"] = home_spread
        game["away_spread"] = away_spread

def update_week_games(cur, week, season, local_path=None):
    """
    Scrapes internet for this weeks games and returns them.

    Parameters
    ----------
    week: current week of the season
    season: current season
    local_path: local path to an html file for debugging

    Returns
    -------
    dict: upcoming games and their parameters for the week.
    """
    #scrape for upcoming games
    upcoming_games = scraper.get_week_games(week, season, local_path)

    for game in upcoming_games:
        if game["pts_win"] == '': game["pts_win"] = '0'
        if game["pts_lose"] == '': game["pts_lose"] = '0'
        game["week"] = week

    set_pregame_spread(upcoming_games, cur)

    return upcoming_games

def move_prev_week_to_db(cur, conn, week, season, local_path=None):
    """
    Scrapes the internet to get the scores from the previous week
    and adds them to the past games table in the db. Also updates
    the elo scores of the teams who played that week.

    Parameters
    ----------
    cur: database cursor
    week: current week of the season
    season: current season
    local_path: local path to an html file for debugging

    Returns
    -------
    """
    season_name = str(season) + "-" + str(season+1)
    season_id = cur.execute("SELECT id FROM Seasons WHERE season = ?", (season_name,)).fetchone()[0]
    week_id = cur.execute("SELECT id FROM Weeks WHERE week = ?", (week,)).fetchone()[0]
    games = scraper.get_week_games(week, season, local_path)

    for game in games:
        #games table update
        assign_home_away(game)
        if game["home"] == "loser":
            home_team = game["loser"]
            away_team = game["winner"]
            home_points = game["pts_lose"]
            away_points = game["pts_win"]
            home_yards = game["yards_lose"]
            away_yards = game["yards_win"]
            home_turnovers = game["to_lose"]
            away_turnovers = game["to_win"]
        else:
            away_team = game["loser"]
            home_team = game["winner"]
            away_points = game["pts_lose"]
            home_points = game["pts_win"]
            away_yards = game["yards_lose"]
            home_yards = game["yards_win"]
            away_turnovers = game["to_lose"]
            home_turnovers = game["to_win"]

        home_elo = cur.execute("SELECT elo FROM Teams WHERE name = ?", (home_team,)).fetchone()[0]
        away_elo = cur.execute("SELECT elo FROM Teams WHERE name = ?", (away_team,)).fetchone()[0]            

        cur.execute("""INSERT OR IGNORE INTO Games
                    (season_id, week_id, home_team, away_team,
                    home_points, away_points, home_yards,
                    away_yards, home_turnovers, away_turnovers,
                    home_pregame_elo, away_pregame_elo, playoffs,
                    home_bye, away_bye, neutral_destination) 
                    VALUES ( ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (season_id, week_id, home_team, away_team, home_points,
                     away_points, home_yards, away_yards, home_turnovers,
                     away_turnovers, home_elo, away_elo, 0, 0, 0, 'None'))
        
        # team elo update
        elo_diff = int(home_elo) - int(away_elo)
        if home_team == "New York Jets":
            print(f"away_elo before: {away_elo}")
            print(f"home_elo before: {home_elo}")
        elo_shift = elo_model.postgame_elo_shift(
            (None, None, int(home_points), int(away_points)),
            cur,
            elo_diff
            )
        away_elo -= elo_shift
        home_elo += elo_shift
        if home_team == "New York Jets":
            print(f"elo_diff: {elo_diff}")
            print(f"elo_shift: {elo_shift}")
            print(f"away_elo: {away_elo}")
            print(f"home_elo: {home_elo}")
        cur.execute("UPDATE Teams SET elo = ? WHERE name = ?",
                    (home_elo, home_team))
        cur.execute("UPDATE Teams SET elo = ? WHERE name = ?",
                    (away_elo, away_team))
    conn.commit()
