# go through previous seasons and calcuate the elo

from main import db, Team, Game, Season, Week
from elo_model import postgame_elo_shift, pre_season_elo, elo_team_adjustment
seasons = Season.query.all()
for idx, season in enumerate(seasons):
    if idx == 0:
        for team in Team.query.all():
            team.elo = 1505
        db.session.commit()
    else:
        for team in Team.query.all():
            team.elo = pre_season_elo(team)
        db.session.commit()
    weeks = season.weeks
    for week in weeks:
        games = week.games
        for game in games:
            home_team = db.session.get(Team, game.home_team_id)
            away_team = db.session.get(Team, game.away_team_id)
            pregame_elo_shift = elo_team_adjustment(game)
            elo_shift = postgame_elo_shift(game)
            game.home_pregame_elo = home_team.elo + pregame_elo_shift
            game.away_pregame_elo = away_team.elo - pregame_elo_shift
            home_team.elo += elo_shift
            away_team.elo -= elo_shift
        db.session.commit()