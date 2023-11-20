import statsapi as mlb
from schedule import schedule
import pandas as pd
from database import database
from sqlalchemy import text
from datetime import datetime, date

engine = database.connect_to_db()
game_sched = mlb.schedule(start_date = "2023-11-01")
playerData = {}

for game in game_sched:
    playerData[game['game_id']] = {}
    playerData[game['game_id']]['away_batter'] = []
    playerData[game['game_id']]['home_batter'] = []
    playerData[game['game_id']]['away_pitcher'] = []
    playerData[game['game_id']]['home_pitcher'] = []
    playerData[game['game_id']]['name'] = {}
    away_batter_atbats = {}
    home_batter_atbats = {}
    away_pitcher_atbats = {}
    home_pitcher_atbats = {}
    away_pitcher_played = {}
    home_pitcher_played = {}
    away_batter = []
    home_batter = []
    away_pitcher = []
    home_pitcher = []
    data = mlb.boxscore_data(game['game_id'])
    game_date = data['gameId'][:10]
    away_team = data['teamInfo']['away']['abbreviation']
    home_team = data['teamInfo']['home']['abbreviation']

    away_batter_res = pd.read_sql(text(f"SELECT * FROM (SELECT * FROM game_table WHERE away_team = '{data['teamInfo']['away']['abbreviation']}' or home_team = '{data['teamInfo']['away']['abbreviation']}' ORDER BY game_date DESC LIMIT 30) games INNER JOIN batter_table ON games.game_id = batter_table.game_id \
        WHERE (games.away_team='{data['teamInfo']['away']['abbreviation']}' AND batter_table.team = 'away') OR (games.home_team='{data['teamInfo']['away']['abbreviation']}' AND batter_table.team = 'home');"), con = engine).to_dict('records')

    home_batter_res = pd.read_sql(text(f"SELECT * FROM (SELECT * FROM game_table WHERE away_team = '{data['teamInfo']['home']['abbreviation']}' or home_team = '{data['teamInfo']['home']['abbreviation']}' ORDER BY game_date DESC LIMIT 30) games INNER JOIN batter_table ON games.game_id = batter_table.game_id \
        WHERE (games.away_team='{data['teamInfo']['home']['abbreviation']}' AND batter_table.team = 'away') OR (games.home_team='{data['teamInfo']['home']['abbreviation']}' AND batter_table.team = 'home');"), con = engine).to_dict('records')


    for away_player in away_batter_res:
        if away_player['playerid'] in away_batter_atbats:
            away_batter_atbats[away_player['playerid']] += int(away_player['atbats'])          
        else:
            away_batter_atbats[away_player['playerid']] = int(away_player['atbats'])

    for home_player in home_batter_res:
        if home_player['playerid'] in home_batter_atbats:
            home_batter_atbats[home_player['playerid']] += int(home_player['atbats'])
        else:
            home_batter_atbats[home_player['playerid']] = int(home_player['atbats'])

    away_batter_atbats_list = sorted(away_batter_atbats.items(), key=lambda x:x[1], reverse = True)
    away_batter_sort_atbats = dict(away_batter_atbats_list)

    home_batter_atbats_list = sorted(home_batter_atbats.items(), key=lambda x:x[1], reverse = True)
    home_batter_sort_atbats = dict(home_batter_atbats_list)

    away_pitcher_res = pd.read_sql(text(f"SELECT * FROM (SELECT * FROM game_table WHERE away_team = '{data['teamInfo']['away']['abbreviation']}' or home_team = '{data['teamInfo']['away']['abbreviation']}' ORDER BY game_date DESC LIMIT 30) games INNER JOIN pitcher_table ON games.game_id = pitcher_table.game_id \
        WHERE (games.away_team='{data['teamInfo']['away']['abbreviation']}' AND pitcher_table.team = 'away' AND pitcher_table.role = 'bullpen') OR (games.home_team='{data['teamInfo']['away']['abbreviation']}' AND pitcher_table.team = 'home' AND pitcher_table.role = 'bullpen');"), con = engine).to_dict('records')

    home_pitcher_res = pd.read_sql(text(f"SELECT * FROM (SELECT * FROM game_table WHERE away_team = '{data['teamInfo']['home']['abbreviation']}' or home_team = '{data['teamInfo']['home']['abbreviation']}' ORDER BY game_date DESC LIMIT 30) games INNER JOIN pitcher_table ON games.game_id = pitcher_table.game_id \
        WHERE (games.away_team='{data['teamInfo']['home']['abbreviation']}' AND pitcher_table.team = 'away' AND pitcher_table.role = 'bullpen') OR (games.home_team='{data['teamInfo']['home']['abbreviation']}' AND pitcher_table.team = 'home' AND pitcher_table.role = 'bullpen');"), con = engine).to_dict('records')


    for away_player in away_pitcher_res:
        if away_player['playerid'] in away_pitcher_atbats:
            away_pitcher_atbats[away_player['playerid']] += int(away_player['atbats'])
        else:
            away_pitcher_atbats[away_player['playerid']] = int(away_player['atbats'])

        if away_player['playerid'] not in away_pitcher_played:
            away_pitcher_played[away_player['playerid']] = {}
            away_pitcher_played[away_player['playerid']]['gamedate'] = away_player['game_date']
            away_pitcher_played[away_player['playerid']]['count'] = 1
        else:
            # print((datetime.combine(date.today(), datetime.min.time()) - datetime.strptime(away_player['game_date'], '%Y/%m/%d')).days)
            if((datetime.strptime(away_player['game_date'], '%Y/%m/%d') - datetime.strptime(away_pitcher_played[away_player['playerid']]['gamedate'], '%Y/%m/%d')).days) == 1:
                away_pitcher_played[away_player['playerid']]['count'] = 2
            else:
                away_pitcher_played[away_player['playerid']]['count'] = 1

            away_pitcher_played[away_player['playerid']]['gamedate'] = away_player['game_date']

    for home_player in home_pitcher_res:
        if home_player['playerid'] in home_pitcher_atbats:
            home_pitcher_atbats[home_player['playerid']] += int(home_player['atbats'])
        else:
            home_pitcher_atbats[home_player['playerid']] = int(home_player['atbats'])

        if home_player['playerid'] not in home_pitcher_played:
            home_pitcher_played[home_player['playerid']] = {}
            home_pitcher_played[home_player['playerid']]['gamedate'] = home_player['game_date']
            home_pitcher_played[home_player['playerid']]['count'] = 1
        else:
            if((datetime.strptime(home_player['game_date'], '%Y/%m/%d') - datetime.strptime(home_pitcher_played[home_player['playerid']]['gamedate'], '%Y/%m/%d')).days) == 1:
                home_pitcher_played[home_player['playerid']]['count'] = 2
            else:
                home_pitcher_played[home_player['playerid']]['count'] = 1

            home_pitcher_played[home_player['playerid']]['gamedate'] = home_player['game_date']

    away_pitcher_atbats_list = sorted(away_pitcher_atbats.items(), key=lambda x:x[1], reverse = True)
    away_pitcher_sort_atbats = dict(away_pitcher_atbats_list)


    home_pitcher_atbats_list = sorted(home_pitcher_atbats.items(), key=lambda x:x[1], reverse = True)
    home_pitcher_sort_atbats = dict(home_pitcher_atbats_list)


    rosters = schedule.get_rosters(game['game_id'])
    name = {}

    for away in rosters['away']:
        name[str(away['id'])] = away['fullName']

    for home in rosters['home']:
        name[str(home['id'])] = home['fullName']

    count = 0
    for key in away_batter_sort_atbats.keys():
        if (count == 15):
            break

        if key not in name:
            continue

        away_batter.append(key)
        count += 1
    
    count = 0
    for key in home_batter_sort_atbats.keys():
        if (count == 15):
            break

        if key not in name:
            continue

        home_batter.append(key)
        count += 1
    
    count = 0
    for key in away_pitcher_sort_atbats.keys():
        if (count == 4):
            break

        if (datetime.combine(date.today(), datetime.min.time()) - datetime.strptime(away_pitcher_played[key]['gamedate'], '%Y/%m/%d')).days == 1 and away_pitcher_played[key]['count'] == 2:
            continue

        if key not in name:
            continue

        away_pitcher.append(key)
        count += 1

    count = 0
    for key in home_pitcher_sort_atbats.keys():
        if (count == 4):
            break

        if (datetime.combine(date.today(), datetime.min.time()) - datetime.strptime(home_pitcher_played[key]['gamedate'], '%Y/%m/%d')).days == 1 and home_pitcher_played[key]['count'] == 2:
            continue

        if key not in name:
            continue

        home_pitcher.append(key)
        count += 1

    playerData[game['game_id']]['away_batter'] = away_batter
    playerData[game['game_id']]['home_batter'] = home_batter
    playerData[game['game_id']]['away_pitcher'] = away_pitcher
    playerData[game['game_id']]['home_pitcher'] = home_pitcher
    playerData[game['game_id']]['name'] = name
    print(playerData)
