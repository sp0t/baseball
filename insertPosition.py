# Dependencies
import statsapi as mlb
import time
from datetime import date, timedelta, datetime
import numpy as np
import pandas as pd
import sqlite3
from database import database
from sqlalchemy import text
import csv
import requests
from schedule import schedule
import pickle
import joblib
import requests

engine = database.connect_to_db()
engine.execute(text("CREATE TABLE IF NOT EXISTS position(game_id TEXT, game_date TEXT, team TEXT, role TEXT, C TEXT, B1 TEXT, B2 TEXT, B3 TEXT, SS TEXT, LF TEXT, CF TEXT, RF TEXT, DH TEXT);"))


year = datetime.now().year
res_game = pd.read_sql(text(f"SELECT * FROM game_table WHERE game_date LIKE '{year}%';"), con = engine).to_dict('records')

for game in res_game:
    print(game['game_id'], game['game_date'])
    data = mlb.boxscore_data(game['game_id'])
    awayBatters = data['awayBatters']
    homeBatters = data['homeBatters']
    gamedate = data['gameId'][0:10]
    away = data['teamInfo']['away']['abbreviation']
    home = data['teamInfo']['home']['abbreviation']

    for batter in awayBatters:
        if batter['personId'] != 0 and batter['substitution'] == False:
            url = f"https://statsapi.mlb.com/api/v1/people/{batter['personId']}"
            response = requests.get(url)
            if response.status_code == 200:
                result = response.json()
                hander = result['people'][0]['batSide']['code']
            else:
                hander = 'R'

            if batter['position'] == 'C':
                away_c = f"{batter['name'].replace("'", " ")}-{hander}"
            elif batter['position'] == '1B':
                away_b1 = f"{batter['name'].replace("'", " ")}-{hander}"
            elif batter['position'] == '2B':
                away_b2 = f"{batter['name'].replace("'", " ")}-{hander}"
            elif batter['position'] == '3B':
                away_b3 = f"{batter['name'].replace("'", " ")}-{hander}"
            elif batter['position'] == 'SS':
                away_ss = f"{batter['name'].replace("'", " ")}-{hander}"
            elif batter['position'] == 'LF':
                away_lf = f"{batter['name'].replace("'", " ")}-{hander}"
            elif batter['position'] == 'CF':
                away_cf = f"{batter['name'].replace("'", " ")}-{hander}"
            elif batter['position'] == 'RF':
                away_rf = f"{batter['name'].replace("'", " ")}-{hander}"
            elif batter['position'] == 'DH':
                away_dh = f"{batter['name'].replace("'", " ")}-{hander}"




    engine.execute(text(f"INSERT INTO position(game_id, game_date, team, role, c, b1, b2, b3, ss, lf, cf, rf, dh) \
                                    VALUES('{game['game_id']}', '{gamedate}', '{away}', 'away', '{away_c}', '{away_b1}', '{away_b2}', '{away_b3}', '{away_ss}', '{away_lf}', '{away_cf}', '{away_rf}', '{away_dh}');"))
    for batter in homeBatters:
        if batter['personId'] != 0 and batter['substitution'] == False:
            url = f"https://statsapi.mlb.com/api/v1/people/{batter['personId']}"
            response = requests.get(url)
            if response.status_code == 200:
                result = response.json()
                hander = result['people'][0]['batSide']['code']
            else:
                hander = 'R'

            if batter['position'] == 'C':
                home_c = f"{batter['name'].replace("'", " ")}-{hander}"
            elif batter['position'] == '1B':
                home_b1 = f"{batter['name'].replace("'", " ")}-{hander}"
            elif batter['position'] == '2B':
                home_b2 = f"{batter['name'].replace("'", " ")}-{hander}"
            elif batter['position'] == '3B':
                home_b3 = f"{batter['name'].replace("'", " ")}-{hander}"
            elif batter['position'] == 'SS':
                home_ss = f"{batter['name'].replace("'", " ")}-{hander}"
            elif batter['position'] == 'LF':
                home_lf = f"{batter['name'].replace("'", " ")}-{hander}"
            elif batter['position'] == 'CF':
                home_cf = f"{batter['name'].replace("'", " ")}-{hander}"
            elif batter['position'] == 'RF':
                home_rf = f"{batter['name'].replace("'", " ")}-{hander}"
            elif batter['position'] == 'DH':
                home_dh = f"{batter['name'].replace("'", " ")}-{hander}"

    engine.execute(text(f"INSERT INTO position(game_id, game_date, team, role, c, b1, b2, b3, ss, lf, cf, rf, dh) \
                                    VALUES('{game['game_id']}', '{gamedate}', '{home}', 'home', '{home_c}', '{home_b1}', '{home_b2}', '{home_b3}', '{home_ss}', '{home_lf}', '{home_cf}', '{home_rf}', '{home_dh}');"))

