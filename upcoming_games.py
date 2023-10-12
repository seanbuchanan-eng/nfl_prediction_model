import elo_model
import scraper
from datetime import date
import pandas as pd
import models
import torch
import numpy as np

def calc_last_game_date(games):
    """
    Calculate the last game date in a week of games.
    
    Parameters
    ----------
    games : dict
        Dictionary of games for a week.

    Returns
    -------
    Date object    
        Date of last game in games as a date object.
    """
    last_game_date = games[-2]['game_date'].split('-')
    last_game_date = date(int(last_game_date[0]), 
                            int(last_game_date[1]), 
                            int(last_game_date[2]))
    return last_game_date

def add_season_to_db(cur, conn):
    """
    Update the Seasons table in the database to include
    the most recent season + 1.

    Parameters
    ----------
    cur : sqlite cursor object
    conn : sqlite connection object
    """
    last_season = cur.execute("SELECT * FROM Seasons").fetchall()[-1]
    year = last_season[1].split("-")
    next_year = year[1] + "-" + str(int(year[1])+1)
    length = 18
    cur.execute("""INSERT OR IGNORE INTO Seasons (season, length)
                VALUES (?, ?)""", (next_year, length))
    conn.commit()

def update_pre_season_elo(cur, conn):
    """
    Update the elo score for each team with their preseason elo.

    Parameters
    ----------
    cur : sqlite cursor object
    conn : sqlite connection object
    """
    teams = cur.execute("SELECT id, elo FROM Teams").fetchall()
    for team in teams:
        elo = elo_model.pre_season_elo(team[1])
        cur.execute("UPDATE Teams SET elo = ? WHERE id = ?", (elo,team[0]))
    conn.commit()

def assign_home_away(game):
    """
    Assign the home and away team to `game`.

    Parameters
    ----------
    game : dict
        Dictionary of game data.
    """
    if game["game_location"] == '@' or game["game_location"] == 'N':
        game["home"] = "loser"
        game["away"] = "winner"
    elif game["game_location"] == '':
        game["home"] = "winner"
        game["away"] = "loser"

def set_pregame_spread(games, cur):
    """
    Sets pregame spread for upcoming games and add it to
    games as another key entry.

    Parameters
    ----------
    games : list[dict]
        List of dictionaries with game data.
    cur : sqlite cursor object
    """
    for game in games:
        assign_home_away(game)
        if game["home"] == "loser":
            game["home_team"] = game["loser"]
            game["away_team"] = game["winner"]
        else:
            game["home_team"] = game["winner"]
            game["away_team"] = game["loser"]

        home_elo = cur.execute("SELECT elo FROM Teams WHERE name = ?", (game["home_team"],)).fetchone()[0]
        away_elo = cur.execute("SELECT elo FROM Teams WHERE name = ?", (game["away_team"],)).fetchone()[0]

        # TODO account for playoffs and implement neutral dest
        game["neutral_dest"] = 'None'
        game["playoffs"] = False
        pregame_elo_shift = elo_model.pregame_elo_shift(game, cur)
        home_elo = home_elo + pregame_elo_shift
        away_elo = away_elo - pregame_elo_shift
        game["home_pregame_elo"] = home_elo
        game["away_pregame_elo"] = away_elo

        home_spread = (away_elo - home_elo)/25
        away_spread = home_spread * -1
        game["home_spread"] = home_spread
        game["away_spread"] = away_spread

