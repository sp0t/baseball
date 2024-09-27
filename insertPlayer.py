import nhlAPI
from database import databaseNHL
import pandas as pd

engine = databaseNHL.connect_to_db()
teams = pd.read_sql("SELECT * FROM team_table WHERE league= '1';", con = engine).to_dict('records')

for team in teams:
    team_data = nhlAPI.get_Team_Roster(team['team_abbr'])

    forwards = team_data['forwards']
    goalies = team_data['goalies']
    defensemen = team_data['defensemen']

    for forward in forwards:
        engine.execute("INSERT INTO player_table(player_id, f_name, l_name, team_id, role) VALUES(%s, %s, %s, %s, %s)", (forward['id'], forward['firstName']['default'], forward['lastName']['default'], team['team_id'], '0'))

    for goalie in goalies:
        engine.execute("INSERT INTO player_table(player_id, f_name, l_name, team_id, role) VALUES(%s, %s, %s, %s, %s)", (goalie['id'], goalie['firstName']['default'], goalie['lastName']['default'], team['team_id'], '1'))

    for defense in defensemen:
        engine.execute("INSERT INTO player_table(player_id, f_name, l_name, team_id, role) VALUES(%s, %s, %s, %s, %s)", (defense['id'], defense['firstName']['default'], defense['lastName']['default'], team['team_id'], '2'))
