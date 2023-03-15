import statsapi as mlb
import pandas as pd
from datetime import date, time, datetime, timedelta


data = mlb.boxscore_data('719146')
away_roster = mlb.get('team_roster', params = {'teamId':'116','date':date.today()})['roster']
home_roster = mlb.get('team_roster', params = {'teamId':'110','date':date.today()})['roster']
res = mlb.get('teams', params={'sportId':1})['teams']
team_dict = [{k:v for k,v in el.items() if k in ['name', 'abbreviation', 'clubName']} for el in res]

# for el in team_dict:
#     team_id = mlb.lookup_team(el['name'])[0]['id']
#     print(team_id, el['name'])

team_roster = mlb.get('team_roster', params = {'teamId':147, 'date':"2022-10-14"})['roster']
team_roster = [el['person'] for el in team_roster]
team_roster = [{k:v for k,v in el.items() if k!='link'} for el in team_roster]


for item in team_roster:
    p_name = item['fullName'].replace("'", " ")
    print(p_name)