def set_ai_pregame_spread(games, cur):
    """
    Calculates the AI predicted spread and adds it to
    `games` with keys "home_ai_spread" and "away_ai_spread".

    Parameters
    ----------
    games : list[dict]
        List of dictionaries with game data.
    cur : sqlite cursor object
    """
    
    for game in games:
        # ensure that home_team has been identified
        try:
            game["home_team"]
            game["away_team"]
        except KeyError:
            print("pregame elo needs to be run on games before running set_ai_pregame_spread")
        
        home_data = cur.execute("""SELECT TeamAiData.* FROM 
                                TeamAiData JOIN Teams
                                on TeamAiData.team_id = Teams.id
                                WHERE Teams.name = ?""",(game["home_team"],)).fetchall()[0]
        away_data = cur.execute("""SELECT TeamAiData.* FROM 
                                TeamAiData JOIN Teams
                                on TeamAiData.team_id = Teams.id
                                WHERE Teams.name = ?""",(game["away_team"],)).fetchall()[0]
        
        if home_data[2] == 1:
            home_points_diff = np.mean(home_data[32:46]) - np.mean(home_data[46:60])
            home_turnover_diff = np.mean(home_data[88:102]) - np.mean(home_data[102:116])
            home_yard_diff = np.mean(home_data[60:74]) - np.mean(home_data[74:88])
            home_elo_diff = np.mean(home_data[4:18]) - np.mean(home_data[18:32])
        else:
            home_points_diff = np.mean(home_data[145:159]) - np.mean(home_data[159:173])
            home_turnover_diff = np.mean(home_data[201:215]) - np.mean(home_data[215:229])
            home_yard_diff = np.mean(home_data[173:187]) - np.mean(home_data[187:201])
            home_elo_diff = np.mean(home_data[117:131]) - np.mean(home_data[131:145])
        if away_data[2] == 1:
            away_points_diff = np.mean(away_data[32:46]) - np.mean(away_data[46:60])
            away_turnover_diff = np.mean(away_data[88:102]) - np.mean(away_data[102:116])
            away_yard_diff = np.mean(away_data[60:74]) - np.mean(away_data[74:88])
            away_elo_diff = np.mean(away_data[4:18]) - np.mean(away_data[18:32])
        else:
            away_points_diff = np.mean(away_data[145:159]) - np.mean(away_data[159:173])
            away_turnover_diff = np.mean(away_data[201:215]) - np.mean(away_data[215:229])
            away_yard_diff = np.mean(away_data[173:187]) - np.mean(away_data[187:201])
            away_elo_diff = np.mean(away_data[117:131]) - np.mean(away_data[131:145])

        points_diff_diff = home_points_diff - away_points_diff
        turnover_diff_diff = home_turnover_diff - away_turnover_diff
        yards_diff_diff = home_yard_diff - away_yard_diff
        elo_diff_diff = home_elo_diff - away_elo_diff
        pred_spread = game["home_spread"]

        input = torch.tensor([[elo_diff_diff,
                              points_diff_diff,
                              yards_diff_diff,
                              turnover_diff_diff,
                              pred_spread]],
                            dtype=torch.float32)
        model = models.v1()
        model_pred_spread = model(input).item()
        game["home_ai_spread"] = model_pred_spread
        game["away_ai_spread"] = model_pred_spread * -1
            
        
def update_week_games(cur, week, season, local_path=None):
    """
    Scrapes internet for this weeks games and then updates
    the games with predicted Elo spreads and AI spreads.

    Parameters
    ----------
    week : int 
        Current week of the season.
    season : int
        Current season. Would be 2023 for 2023-2024 season.
    local_path : str
        Local path to an html file for debugging.

    Returns
    -------
    dict
        Upcoming games and their predictions for the week.
    """
    #scrape for upcoming games
    upcoming_games = scraper.get_week_games(week, season, local_path)

    for game in upcoming_games:
        if game["pts_win"] == '': game["pts_win"] = '0'
        if game["pts_lose"] == '': game["pts_lose"] = '0'
        game["week"] = week

    # set pregame spread for the elo model
    set_pregame_spread(upcoming_games, cur)

    # update ai-games
    set_ai_pregame_spread(upcoming_games, cur)

    return upcoming_games

