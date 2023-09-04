import os
import sqlite3
import json
from flask import Flask, request, jsonify

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))

# connect to db
conn = sqlite3.connect('db.sqlite', check_same_thread=False)
cur = conn.cursor()

# For initializing the db from the CLI
# app.app_context().push()

# routes
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
