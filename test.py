
from logging import raiseExceptions
from datetime import datetime, date
import statsapi as mlb
from database import database
from sqlalchemy import create_engine


engine = create_engine('postgresql://postgres:123@ec2-18-180-226-162.ap-northeast-1.compute.amazonaws.com:5432/betmlb', 
                                connect_args = {'connect_timeout': 10}, 
                                echo=False, pool_size=20, max_overflow=0)
print('crone-start')

exec(open("./modify_atbat.py").read(), globals())

res = mlb.get('teams', params={'sportId':1})['teams']

team_dict = [{k:v for k,v in el.items() if k in ['name', 'abbreviation', 'clubName']} for el in res]

engine.execute("DROP TABLE IF EXISTS team_table;")
engine.execute("DROP TABLE IF EXISTS player_table;")

engine.execute("CREATE TABLE IF NOT EXISTS team_table(team_id TEXT, team_name TEXT, team_abbr TEXT, club_name TEXT);")
engine.execute("CREATE TABLE IF NOT EXISTS player_table(p_id TEXT, p_name TEXT, t_id TEXT);")


# team_data = request.get_json()

for el in team_dict:
    team_id = mlb.lookup_team(el['name'])[0]['id']

    engine.execute(f"INSERT INTO team_table(team_id, team_name, team_abbr, club_name) VALUES('{team_id}', '{el['name']}', '{el['abbreviation']}', '{el['clubName']}');") 
    
    team_roster = {}
    team_roster = mlb.get('team_roster', params = {'teamId':team_id, 'date':date.today()})['roster']
    team_roster = [el['person'] for el in team_roster]
    team_roster = [{k:v for k,v in el.items() if k!='link'} for el in team_roster]

    for item in team_roster:
        p_name = item['fullName'].replace("'", " ")
        engine.execute(f"INSERT INTO player_table(p_id, p_name, t_id) VALUES('{item['id']}', '{p_name}','{team_id}');") 