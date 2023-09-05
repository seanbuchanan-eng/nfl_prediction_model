import pytest
from elo_model import *
import sqlite3
from numpy import log

conn = sqlite3.connect('db.sqlite')
cur = conn.cursor()

# cur.execute("UPDATE Teams SET elo = 1505")

@pytest.fixture
def kc_object():
    result = cur.execute("SELECT * FROM Teams WHERE ticker = 'KC'").fetchall()[0]
    return result

@pytest.fixture
def hou_object():
    result = cur.execute("SELECT * FROM Teams WHERE ticker = 'HOU'").fetchall()[0]
    return result

@pytest.fixture
def sea_object():
    result = cur.execute("SELECT * FROM Teams WHERE ticker = 'SEA'").fetchall()[0]
    return result

@pytest.fixture
def nyj_object():
    result = cur.execute("SELECT * FROM Teams WHERE ticker = 'NYJ'").fetchall()[0]
    return result

@pytest.fixture
def nyg_object():
    result = cur.execute("SELECT * FROM Teams WHERE ticker = 'NYG'").fetchall()[0]
    return result

# @pytest.fixture
# def game_objects():
#     kcq = m.Game.query.filter_by(home_team_id='KC')
#     houq = m.Game.query.filter_by(home_team_id='HOU')
#     seaq = m.Game.query.filter_by(home_team_id='SEA')
#     nyjq = m.Game.query.filter_by(home_team_id='NYJ')
#     nygq = m.Game.query.filter_by(home_team_id='NYG')
#     return [kcq, houq, seaq, nyjq, nygq]

def test_get_distance(kc_object, hou_object, sea_object, nyg_object, nyj_object):

    # different stadium teams
    assert round(get_distance(kc_object[3], 
                              kc_object[4],  
                              hou_object[3],
                              hou_object[4])) == 648
    # same stadium team
    assert round(get_distance(nyj_object[3],
                              nyj_object[4],
                              nyg_object[3],
                              nyg_object[4])) == 0
    
def calc_distance(home_team, away_team):
    return get_distance(home_team[3],
                        home_team[4],
                        away_team[3],
                        away_team[4])

def test_elo_team_adjustment(kc_object, hou_object, sea_object, nyg_object, nyj_object):

    # same stadium teams
    # game1 = nyjq.filter_by(away_team_id='NYG').first()
    game1 = cur.execute("""SELECT home_team, away_team, playoffs, neutral_destination
                        FROM Games WHERE home_team = 'New York Jets' 
                        and away_team = 'New York Giants'""").fetchone()
    assert elo_team_adjustment(*game1, cur) == -28

    # # different stadium teams
    # game2 = houq.filter_by(away_team_id='KC').first()
    game2 = cur.execute("""SELECT home_team, away_team, playoffs, neutral_destination
                        FROM Games WHERE home_team = 'Houston Texans' 
                        and away_team = 'Kansas City Chiefs'""").fetchone()
    distance = calc_distance(hou_object, kc_object)
    assert (elo_team_adjustment(*game2, cur) 
            == (hou_object[5]+48+round(distance*0.004)-kc_object[5]))
    
    # # test neutral location (arizona)
    cur.execute("UPDATE Games SET neutral_destination = 'ARI' WHERE id = ?", (game2[0],))
    game3 = cur.execute("""SELECT home_team, away_team, playoffs, neutral_destination
                        FROM Games WHERE home_team = 'Houston Texans' 
                        and away_team = 'Kansas City Chiefs'""").fetchone()
    neutral_lat, neutral_long = cur.execute("SELECT latitude, longitude FROM Teams WHERE ticker = 'ARI'").fetchall()[0]
    home_distance = get_distance(hou_object[3],
                                 hou_object[4],
                                 neutral_lat,
                                 neutral_long)
    away_distance = get_distance(kc_object[3],
                                 kc_object[4],
                                 neutral_lat,
                                 neutral_long)
    assert (elo_team_adjustment(*game3, cur)
            == (hou_object[5]-round(home_distance*0.004)-(kc_object[5]-round(away_distance*0.004))))

    # # test bye
    # game4 = seaq.filter_by(away_team_id='NYJ').first()
    # distance = calc_distance(game4)
    # assert (elo_team_adjustment(game4)
    #         == (sea.elo+48+25+round(distance*0.004)-nyj.elo))
    
    # # test playoff with bye
    # game5 = seaq.filter_by(away_team_id='KC').first()
    # game5.playoff = True
    # distance = calc_distance(game5)
    # assert (elo_team_adjustment(game5)
    #         == (sea.elo+48+25+round(distance*0.004)-kc.elo)*1.2)

# def test_win_prob(team_objects, game_objects):
#     hou = team_objects[1]
#     sea = team_objects[2]
#     houq = game_objects[1]
#     seaq = game_objects[2]

#     game = houq.filter_by(away_team_id='SEA').first()
#     assert win_prob(game) == 1/(10**(-1*elo_team_adjustment(game)/400) + 1)

# def test_postgame_elo_shift(game_objects):
#     houq = game_objects[1]
#     nygq = game_objects[4]
#     K = 20 # recommended k-factor

#     # test home team thats predicted to win wins
#     game1 = nygq.filter_by(away_team_id='HOU').first()
#     game1.away_points = 20
#     game1.home_points = 35
#     assert postgame_elo_shift(game1) == round(K*mov_multiplier(game1)*forcast_delta(game1))
#     assert postgame_elo_shift(game1) > 0
#     print(f'win win elo shift {postgame_elo_shift(game1)}')

#     # test home team that's predicted to win loses
#     game2 = nygq.filter_by(away_team_id='HOU').first()
#     game2.away_points = 30
#     game2.home_points = 15
#     assert postgame_elo_shift(game2) == round(K*mov_multiplier(game2)*forcast_delta(game2))
#     assert postgame_elo_shift(game2) < 0
#     print(f'win lose elo shift {postgame_elo_shift(game2)}')

#     # test home team that's predicted to win ties
#     game3 = nygq.filter_by(away_team_id='HOU').first()
#     game3.away_points = 30
#     game3.home_points = 30
#     assert postgame_elo_shift(game3) == round(K*mov_multiplier(game3)*forcast_delta(game3))
#     assert postgame_elo_shift(game3) < 0
#     print(f'win tie elo shift {postgame_elo_shift(game3)}')

#     # test home team that's predicted to lose ties
#     game4 = houq.filter_by(away_team_id='NYG').first()
#     game4.away_points = 30
#     game4.home_points = 30
#     assert postgame_elo_shift(game4) == round(K*mov_multiplier(game4)*forcast_delta(game4))
#     assert postgame_elo_shift(game4) > 0
#     print(f'lose tie elo shift {postgame_elo_shift(game4)}')

# def mov_multiplier(game):
#     point_diff = game.home_points - game.away_points
#     elo_diff = elo_team_adjustment(game) # calcs wrt home team
#     if point_diff == 0:
#         return 1.525
#     else:
#         return log(abs(point_diff)+1)*(2.2/(elo_diff*0.001+2.2))

# def forcast_delta(game):
#     win_probability = win_prob(game)
#     if game.home_points == game.away_points:
#         return 0.5 - win_probability
#     elif game.home_points > game.away_points:
#         return 1 - win_probability
#     else:
#         return 0 - win_probability

