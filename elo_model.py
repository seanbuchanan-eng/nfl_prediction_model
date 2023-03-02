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

def elo_team_adjustment(game):
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
    home_team = game.home_team
    away_team = game.away_team
    home_team_elo = home_team.elo
    away_team_elo = away_team.elo

    # travel adjustment
    if game.neutral_destination:
        # Neutral game, make no base adjustment. Adjust both teams for distance only.
        home_travel_distance = get_distance(home_team.latitude,
                                            home_team.longitude,
                                            game.neutral_destination[0],
                                            game.neutral_destination[1])
        away_travel_distance = get_distance(away_team.latitude,
                                            away_team.longitude,
                                            game.neutral_destination[0],
                                            game.neutral_destination[1])
        home_team_elo -= round(home_travel_distance*0.004)
        away_team_elo -= round(away_travel_distance*0.004)
    else:
        distance = get_distance(home_team.latitude,
                                home_team.longitude,
                                away_team.latitude,
                                away_team.longitude)
        home_team_elo += 48
        home_team_elo += round(distance*0.004)

    # bye adjustment
    if home_team.bye:
        home_team_elo += 25
    elif away_team.bye:
        away_team_elo += 25
    else:
        pass

    # playoff adjustment
    if game.playoff:
        elo_diff = (home_team_elo - away_team_elo)*1.2
    else:
        elo_diff = (home_team_elo - away_team_elo)

    return elo_diff

def win_prob(game):
    "Calculates win probability with respect to the home team"
    elo_diff = elo_team_adjustment(game)
    win_probability = 1/(10**(-elo_diff/400)+1)
    return win_probability

def postgame_elo_shift(game):
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
    # recommended K-factor
    K = 20 
    
    # forcast delta
    win_probability = win_prob(game)
    if game.home_points == game.away_points:
        forecast_delta = 0.5 - win_probability
    elif game.home_points > game.away_points:
        forecast_delta = 1 - win_probability
    else:
        forecast_delta = 0 - win_probability
    
    # mov multiplier
    point_diff = game.home_points - game.away_points
    elo_diff = elo_team_adjustment(game) # calcs wrt home team
    if point_diff == 0:
        # Doesn't seem to be on the website explanation anymore but I'm keeping
        # it because it makes sense that a team that is predicted to win ties
        # should lose points.
        mov = 1.525
    else:
        mov = np.log(abs(point_diff)+1)*(2.2/(elo_diff*0.001+2.2))

    return round(K*forecast_delta*mov)

def pre_season_elo(team):
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
    new_elo = team.elo - (team.elo - mean)/3
    return round(new_elo)        