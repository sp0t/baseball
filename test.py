from database import database
import pandas as pd
from sqlalchemy import text

engine = database.connect_to_db()

bet_res = pd.read_sql(text(f"SELECT * FROM test_betting;"), con = engine).to_dict('records')

for bet in bet_res:
    away_res = pd.read_sql(text(f"SELECT * FROM team_table WHERE team_name = '{bet['team1']}';"), con = engine).to_dict('records')
    home_res = pd.read_sql(text(f"SELECT * FROM team_table WHERE team_name = '{bet['team2']}';"), con = engine).to_dict('records')
    gameid_res = pd.read_sql(text(f"SELECT * FROM game_table WHERE away_team = '{away_res[0]['team_abbr']}' AND home_team = '{home_res[0]['team_abbr']}' AND game_date = '{bet['betdate']}';"), con = engine).to_dict('records')
    if len(gameid_res) == 0:
        gameid_res = pd.read_sql(text(f"SELECT * FROM game_table WHERE away_team = '{away_res[0]['team_abbr']}' AND home_team = '{home_res[0]['team_abbr']}' AND game_date = '{bet['betdate']}';"), con = engine).to_dict('records')
        if len(gameid_res) == 0:
            continue
    engine.execute(f"UPDATE test_betting SET game_id = '{gameid_res[0]['game_id']}' WHERE team1 = '{bet['team1']}' AND team2 = '{bet['team2']}' AND betdate = '{bet['betdate']}';") 