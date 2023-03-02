import pytest
from elo_model import *
from numpy import log

class Team:
    def __init__(self, id, name, latitude, longitude, elo, bye) -> None:
        self.id = id
        self.name = name
        self.latitude = latitude
        self.longitude = longitude
        self.elo = elo
        self.bye = bye

class Game:
    def __init__(self, home_team, away_team, playoff=False, neutral_destination=[]) -> None:
        self.home_team = home_team
        self.away_team = away_team
        self.neutral_destination = neutral_destination
        self.playoff = playoff
        self.home_points = 0
        self.away_points = 0

@pytest.fixture
def team_objects():
    kc = Team('KC', 'Kansas City Chiefs', 39.099789, -94.578560, 1000, False)
    hou = Team('HOU', 'Houston Texans', 29.760427, -95.369804, 1250, False)
    sea = Team('SEA', 'Seattle Seahawks', 47.603230, -122.330276, 1700, True)
    nyj = Team('NYJ', 'New York Jets', 40.814947462026176, -74.07665577312015, 1550, False)
    nyg = Team('NYG', 'New York Giants', 40.814947462026176, -74.07665577312015, 1660, False)
    return [kc, hou, sea, nyj, nyg]

def test_get_distance(team_objects):
    kc = team_objects[0]
    hou = team_objects[1]
    nyj = team_objects[3]
    nyg = team_objects[4]

    # different stadium teams
    assert round(get_distance(kc.latitude, 
                              kc.longitude,  
                              hou.latitude,
                              hou.longitude)) == 648
    # same stadium team
    assert round(get_distance(nyj.latitude,
                              nyj.longitude,
                              nyg.latitude,
                              nyg.longitude)) == 0
    
def calc_distance(game):
    return get_distance(game.home_team.latitude,
                        game.home_team.longitude,
                        game.away_team.latitude,
                        game.away_team.longitude)

def test_elo_team_adjustment(team_objects):
    kc = team_objects[0]
    hou = team_objects[1]
    sea = team_objects[2]
    nyj = team_objects[3]
    nyg = team_objects[4]

    # same stadium teams
    game1 = Game(nyj, nyg)
    assert elo_team_adjustment(game1) == -62

    # different stadium teams
    game2 = Game(hou, kc)
    distance = calc_distance(game2)
    assert (elo_team_adjustment(game2) 
            == (game2.home_team.elo+48+round(distance*0.004)-game2.away_team.elo))
    
    # test neutral location (arizona)
    game3 = Game(hou, kc, neutral_destination=[33.52738095014831, -112.26238094759978])
    home_distance = get_distance(game3.home_team.latitude,
                                 game3.home_team.longitude,
                                 game3.neutral_destination[0],
                                 game3.neutral_destination[1])
    away_distance = get_distance(game3.away_team.latitude,
                                 game3.away_team.longitude,
                                 game3.neutral_destination[0],
                                 game3.neutral_destination[1])
    assert (elo_team_adjustment(game3)
            == (game3.home_team.elo-round(home_distance*0.004)-(game3.away_team.elo-round(away_distance*0.004))))

    # test bye
    game4 = Game(sea, nyj)
    distance = calc_distance(game4)
    assert (elo_team_adjustment(game4)
            == (game4.home_team.elo+48+25+round(distance*0.004)-game4.away_team.elo))
    
    # test playoff with bye
    game5 = Game(sea, kc, playoff=True)
    distance = calc_distance(game5)
    assert (elo_team_adjustment(game5)
            == (game5.home_team.elo+48+25+round(distance*0.004)-game5.away_team.elo)*1.2)

def test_win_prob(team_objects):
    hou = team_objects[1]
    sea = team_objects[2]

    game = Game(hou, sea)
    distance = calc_distance(game)
    assert win_prob(game) == 1/(10**(-1*elo_team_adjustment(game)/400) + 1)

def test_postgame_elo_shift(team_objects):
    kc = team_objects[0]
    hou = team_objects[1]
    sea = team_objects[2]
    nyj = team_objects[3]
    nyg = team_objects[4]
    K = 20 # recommended k-factor

    # test home team thats predicted to win wins
    game1 = Game(nyg, hou)
    game1.away_points = 20
    game1.home_points = 35
    assert postgame_elo_shift(game1) == round(K*mov_multiplier(game1)*forcast_delta(game1))
    assert postgame_elo_shift(game1) > 0
    print(f'win win elo shift {postgame_elo_shift(game1)}')

    # test home team that's predicted to win loses
    game2 = Game(nyg, hou)
    game2.away_points = 30
    game2.home_points = 15
    assert postgame_elo_shift(game2) == round(K*mov_multiplier(game2)*forcast_delta(game2))
    assert postgame_elo_shift(game2) < 0
    print(f'win lose elo shift {postgame_elo_shift(game2)}')

    # test home team that's predicted to win ties
    game3 = Game(nyg, hou)
    game3.away_points = 30
    game3.home_points = 30
    assert postgame_elo_shift(game3) == round(K*mov_multiplier(game3)*forcast_delta(game3))
    assert postgame_elo_shift(game3) < 0
    print(f'win tie elo shift {postgame_elo_shift(game3)}')

    # test home team that's predicted to lose ties
    game4 = Game(hou, nyg)
    game4.away_points = 30
    game4.home_points = 30
    assert postgame_elo_shift(game4) == round(K*mov_multiplier(game4)*forcast_delta(game4))
    assert postgame_elo_shift(game4) > 0
    print(f'lose tie elo shift {postgame_elo_shift(game4)}')

def mov_multiplier(game):
    point_diff = game.home_points - game.away_points
    elo_diff = elo_team_adjustment(game) # calcs wrt home team
    if point_diff == 0:
        return 1.525
    else:
        return log(abs(point_diff)+1)*(2.2/(elo_diff*0.001+2.2))

def forcast_delta(game):
    win_probability = win_prob(game)
    if game.home_points == game.away_points:
        return 0.5 - win_probability
    elif game.home_points > game.away_points:
        return 1 - win_probability
    else:
        return 0 - win_probability

