import statsapi as mlb
from schedule import schedule


game_sched = mlb.schedule(start_date = "2023-10-01")
for game in game_sched:
    data = mlb.boxscore_data(game['game_id'])
    game_date = data['gameId'][:10]
    away_team = data['teamInfo']['away']['abbreviation']
    home_team = data['teamInfo']['home']['abbreviation']
    print(game_date, away_team, home_team)