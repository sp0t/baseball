import os
from database import database
from sqlalchemy import text
import pandas as pd
from datetime import date

dir = './MLB Games 2023'
dir_list = os.listdir(dir)
engine = database.connect_to_db()

# engine.execute(text("CREATE TABLE IF NOT EXISTS batter_stats(game_id TEXT, game_date TEXT, position TEXT, player_id TEXT, career_atBats float8, career_avg float8, career_homeRuns float8, career_obp float8, career_ops float8, career_rbi float8, career_slg float8, career_strikeOuts float8, recent_atBats float8, recent_avg float8, recent_homeRuns float8, recent_obp float8, recent_ops float8, recent_rbi float8, recent_slg float8, recent_strikeOuts float8);"))
# engine.execute(text("CREATE TABLE IF NOT EXISTS pitcher_stats(game_id TEXT, game_date TEXT, position TEXT, player_id TEXT, career_era float8, career_homeRuns float8, career_whip float8, career_battersFaced float8, recent_era float8, recent_homeRuns float8, recent_whip float8, recent_battersFaced float8);"))
engine.execute(text("CREATE TABLE IF NOT EXISTS win_percent(game_id TEXT, game_date TEXT, away_prob_a float8 default 0, home_prob_a float8 default 0, away_prob_b float8 default 0, home_prob_b float8 default 0);"))

# today = date.today()
# gamedate = today.strftime("%Y/%m/%d")
# print(gamedate)
# for filename in dir_list:
#     pathbreak = filename.split('_')
#     role = pathbreak[0]
#     idbreak = pathbreak[1].split('.')
#     gameid = idbreak[0]
#     filepath = dir + '/' + filename

#     data = pd.read_csv(filepath, index_col ="index")


#     result = engine.execute(text(f"SELECT * FROM game_table WHERE game_id = '{gameid}';")).fetchall()
#     gamedate =  result[0][1]

#     if role == 'BatterData':
#         data.drop(data.iloc[:, 0:3], inplace=True, axis=1)
#         for index, row in data.iterrows():
#             engine.execute(text(f"INSERT INTO batter_stats(game_id, game_date, position, player_id, career_atBats, career_avg, career_homeRuns, career_obp, career_ops, career_rbi, career_slg, career_strikeOuts, recent_atBats, recent_avg, recent_homeRuns, recent_obp, recent_ops, recent_rbi, recent_slg, recent_strikeOuts) \
#                                 VALUES('{gameid}', '{gamedate}', '{index}', '{int(row['player_id'])}', '{round(float(row['career_atBats']), 3)}', '{round(float(row['career_avg']), 3)}', '{round(float(row['career_homeRuns']), 3)}', '{round(float(row['career_obp']), 3)}', '{round(float(row['career_ops']), 3)}', '{round(float(row['career_rbi']), 3)}', '{round(float(row['career_slg']), 3)}', '{round(float(row['career_strikeOuts']), 3)}', '{round(float(row['recent_atBats']), 3)}', '{round(float(row['recent_avg']), 3)}', '{round(float(row['recent_homeRuns']), 3)}', '{round(float(row['recent_obp']), 3)}', '{round(float(row['recent_ops']), 3)}', '{round(float(row['recent_rbi']), 3)}', '{round(float(row['recent_slg']), 3)}', '{round(float(row['recent_strikeOuts']), 3)}') \
#                                     ON CONFLICT ON CONSTRAINT unique_game_player DO UPDATE SET game_date = excluded.game_date, career_atBats = excluded.career_atBats, career_avg = excluded.career_avg, career_homeRuns = excluded.career_homeRuns, career_obp = excluded.career_obp, career_ops = excluded.career_ops, career_rbi = excluded.career_rbi, career_slg = excluded.career_slg, career_strikeOuts = excluded.career_strikeOuts, \
#                                     recent_atBats = excluded.recent_atBats, recent_avg = excluded.recent_avg, recent_homeRuns = excluded.recent_homeRuns, recent_obp = excluded.recent_obp, recent_ops = excluded.recent_ops, recent_rbi = excluded.recent_rbi, recent_slg = excluded.recent_slg, recent_strikeOuts = excluded.recent_strikeOuts;"))

#     if role == 'PitcherData':
#         data.drop(data.iloc[:, 0:3], inplace=True, axis=1)
#         pitchers = data.T
#         for index, row in pitchers.iterrows():
#             engine.execute(text(f"INSERT INTO pitcher_stats(game_id, game_date, position, player_id, career_era, career_homeRuns, career_whip, career_battersFaced, recent_era, recent_homeRuns, recent_whip, recent_battersFaced) \
#                                 VALUES('{gameid}', '{gamedate}', '{index}', '{int(row['player_id'])}', '{round(float(row['career_era']), 3)}', '{round(float(row['career_homeRuns']), 3)}', '{round(float(row['career_whip']), 3)}', '{round(float(row['career_battersFaced']), 3)}', '{round(float(row['recent_era']), 3)}', '{round(float(row['recent_homeRuns']), 3)}', '{round(float(row['recent_whip']), 3)}', '{round(float(row['recent_battersFaced']), 3)}') \
#                                 ON CONFLICT ON CONSTRAINT unique_pitcher_player DO UPDATE SET game_date = excluded.game_date, career_era = excluded.career_era, career_homeRuns = excluded.career_homeRuns, career_whip = excluded.career_whip, career_battersFaced = excluded.career_battersFaced, recent_era = excluded.recent_era, recent_homeRuns = excluded.recent_homeRuns, recent_whip = excluded.recent_whip, recent_battersFaced = excluded.recent_battersFaced;"))