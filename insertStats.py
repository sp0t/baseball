import os
from database import database
from sqlalchemy import text
import pandas as pd
from datetime import date

dir = './MLB Games 2023'
dir_list = os.listdir(dir)
engine = database.connect_to_db()

engine.execute(text("CREATE TABLE IF NOT EXISTS batter_stats(game_id TEXT, game_date TEXT, player_id TEXT, career_atBats float8, career_avg float8, career_homeRuns float8, career_obp float8, career_ops float8, career_rbi float8, career_slg float8, career_strikeOuts float8, recent_atBats float8, recent_avg float8, recent_homeRuns float8, recent_obp float8, recent_ops float8, recent_rbi float8, recent_slg float8, recent_strikeOuts float8);"))
engine.execute(text("CREATE TABLE IF NOT EXISTS pitcher_stats(game_id TEXT, game_date TEXT, player_id TEXT, career_era float8, career_homeRuns float8, career_whip float8, career_battersFaced float8, recent_era float8, recent_homeRuns float8, recent_whip float8, recent_battersFaced float8);"))

# today = date.today()
# gamedate = today.strftime("%Y/%m/%d")
# print(gamedate)
for filename in dir_list:
    pathbreak = filename.split('_')
    role = pathbreak[0]
    idbreak = pathbreak[1].split('.')
    gameid = idbreak[0]
    filepath = dir + '/' + filename

    data = pd.read_csv(filepath, index_col ="index")


    result = engine.execute(text(f"SELECT * FROM game_table WHERE game_id = '{gameid}';")).fetchall()
    gamedate =  result[0][1]

    if role == 'BatterData':
        data.drop(data.iloc[:, 0:3], inplace=True, axis=1)
        for index, row in data.iterrows():
            engine.execute(text(f"INSERT INTO batter_stats(game_id, game_date, player_id, career_atBats, career_avg, career_homeRuns, career_obp, career_ops, career_rbi, career_slg, career_strikeOuts, recent_atBats, recent_avg, recent_homeRuns, recent_obp, recent_ops, recent_rbi, recent_slg, recent_strikeOuts) \
                                VALUES('{gameid}', '{gamedate}', '{int(row['player_id'])}', '{round(row['career_atBats'], 3)}', '{round(row['career_avg'], 3)}', '{round(row['career_homeRuns'], 3)}', '{round(row['career_obp'], 3)}', '{round(row['career_ops'], 3)}', '{round(row['career_rbi'], 3)}', '{round(row['career_slg'], 3)}', '{round(row['career_strikeOuts'], 3)}', '{round(row['recent_atBats'], 3)}', '{round(row['recent_avg'], 3)}', '{round(row['recent_homeRuns'], 3)}', '{round(row['recent_obp'], 3)}', '{round(row['recent_ops'], 3)}', '{round(row['recent_rbi'], 3)}', '{round(row['recent_slg'], 3)}', '{round(row['recent_strikeOuts'], 3)}');"))

    if role == 'PitcherData':
        data.drop(data.iloc[:, 0:3], inplace=True, axis=1)
        pitchers = data.T
        for index, row in pitchers.iterrows():
            insertquery = f"INSERT INTO pitcher_stats(game_id, game_date, player_id, career_era, career_homeRuns, career_whip, career_battersFaced, recent_era, recent_homeRuns, recent_whip, recent_battersFaced)"
            engine.execute(text(f"INSERT INTO pitcher_stats(game_id, game_date, player_id, career_era, career_homeRuns, career_whip, career_battersFaced, recent_era, recent_homeRuns, recent_whip, recent_battersFaced) \
                                VALUES('{gameid}', '{gamedate}', '{int(row['player_id'])}', '{round(row['career_era'], 3)}', '{round(row['career_homeRuns'], 3)}', '{round(row['career_whip'], 3)}', '{round(row['career_battersFaced'], 3)}', '{round(row['recent_era'], 3)}', '{round(row['recent_homeRuns'], 3)}', '{round(row['recent_whip'], 3)}', '{round(row['recent_battersFaced'], 3)}');"))