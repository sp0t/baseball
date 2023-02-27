from datetime import date, time, datetime, timedelta
import numpy as np
import pandas as pd
import statsapi as mlb
from sqlalchemy import create_engine

engine = create_engine('postgresql://postgres:123@ec2-18-180-226-162.ap-northeast-1.compute.amazonaws.com:5432/betmlb', 
                                connect_args = {'connect_timeout': 10}, 
                                echo=False, pool_size=20, max_overflow=0)

away_name = 'West Virginia Mountaineers'
home_name = 'Arizona Diamondbacks'
game_id = '719466'
away_state = True
home_state = True
data = mlb.boxscore_data(game_id)

away_Id = data['teamInfo']['away']['id']
home_Id = data['teamInfo']['home']['id']

print(away_Id)
print(home_Id)


away_abbr = data['teamInfo']['away']['abbreviation']
home_abbr = data['teamInfo']['home']['abbreviation']
away_club = data['teamInfo']['away']['teamName']
home_club = data['teamInfo']['home']['teamName']


engine.execute(f"INSERT INTO team_table(team_id, team_name, team_abbr, club_name) VALUES('{away_Id}', '{away_name}', '{away_abbr}', '{away_club}');") 


engine.execute(f"INSERT INTO team_table(team_id, team_name, team_abbr, club_name) VALUES('{home_Id}', '{home_name}', '{home_abbr}', '{home_club}');") 


away_roster = mlb.get('team_roster', params = {'teamId':away_Id,'date':date.today()})['roster']
away_roster = [el['person'] for el in away_roster]
away_roster = [{k:v for k,v in el.items() if k!='link'} for el in away_roster]
for el in away_roster:
    engine.execute(f"INSERT INTO player_table(p_id, p_name, t_id) VALUES('{el['id']}', '{el['fullName']}','{away_Id}');") 


home_roster = mlb.get('team_roster', params = {'teamId':home_Id,'date':date.today()})['roster']
home_roster = [el['person'] for el in home_roster]
home_roster = [{k:v for k,v in el.items() if k!='link'} for el in home_roster]  
for el in home_roster:
    engine.execute(f"INSERT INTO player_table(p_id, p_name, t_id) VALUES('{el['id']}', '{el['fullName']}','{home_Id}');")  

print('end')
