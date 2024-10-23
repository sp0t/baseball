from database import databaseNHL
from API import nhlAPI
import pandas as pd

engine_nhl = databaseNHL.connect_to_db()
game_res = pd.read_sql(f"SELECT * FROM game_table", con = engine_nhl).to_dict('records')

for el in game_res:
    boxscore = nhlAPI.get_Boxscore(el['game_id'])
    print(el['game_id'])
    game_type = ''
    if 'gameOutcome' in boxscore:
        if 'lastPeriodType' in boxscore['gameOutcome']:
            game_type = boxscore['gameOutcome']['lastPeriodType']
    
    engine_nhl.execute(f"UPDATE game_table SET game_type = '{game_type}' WHERE game_id = '{el['game_id']}'")