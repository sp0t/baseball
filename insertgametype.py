from database import databaseNHL
from API import nhlAPI
import pandas as pd

engine_nhl = databaseNHL.connect_to_db()
game_res = pd.read_sql(f"SELECT * FROM game_table", con = engine_nhl).to_dict('records')

for el in game_res:
    boxscore = nhlAPI.get_Boxscore(el['game_id'])
    print(boxscore['gameOutcome'])