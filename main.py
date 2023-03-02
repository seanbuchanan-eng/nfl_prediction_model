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

    # number is the assciated week number of the season
    # example 2022-1 or 2022-WildCard
    number = db.Column(db.String, primary_key=True)
    season_id = db.Column(db.String(9), db.ForeignKey('seasons.year'))
    year = db.relationship('Season', back_populates='weeks')
    games = db.relationship('Game', back_populates='week')

    def __init__(self, number) -> None:
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


# Schema
class TeamSchema(ma.Schema):
    class Meta:
        fields = ('id', 'name', 'latitude', 'longitude', 'elo')

# TODO: Add Schema for other models

# Initialize schema
team_schema = TeamSchema()
teams_schema = TeamSchema(many=True)

# For initializing the db from the CLI
app.app_context().push()
