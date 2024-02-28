from sqlalchemy import create_engine
import pandas as pd
import statsapi as mlb
from datetime import date, time, datetime, timedelta
from pytz import timezone
import numpy as np
from database import database
from schedule import schedule


game_sched = mlb.schedule(start_date = date.today())
print(game_sched)
#testcommit
# game_sched = mlb.schedule(start_date = "2023-11-01")
info_keys = ['game_id', 'game_datetime','away_name', 'home_name']

game_sched = [{k:v for k,v in el.items() if k in info_keys} for el in game_sched]

tz = timezone('US/Eastern')
for el in game_sched: 
    el['game_datetime'] = el['game_datetime'].split('T')[1][:-1] 
    el['game_id'] = str(el['game_id'])
    # el['game_datetime'] = datetime.strptime(el['game_datetime'], '%H:%M:%S')-timedelta(hours = 3)
    el['game_datetime'] = datetime.strptime(el['game_datetime'], '%H:%M:%S')
    el['game_datetime'] = datetime.strftime(el['game_datetime'], '%H:%M:%S')
    
game_sched = pd.DataFrame(game_sched)
print(game_sched)