import numpy as np

"""
Elo model developed by Jay Boice at FiveThirtyEight.
see https://fivethirtyeight.com/methodology/how-our-nfl-predictions-work/
"""

def get_distance(teamA_lat, teamA_long, teamB_lat, teamB_long):
    """
    Calculates distance between teams using haversine formula.
    
    Parameters
    ----------
    teamA: main.Team
        Team object of in game team
    teamB: main.Team
        Team object of other in game team
    
    Returns:
    --------
    float
        Distance between teams in miles.
    """
    r = 6378.137 #Radius of earth (Km)
    latA = np.radians(teamA_lat)
    latB = np.radians(teamB_lat)
    longA = np.radians(teamA_long)
    longB = np.radians(teamB_long)

    # Haversine formula see: https://en.wikipedia.org/wiki/Haversine_formula
    distance = 2*r*np.arcsin(np.sqrt(np.sin((latB-latA)/2)**2 + 
    (1 - np.sin((latA-latB)/2)**2 - np.sin((latA+latB)/2)**2)*np.sin((longB-longA)/2)**2))

    return distance/1.609 # Miles

def pregame_elo_shift(game_dict, cur):
    home_team = cur.execute("SELECT latitude, longitude FROM Teams WHERE name = ? ", 
                                (game_dict["home_team"],)).fetchall()[0]
    away_team = cur.execute("SELECT latitude, longitude FROM Teams WHERE name = ? ", 
                                (game_dict["away_team"],)).fetchall()[0]

    elo_shift = 0
    # travel adjustment
    if game_dict["neutral_dest"] != 'None':
        # Neutral game, make no base adjustment. Adjust both teams for distance only.
        neutral_lat, neutral_long = cur.execute("SELECT latitude, longitude FROM Teams WHERE ticker = ?", 
                                  (game_dict["neutral_dest"],)).fetchall()[0]
        home_travel_distance = get_distance(home_team[0],
                                            home_team[1],
                                            neutral_lat,
                                            neutral_long)
        away_travel_distance = get_distance(away_team[0],
                                            away_team[1],
                                            neutral_lat,
                                            neutral_long)
        home_team_shift = round(home_travel_distance*0.004)
        away_team_shift = round(away_travel_distance*0.004)
        elo_shift -= home_team_shift + away_team_shift
    else:
        distance = get_distance(home_team[0],
                                home_team[1],
                                away_team[0],
                                away_team[1])
        elo_shift += 48/2
        elo_shift += round(distance*0.004/2)

    return elo_shift

def win_prob(elo_diff):
    "Calculates win probability with respect to the home team"
    win_probability = 1/(10**(-elo_diff/400)+1)
    return win_probability

def postgame_elo_shift(game_dict, cur):
    """
    Calculates the points to be added or subtracted to the home team.
    The opposite must be done to the away team.

    Parameters:
    -----------
    teamA: main.Team
        One of the teams playing
    teamB: main.Team
        The other team playing
    result: float
        All results are with respect to TeamA 1-win, 0-loss, 0.5-tie.
    pointdiff: float
        Point differential (positive)
    playoff: bool
        True if playoffs False otherwise (optional)

    Returns:
    --------
    Elo Shift: float
        The number of Elo points that need to be shifted from teamA to teamB
        based on the game result. Positive indicates points go to teamA, negative
        indicates points go to teamB.
    """
    home_points = int(game_dict["home_points"])
    away_points = int(game_dict["away_points"])

    # recommended K-factor
    K = 20 
    
    # elo_diff = elo_team_adjustment(game_dict, cur) # calcs wrt home team
    if game_dict["playoffs"]:
        elo_diff = (game_dict["home_pregame_elo"] - game_dict["away_pregame_elo"])*1.2
    else:
        elo_diff = game_dict["home_pregame_elo"] - game_dict["away_pregame_elo"]
        
    # forcast delta
    win_probability = win_prob(elo_diff)
    if home_points == away_points:
        forecast_delta = 0.5 - win_probability
    elif home_points > away_points:
        forecast_delta = 1 - win_probability
    else:
        forecast_delta = 0 - win_probability
    
    # mov multiplier
    point_diff = home_points - away_points
    
    if point_diff == 0:
        # The explanation for accounting for a tie doesn't seem to be on the website
        # anymore but I've decided to keep this value it because it makes sense 
        # that a team that is predicted to win ties should lose points.
        mov = 1.525
    else:
        if point_diff < 0:
            elo_diff *= -1
        mov = np.log(abs(point_diff)+1)*(2.2/(elo_diff*0.001+2.2))

    return round(K*forecast_delta*mov)

def pre_season_elo(elo):
    """
    Calculate team's pre-season elo rating. It is essentially
    just a regression to the mean.
    
    Parameters:
    -----------
    team: main.Team
        team calculate pre-season elo from.

    Returns:
    --------
    int
        New elo value for team.
    """
    mean = 1505
    new_elo = elo - (elo - mean)/3
    return round(new_elo)        