def update_inference_data(game, game_id, week, cur):
    """
    Updates the InferenceData table in the db with new game data.

    Parameters
    ----------
    game : dict
        Dictionary with game data.
    game_id : int
        Id of the game in the database.
    week : int
        Week of the season that the game occurs in.
    cur : sqlite database cursor
    """
    update_string = build_inference_update_string("InferenceData", game_id, 14)

    home_ai_data = cur.execute("""SELECT TeamAiData.* 
                                FROM TeamAiData JOIN Teams on TeamAiData.team_id = Teams.id
                                WHERE Teams.name = ?""", (game["home_team"],)).fetchall()[0]
    away_ai_data = cur.execute("""SELECT TeamAiData.* 
                                FROM TeamAiData JOIN Teams on TeamAiData.team_id = Teams.id
                                WHERE Teams.name = ?""", (game["away_team"],)).fetchall()[0]

    if home_ai_data[2] == 1:
        home_elo_for = list(home_ai_data[4:18])
        home_elo_against = list(home_ai_data[18:32])
        home_points_for = list(home_ai_data[32:46])
        home_points_against = list(home_ai_data[46:60])
        home_yards_for = list(home_ai_data[60:74])
        home_yards_against = list(home_ai_data[74:88])
        home_turnovers_for = list(home_ai_data[88:102])
        home_turnovers_against = list(home_ai_data[102:116])
    else:
        home_elo_for = list(home_ai_data[117:131])
        home_elo_against = list(home_ai_data[131:145])
        home_points_for = list(home_ai_data[145:159])
        home_points_against = list(home_ai_data[159:173])
        home_yards_for = list(home_ai_data[173:187])
        home_yards_against = list(home_ai_data[187:201])
        home_turnovers_for = list(home_ai_data[201:215])
        home_turnovers_against = list(home_ai_data[215:229])
    if away_ai_data[2] == 1:
        away_elo_for = list(away_ai_data[4:18])
        away_elo_against = list(away_ai_data[18:32])
        away_points_for = list(away_ai_data[32:46])
        away_points_against = list(away_ai_data[46:60])
        away_yards_for = list(away_ai_data[60:74])
        away_yards_against = list(away_ai_data[74:88])
        away_turnovers_for = list(away_ai_data[88:102])
        away_turnovers_against = list(away_ai_data[102:116])
    else:
        away_elo_for = list(away_ai_data[117:131])
        away_elo_against = list(away_ai_data[131:145])
        away_points_for = list(away_ai_data[145:159])
        away_points_against = list(away_ai_data[159:173])
        away_yards_for = list(away_ai_data[173:187])
        away_yards_against = list(away_ai_data[187:201])
        away_turnovers_for = list(away_ai_data[201:215])
        away_turnovers_against = list(away_ai_data[215:229])

    cur.execute(update_string, (game_id, game["home_pregame_elo"],
                                *home_elo_for, *home_elo_against,
                                *home_points_for, *home_points_against,
                                *home_yards_for, *home_yards_against,
                                *home_turnovers_for, *home_turnovers_against,
                                game["away_pregame_elo"], *away_elo_for,
                                *away_elo_against, *away_points_for,
                                *away_points_against, *away_yards_for,
                                *away_yards_against, *away_turnovers_for,
                                *away_turnovers_against, week))
        
def build_inference_update_string(table_name, game_id, number):
    """
    Builds the INSERT string for updating all columns of the `table_name`
    table in the database.

    Parameters
    ----------
    table_name : str
        Name of the table.
    game_id : int
        Id of the game in the database.
    number : int
        Number of games that are included in the backwards averaging
        for the ML model. Currently 14.

    Returns
    -------
    str
        INSERT string for updating the `table_name` table in the database.
    """
    update_string = f"""INSERT OR IGNORE INTO {table_name}
                        (game_id, home_pregame_elo"""
    
    items = {}
    items["home_elo_for"] = number
    items["home_elo_against"] = number
    items["home_points_for"] = number
    items["home_points_against"] = number
    items["home_yards_for"] = number
    items["home_yards_against"] = number
    items["home_turnovers_for"] = number
    items["home_turnovers_against"] = number
    items["away_pregame_elo"] = 0
    items["away_elo_for"] = number
    items["away_elo_against"] = number
    items["away_points_for"] = number
    items["away_points_against"] = number
    items["away_yards_for"] = number
    items["away_yards_against"] = number
    items["away_turnovers_for"] = number
    items["away_turnovers_against"] = number
    for name, number in items.items():
        if name == "away_pregame_elo":
            update_string += f", {name}"
        for idx in range(1, number+1):
            update_string += f", {name}_{idx}"
    update_string += f", week_number) VALUES (?"
    for idx in range(0,227):
        update_string += ", ?"
    update_string += ")"
    return update_string

