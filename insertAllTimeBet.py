from database import databaseNHL
import pandas as pd
import csv
from datetime import datetime

engine = databaseNHL.connect_to_db()
engine.execute("CREATE TABLE IF NOT EXISTS betting_table(id SERIAL PRIMARY KEY, betdate TEXT, away TEXT, home TEXT, place TEXT, market TEXT, site TEXT, odds TEXT, stake TEXT, wins TEXT, result TEXT);")
engine.execute("CREATE TABLE IF NOT EXISTS graph_table(id SERIAL PRIMARY KEY, betdate TEXT, away TEXT, home TEXT, place TEXT, result TEXT, ncount TEXT, wcount TEXT, run_win TEXT, risk TEXT, pl TEXT);")

df = pd.read_csv('3.csv').to_dict('records')
for row in df:
    away_res = pd.read_sql(f"SELECT * FROM team_table WHERE team_abbr = '{row['away']}'", con = engine).to_dict('records')
    if len(away_res) == 0:
        away_name = row['away']
    else:
        away_name = away_res[0]['team_name']
    
    home_res = pd.read_sql(f"SELECT * FROM team_table WHERE team_abbr = '{row['home']}'", con = engine).to_dict('records')

    if len(home_res) == 0:
        home_name = row['home']
    else:
        home_name = home_res[0]['team_name']

    if row['home'] == 'away':
        place = away_name
    else:
        place = home_name

    date_obj = datetime.strptime(row['date'], "%m/%d/%Y")
    
    betdate = date_obj.strftime("%Y-%m-%d")

    if betdate > "2024-12-13":
        engine.execute("INSERT INTO betting_table(betdate, away, home, place, market, site, odds, stake, wins, result) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (betdate, away_name, home_name, place, row['market'], row['site'], row['odds'], row['stake'], row['wins'], row['result']))
        engine.execute("INSERT INTO graph_table(betdate, away, home, place, result, ncount, wcount, run_win, risk, pl) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (betdate, away_name, home_name, place, row['result'], row['ncount'], row['wcount'], row['run_win'], row['risk'], row['pl']))


    