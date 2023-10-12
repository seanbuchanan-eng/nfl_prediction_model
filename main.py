"""
This program manages website startup and the API for requesting
data.
"""
import os
import sqlite3
import json
import elo_sim
import init_db
import process_train_test_data
import process_inference_data
import upcoming_games
from datetime import datetime, date
from pytz import timezone
from flask import Flask, send_from_directory
from flask_cors import CORS

def setup():
    """
    Run initialization scripts for the database so that
    it is up to date with most recent games.

    Required to be run before the app is started!
    """
    init_db.run()
    elo_sim.run()
    process_train_test_data.run()
    process_inference_data.run()


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
    """
    Handles website page changes.

    Parameters
    ----------
    path : str
        name of requested html page file name.

    Returns
    -------
    str
        a string of html from the requested html file.
        If the html file requested doesn't exist the 
        home page is returned by default.
    """
    if path.endswith("html") and os.path.exists(app.static_folder + '/html/' + path):
        return send_from_directory(app.static_folder, 'html/' + path)
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'html/home.html')

@app.route('/seasons', methods=['GET'])
def get_seasons():
    """
    Get season meta data.

    Returns
    -------
    json
        list of lists of [year, length] of seasons.
    """
    all_seasons = cur.execute("SELECT season, length FROM Seasons").fetchall()
    result = json.dumps(all_seasons)

    return result

@app.route('/games/<season>/<week>', methods=['GET'])
def get_week_games(season, week):
    """
    Get game data for a particular season and week.

    Parameters
    ----------
    season : str
        Season to get data from (e.g. "2022-2023")
    week : str
        Week of season to get data from (e.g. "1" or "SuperBowl)

    Returns
    -------
    json
        list of [game_id, season_id, week_id, home_team, away_team, home_points,
        away_points, home_yards, away_yards, home_turnovers, away_turnovers,
        home_pregame_elo, away_pregame_elo, playoff_bool, home_bye_bool, 
        away_bye_bool, neutral_destination]
    """
    games = cur.execute("""SELECT Games.*
                        FROM Games JOIN Weeks JOIN Seasons
                        on Games.week_id = Weeks.id and Games.season_id = Seasons.id
                        WHERE Weeks.week = ? and Seasons.season = ? """,
                        (week, season)).fetchall()
    result = json.dumps(games)
    return result

@app.route('/ai-games/<season>/<week>', methods=['GET'])
def get_ai_pred(season, week):
    """
    Get AI model prediction data.

    Parameters
    ----------
    season : str
        Season to get data from (e.g. "2022-2023")
    week : str
        Week of season to get data from (e.g. "1" or "SuperBowl)

    Returns
    -------
    json
        list of {"home_team": str, "away_team": str, "home_points": int, 
        "away_points": int, "elo_spread": float, "ai_spread": float}.
        "ai_spread" is with respect to the home team.
    """
    games = cur.execute("""SELECT Games.home_team, Games.away_team,
                        Games.home_points, Games.away_points, 
                        AiInput.elo_pred_spread, AiInput.ai_spread
                        FROM Games JOIN Weeks JOIN Seasons JOIN AiInput
                        on Games.week_id = Weeks.id 
                        and Games.season_id = Seasons.id 
                        and Games.id = AiInput.game_id
                        WHERE Weeks.week = ? and Seasons.season = ?""",
                        (week, season)).fetchall()
    result = []
    for game in games:
        game_dict = {}
        game_dict["home_team"] = game[0]
        game_dict["away_team"] = game[1]
        game_dict["home_points"] = game[2]
        game_dict["away_points"] = game[3]
        game_dict["elo_spread"] = game[4]
        game_dict["ai_spread"] = game[5]
        result.append(game_dict)
    return json.dumps(result)


@app.route('/get-upcoming-games', methods=['GET'])
def serve_upcoming_games():
    """
    Get game data for this weeks games.

    Scrapes https://www.pro-football-reference.com/ to get
    game data for upcoming games as well as results data
    for the most recently played week. If the data is 
    updated it updates the database with the new data 
    and calculates new spreads for the upcoming games.
    Understandably, this takes some time so a request
    to this method may take a few seconds if the data
    is updated.

    Returns
    -------
    json
        list of e.g. {"game_day_of_week": "Thu", "game_date": "2023-10-05", 
        "gametime": "8:15PM", "winner": "Chicago Bears",
        "game_location": "@", "loser": "Washington Commanders", 
        "boxscore_word": "preview", "pts_win": "0", "pts_lose": "0",
        "yards_win": "", "to_win": "", "yards_lose": "", "to_lose": "", 
        "week": 5, "home": "loser", "away": "winner",
        "home_team": "Washington Commanders", "away_team": "Chicago Bears", 
        "neutral_dest": "None", "playoffs": false,
        "home_pregame_elo": 1536.0, "away_pregame_elo": 1333.0, 
        "home_spread": -8.12, "away_spread": 8.12, "home_ai_spread":
        -12.816336631774902, "away_ai_spread": 12.816336631774902}

    """
    # TODO handle end of season condition and playoffs
    global UPCOMING_GAMES
    global WEEK
    global SEASON
    global PRESEASON_ELO

    if PRESEASON_ELO:
        upcoming_games.add_season_to_db(cur, conn)
        upcoming_games.update_pre_season_elo(cur, conn)
        PRESEASON_ELO = False      

    if WEEK == 0:
        WEEK += 1
        UPCOMING_GAMES = upcoming_games.update_week_games(cur,
                                                          WEEK,
                                                          SEASON, local_path='test_page.html')

    now = datetime.now(timezone('EST'))
    last_game_date = upcoming_games.calc_last_game_date(UPCOMING_GAMES)

    while now.date() > last_game_date:
        upcoming_games.move_prev_week_to_db(cur, conn, WEEK, SEASON, local_path='test_page.html')
        
        WEEK += 1
        UPCOMING_GAMES = upcoming_games.update_week_games(cur,
                                                          WEEK,
                                                          SEASON, local_path='test_page.html')
        last_game_date = upcoming_games.calc_last_game_date(UPCOMING_GAMES)

    return json.dumps(UPCOMING_GAMES)

@app.route('/team/<name>', methods=['GET'])
def get_team(name):
    team = cur.execute("""SELECT * FROM Teams WHERE name = ?""", (name, )).fetchall()

    return json.dumps(team)

if __name__ == '__main__':
    setup()
    app.run(debug=True)
    conn.close()