import itertools
import math
from sqlalchemy import text
from database import database
import pandas as pd

engine = database.connect_to_db()
teams = ['OAK', 'PIT', 'SD', 'SEA', 'SF', 'STL', 'TB', 'TEX', 'TOR', 'MIN', 'PHI', 'ATL', 'CWS', 'MIA', 'NYY', 'MIL', 'LAA', 'AZ', 'BAL', 'BOS', 'CHC', 'CIN', 'CLE', 'COL', 'DET', 'HOU', 'KC', 'LAD', 'WSH', 'NYM']
seasons = ['2023']

engine.execute(text("CREATE TABLE IF NOT EXISTS distance_average_table(team TEXT, season TEXT, distance FLOAT);"))

for team in teams:
    for season in seasons:
        distance = 0
        count = 0
        state = False
        pre_away_team = ''
        pre_home_team = ''
        game_res = pd.read_sql(f"SELECT * FROM game_table WHERE (away_team = '{team}' OR home_team = '{team}') AND game_date LIKE '{season}%%';", con = engine).to_dict('records')
        for game in game_res:
            print('current', game['away_team'], game['home_team'])
            if game['away_team'] == team:
                count = count + 1
                state = True
                if pre_away_team == '' or pre_home_team == '' or pre_home_team == team:
                    print('===================1')
                    team1 = team
                    team2 = game['home_team']
                elif pre_away_team == team:
                    print('===================2')
                    team1 = game['home_team']
                    team2 = pre_home_team
            elif game['home_team'] == team:
                if pre_away_team == '' or pre_home_team == '' or pre_home_team == team:
                    print('===================3')
                    state = False
                elif pre_away_team == team:
                    print('===================4')

                    count = count + 1
                    state = True
                    team1 = team
                    team2 = pre_home_team

            if state == True:
                print(team1, team2)
                distance_res = pd.read_sql(f"SELECT * FROM distance_table WHERE (team1 = '{team1}' AND team2 = '{team2}') OR (team1 = '{team2}' AND team2 = '{team1}');", con = engine).to_dict('records')
                
                print(distance_res)
            pre_away_team = game['away_team']
            pre_home_team = game['home_team']
            print('before', pre_away_team, pre_home_team)
            