import statsapi as mlb
import pandas as pd
from datetime import date, time, datetime, timedelta
from database import database
from pytz import timezone


def get_schedule(): 
    
    engine = database.connect_to_db()
    try: 
        schedule = list(pd.read_sql('SELECT * FROM schedule', con = engine).T.to_dict().values())
    except: 
        schedule = get_schedule_from_mlb()
        return "Today's schedule can't be found. Try force-updating or waiting a few minutes to refresh!"
    
    res = mlb.get('teams', params = {'sportId': 1})['teams']
    team_dict = [{k:v for k,v in el.items() if k in ['name', 'teamName']} for el in res]
    team_dict = {el['name']:el['teamName'] for el in team_dict}
    
    for game in schedule: 
        game['home_name'] = team_dict[game['home_name']]
        game['away_name'] = team_dict[game['away_name']]
        
    
    return schedule

def get_rosters(game_id):
    data = mlb.boxscore_data(game_id)

    away_team_id = data['teamInfo']['away']['id']
    home_team_id = data['teamInfo']['home']['id']

    #away_roster = mlb.get('team_roster', params = {'teamId':away_team_id,'date':date.today()})['roster']
    away_roster = mlb.get('team_roster', params = {'teamId':away_team_id,'date':"2022-11-03"})['roster']
    away_roster = [el['person'] for el in away_roster]
    away_roster = [{k:v for k,v in el.items() if k!='link'} for el in away_roster]

    #home_roster = mlb.get('team_roster', params = {'teamId':home_team_id,'date':date.today()})['roster']
    home_roster = mlb.get('team_roster', params = {'teamId':home_team_id,'date':"2022-11-03"})['roster']
    home_roster = [el['person'] for el in home_roster]
    home_roster = [{k:v for k,v in el.items() if k!='link'} for el in home_roster]
    
    rosters = {'home': home_roster, 'away': away_roster}
    
    return rosters

def get_schedule_from_mlb():
    #game_sched = mlb.schedule(start_date = date.today())
    game_sched = mlb.schedule("2022-11-03")
    info_keys = ['game_id', 'game_datetime','away_name', 'home_name']
    game_sched = [{k:v for k,v in el.items() if k in info_keys} for el in game_sched]
    
    tz = timezone('US/Eastern')
    for el in game_sched: 
        el['game_datetime'] = el['game_datetime'].split('T')[1][:-1] 
        el['game_id'] = str(el['game_id'])
        el['game_datetime'] = datetime.strptime(el['game_datetime'], '%H:%M:%S')-timedelta(hours = 4)
        el['game_datetime'] = datetime.strftime(el['game_datetime'], '%H:%M:%S')
        
    game_sched = pd.DataFrame(game_sched)
    return game_sched

def update_schedule(): 
    
    engine = database.connect_to_db()
    engine.execute("DELETE FROM schedule")
    
    new_schedule = get_schedule_from_mlb()
    new_schedule.to_sql("schedule", con = engine, index = False, if_exists = 'replace')
    
    
    return

