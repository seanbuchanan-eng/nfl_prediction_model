import os
import sqlite3
import json
import scraper
import elo_sim
import elo_model
import init_db
import upcoming_games
from datetime import datetime, date
from pytz import timezone
from flask import Flask, send_from_directory
from flask_cors import CORS

def setup():
    init_db.run()
    elo_sim.run()

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

@app.route('/ai-games/<season>/<week>', methods=['GET'])
def get_ai_pred(season, week):
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
def serve_past_games():
    # TODO handle end of season condition and playoffs
    global UPCOMING_GAMES
    global WEEK
    global SEASON
    global PRESEASON_ELO

    if PRESEASON_ELO:
        upcoming_games.add_season_to_db(cur, conn)
        upcoming_games.update_pre_season_elo(cur, conn)
        PRESEASON_ELO = False
        print("hit preseason loop")

    if UPCOMING_GAMES:
        # get date from last game in the week
        now = datetime.now(timezone('EST'))
        last_game_date = UPCOMING_GAMES[-2]['game_date'].split('-')
        last_game_date = date(int(last_game_date[0]), 
                              int(last_game_date[1]), 
                              int(last_game_date[2]))
    
    if WEEK == 0:
        WEEK += 1
        UPCOMING_GAMES = upcoming_games.update_week_games(cur,
                                                          WEEK,
                                                          SEASON,
                                                          local_path='test_page.html')

    elif now.date() > last_game_date:
        upcoming_games.move_prev_week_to_db(cur, conn, WEEK, SEASON, local_path='test_page.html')
        
        WEEK += 1
        UPCOMING_GAMES = upcoming_games.update_week_games(cur,
                                                          WEEK,
                                                          SEASON,
                                                          local_path='test_page.html')

    return json.dumps(UPCOMING_GAMES)

@app.route('/team/<name>', methods=['GET'])
def get_team(name):
    team = cur.execute("""SELECT * FROM Teams WHERE name = ?""", (name, )).fetchall()

    return json.dumps(team)

if __name__ == '__main__':
    setup()
    app.run(debug=True)
    conn.close()
