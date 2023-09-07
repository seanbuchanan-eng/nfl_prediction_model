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

def elo_team_adjustment(home_team_id, away_team_id, playoff, neutral_dest, cur):
    """
    Adjusts base elo rating for home field, travel distance, bye week,
    and playoffs. Adjusts relative to the home team, therefore a negative
    number means predicted loss by home team and visa versa.
    
    Parameters:
    ----------
    teamA: main.Team
        Team object of the home team
    teamB: main.Team
        Team object of away team
    playoff: bool
        True or False whether it is a playoff game. Initialized to False.
    
    Returns:
    --------
    Elodiff: float
        Difference in Elo score based on current elo score, home field, travel,
        buy, and playoffs. Difference is relative to teamA => positive means elodiff is added
        to teamA temporary Elo, negative means difference is added to teamB temp Elo.
    """
    home_team = cur.execute("SELECT latitude, longitude, elo FROM Teams WHERE name = ? ", 
                                (home_team_id,)).fetchall()[0]
    away_team = cur.execute("SELECT latitude, longitude, elo FROM Teams WHERE name = ? ", 
                                (away_team_id,)).fetchall()[0]
    home_team_elo = home_team[2]
    away_team_elo = away_team[2]

    # travel adjustment
    if neutral_dest != 'None':
        # Neutral game, make no base adjustment. Adjust both teams for distance only.
        neutral_lat, neutral_long = cur.execute("SELECT latitude, longitude FROM Teams WHERE ticker = ?", 
                                  (neutral_dest,)).fetchall()[0]
        home_travel_distance = get_distance(home_team[0],
                                            home_team[1],
                                            neutral_lat,
                                            neutral_long)
        away_travel_distance = get_distance(away_team[0],
                                            away_team[1],
                                            neutral_lat,
                                            neutral_long)
        home_team_elo -= round(home_travel_distance*0.004)
        away_team_elo -= round(away_travel_distance*0.004)
    else:
        distance = get_distance(home_team[0],
                                home_team[1],
                                away_team[0],
                                away_team[1])
        home_team_elo += 48
        home_team_elo += round(distance*0.004)

    # bye adjustment (still need to implement when setting up the db)
    # if home_team.bye:
    #     home_team_elo += 25
    # elif away_team.bye:
    #     away_team_elo += 25
    # else:
    #     pass

    # playoff adjustment
    if playoff:
        elo_diff = (home_team_elo - away_team_elo)*1.2
    else:
        elo_diff = (home_team_elo - away_team_elo)

    return round(elo_diff)

def win_prob(game, cur):
    "Calculates win probability with respect to the home team"
    elo_diff = elo_team_adjustment(game[0], game[1], game[4], game[5], cur)
    win_probability = 1/(10**(-elo_diff/400)+1)
    return win_probability

def postgame_elo_shift(game, cur):
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
    home_points = game[2]
    away_points = game[3]

    # recommended K-factor
    K = 20 
    
    # forcast delta
    win_probability = win_prob(game, cur)
    if home_points == away_points:
        forecast_delta = 0.5 - win_probability
    elif home_points > away_points:
        forecast_delta = 1 - win_probability
    else:
        forecast_delta = 0 - win_probability
    
    # mov multiplier
    point_diff = home_points - away_points
    elo_diff = elo_team_adjustment(game[0], game[1], game[4], game[5], cur) # calcs wrt home team
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