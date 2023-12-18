from sqlalchemy import create_engine
import pandas as pd
import statsapi as mlb
from datetime import date, time, datetime, timedelta
from pytz import timezone
import numpy as np
from database import database

engine = database.connect_to_db()

# engine.execute("CREATE TABLE IF NOT EXISTS odds_table(game_id TEXT, game_date TEXT, away TEXT, home TEXT, start_time TEXT, away_open INT, away_close INT, home_open INT, home_close INT);")

df = pd.read_csv("MLB_Basic.csv")
data = df.T.to_dict('dict')

for el in data:
    print(data[el]['Game ID'])
    gameData = pd.read_sql(f"SELECT * FROM game_table WHERE game_id = '{data[el]['Game ID']}';", con = engine).to_dict('records')
    if(len(gameData) == 0):
        continue

    awayData = pd.read_sql(f"SELECT * FROM team_table WHERE team_abbr = '{data[el]['Away Team']}';", con = engine).to_dict('records')
    if(len(awayData) == 0):
        continue

    homeData = pd.read_sql(f"SELECT * FROM team_table WHERE team_abbr = '{data[el]['Home Team']}';", con = engine).to_dict('records')
    if(len(homeData) == 0):
        continue

    print(data[el]['Game ID'], gameData[0]['game_date'], data[el]['Away Team'], data[el]['Home Team'], int(data[el]['Away ML Open']), int(data[el]['Away ML Close']), int(data[el]['Home ML Open']), int(data[el]['Home ML Close']))

    engine.execute((f"INSERT INTO odds_table(game_id, game_date, away, home, away_open, away_close, home_open, home_close  VALUES('{data[el]['Game ID']}', '{gameData[0]['game_date']}', '{awayData[0]['team_name']}', '{homeData[0]['team_name']}', '{int(data[el]['Away ML Open'])}', '{int(data[el]['Away ML Close'])}', '{int(data[el]['Home ML Open'])}', '{int(data[el]['Home ML Close'])}');"))