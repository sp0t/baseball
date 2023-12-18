from sqlalchemy import create_engine
import pandas as pd
import statsapi as mlb
from datetime import date, time, datetime, timedelta
from pytz import timezone
import numpy as np
from database import database

def format_date(date_string):
    date = datetime.strptime(str(date_string), "%Y%m%d")
    return date.strftime("%Y/%m/%d")

engine = database.connect_to_db()

# engine.execute("CREATE TABLE IF NOT EXISTS odds_table(game_id TEXT, game_date TEXT, away TEXT, home TEXT, start_time TEXT, away_open INT, away_close INT, home_open INT, home_close INT);")

df = pd.read_csv("MLB_Basic.csv")
data = df.T.to_dict('dict')

for el in data:
    formatted_date = format_date(data[el]['Date'])
    print(formatted_date)
    gameData = pd.read_sql(f"SELECT * FROM game_table WHERE game_date = '{formatted_date}' AND away_team = '{data[el]['Away Team']}' AND home_team = '{data[el]['Home Team']}';", con = engine).to_dict('records')
    if(len(gameData) == 0):
        continue

    awayData = pd.read_sql(f"SELECT * FROM team_table WHERE team_abbr = '{data[el]['Away Team']}';", con = engine).to_dict('records')
    if(len(awayData) == 0):
        continue

    homeData = pd.read_sql(f"SELECT * FROM team_table WHERE team_abbr = '{data[el]['Home Team']}';", con = engine).to_dict('records')
    if(len(homeData) == 0):
        continue

    print(data[el]['Game ID'], formatted_date, data[el]['Away Team'], data[el]['Home Team'], int(data[el]['Away ML Open']), int(data[el]['Away ML Close']), int(data[el]['Home ML Open']), int(data[el]['Home ML Close']))
    if data[el]['Away ML Open'] == None or data[el]['Away ML Close'] == None or data[el]['Home ML Open'] == None or data[el]['Home ML Close'] == None:
        continue

    engine.execute((f"INSERT INTO odds_table(game_id, game_date, away, home, away_open, away_close, home_open, home_close) VALUES('{gameData[0]['game_id']}', '{gameData[0]['game_date']}', '{awayData[0]['team_name']}', '{homeData[0]['team_name']}', '{int(data[el]['Away ML Open'])}', '{int(data[el]['Away ML Close'])}', '{int(data[el]['Home ML Open'])}', '{int(data[el]['Home ML Close'])}');"))