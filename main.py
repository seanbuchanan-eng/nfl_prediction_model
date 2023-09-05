import os
import sqlite3
import json
from flask import Flask, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder='static')
CORS(app)
basedir = os.path.abspath(os.path.dirname(__file__))

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
        return send_from_directory(app.static_folder, '/html/home.html')

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

@app.route('/team/<name>', methods=['GET'])
def get_team(name):
    team = cur.execute("""SELECT * FROM Teams WHERE name = ?""", (name, )).fetchall()

    return json.dumps(team)

if __name__ == '__main__':
    app.run(debug=True)
    conn.close()
