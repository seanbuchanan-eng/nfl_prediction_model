import pytest
from elo_model import *
import main as m
from numpy import log

@pytest.fixture
def team_objects():
    kc = m.db.session.get(m.Team, 'KC')
    kc.elo = 1000
    hou = m.db.session.get(m.Team, 'HOU')
    hou.elo = 1250
    sea = m.db.session.get(m.Team, 'SEA')
    sea.elo = 1700
    sea.bye = True
    nyj = m.db.session.get(m.Team, 'NYJ')
    nyj.elo = 1550
    nyg = m.db.session.get(m.Team, 'NYG')
    nyg.elo = 1660
    return [kc, hou, sea, nyj, nyg]

@pytest.fixture
def game_objects():
    kcq = m.Game.query.filter_by(home_team_id='KC')
    houq = m.Game.query.filter_by(home_team_id='HOU')
    seaq = m.Game.query.filter_by(home_team_id='SEA')
    nyjq = m.Game.query.filter_by(home_team_id='NYJ')
    nygq = m.Game.query.filter_by(home_team_id='NYG')
    return [kcq, houq, seaq, nyjq, nygq]

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
    home_team = m.db.session.get(m.Team, game.home_team_id)
    away_team = m.db.session.get(m.Team, game.away_team_id)
    return get_distance(home_team.latitude,
                        home_team.longitude,
                        away_team.latitude,
                        away_team.longitude)

def test_elo_team_adjustment(team_objects, game_objects):
    kc = team_objects[0]
    hou = team_objects[1]
    sea = team_objects[2]
    nyj = team_objects[3]
    nyg = team_objects[4]
    kcq = game_objects[0]
    houq = game_objects[1]
    seaq = game_objects[2]
    nyjq = game_objects[3]
    nygq = game_objects[4]

    # same stadium teams
    game1 = nyjq.filter_by(away_team_id='NYG').first()
    assert elo_team_adjustment(game1) == -62

    # different stadium teams
    game2 = houq.filter_by(away_team_id='KC').first()
    distance = calc_distance(game2)
    assert (elo_team_adjustment(game2) 
            == (hou.elo+48+round(distance*0.004)-kc.elo))
    
    # test neutral location (arizona)
    game3 = houq.filter_by(away_team_id='KC').first()
    game3.neutral_destination_id = 'ARI'
    neutral_lat = m.db.session.get(m.Team, game3.neutral_destination_id).latitude
    neutral_long = m.db.session.get(m.Team, game3.neutral_destination_id).longitude
    home_distance = get_distance(hou.latitude,
                                 hou.longitude,
                                 neutral_lat,
                                 neutral_long)
    away_distance = get_distance(kc.latitude,
                                 kc.longitude,
                                 neutral_lat,
                                 neutral_long)
    assert (elo_team_adjustment(game3)
            == (hou.elo-round(home_distance*0.004)-(kc.elo-round(away_distance*0.004))))

    # test bye
    game4 = seaq.filter_by(away_team_id='NYJ').first()
    distance = calc_distance(game4)
    assert (elo_team_adjustment(game4)
            == (sea.elo+48+25+round(distance*0.004)-nyj.elo))
    
    # test playoff with bye
    game5 = seaq.filter_by(away_team_id='KC').first()
    game5.playoff = True
    distance = calc_distance(game5)
    assert (elo_team_adjustment(game5)
            == (sea.elo+48+25+round(distance*0.004)-kc.elo)*1.2)

def test_win_prob(team_objects, game_objects):
    hou = team_objects[1]
    sea = team_objects[2]
    houq = game_objects[1]
    seaq = game_objects[2]

    game = houq.filter_by(away_team_id='SEA').first()
    assert win_prob(game) == 1/(10**(-1*elo_team_adjustment(game)/400) + 1)

def test_postgame_elo_shift(game_objects):
    houq = game_objects[1]
    nygq = game_objects[4]
    K = 20 # recommended k-factor

    # test home team thats predicted to win wins
    game1 = nygq.filter_by(away_team_id='HOU').first()
    game1.away_points = 20
    game1.home_points = 35
    assert postgame_elo_shift(game1) == round(K*mov_multiplier(game1)*forcast_delta(game1))
    assert postgame_elo_shift(game1) > 0
    print(f'win win elo shift {postgame_elo_shift(game1)}')

    # test home team that's predicted to win loses
    game2 = nygq.filter_by(away_team_id='HOU').first()
    game2.away_points = 30
    game2.home_points = 15
    assert postgame_elo_shift(game2) == round(K*mov_multiplier(game2)*forcast_delta(game2))
    assert postgame_elo_shift(game2) < 0
    print(f'win lose elo shift {postgame_elo_shift(game2)}')

    # test home team that's predicted to win ties
    game3 = nygq.filter_by(away_team_id='HOU').first()
    game3.away_points = 30
    game3.home_points = 30
    assert postgame_elo_shift(game3) == round(K*mov_multiplier(game3)*forcast_delta(game3))
    assert postgame_elo_shift(game3) < 0
    print(f'win tie elo shift {postgame_elo_shift(game3)}')

    # test home team that's predicted to lose ties
    game4 = houq.filter_by(away_team_id='NYG').first()
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

