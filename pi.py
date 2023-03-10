input_team_name_2 = 'Philadelphia Phillies'
input_team_name_1 = 'Houston Astros'
team = "away"
player_name = 'Ranger Suarez'
game_id = '715720'

from datetime import date, time, datetime, timedelta
import numpy as np
import pandas as pd
import statsapi as mlb
from sqlalchemy import create_engine


engine = create_engine('postgresql://postgres:lucamlb123@ec2-3-115-115-146.ap-northeast-1.compute.amazonaws.com:5432/betmlb', connect_args = {'connect_timeout': 10}, echo=False, pool_size=20, max_overflow=0)
# res = pd.read_sql(f"SELECT * FROM schedule WHERE away_name = '{input_team_name_1}' and home_name = '{input_team_name_2}'", con = engine).iloc[0]
# game_id = res['game_id']

data = mlb.boxscore_data(game_id)

away_team_id = data['teamInfo']['away']['id']
home_team_id = data['teamInfo']['home']['id']
away_roster = mlb.get('team_roster', params = {'teamId':away_team_id,'date':date.today()})['roster']
away_roster = [el['person'] for el in away_roster]
away_roster = [{k:v for k,v in el.items() if k!='link'} for el in away_roster]
home_roster = mlb.get('team_roster', params = {'teamId':home_team_id,'date':date.today()})['roster']
home_roster = [el['person'] for el in home_roster]
home_roster = [{k:v for k,v in el.items() if k!='link'} for el in home_roster]  
rosters = home_roster + away_roster
player_id = [x['id'] for x in rosters if x['fullName'] == player_name][0]

df = pd.read_sql("SELECT b.game_id, b.game_date, b.home_team, b.away_team, b.home_score, b.away_score, (a.atbats)atBats, "
            "(a.baseonballs)baseonBalls, a.blownsaves, a.doubles, (a.earnedruns)earnedRuns, a.era, a.hits, a.holds, (a.homeruns)homeRuns, "
            "(a.inningspitched)inningsPitched, a.losses, (a.pitchesthrown)pitchesThrown, (a.playerid)playerId, a.rbi, a.runs, (a.strikeouts)strikeOuts, "
            "a.strikes, a.triples, a.whip, a.wins FROM pitcher_table a LEFT JOIN game_table b ON a.game_id = b.game_id WHERE a.playerid = '%s' ORDER BY game_date DESC LIMIT 15;" %(player_id), con = engine)

string_cols = [col for col in df.columns if 'id' in col.lower()] + ['game_date', 'away_team', 'home_team']

player_df = df.loc[:,:]

player_df[string_cols] = df[string_cols].astype(str)
non_string_cols = [col for col in df.columns if col not in string_cols]
player_df[non_string_cols] = df[non_string_cols].astype(float)
player_df['game_date'] = pd.to_datetime(df['game_date'])
rename_dict = {'pitchesthrown': 'pitchesThrown', 'playerid': 'playerId', 'strikeouts': 'strikeOuts', 
        'baseonballs': 'baseOnBalls', 'homeruns': 'homeRuns', 'atbats': 'atBats', 
        'inningspitched': 'inningsPitched', 'earnedruns': 'earnedRuns'
        }

new_col_names = []

for col in player_df.columns: 
    for k,v in rename_dict.items(): 
        col = col.replace(k,v)
    new_col_names.append(col)
player_df.columns = new_col_names

player_df = player_df.reset_index(drop = True)

print(player_df)