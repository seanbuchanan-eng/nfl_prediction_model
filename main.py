import os
import sqlite3
import json
import scraper
import elo_sim
import elo_model
from datetime import datetime, date
from pytz import timezone
from flask import Flask, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder='static')
CORS(app)
basedir = os.path.abspath(os.path.dirname(__file__))

# global week
WEEK = 0
SEASON = 2023
UPCOMING_GAMES = None
PRESEASON_ELO = True

# connect to db
conn = sqlite3.connect('db.sqlite', check_same_thread=False)
cur = conn.cursor()

# routes
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path.endswith("html") and os.path.exists(app.static_folder + '/html/' + path):
        return send_from_directory(app.static_folder, 'html/' + path)
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'html/home.html')

@app.route('/seasons', methods=['GET'])
def get_seasons():
    all_seasons = cur.execute("SELECT season, length FROM Seasons").fetchall()
    result = json.dumps(all_seasons)

    return result

@app.route('/games/<season>/<week>', methods=['GET'])
def get_week_games(season, week):
    games = cur.execute("""SELECT Games.*
                        FROM Games JOIN Weeks JOIN Seasons
                        on Games.week_id = Weeks.id and Games.season_id = Seasons.id
                        WHERE Weeks.week = ? and Seasons.season = ? """,
                        (week, season)).fetchall()
    result = json.dumps(games)
    return result

def set_pregame_spread(games):
    neutral_dest = 'None'
    for game in games:
        if game["game_location"] == '@' or game["game_location"] == 'N':
            home_team = game["loser"]
            away_team = game["winner"]
            game["home"] = "loser"
            game["away"] = "winner"
        elif game["game_location"] == '':
            home_team = game["winner"]
            away_team = game["loser"]
            game["home"] = "winner"
            game["away"] = "loser"

        home_elo = cur.execute("SELECT elo FROM Teams WHERE name = ?", (home_team,)).fetchone()[0]
        away_elo = cur.execute("SELECT elo FROM Teams WHERE name = ?", (away_team,)).fetchone()[0]

        # TODO account for playoffs and implement neutral dest
        pregame_elo_shift = elo_model.elo_team_adjustment(home_team, away_team, False, neutral_dest, cur)
        home_elo = home_elo + pregame_elo_shift
        away_elo = away_elo - pregame_elo_shift

        home_spread = (away_elo - home_elo)/25
        away_spread = home_spread * -1
        game["home_spread"] = home_spread
        game["away_spread"] = away_spread

@app.route('/get-upcoming-games', methods=['GET'])
def serve_past_games():
    global UPCOMING_GAMES
    global WEEK
    global SEASON
    global PRESEASON_ELO

    if PRESEASON_ELO:
        # calc pregame elo and store in db for every team
        teams = cur.execute("SELECT id, elo FROM Teams").fetchall()
        for team in teams:
            elo = elo_model.pre_season_elo(team[1])
            cur.execute("UPDATE Teams SET elo = ? WHERE id = ?", (elo,team[0]))
        conn.commit()
        PRESEASON_ELO = False

    if UPCOMING_GAMES:
        now = datetime.now(timezone('EST'))
        last_game_date = UPCOMING_GAMES[-2]['game_date'].split('-')
        last_game_date = date(int(last_game_date[0]), 
                              int(last_game_date[1]), 
                              int(last_game_date[2]))
    
    if WEEK == 0:
        #increment week
        WEEK += 1
        #scrape and store globably
        UPCOMING_GAMES = scraper.get_week_games(WEEK, SEASON, local_path='test_page.html')

        for game in UPCOMING_GAMES:
            if game["pts_win"] == '': game["pts_win"] = '0'
            if game["pts_lose"] == '': game["pts_lose"] = '0'
            game["week"] = WEEK

        set_pregame_spread(UPCOMING_GAMES)

    #elif datetime > last games datetime
    elif now.date() > last_game_date:
        #scrape previous week
        last_week_games = scraper.get_week_games(WEEK, SEASON, local_path='test_page.html')
        
        # TODO move stored week to previous games storage
            #put function here
        
        WEEK += 1
        UPCOMING_GAMES = scraper.get_week_games(WEEK, SEASON, local_path='test_page.html')

        for game in UPCOMING_GAMES:
            if game["pts_win"] == '': game["pts_win"] = '0'
            if game["pts_lose"] == '': game["pts_lose"] = '0'
            game["week"] = WEEK

        set_pregame_spread(UPCOMING_GAMES)

    return json.dumps(UPCOMING_GAMES)

    # TODO check for end of season somehow
        # do something about it
    

@app.route('/team/<name>', methods=['GET'])
def get_team(name):
    team = cur.execute("""SELECT * FROM Teams WHERE name = ?""", (name, )).fetchall()

    return json.dumps(team)

if __name__ == '__main__':
    app.run(debug=True)
    conn.close()
