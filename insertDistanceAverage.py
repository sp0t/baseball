import itertools
import math
from sqlalchemy import text
from database import database
import pandas as pd

engine = database.connect_to_db()
teams = ['OAK', 'PIT', 'SD', 'SEA', 'SF', 'STL', 'TB', 'TEX', 'TOR', 'MIN', 'PHI', 'ATL', 'CWS', 'MIA', 'NYY', 'MIL', 'LAA', 'AZ', 'BAL', 'BOS', 'CHC', 'CIN', 'CLE', 'COL', 'DET', 'HOU', 'KC', 'LAD', 'WSH', 'NYM']
seasons = ['2021', '2023']

for team in teams:
    print('======================================================')
    print('======================================================')
    print('======================================================')
    print(team)
    print('======================================================')
    print('======================================================')
    print('======================================================')
    for season in seasons:
        game_res = pd.read_sql(f"SELECT * FROM game_table WHERE (away_team = '{team}' OR home_team = '{team}') AND game_date LIKE '{season}%%';", con = engine).to_dict('records')
        for game in game_res:
            print(game)