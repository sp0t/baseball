import statsapi as mlb
import pandas as pd
from datetime import date, time, datetime, timedelta
from database import databaseNHL
from API import nhlAPI
from functions import odds
from pytz import timezone
import math
from functions import modelInput 

def get_schedule(engine): 
    try: 
        schedule = list(pd.read_sql('SELECT * FROM schedule;', con = engine).T.to_dict().values())
    except: 
        schedule = get_schedule_from_nhl()
        return "Today's schedule can't be found. Try force-updating or waiting a few minutes to refresh!"

    for el in schedule:
        el['away_fcnn'] = 0
        el['home_fcnn'] = 0
        el['away_lr'] = 0
        el['home_lr'] = 0
        prediction = pd.read_sql(f"SELECT * FROM predictions WHERE game_id = '{el['game_id']}';", con = engine).to_dict('records')
        if len(prediction) != 0:
            for pr in prediction:
                if pr['model_type'] == 'fcnn_1':
                    el['away_fcnn'] = round(float(pr['away_team']), 2)
                    el['home_fcnn'] = round(1 - float(pr['away_team']), 2)
                elif pr['model_type'] == 'lr_1':
                    el['away_lr'] = round(float(pr['away_team']), 2)
                    el['home_lr'] = round(1 - float(pr['away_team']), 2)
                elif pr['model_type'] == 'rf_1':
                    el['away_rf'] = round(float(pr['away_team']), 2)
                    el['home_rf'] = round(1 - float(pr['away_team']), 2)

    return schedule

def get_schedule_from_nhl(engine):
    start_date = date.today()
    game_sched = nhlAPI.get_Daily_Scores_By_Date(date = date.today())
    games = game_sched['games']
    info_keys = ['game_id', 'game_datetime','away_name', 'home_name']
    
    for el in games:
        el['game_datetime'] = el['startTimeUTC'].split('T')[1][:-1] 
        el['game_id'] = str(el['id'])
        el['game_datetime'] = datetime.strptime(el['game_datetime'], '%H:%M:%S')
        offset_sign = 1 if el['easternUTCOffset'][0] == '+' else -1 
        offset_hours, offset_minutes = map(int,  el['easternUTCOffset'][1:].split(':'))
        time_offset = timedelta(hours=offset_hours * offset_sign, minutes=offset_minutes * offset_sign)
        el['game_datetime'] = el['game_datetime'] + time_offset
        el['game_datetime'] = el['game_datetime'].strftime('%H:%M:%S')
        el['away_name'] = el['awayTeam']['name']['default']
        el['home_name'] = el['homeTeam']['name']['default']
        modelInput.generate_model_input(el['game_id'], engine, 1)

    games = [{k:v for k,v in el.items() if k in info_keys} for el in games]    
    games = pd.DataFrame(games)
    return games

def update_schedule(): 
    
    engine = databaseNHL.connect_to_db()
    engine.execute("DELETE FROM schedule")
    
    new_schedule = get_schedule_from_nhl(engine)
    new_schedule.to_sql("schedule", con = engine, index = False, if_exists = 'replace')
    
    return