# go through previous seasons and calcuate the elo

import sqlite3
from elo_model import postgame_elo_shift, pre_season_elo, elo_team_adjustment

conn = sqlite3.connect('db.sqlite')
cur = conn.cursor()

cur.execute("UPDATE Teams SET elo=1505")
conn.commit()

seasons = cur.execute("SELECT season FROM Seasons").fetchall()
teams = cur.execute("SELECT * FROM Teams").fetchall()
weeks = cur.execute("SELECT week FROM Weeks").fetchall()

for idx, season in enumerate(seasons):
    season = season[0]

    for team in teams:
        elo = pre_season_elo(team[5])
        cur.execute("UPDATE Teams SET elo = ? WHERE id = ?",
                    ( elo, team[0] ))
    conn.commit()

    season_len = cur.execute("SELECT length FROM Seasons WHERE season = ? ", ( season, )).fetchone()[0]
    weeks = list(range(1,season_len+1)) + ["WildCard", "Division", "ConfChamp", "SuperBowl"]

    for week in weeks:
        games = cur.execute("""SELECT Games.home_team, Games.away_team,
                            Games.home_points, Games.away_points, Games.playoffs,
                            Games.neutral_destination, Games.id
                            FROM Games JOIN Weeks JOIN Seasons 
                            on Games.week_id = Weeks.id and Games.season_id = Seasons.id 
                            WHERE Weeks.week = ? and Seasons.season = ? """,
                            ( week, season) ).fetchall()
        
        for game in games:
            home_team = game[0]
            away_team = game[1]
            playoffs = game[4]
            neutral_dest = game[5]
            game_id = game[6]
            pregame_elo_shift = elo_team_adjustment(home_team, away_team, playoffs, neutral_dest, cur)
            elo_shift = postgame_elo_shift(game, cur)

            home_team_elo = cur.execute("SELECT elo FROM Teams WHERE name = ?", (home_team,)).fetchone()[0]
            away_team_elo = cur.execute("SELECT elo FROM Teams WHERE name = ?", (away_team,)).fetchone()[0]
            home_pregame_elo = home_team_elo + pregame_elo_shift
            away_pregame_elo = away_team_elo - pregame_elo_shift            
            cur.execute("UPDATE Games SET home_pregame_elo = ? WHERE id = ?", 
                        (home_pregame_elo, game_id))
            cur.execute("UPDATE Games SET away_pregame_elo = ? WHERE id = ?", 
                        (away_pregame_elo, game_id))

            away_team_elo -= elo_shift
            home_team_elo += elo_shift
            cur.execute("UPDATE Teams SET elo = ? WHERE name = ?", (home_team_elo, home_team))
            cur.execute("UPDATE Teams SET elo = ? WHERE name = ?", (away_team_elo, away_team))

        conn.commit()
conn.close()