import os
import pandas as pd
import sqlite3
import models
import torch

def run():
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
    }

    conn = sqlite3.connect('db.sqlite')
    cur = conn.cursor()

    cur.executescript("""
    DROP TABLE IF EXISTS InferenceData;
                    
    CREATE TABLE InferenceData (
        id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
        game_id INTEGER,
        home_pregame_elo INTEGER,                  
        home_elo_for_1 INTEGER,
        home_elo_for_2 INTEGER,
        home_elo_for_3 INTEGER,
        home_elo_for_4 INTEGER,
        home_elo_for_5 INTEGER,
        home_elo_for_6 INTEGER,
        home_elo_for_7 INTEGER,
        home_elo_for_8 INTEGER,
        home_elo_for_9 INTEGER,
        home_elo_for_10 INTEGER,
        home_elo_for_11 INTEGER,
        home_elo_for_12 INTEGER,
        home_elo_for_13 INTEGER,
        home_elo_for_14 INTEGER,
        home_elo_against_1 INTEGER,
        home_elo_against_2 INTEGER,
        home_elo_against_3 INTEGER,
        home_elo_against_4 INTEGER,
        home_elo_against_5 INTEGER,
        home_elo_against_6 INTEGER,
        home_elo_against_7 INTEGER,
        home_elo_against_8 INTEGER,
        home_elo_against_9 INTEGER,
        home_elo_against_10 INTEGER,
        home_elo_against_11 INTEGER,
        home_elo_against_12 INTEGER,
        home_elo_against_13 INTEGER,
        home_elo_against_14 INTEGER,
        home_points_for_1 INTEGER,
        home_points_for_2 INTEGER,
        home_points_for_3 INTEGER,
        home_points_for_4 INTEGER,
        home_points_for_5 INTEGER,
        home_points_for_6 INTEGER,
        home_points_for_7 INTEGER,
        home_points_for_8 INTEGER,
        home_points_for_9 INTEGER,
        home_points_for_10 INTEGER,
        home_points_for_11 INTEGER,
        home_points_for_12 INTEGER,
        home_points_for_13 INTEGER,
        home_points_for_14 INTEGER,
        home_points_against_1 INTEGER,
        home_points_against_2 INTEGER,
        home_points_against_3 INTEGER,
        home_points_against_4 INTEGER,
        home_points_against_5 INTEGER,
        home_points_against_6 INTEGER,
        home_points_against_7 INTEGER,
        home_points_against_8 INTEGER,
        home_points_against_9 INTEGER,
        home_points_against_10 INTEGER,
        home_points_against_11 INTEGER,
        home_points_against_12 INTEGER,
        home_points_against_13 INTEGER,
        home_points_against_14 INTEGER,
        home_yards_for_1 INTEGER,
        home_yards_for_2 INTEGER,
        home_yards_for_3 INTEGER,
        home_yards_for_4 INTEGER,
        home_yards_for_5 INTEGER,
        home_yards_for_6 INTEGER,
        home_yards_for_7 INTEGER,
        home_yards_for_8 INTEGER,
        home_yards_for_9 INTEGER,
        home_yards_for_10 INTEGER,
        home_yards_for_11 INTEGER,
        home_yards_for_12 INTEGER,
        home_yards_for_13 INTEGER,
        home_yards_for_14 INTEGER,
        home_yards_against_1 INTEGER,
        home_yards_against_2 INTEGER,
        home_yards_against_3 INTEGER,
        home_yards_against_4 INTEGER,
        home_yards_against_5 INTEGER,
        home_yards_against_6 INTEGER,
        home_yards_against_7 INTEGER,
        home_yards_against_8 INTEGER,
        home_yards_against_9 INTEGER,
        home_yards_against_10 INTEGER,
        home_yards_against_11 INTEGER,
        home_yards_against_12 INTEGER,
        home_yards_against_13 INTEGER,
        home_yards_against_14 INTEGER,
        home_turnovers_for_1 INTEGER,
        home_turnovers_for_2 INTEGER,
        home_turnovers_for_3 INTEGER,
        home_turnovers_for_4 INTEGER,
        home_turnovers_for_5 INTEGER,
        home_turnovers_for_6 INTEGER,
        home_turnovers_for_7 INTEGER,
        home_turnovers_for_8 INTEGER,
        home_turnovers_for_9 INTEGER,
        home_turnovers_for_10 INTEGER,
        home_turnovers_for_11 INTEGER,
        home_turnovers_for_12 INTEGER,
        home_turnovers_for_13 INTEGER,
        home_turnovers_for_14 INTEGER,
        home_turnovers_against_1 INTEGER,
        home_turnovers_against_2 INTEGER,
        home_turnovers_against_3 INTEGER,
        home_turnovers_against_4 INTEGER,
        home_turnovers_against_5 INTEGER,
        home_turnovers_against_6 INTEGER,
        home_turnovers_against_7 INTEGER,
        home_turnovers_against_8 INTEGER,
        home_turnovers_against_9 INTEGER,
        home_turnovers_against_10 INTEGER,
        home_turnovers_against_11 INTEGER,
        home_turnovers_against_12 INTEGER,
        home_turnovers_against_13 INTEGER,
        home_turnovers_against_14 INTEGER,
        away_pregame_elo INTEGER,                  
        away_elo_for_1 INTEGER,
        away_elo_for_2 INTEGER,
        away_elo_for_3 INTEGER,
        away_elo_for_4 INTEGER,
        away_elo_for_5 INTEGER,
        away_elo_for_6 INTEGER,
        away_elo_for_7 INTEGER,
        away_elo_for_8 INTEGER,
        away_elo_for_9 INTEGER,
        away_elo_for_10 INTEGER,
        away_elo_for_11 INTEGER,
        away_elo_for_12 INTEGER,
        away_elo_for_13 INTEGER,
        away_elo_for_14 INTEGER,
        away_elo_against_1 INTEGER,
        away_elo_against_2 INTEGER,
        away_elo_against_3 INTEGER,
        away_elo_against_4 INTEGER,
        away_elo_against_5 INTEGER,
        away_elo_against_6 INTEGER,
        away_elo_against_7 INTEGER,
        away_elo_against_8 INTEGER,
        away_elo_against_9 INTEGER,
        away_elo_against_10 INTEGER,
        away_elo_against_11 INTEGER,
        away_elo_against_12 INTEGER,
        away_elo_against_13 INTEGER,
        away_elo_against_14 INTEGER,
        away_points_for_1 INTEGER,
        away_points_for_2 INTEGER,
        away_points_for_3 INTEGER,
        away_points_for_4 INTEGER,
        away_points_for_5 INTEGER,
        away_points_for_6 INTEGER,
        away_points_for_7 INTEGER,
        away_points_for_8 INTEGER,
        away_points_for_9 INTEGER,
        away_points_for_10 INTEGER,
        away_points_for_11 INTEGER,
        away_points_for_12 INTEGER,
        away_points_for_13 INTEGER,
        away_points_for_14 INTEGER,
        away_points_against_1 INTEGER,
        away_points_against_2 INTEGER,
        away_points_against_3 INTEGER,
        away_points_against_4 INTEGER,
        away_points_against_5 INTEGER,
        away_points_against_6 INTEGER,
        away_points_against_7 INTEGER,
        away_points_against_8 INTEGER,
        away_points_against_9 INTEGER,
        away_points_against_10 INTEGER,
        away_points_against_11 INTEGER,
        away_points_against_12 INTEGER,
        away_points_against_13 INTEGER,
        away_points_against_14 INTEGER,
        away_yards_for_1 INTEGER,
        away_yards_for_2 INTEGER,
        away_yards_for_3 INTEGER,
        away_yards_for_4 INTEGER,
        away_yards_for_5 INTEGER,
        away_yards_for_6 INTEGER,
        away_yards_for_7 INTEGER,
        away_yards_for_8 INTEGER,
        away_yards_for_9 INTEGER,
        away_yards_for_10 INTEGER,
        away_yards_for_11 INTEGER,
        away_yards_for_12 INTEGER,
        away_yards_for_13 INTEGER,
        away_yards_for_14 INTEGER,
        away_yards_against_1 INTEGER,
        away_yards_against_2 INTEGER,
        away_yards_against_3 INTEGER,
        away_yards_against_4 INTEGER,
        away_yards_against_5 INTEGER,
        away_yards_against_6 INTEGER,
        away_yards_against_7 INTEGER,
        away_yards_against_8 INTEGER,
        away_yards_against_9 INTEGER,
        away_yards_against_10 INTEGER,
        away_yards_against_11 INTEGER,
        away_yards_against_12 INTEGER,
        away_yards_against_13 INTEGER,
        away_yards_against_14 INTEGER,
        away_turnovers_for_1 INTEGER,
        away_turnovers_for_2 INTEGER,
        away_turnovers_for_3 INTEGER,
        away_turnovers_for_4 INTEGER,
        away_turnovers_for_5 INTEGER,
        away_turnovers_for_6 INTEGER,
        away_turnovers_for_7 INTEGER,
        away_turnovers_for_8 INTEGER,
        away_turnovers_for_9 INTEGER,
        away_turnovers_for_10 INTEGER,
        away_turnovers_for_11 INTEGER,
        away_turnovers_for_12 INTEGER,
        away_turnovers_for_13 INTEGER,
        away_turnovers_for_14 INTEGER,
        away_turnovers_against_1 INTEGER,
        away_turnovers_against_2 INTEGER,
        away_turnovers_against_3 INTEGER,
        away_turnovers_against_4 INTEGER,
        away_turnovers_against_5 INTEGER,
        away_turnovers_against_6 INTEGER,
        away_turnovers_against_7 INTEGER,
        away_turnovers_against_8 INTEGER,
        away_turnovers_against_9 INTEGER,
        away_turnovers_against_10 INTEGER,
        away_turnovers_against_11 INTEGER,
        away_turnovers_against_12 INTEGER,
        away_turnovers_against_13 INTEGER,
        away_turnovers_against_14 INTEGER,
        week_number INTEGER                  
    );                  
    """)

    conn.commit()

    def build_insert_string(table_name, num_items):
        insert_string = f"INSERT INTO {table_name} VALUES ("
        for idx in range(0, num_items-1):
            insert_string += " ?,"
        insert_string += " ?);"

        return insert_string

    insert_command = build_insert_string("InferenceData", 229)

    last_14_games = {}
    for team in teams.keys():
        home_team, away_team = False, False
        last_14_games[team] = {
            "elo_for": [],
            "elo_against": [],
            "points_for": [],
            "points_against": [],
            "yards_for": [],
            "yards_against": [],
            "turnovers_for": [],
            "turnovers_against": [],
        }

        # get year1 data for team
        first_year_data = cur.execute("""
                    SELECT Games.home_team, Games.away_team, Games.home_points, Games.away_points, Games.home_yards,
                    Games.away_yards, Games.home_turnovers, Games.away_turnovers,
                    Games.home_pregame_elo, Games.away_pregame_elo, Weeks.week, Games.id 
                    FROM Games JOIN Weeks JOIN Seasons on Games.week_id = Weeks.id and Games.season_id = Seasons.id
                    WHERE Weeks.id < 16 and (Games.home_team = ? or Games.away_team = ? ) and Seasons.id = 1
                    """, (team, team)).fetchall()
        
        # put data into dictionary
        for game in first_year_data:
            home_team_name = game[0]
            away_team_name = game[1]
            home_points = game[2]
            away_points = game[3]
            home_yards = game[4]
            away_yards = game[5]
            home_turnovers = game[6]
            away_turnovers = game[7]
            home_pregame_elo = game[8]
            away_pregame_elo = game[9]
            week_id = game[10]
            game_id = game[11]
            if home_team_name == team: home_team = True
            elif away_team_name == team: away_team = True
            else: print("something went wrong, game not in first_year_data")

            if home_team:
                last_14_games[team]["elo_for"].append(home_pregame_elo)
                last_14_games[team]["elo_against"].append(away_pregame_elo)
                last_14_games[team]["points_for"].append(home_points)
                last_14_games[team]["points_against"].append(away_points)
                last_14_games[team]["yards_for"].append(home_yards)
                last_14_games[team]["yards_against"].append(away_yards)
                last_14_games[team]["turnovers_for"].append(away_turnovers)
                last_14_games[team]["turnovers_against"].append(home_turnovers)
            elif away_team:
                last_14_games[team]["elo_for"].append(away_pregame_elo)
                last_14_games[team]["elo_against"].append(home_pregame_elo)
                last_14_games[team]["points_for"].append(away_points)
                last_14_games[team]["points_against"].append(home_points)
                last_14_games[team]["yards_for"].append(away_yards)
                last_14_games[team]["yards_against"].append(home_yards)
                last_14_games[team]["turnovers_for"].append(home_turnovers)
                last_14_games[team]["turnovers_against"].append(away_turnovers)

    for name, values in last_14_games.items():
        for value in values.values():
            assert(len(value) == 14)
        
    #get all games excluding year 1
    rest_of_data = cur.execute("""
                SELECT Games.home_team, Games.away_team, Games.home_points, Games.away_points, Games.home_yards,
                Games.away_yards, Games.home_turnovers, Games.away_turnovers,
                Games.home_pregame_elo, Games.away_pregame_elo, Weeks.week, Games.id, Seasons.id
                FROM Games JOIN Weeks JOIN Seasons on Games.week_id = Weeks.id and Games.season_id = Seasons.id
                WHERE Seasons.id > 1
                """).fetchall()
        
    # for each game in all the games:
    table_id = 1
    for game in rest_of_data:
        home_team_name = game[0]
        away_team_name = game[1]
        home_points = game[2]
        away_points = game[3]
        home_yards = game[4]
        away_yards = game[5]
        home_turnovers = game[6]
        away_turnovers = game[7]
        home_pregame_elo = game[8]
        away_pregame_elo = game[9]
        week_id = game[10]
        game_id = game[11]
        season_id = game[12]
        
        # insert data into mldata table for team
        cur.execute(insert_command, 
                    (table_id, game_id, home_pregame_elo, 
                        *last_14_games[home_team_name]["elo_for"], 
                        *last_14_games[home_team_name]["elo_against"], 
                        *last_14_games[home_team_name]["points_for"], 
                        *last_14_games[home_team_name]["points_against"],
                        *last_14_games[home_team_name]["yards_for"],
                        *last_14_games[home_team_name]["yards_against"], 
                        *last_14_games[home_team_name]["turnovers_for"], 
                        *last_14_games[home_team_name]["turnovers_against"],
                        away_pregame_elo,
                        *last_14_games[away_team_name]["elo_for"], 
                        *last_14_games[away_team_name]["elo_against"], 
                        *last_14_games[away_team_name]["points_for"], 
                        *last_14_games[away_team_name]["points_against"],
                        *last_14_games[away_team_name]["yards_for"],
                        *last_14_games[away_team_name]["yards_against"], 
                        *last_14_games[away_team_name]["turnovers_for"], 
                        *last_14_games[away_team_name]["turnovers_against"],
                        week_id))
        
        table_id += 1
        
        # update data array by appending new data points to end and removing the old one from the front.
        last_14_games[home_team_name]["elo_for"].append(home_pregame_elo)
        last_14_games[home_team_name]["elo_against"].append(away_pregame_elo)
        last_14_games[home_team_name]["points_for"].append(home_points)
        last_14_games[home_team_name]["points_against"].append(away_points)
        last_14_games[home_team_name]["yards_for"].append(home_yards)
        last_14_games[home_team_name]["yards_against"].append(away_yards)
        last_14_games[home_team_name]["turnovers_for"].append(away_turnovers)
        last_14_games[home_team_name]["turnovers_against"].append(home_turnovers)
        last_14_games[away_team_name]["elo_for"].append(away_pregame_elo)
        last_14_games[away_team_name]["elo_against"].append(home_pregame_elo)
        last_14_games[away_team_name]["points_for"].append(away_points)
        last_14_games[away_team_name]["points_against"].append(home_points)
        last_14_games[away_team_name]["yards_for"].append(away_yards)
        last_14_games[away_team_name]["yards_against"].append(home_yards)
        last_14_games[away_team_name]["turnovers_for"].append(home_turnovers)
        last_14_games[away_team_name]["turnovers_against"].append(away_turnovers)

        last_14_games[home_team_name]["elo_for"].pop(0)
        last_14_games[home_team_name]["elo_against"].pop(0)
        last_14_games[home_team_name]["points_for"].pop(0)
        last_14_games[home_team_name]["points_against"].pop(0)
        last_14_games[home_team_name]["yards_for"].pop(0)
        last_14_games[home_team_name]["yards_against"].pop(0)
        last_14_games[home_team_name]["turnovers_for"].pop(0)
        last_14_games[home_team_name]["turnovers_against"].pop(0)
        last_14_games[away_team_name]["elo_for"].pop(0)
        last_14_games[away_team_name]["elo_against"].pop(0)
        last_14_games[away_team_name]["points_for"].pop(0)
        last_14_games[away_team_name]["points_against"].pop(0)
        last_14_games[away_team_name]["yards_for"].pop(0)
        last_14_games[away_team_name]["yards_against"].pop(0)
        last_14_games[away_team_name]["turnovers_for"].pop(0)
        last_14_games[away_team_name]["turnovers_against"].pop(0)

    conn.commit()

    # make table with means (input features)
    cur.executescript("""
    DROP TABLE IF EXISTS AiInput;
                    
    CREATE TABLE AiInput (
        id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
        game_id INTEGER,
        ai_spread REAL,                  
        elo_diff REAL,
        point_diff REAL,
        yard_diff REAL,
        turnover_diff REAL,
        elo_pred_spread REAL                                                                                                                
    )                
    """)
    conn.commit()

    games = cur.execute("""
                        SELECT Games.id, Games.home_points, Games.away_points,
                        Games.home_pregame_elo, Games.away_pregame_elo, InferenceData.*
                        FROM Games JOIN InferenceData on Games.id = InferenceData.game_id""").fetchall()

    # load nn model
    model = models.v1()

    # calculate averages
    games_df = pd.DataFrame(games)

    games_df["home_point_diff"] = games_df.iloc[:,36:50].mean(axis=1) - games_df.iloc[:,50:64].mean(axis=1)
    games_df["away_point_diff"] = games_df.iloc[:,149:163].mean(axis=1) - games_df.iloc[:,163:177].mean(axis=1)
    games_df["point_diff_diff"] = games_df["home_point_diff"] - games_df["away_point_diff"]
    games_df["home_turnover_diff"] = games_df.iloc[:,92:106].mean(axis=1) - games_df.iloc[:,106:120].mean(axis=1)
    games_df["away_turnover_diff"] = games_df.iloc[:,205:219].mean(axis=1) - games_df.iloc[:,219:233].mean(axis=1)
    games_df["turnover_diff_diff"] = games_df["home_turnover_diff"] - games_df["away_turnover_diff"]
    games_df["home_yard_diff"] = games_df.iloc[:,64:78].mean(axis=1) - games_df.iloc[:,78:92].mean(axis=1)
    games_df["away_yard_diff"] = games_df.iloc[:,177:191].mean(axis=1) - games_df.iloc[:,191:205].mean(axis=1)
    games_df["yard_diff_diff"] = games_df["home_yard_diff"] - games_df["away_yard_diff"]
    games_df["home_elo_diff"] = games_df.iloc[:,8:22].mean(axis=1) - games_df.iloc[:,22:36].mean(axis=1)
    games_df["away_elo_diff"] = games_df.iloc[:,121:135].mean(axis=1) - games_df.iloc[:,135:149].mean(axis=1)
    games_df["elo_diff_diff"] = games_df["home_elo_diff"] - games_df["away_elo_diff"]
    games_df["pred_spread"] = (games_df.iloc[:, 4] - games_df.iloc[:, 3])/25

    # populate table
    count = 0
    for index, row in games_df.iterrows():
        input = torch.tensor(row[["elo_diff_diff",
                                "point_diff_diff",
                                "yard_diff_diff",
                                "turnover_diff_diff",
                                "pred_spread"]].to_numpy(dtype=float),
                                dtype=torch.float32)
        model_pred = model(input).item()
        cur.execute("""INSERT INTO AiInput Values
                    (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (count, row.iloc[0], model_pred, row["elo_diff_diff"],
                    row["point_diff_diff"], row["yard_diff_diff"],
                    row["turnover_diff_diff"], row["pred_spread"])
                    )
        count += 1
    conn.commit()

    # make table with the unaveraged input features for each team
    cur.executescript("""
    DROP TABLE IF EXISTS TeamAiData;
                    
    CREATE TABLE TeamAiData (
        id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
        team_id INTEGER,
        home_team INTEGER,
        home_pregame_elo INTEGER,                  
        home_elo_for_1 INTEGER,
        home_elo_for_2 INTEGER,
        home_elo_for_3 INTEGER,
        home_elo_for_4 INTEGER,
        home_elo_for_5 INTEGER,
        home_elo_for_6 INTEGER,
        home_elo_for_7 INTEGER,
        home_elo_for_8 INTEGER,
        home_elo_for_9 INTEGER,
        home_elo_for_10 INTEGER,
        home_elo_for_11 INTEGER,
        home_elo_for_12 INTEGER,
        home_elo_for_13 INTEGER,
        home_elo_for_14 INTEGER,
        home_elo_against_1 INTEGER,
        home_elo_against_2 INTEGER,
        home_elo_against_3 INTEGER,
        home_elo_against_4 INTEGER,
        home_elo_against_5 INTEGER,
        home_elo_against_6 INTEGER,
        home_elo_against_7 INTEGER,
        home_elo_against_8 INTEGER,
        home_elo_against_9 INTEGER,
        home_elo_against_10 INTEGER,
        home_elo_against_11 INTEGER,
        home_elo_against_12 INTEGER,
        home_elo_against_13 INTEGER,
        home_elo_against_14 INTEGER,
        home_points_for_1 INTEGER,
        home_points_for_2 INTEGER,
        home_points_for_3 INTEGER,
        home_points_for_4 INTEGER,
        home_points_for_5 INTEGER,
        home_points_for_6 INTEGER,
        home_points_for_7 INTEGER,
        home_points_for_8 INTEGER,
        home_points_for_9 INTEGER,
        home_points_for_10 INTEGER,
        home_points_for_11 INTEGER,
        home_points_for_12 INTEGER,
        home_points_for_13 INTEGER,
        home_points_for_14 INTEGER,
        home_points_against_1 INTEGER,
        home_points_against_2 INTEGER,
        home_points_against_3 INTEGER,
        home_points_against_4 INTEGER,
        home_points_against_5 INTEGER,
        home_points_against_6 INTEGER,
        home_points_against_7 INTEGER,
        home_points_against_8 INTEGER,
        home_points_against_9 INTEGER,
        home_points_against_10 INTEGER,
        home_points_against_11 INTEGER,
        home_points_against_12 INTEGER,
        home_points_against_13 INTEGER,
        home_points_against_14 INTEGER,
        home_yards_for_1 INTEGER,
        home_yards_for_2 INTEGER,
        home_yards_for_3 INTEGER,
        home_yards_for_4 INTEGER,
        home_yards_for_5 INTEGER,
        home_yards_for_6 INTEGER,
        home_yards_for_7 INTEGER,
        home_yards_for_8 INTEGER,
        home_yards_for_9 INTEGER,
        home_yards_for_10 INTEGER,
        home_yards_for_11 INTEGER,
        home_yards_for_12 INTEGER,
        home_yards_for_13 INTEGER,
        home_yards_for_14 INTEGER,
        home_yards_against_1 INTEGER,
        home_yards_against_2 INTEGER,
        home_yards_against_3 INTEGER,
        home_yards_against_4 INTEGER,
        home_yards_against_5 INTEGER,
        home_yards_against_6 INTEGER,
        home_yards_against_7 INTEGER,
        home_yards_against_8 INTEGER,
        home_yards_against_9 INTEGER,
        home_yards_against_10 INTEGER,
        home_yards_against_11 INTEGER,
        home_yards_against_12 INTEGER,
        home_yards_against_13 INTEGER,
        home_yards_against_14 INTEGER,
        home_turnovers_for_1 INTEGER,
        home_turnovers_for_2 INTEGER,
        home_turnovers_for_3 INTEGER,
        home_turnovers_for_4 INTEGER,
        home_turnovers_for_5 INTEGER,
        home_turnovers_for_6 INTEGER,
        home_turnovers_for_7 INTEGER,
        home_turnovers_for_8 INTEGER,
        home_turnovers_for_9 INTEGER,
        home_turnovers_for_10 INTEGER,
        home_turnovers_for_11 INTEGER,
        home_turnovers_for_12 INTEGER,
        home_turnovers_for_13 INTEGER,
        home_turnovers_for_14 INTEGER,
        home_turnovers_against_1 INTEGER,
        home_turnovers_against_2 INTEGER,
        home_turnovers_against_3 INTEGER,
        home_turnovers_against_4 INTEGER,
        home_turnovers_against_5 INTEGER,
        home_turnovers_against_6 INTEGER,
        home_turnovers_against_7 INTEGER,
        home_turnovers_against_8 INTEGER,
        home_turnovers_against_9 INTEGER,
        home_turnovers_against_10 INTEGER,
        home_turnovers_against_11 INTEGER,
        home_turnovers_against_12 INTEGER,
        home_turnovers_against_13 INTEGER,
        home_turnovers_against_14 INTEGER,
        away_pregame_elo INTEGER,                  
        away_elo_for_1 INTEGER,
        away_elo_for_2 INTEGER,
        away_elo_for_3 INTEGER,
        away_elo_for_4 INTEGER,
        away_elo_for_5 INTEGER,
        away_elo_for_6 INTEGER,
        away_elo_for_7 INTEGER,
        away_elo_for_8 INTEGER,
        away_elo_for_9 INTEGER,
        away_elo_for_10 INTEGER,
        away_elo_for_11 INTEGER,
        away_elo_for_12 INTEGER,
        away_elo_for_13 INTEGER,
        away_elo_for_14 INTEGER,
        away_elo_against_1 INTEGER,
        away_elo_against_2 INTEGER,
        away_elo_against_3 INTEGER,
        away_elo_against_4 INTEGER,
        away_elo_against_5 INTEGER,
        away_elo_against_6 INTEGER,
        away_elo_against_7 INTEGER,
        away_elo_against_8 INTEGER,
        away_elo_against_9 INTEGER,
        away_elo_against_10 INTEGER,
        away_elo_against_11 INTEGER,
        away_elo_against_12 INTEGER,
        away_elo_against_13 INTEGER,
        away_elo_against_14 INTEGER,
        away_points_for_1 INTEGER,
        away_points_for_2 INTEGER,
        away_points_for_3 INTEGER,
        away_points_for_4 INTEGER,
        away_points_for_5 INTEGER,
        away_points_for_6 INTEGER,
        away_points_for_7 INTEGER,
        away_points_for_8 INTEGER,
        away_points_for_9 INTEGER,
        away_points_for_10 INTEGER,
        away_points_for_11 INTEGER,
        away_points_for_12 INTEGER,
        away_points_for_13 INTEGER,
        away_points_for_14 INTEGER,
        away_points_against_1 INTEGER,
        away_points_against_2 INTEGER,
        away_points_against_3 INTEGER,
        away_points_against_4 INTEGER,
        away_points_against_5 INTEGER,
        away_points_against_6 INTEGER,
        away_points_against_7 INTEGER,
        away_points_against_8 INTEGER,
        away_points_against_9 INTEGER,
        away_points_against_10 INTEGER,
        away_points_against_11 INTEGER,
        away_points_against_12 INTEGER,
        away_points_against_13 INTEGER,
        away_points_against_14 INTEGER,
        away_yards_for_1 INTEGER,
        away_yards_for_2 INTEGER,
        away_yards_for_3 INTEGER,
        away_yards_for_4 INTEGER,
        away_yards_for_5 INTEGER,
        away_yards_for_6 INTEGER,
        away_yards_for_7 INTEGER,
        away_yards_for_8 INTEGER,
        away_yards_for_9 INTEGER,
        away_yards_for_10 INTEGER,
        away_yards_for_11 INTEGER,
        away_yards_for_12 INTEGER,
        away_yards_for_13 INTEGER,
        away_yards_for_14 INTEGER,
        away_yards_against_1 INTEGER,
        away_yards_against_2 INTEGER,
        away_yards_against_3 INTEGER,
        away_yards_against_4 INTEGER,
        away_yards_against_5 INTEGER,
        away_yards_against_6 INTEGER,
        away_yards_against_7 INTEGER,
        away_yards_against_8 INTEGER,
        away_yards_against_9 INTEGER,
        away_yards_against_10 INTEGER,
        away_yards_against_11 INTEGER,
        away_yards_against_12 INTEGER,
        away_yards_against_13 INTEGER,
        away_yards_against_14 INTEGER,
        away_turnovers_for_1 INTEGER,
        away_turnovers_for_2 INTEGER,
        away_turnovers_for_3 INTEGER,
        away_turnovers_for_4 INTEGER,
        away_turnovers_for_5 INTEGER,
        away_turnovers_for_6 INTEGER,
        away_turnovers_for_7 INTEGER,
        away_turnovers_for_8 INTEGER,
        away_turnovers_for_9 INTEGER,
        away_turnovers_for_10 INTEGER,
        away_turnovers_for_11 INTEGER,
        away_turnovers_for_12 INTEGER,
        away_turnovers_for_13 INTEGER,
        away_turnovers_for_14 INTEGER,
        away_turnovers_against_1 INTEGER,
        away_turnovers_against_2 INTEGER,
        away_turnovers_against_3 INTEGER,
        away_turnovers_against_4 INTEGER,
        away_turnovers_against_5 INTEGER,
        away_turnovers_against_6 INTEGER,
        away_turnovers_against_7 INTEGER,
        away_turnovers_against_8 INTEGER,
        away_turnovers_against_9 INTEGER,
        away_turnovers_against_10 INTEGER,
        away_turnovers_against_11 INTEGER,
        away_turnovers_against_12 INTEGER,
        away_turnovers_against_13 INTEGER,
        away_turnovers_against_14 INTEGER,
        week_number INTEGER                  
    );                  
    """)

    # for each team name
    table_id = 1
    insert_command = build_insert_string("TeamAiData", 230)
    for team in teams.keys():
        team_id = cur.execute("SELECT id FROM Teams WHERE name = ?", (team,)).fetchone()[0]
        last_game_id, home_team, away_team = cur.execute(
            "SELECT MAX(id), home_team, away_team FROM Games WHERE home_team = ? or away_team = ?",
            (team, team)
            ).fetchall()[0]
        inference_data = cur.execute("SELECT * FROM InferenceData WHERE game_id = ?", 
                                    (last_game_id,)).fetchall()[0]
        home = 0
        if team == home_team: home = 1

        cur.execute(insert_command, (table_id, team_id, home, *inference_data[2:]))
        table_id += 1
    conn.commit()

    conn.close()