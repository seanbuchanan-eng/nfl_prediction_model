# go through previous seasons and calcuate the elo

import sqlite3
from elo_model import postgame_elo_shift, pre_season_elo, elo_team_adjustment

conn = sqlite3.connect('db.sqlite')
cur = conn.cursor()

seasons = cur.execute("SELECT season FROM Seasons").fetchall()
teams = cur.execute("SELECT * FROM Teams").fetchall()
weeks = cur.execute("SELECT week FROM Weeks").fetchall()

cur.execute("UPDATE Teams SET elo=1505")
conn.commit()

for idx, season in enumerate(seasons):
    season = season[0]

    for team in teams:
        elo = pre_season_elo(team[5])
        cur.execute("UPDATE Teams SET elo = ? WHERE id = ?",
                    ( elo, team[0] ))
    conn.commit()

    games = cur.execute("")

    season_len = cur.execute("SELECT length FROM Seasons WHERE season = ? ", ( season, )).fetchone()[0]
    weeks = list(range(1,season_len+1)) + ["WildCard", "Division", "ConfChamp", "SuperBowl"]

    for week in weeks:
        games = cur.execute("""SELECT Games.home_team_id, Games.away_team_id,
                            Games.home_points, Games.away_points, Games.playoffs 
                            FROM Games JOIN Weeks JOIN Seasons 
                            on Games.week_id = Weeks.id and Games.season_id = Seasons.id 
                            WHERE Weeks.week = ? and Seasons.season = ? """,
                            ( week, season) ).fetchall()
        conn.commit()
        
        for game in games:
            home_team_id = game[0]
            away_team_id = game[1]
            pregame_elo_shift = elo_team_adjustment(game[0], game[1], game[-1], cur)
            elo_shift = postgame_elo_shift(game, cur)

            home_team_elo = cur.execute("SELECT elo FROM Teams WHERE id = ?", (home_team_id,)).fetchone()[0]
            away_team_elo = cur.execute("SELECT elo FROM Teams WHERE id = ?", (away_team_id,)).fetchone()[0]
            home_pregame_elo = home_team_elo + pregame_elo_shift
            away_pregame_elo = away_team_elo - pregame_elo_shift            
            cur.execute("UPDATE Games SET home_pregame_elo = ? WHERE id = ?", 
                        (home_pregame_elo, home_team_id))
            cur.execute("UPDATE Games SET away_pregame_elo = ? WHERE id = ?", 
                        (away_pregame_elo, away_team_id))

            away_team_elo -= elo_shift
            home_team_elo += elo_shift
            cur.execute("UPDATE Teams SET elo = ? WHERE id = ?", (home_team_elo, home_team_id))
            cur.execute("UPDATE Teams SET elo = ? WHERE id = ?", (away_team_elo, away_team_id))

        conn.commit()
conn.close()