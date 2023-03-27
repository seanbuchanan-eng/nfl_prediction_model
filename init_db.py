import os
from main import db
from main import Team, Season, Week, Game

teams = {
    "Kansas City Chiefs": [39.099789, -94.578560, "KC"],
    "Houston Texans": [29.760427, -95.369804, "HOU"],
    "Seattle Seahawks": [47.603230, -122.330276, "SEA"],
    "Atlanta Falcons": [33.748997, -84.387985, "ATL"],
    "Buffalo Bills": [42.887691, -78.879372, "BUF"],
    "New York Jets": [40.814947462026176, -74.07665577312015, "NYJ"],
    "Las Vegas Raiders": [36.13138384905654, -115.13169451756163, "LV"],
    "Carolina Panthers": [35.25251233973856, -80.84120226587098, "CAR"],
    "Chicago Bears": [41.84754487986402, -87.67153913855199, "CHI"],
    "Detroit Lions": [42.36480313066512, -83.08960351424362, "DET"],
    "Baltimore Ravens": [39.308003294731584, -76.6205088127477, "BAL"],
    "Cleveland Browns": [41.46606790678101, -81.67222601665915, "CLE"],
    "Jacksonville Jaguars": [30.373130908558224, -81.68590701566833, "JAC"],
    "Indianapolis Colts": [39.82165042217416, -86.14927731202125, "IND"],
    "Green Bay Packers": [44.52030015455375, -88.02808200465094, "GB"],
    "Minnesota Vikings": [44.95461717252483, -93.16928759979443, "MIN"],
    "New England Patriots": [42.09250215474584, -71.2639840458412, "NE"],
    "Miami Dolphins": [25.958159412628838, -80.23881748795804, "MIA"],
    "Washington Commanders": [38.907843649151665, -76.86454540290117, "WAS"],
    "Philadelphia Eagles": [39.90153409172584, -75.1675215028637, "PHI"],
    "Los Angeles Chargers": [33.95369646674758, -118.33909324725614, "LAC"],
    "Cincinnati Bengals": [39.095483938138024, -84.51594106292978, "CIN"],
    "Arizona Cardinals": [33.52738095014831, -112.26238094759978, "ARI"],
    "San Francisco 49ers": [37.4032482976688, -121.96987092942953, "SF"],
    "New Orleans Saints": [29.95130267822774, -90.08121201668786, "NO"],
    "Tampa Bay Buccaneers": [27.976153335923133, -82.50335586092449, "TB"],
    "Los Angeles Rams": [33.95369646674758, -118.33909324725614, "LAR"],
    "Dallas Cowboys": [32.7480062696302, -97.09303478136525, "DAL"],
    "Pittsburgh Steelers": [40.4470587094102, -80.01595342189762, "PIT"],
    "New York Giants": [40.814947462026176, -74.07665577312015, "NYG"],
    "Tennessee Titans": [36.16623854753519, -86.77101512830522, "TEN"],
    "Denver Broncos": [39.74381523382964, -105.02021669123351, "DEN"],
    "St. Louis Rams": [38.627003, -90.199402, "STL"],
    "San Diego Chargers": [32.71533, -117.15726, "SD"],
    "Oakland Raiders": [37.804363, -122.271111, "OAK"]
}

superbowl_locations = {
    '2011': 'DAL',
    '2012': 'IND',
    '2013': 'NO',
    '2014': 'NYG',
    '2015': 'ARI',
    '2016': 'SF',
    '2017': 'HOU',
    '2018': 'MIN',
    '2019': 'ATL',
    '2020': 'MIA',
    '2021': 'TB',
    '2022': 'LAR',
    '2023': 'ARI' ,
    '2024': 'LV',
    '2025': 'NO'
}

db.create_all()

# make teams
for name, values in teams.items():
    # TODO account for teams that moved
    db.session.add(
        Team(values[2], name, values[0], values[1], 1505, False)
    )

def build_game(cols, playoff=False):
    day = cols[1]
    date = cols[2]
    winner = cols[4]
    symbol = cols[5]
    loser = cols[6]
    winner_points = cols[8]
    loser_points = cols[9]
    winner_yards = cols[10]
    winner_turnovers = cols[11]
    loser_yards = cols[12]
    loser_turnovers = cols[13]
    neutral_game = False

    if 'Washington' in winner:
        winner = 'Washington Commanders'
    elif 'Washington' in loser:
        loser = 'Washington Commanders'

    if symbol == '':
        home_team_id = teams[winner][2]
        away_team_id = teams[loser][2]
        home_team_points = winner_points
        away_team_points = loser_points
    elif symbol == '@':
        home_team_id = teams[loser][2]
        away_team_id = teams[winner][2]
        home_team_points = loser_points
        away_team_points = winner_points
    elif symbol == 'N':
        # assign winner to hometeam and loser to awayteam
        home_team_id = teams[winner][2]
        away_team_id = teams[loser][2]
        home_team_points = winner_points
        away_team_points = loser_points
        neutral_game = True

    game = Game(home_team_id, away_team_id, day, date)
    game.home_points = home_team_points
    game.away_points = away_team_points

    if neutral_game:
        game.neutral_destination_id = superbowl_locations[date.split('-')[0]]
    if playoff:
        game.playoff = True
    return game

# store season data
cwd = os.getcwd()
for file in os.listdir(cwd+'/data'):

    with open(cwd+'/data/'+file, 'r') as f:
        start_year = file.split('_')[1].split('.')[0]
        last_digits = str(int(start_year[-2:])+1)
        season_id = start_year + '-20' + last_digits
        season = Season(season_id)
        current_week = '0'
        playoff_bool = False
        weeks = []
        for line in f:
            cols = line.split(',')

            if cols[0] == 'Week':
                continue
            if cols[2] == 'Playoffs':
                playoff_bool = True
                continue

            date = cols[2]

            if cols[0] != current_week:
                current_week = cols[0]

                # make a new week
                if weeks:
                    weeks[-1].games = games
                weeks.append(Week(season_id + '-' + cols[0], current_week))
                games = []
                
            games.append(build_game(cols, playoff=playoff_bool))
            
            # add last games to the last week
            if current_week == 'SuperBowl':
                weeks[-1].games = games
                season.weeks = weeks
                db.session.add(season)

db.session.commit()