def move_prev_week_to_db(cur, conn, week, season, local_path=None):
    """
    Scrapes the internet to get the scores from the previous week
    and adds the data to the db. Also updates
    the elo scores of the teams who played that week.

    Parameters
    ----------
    cur : database cursor
    week : int
        Current week of the season
    season : int
        Current season. Would be 2023 for 2023-2024 season.
    local_path : str
        Local path to an html file for debugging.
    """
    season_name = str(season) + "-" + str(season+1)
    season_id = cur.execute("SELECT id FROM Seasons WHERE season = ?", (season_name,)).fetchone()[0]
    week_id = cur.execute("SELECT id FROM Weeks WHERE week = ?", (week,)).fetchone()[0]
    games = update_week_games(cur, week, season, local_path)

    for game in games:
        #games table update
        # assign_home_away(game)
        if game["home"] == "loser":
            game["home_team"] = game["loser"]
            game["away_team"] = game["winner"]
            game["home_points"] = game["pts_lose"]
            game["away_points"] = game["pts_win"]
            game["home_yards"] = game["yards_lose"]
            game["away_yards"] = game["yards_win"]
            game["home_turnovers"] = game["to_lose"]
            game["away_turnovers"] = game["to_win"]
        else:
            game["away_team"] = game["loser"]
            game["home_team"] = game["winner"]
            game["away_points"] = game["pts_lose"]
            game["home_points"] = game["pts_win"]
            game["away_yards"] = game["yards_lose"]
            game["home_yards"] = game["yards_win"]
            game["away_turnovers"] = game["to_lose"]
            game["home_turnovers"] = game["to_win"]

        cur.execute("""INSERT OR IGNORE INTO Games
                    (season_id, week_id, home_team, away_team,
                    home_points, away_points, home_yards,
                    away_yards, home_turnovers, away_turnovers,
                    home_pregame_elo, away_pregame_elo, playoffs,
                    home_bye, away_bye, neutral_destination) 
                    VALUES ( ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (season_id, week_id, game["home_team"], game["away_team"], game["home_points"],
                     game["away_points"], game["home_yards"], game["away_yards"], game["home_turnovers"],
                     game["away_turnovers"], game["home_pregame_elo"], game["away_pregame_elo"], 0, 0, 0, 'None'))
        
        game_id = cur.execute("SELECT last_insert_rowid()").fetchone()[0]

        # team elo update
        elo_shift = elo_model.postgame_elo_shift(game, cur)
        away_elo = game["away_pregame_elo"] - elo_shift
        home_elo = game["home_pregame_elo"] + elo_shift
        cur.execute("UPDATE Teams SET elo = ? WHERE name = ?",
                    (home_elo, game["home_team"]))
        cur.execute("UPDATE Teams SET elo = ? WHERE name = ?",
                    (away_elo, game["away_team"]))
        
        update_inference_data(game, game_id, week, cur)
        update_ai_input(game_id, cur)
        
        update_ai_data(game["home_team"], 1, game, week, cur)
        update_ai_data(game["away_team"], 0, game, week, cur)

    conn.commit()

def update_ai_data(team, home, game, week, cur):
    """
    Updates the TeamAiData table in the database. 
    NOTE: Commit must be made after the function returns.

    Parameters
    ----------
    team : str
        Name of the team whose data is to be updated.
    home : bool
        True if `team` was the hometeam in the most recent game.
        Else false.
    game : dict
        Dictionary with game data.
    week : int
        Week that the game was played in.
    cur : sqlite cursor object 
    """
    ai_data = cur.execute("""SELECT TeamAiData.* 
                            FROM TeamAiData JOIN Teams on TeamAiData.team_id = Teams.id
                            WHERE Teams.name = ?""", (team,)).fetchall()[0]
    home_team = 1
    # get the last 13 of 14 attribute columns
    home_elo_for = list(ai_data[5:18])
    home_elo_against = list(ai_data[19:32])
    home_points_for = list(ai_data[33:46])
    home_points_against = list(ai_data[47:60])
    home_yards_for = list(ai_data[61:74])
    home_yards_against = list(ai_data[75:88])
    home_turnovers_for = list(ai_data[89:102])
    home_turnovers_against = list(ai_data[103:116])
    away_elo_for = list(ai_data[118:131])
    away_elo_against = list(ai_data[132:145])
    away_points_for = list(ai_data[146:159])
    away_points_against = list(ai_data[160:173])
    away_yards_for = list(ai_data[174:187])
    away_yards_against = list(ai_data[188:201])
    away_turnovers_for = list(ai_data[202:215])
    away_turnovers_against = list(ai_data[216:229])
    team_id = ai_data[1]

    # get command for updating the db
    update_string = build_aidata_update_string("TeamAiData", team_id, 14)

    # add the recent game stats to the existing ones
    home_elo_for.append(game["home_pregame_elo"])
    home_elo_against.append(game["away_pregame_elo"])
    home_points_for.append(game["home_points"])
    home_points_against.append(game["away_points"])
    home_yards_for.append(game["home_yards"])
    home_yards_against.append(game["away_yards"])
    home_turnovers_for.append(game["away_turnovers"])
    home_turnovers_against.append(game["home_turnovers"])
    away_elo_for.append(game["away_pregame_elo"])
    away_elo_against.append(game["home_pregame_elo"])
    away_points_for.append(game["away_points"])
    away_points_against.append(game["home_points"])
    away_yards_for.append(game["away_yards"])
    away_yards_against.append(game["home_yards"])
    away_turnovers_for.append(game["home_turnovers"])
    away_turnovers_against.append(game["away_turnovers"])

    if home: home_team = 1
    else: home_team = 0

    cur.execute(update_string, (home_team, game["home_pregame_elo"],
                                *home_elo_for, *home_elo_against,
                                *home_points_for, *home_points_against,
                                *home_yards_for, *home_yards_against,
                                *home_turnovers_for, *home_turnovers_against,
                                game["away_pregame_elo"], *away_elo_for,
                                *away_elo_against, *away_points_for,
                                *away_points_against, *away_yards_for,
                                *away_yards_against, *away_turnovers_for,
                                *away_turnovers_against, week))
    

def build_aidata_update_string(table_name, team_id, number):
    """
    Builds the INSERT string for updating all columns of the `table_name`
    table in the database.

    Parameters
    ----------
    table_name : str
        Name of the table.
    team_id : int
        Id of the team in the database.
    number : int
        Number of games that are included in the backwards averaging
        for the ML model. Currently 14.

    Returns
    -------
    str
        INSERT string for updating the `table_name` table in the database.
    """
    update_string = f"""UPDATE {table_name} SET
                        team_id = {team_id}, home_team = ?, home_pregame_elo = ?"""
    
    items = {}
    items["home_elo_for"] = number
    items["home_elo_against"] = number
    items["home_points_for"] = number
    items["home_points_against"] = number
    items["home_yards_for"] = number
    items["home_yards_against"] = number
    items["home_turnovers_for"] = number
    items["home_turnovers_against"] = number
    items["away_pregame_elo"] = 0
    items["away_elo_for"] = number
    items["away_elo_against"] = number
    items["away_points_for"] = number
    items["away_points_against"] = number
    items["away_yards_for"] = number
    items["away_yards_against"] = number
    items["away_turnovers_for"] = number
    items["away_turnovers_against"] = number
    for name, number in items.items():
        if name == "away_pregame_elo":
            update_string += f", {name} = ?"
        for idx in range(1, number+1):
            update_string += f", {name}_{idx} = ?"
    update_string += f", week_number = ? WHERE team_id = {team_id}"
    return update_string

def update_ai_input(game_id, cur):
    """
    Copies new data from the Games and InferenceData tables to
    the AiInput table in the database.

    Parameters
    ----------
    game_id : int
        Id of the game to have data copied.
    cur : sqlite cursor object.
    """
    game = cur.execute("""
                    SELECT Games.id, Games.home_points, Games.away_points,
                    Games.home_pregame_elo, Games.away_pregame_elo, InferenceData.*
                    FROM Games JOIN InferenceData on Games.id = InferenceData.game_id
                    WHERE Games.id = ?""", (game_id,)).fetchall()

    # load nn model
    model = models.v1()

    # calculate averages
    games_df = pd.DataFrame(game)

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
    input = torch.tensor(games_df[["elo_diff_diff",
                            "point_diff_diff",
                            "yard_diff_diff",
                            "turnover_diff_diff",
                            "pred_spread"]].to_numpy(dtype=float),
                            dtype=torch.float32)
    model_pred = model(input).item()
    cur.execute("""INSERT OR IGNORE INTO AiInput 
                (game_id, ai_spread, elo_diff, point_diff,
                yard_diff, turnover_diff, elo_pred_spread) Values
                (?, ?, ?, ?, ?, ?, ?)""",
                (game_id, model_pred, games_df["elo_diff_diff"].to_numpy()[0],
                games_df["point_diff_diff"].to_numpy()[0], games_df["yard_diff_diff"].to_numpy()[0],
                games_df["turnover_diff_diff"].to_numpy()[0], games_df["pred_spread"].to_numpy()[0])
                )