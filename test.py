import statsapi as mlb
from schedule import schedule
import pandas as pd
from database import database

engine = database.connect_to_db()
game_sched = mlb.schedule(start_date = "2023-11-01")
for game in game_sched:
    data = mlb.boxscore_data(game['game_id'])
    game_date = data['gameId'][:10]
    away_team = data['teamInfo']['away']['abbreviation']
    home_team = data['teamInfo']['home']['abbreviation']
    print(game_date, away_team, home_team)
    away_res = pd.read_sql(f"SELECT * FROM (SELECT * FROM game_table WHERE away_team = '{data['teamInfo']['away']['abbreviation']}' or home_team = '{data['teamInfo']['away']['abbreviation']}' ORDER BY game_date DESC LIMIT 30) games INNER JOIN batter_table ON games.game_id = batter_table.game_id \ 
        WHERE (games.away_team='{data['teamInfo']['away']['abbreviation']}' AND batter_table.team = 'away') OR (games.home_team='{data['teamInfo']['away']['abbreviation']}' AND batter_table.team = 'home');", con = engine).to_dict('records')

    home_res = pd.read_sql(f"SELECT * FROM (SELECT * FROM game_table WHERE away_team = '{data['teamInfo']['home']['abbreviation']}' or home_team = '{data['teamInfo']['home']['abbreviation']}' ORDER BY game_date DESC LIMIT 30) games INNER JOIN batter_table ON games.game_id = batter_table.game_id \ 
        WHERE (games.away_team='{data['teamInfo']['home']['abbreviation']}' AND batter_table.team = 'away') OR (games.home_team='{data['teamInfo']['home']['abbreviation']}' AND batter_table.team = 'home');", con = engine).to_dict('records')


    print(away_res)
    print(home_res)