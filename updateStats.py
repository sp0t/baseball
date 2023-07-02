import os
from database import database
from sqlalchemy import text
import pandas as pd
from datetime import date
from functions import batting, starters, bullpen, predict

engine = database.connect_to_db()

gamedata = pd.read_sql(f"SELECT DISTINCT game_table.* FROM game_table INNER JOIN batter_stats ON game_table.game_id = batter_stats.game_id WHERE game_table.game_date >= '2023/06/23' ORDER BY game_table.game_date ASC;", con = engine).to_dict('records')

for i in gamedata:
    engine.execute(text(f"DELETE FROM batter_stats WHERE game_id = '{i['game_id']}';"))
    engine.execute(text(f"DELETE FROM pitcher_stats WHERE game_id = '{i['game_id']}';"))
    print(i['game_date'], i['game_id'], i['away_team'], i['home_team'])
    batterData = pd.read_sql(f"SELECT * FROM batter_table WHERE game_id = '{i['game_id']}' ORDER BY team, position;", con = engine).to_dict('records')
    pitcherData = pd.read_sql(f"SELECT * FROM pitcher_table WHERE game_id = '{i['game_id']}' AND role = 'starter' ORDER BY team;", con = engine).to_dict('records')
    awayData = pd.read_sql(f"SELECT * FROM team_table WHERE team_abbr = '{i['away_team']}';", con = engine).to_dict('records')
    homeData = pd.read_sql(f"SELECT * FROM team_table WHERE team_abbr = '{i['home_team']}';", con = engine).to_dict('records')
    team_batter = []
    team_home = []
    away_starter = ''
    home_starter = ''
    countaway = 1
    counthome = 1
    awayname = ''
    homename = ''

    if len(awayData) != 0:
        awayname = awayData[0]['club_name']
    if len(awayData) != 0:
        homename = homeData[0]['club_name']

    if awayname == '' or homename == '':
        continue

    for el in batterData:
        if int(el['position']) == countaway and el['team'] == 'away':
            team_batter.append(el['playerid'])
            countaway += 1

        if int(el['position']) == counthome and el['team'] == 'home':
            team_home.append(el['playerid'])
            counthome += 1

        if countaway == 10:
            countaway = 1
        if counthome == 10:
            counthome = 1


    for el in pitcherData:
        if el['team'] == 'away':
            away_starter = el['playerid']
        if el['team'] == 'home':
            home_starter = el['playerid']

    # Batters 
    away_batter_data = batting.process_team_batter_data(team_batter, 'away', i['game_date'])
    home_batter_data = batting.process_team_batter_data(team_home, 'home', i['game_date'])
    # Starters 
    away_starter_data = starters.process_starter_data(away_starter, 'away', i['game_date'])
    home_starter_data = starters.process_starter_data(home_starter, 'home', i['game_date'])
    # Bullpen 
    away_bullpen_data = bullpen.process_bullpen_data(awayname, 'away', i['game_date'])
    home_bullpen_data = bullpen.process_bullpen_data(homename, 'home', i['game_date'])

    # Combine 
    game_data = {}
    game_data.update(away_bullpen_data)
    game_data.update(away_batter_data)
    game_data.update(away_starter_data)

    game_data.update(home_bullpen_data)
    game_data.update(home_batter_data)
    game_data.update(home_starter_data)

    X_test = pd.DataFrame(game_data, index = [0])

    X_test = predict.feature_selection(X_test, fill_null = True)
    X_test, column_names = predict.addBattersFaced(X_test, bullpen = False)

    predict.save_batter_data(engine, X_test, team_batter, team_home, i['game_id'])
    predict.save_pitcher_data(engine, X_test, away_starter, home_starter, i['game_id'])

    