from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
import os

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'db.sqlite')


app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
ma = Marshmallow(app)

# Models
class Team(db.Model):
    __tablename__ = 'teams'

    # id is the teams can't remember the word for it
    id = db.Column(db.String(3), primary_key=True)
    name = db.Column(db.String)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    elo = db.Column(db.Integer)
    bye = db.Column(db.Boolean)
    previous_id = db.Column(db.String(4), db.ForeignKey('teams.id'))
    # previous_elo = db.relationship('Team', back_populates='elo')
    move_year = db.Column(db.Integer)

    def __init__(self, id, name, latitude, longitude, elo, bye, move_year=0, previous_id='None') -> None:
        self.id = id
        self.name = name
        self.latitude = latitude
        self.longitude = longitude
        self.elo = elo
        self.bye = bye
        self.move_year = move_year
        self.previous_id = previous_id

class Season(db.Model):
    __tablename__ = 'seasons'
    # year is of the format yyyy-yyyy
    year = db.Column(db.String(9), primary_key=True)
    weeks = db.relationship('Week', back_populates='year')

    def __init__(self, year) -> None:
        self.year = year

class Week(db.Model):
    __tablename__ = 'weeks'

    # id is the assciated week number of the season
    # example yyyy-mm-dd-1 or yyyy-mm-dd-WildCard
    id = db.Column(db.String, primary_key=True)
    number = db.Column(db.String)
    season_id = db.Column(db.String(9), db.ForeignKey('seasons.year'))
    year = db.relationship('Season', back_populates='weeks')
    games = db.relationship('Game', back_populates='week')

    def __init__(self, id, number) -> None:
        self.id = id
        self.number = number

class Game(db.Model):
    __tablename__ = 'games'

    # id example hometeam_vs_awayteam_yyyy-mm-dd
    id = db.Column(db.String(21), primary_key=True)
    playoff = db.Column(db.Boolean)
    home_points = db.Column(db.Integer)
    away_points = db.Column(db.Integer)
    home_team_id = db.Column(db.String(3))
    away_team_id = db.Column(db.String(3))
    home_pregame_elo = db.Column(db.Integer)
    away_pregame_elo = db.Column(db.Integer)
    day = db.Column(db.String)
    date = db.Column(db.String)
    neutral_destination_id = db.Column(db.String(4))
    week_id = db.Column(db.Integer, db.ForeignKey('weeks.number'))
    week = db.relationship('Week', back_populates='games')

    def __init__(self, home_team_id, away_team_id, day, date, neutral_destination_id='None', playoff=False) -> None:
        self.id = home_team_id + '_vs_' + away_team_id + '_' + date
        self.home_team_id = home_team_id
        self.away_team_id = away_team_id
        self.neutral_destination_id = neutral_destination_id
        self.playoff = playoff
        self.day = day
        self.date = date
        self.home_pregame_elo = 0
        self.away_pregame_elo = 0


# Schema
class TeamSchema(ma.Schema):
    class Meta:
        fields = ('id', 'name', 'elo')

class GameSchema(ma.Schema):
    class Meta:
        fields = ('id','home_points','away_points')

class SeasonSchema(ma.Schema):
    class Meta:
        fields= ('year',)

class WeekSchema(ma.Schema):
    class Meta:
        fields= ('id', 'number', 'year')

# Initialize schema
team_schema = TeamSchema()
teams_schema = TeamSchema(many=True)
game_schema = GameSchema()
games_schema = GameSchema(many=True)
season_schema = SeasonSchema()
seasons_schema = SeasonSchema(many=True)
week_schema = WeekSchema()
weeks_schema = WeekSchema(many=True)

# For initializing the db from the CLI
app.app_context().push()

# routes
@app.route('/seasons', methods=['GET'])
def get_seasons():
    all_seasons = db.session.query(Season).all()
    result = seasons_schema.dump(all_seasons)

    return seasons_schema.jsonify(result)

@app.route('/weeks/<season_id>', methods=['GET'])
def get_weeks(season_id):
    all_season_weeks = db.session.query(Week, season_id).all()
    result = seasons_schema.dump(all_season_weeks)

    return seasons_schema.jsonify(result)

@app.route('/team/<id>', methods=['GET'])
def get_team(id):
    team = db.session.get(Team, id)

    return team_schema.jsonify(team)

@app.route('/game/<id>', methods=['GET'])
def get_game(id):
    game = db.session.get(Game, id)

    return game_schema.jsonify(game)

if __name__ == '__main__':
    app.run(debug=True)
