from passlib.hash import sha256_crypt
import statsapi as mlb
import pandas as pd
from datetime import date, time, datetime, timedelta
from database import database
from pytz import timezone
from zoneinfo import ZoneInfo


game_sched = mlb.schedule(start_date = date.today())
#testcommit
# game_sched = mlb.schedule(start_date = "2023-11-01")
info_keys = ['game_id', 'game_datetime','away_name', 'home_name']
game_sched = [{k:v for k,v in el.items() if k in info_keys} for el in game_sched]
    
tz = timezone('America/New_York')
for el in game_sched: 
    el['game_datetime'] = el['game_datetime'].split('T')[1][:-1] 
    el['game_id'] = str(el['game_id'])
    el['game_datetime'] = datetime.strptime(el['game_datetime'], '%H:%M:%S')
    el['game_datetime'] = el['game_datetime'].astimezone(tz) 
    el['game_datetime'] = datetime.strftime(el['game_datetime'], '%H:%M:%S')
    print(el['game_datetime'])
