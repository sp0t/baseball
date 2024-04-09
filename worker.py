from passlib.hash import sha256_crypt
import statsapi as mlb
import pandas as pd
from datetime import date, time, datetime, timedelta
from database import database
from pytz import timezone
from functions import batting, predict, starters, smartContract, sanitycheck, odds
from schedule import schedule
import requests
from sqlalchemy import text
from functions_c import batting_c, starters_c, predict_c
import psycopg2
from io import StringIO
import statsapi as mlb
from datetime import date, datetime, timedelta
import time
import pandas as pd
from pytz import timezone
import psycopg2.extras as extras
from sqlalchemy import create_engine
import uuid
import requests


engine = database.connect_to_db()
game_sched = mlb.schedule(start_date = date.today())
#testcommit
# game_sched = mlb.schedule(start_date = "2024-04-04")
info_keys = ['game_id', 'game_datetime','away_name', 'home_name']
game_sched = [{k:v for k,v in el.items() if k in info_keys} for el in game_sched]
game_date = ''

print(game_sched)

if len(game_sched) > 0:
    game_date = game_sched[0]['game_datetime'][0:10]
    date_obj = datetime.strptime(game_date, "%Y-%m-%d")
    game_date = date_obj.strftime("%Y/%m/%d") 

tz = timezone('US/Eastern')
for el in game_sched:
    engine.execute(f"INSERT INTO odds_table(game_id, game_date, away, home, start_time, away_open, away_close, home_open, home_close, state) VALUES('{el['game_id']}', '{game_date}', '{el['away_name']}', '{el['home_name']}', '{el['game_datetime']}', '0', '0', '0', '0', '0');") 