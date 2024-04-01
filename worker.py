from passlib.hash import sha256_crypt
import statsapi as mlb
import pandas as pd
from datetime import date, time, datetime, timedelta
from database import database
from pytz import timezone
from functions import batting, predict, starters, smartContract, sanitycheck, odds
from schedule import schedule
import requests
from sqlalchemy import text
from functions_c import batting_c, starters_c, predict_c

playerData = {}
engine = database.connect_to_db()
game_sched = mlb.schedule(start_date = date.today())

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
        if 'fullName' in away:
            name[str(away['id'])] = away['fullName']
        else:
            name[str(away['id'])] = ''

    for home in rosters['home']:
        if 'fullName' in home:
            name[str(home['id'])] = home['fullName']
        else:
            name[str(home['id'])] = ''

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

today  = date.today()
output_date = today.strftime("%Y/%m/%d")

batter_stat_list = ['home_score', 'away_score', 'atBats', 'avg', 'baseOnBalls', 'doubles', 'hits', 'homeRuns', 'obp', 'ops', 'playerId', 'rbi', 'runs', 
                    'slg', 'strikeOuts', 'triples', 'season', 'singles']
pitcher_stat_list=['atBats', 'baseOnBalls', 'blownSave', 'doubles', 'earnedRuns', 'era', 'hits', 'holds', 'homeRuns', 'inningsPitched', 
    'losses', 'pitchesThrown', 'playerId', 'rbi', 'runs', 'strikeOuts', 'strikes', 'triples', 'whip',  'wins']

for gameid in playerData:
    print('gameid')
    print(gameid)
    away_batters = playerData[gameid]['away_batter']
    for away_batter in away_batters:
        print('away_batter_id')
        print(away_batter)
        player_df = batting_c.get_batter_df(away_batter, output_date)
        recent_batter_stats, games = batting_c.process_recent_batter_data(player_df, output_date, '', batter_stat_list)
        career_batter_data = batting_c.process_career_batter_data(games, batter_stat_list)

        engine.execute(text(f"INSERT INTO predict_batter_stats(game_date, game_id, player_id, player_name, team, role, atBats, avg, baseOnBalls, doubles, hits, homeRuns, obp, ops, rbi, runs, slg, strikeOuts, triples, singles, difficulty) \
                                VALUES('{output_date}', '{gameid}', '{away_batter}', '{playerData[gameid]['name'][str(away_batter)]}', 'away', 'recent', '{round(float(recent_batter_stats['atBats']), 3)}', '{round(float(recent_batter_stats['avg']), 3)}', '{round(float(recent_batter_stats['baseOnBalls']), 3)}', '{round(float(recent_batter_stats['doubles']), 3)}', '{round(float(recent_batter_stats['hits']), 3)}', '{round(float(recent_batter_stats['homeRuns']), 3)}', '{round(float(recent_batter_stats['obp']), 3)}', '{round(float(recent_batter_stats['ops']), 3)}', '{round(float(recent_batter_stats['rbi']), 3)}', '{round(float(recent_batter_stats['runs']), 3)}', '{round(float(recent_batter_stats['slg']), 3)}', '{round(float(recent_batter_stats['strikeOuts']), 3)}', '{round(float(recent_batter_stats['triples']), 3)}', '{round(float(recent_batter_stats['singles']), 3)}', '{round(float(recent_batter_stats['difficulty']), 3)}')\
                                ON CONFLICT ON CONSTRAINT predict_batter_stats_key DO UPDATE SET atBats = excluded.atBats, avg = excluded.avg, baseOnBalls = excluded.baseOnBalls, doubles = excluded.doubles, hits = excluded.hits, homeRuns = excluded.homeRuns, obp = excluded.obp, ops = excluded.ops, rbi = excluded.rbi, runs = excluded.runs, slg = excluded.slg, strikeOuts = excluded.strikeOuts, triples = excluded.triples, singles = excluded.singles, difficulty = excluded.difficulty;"))
        engine.execute(text(f"INSERT INTO predict_batter_stats(game_date, game_id, player_id, player_name, team, role, atBats, avg, baseOnBalls, doubles, hits, homeRuns, obp, ops, rbi, runs, slg, strikeOuts, triples, singles, difficulty) \
                                VALUES('{output_date}', '{gameid}', '{away_batter}', '{playerData[gameid]['name'][str(away_batter)]}', 'away', 'career', '{round(float(career_batter_data['atBats']), 3)}', '{round(float(career_batter_data['avg']), 3)}', '{round(float(career_batter_data['baseOnBalls']), 3)}', '{round(float(career_batter_data['doubles']), 3)}', '{round(float(career_batter_data['hits']), 3)}', '{round(float(career_batter_data['homeRuns']), 3)}', '{round(float(career_batter_data['obp']), 3)}', '{round(float(career_batter_data['ops']), 3)}', '{round(float(career_batter_data['rbi']), 3)}', '{round(float(career_batter_data['runs']), 3)}', '{round(float(career_batter_data['slg']), 3)}', '{round(float(career_batter_data['strikeOuts']), 3)}', '{round(float(career_batter_data['triples']), 3)}', '{round(float(career_batter_data['singles']), 3)}', '1')\
                                ON CONFLICT ON CONSTRAINT predict_batter_stats_key DO UPDATE SET atBats = excluded.atBats, avg = excluded.avg, baseOnBalls = excluded.baseOnBalls, doubles = excluded.doubles, hits = excluded.hits, homeRuns = excluded.homeRuns, obp = excluded.obp, ops = excluded.ops, rbi = excluded.rbi, runs = excluded.runs, slg = excluded.slg, strikeOuts = excluded.strikeOuts, triples = excluded.triples, singles = excluded.singles, difficulty = excluded.difficulty;"))


    home_batters = playerData[gameid]['home_batter']
    for home_batter in home_batters:
        print('home_batter_id')
        print(home_batter)
        player_df = batting_c.get_batter_df(home_batter, output_date)
        recent_batter_stats, games = batting_c.process_recent_batter_data(player_df, output_date, '', batter_stat_list)
        career_batter_data = batting_c.process_career_batter_data(games, batter_stat_list)

        engine.execute(text(f"INSERT INTO predict_batter_stats(game_date, game_id, player_id, player_name, team, role, atBats, avg, baseOnBalls, doubles, hits, homeRuns, obp, ops, rbi, runs, slg, strikeOuts, triples, singles, difficulty) \
                                VALUES('{output_date}', '{gameid}', '{home_batter}', '{playerData[gameid]['name'][str(home_batter)]}', 'home', 'recent', '{round(float(recent_batter_stats['atBats']), 3)}', '{round(float(recent_batter_stats['avg']), 3)}', '{round(float(recent_batter_stats['baseOnBalls']), 3)}', '{round(float(recent_batter_stats['doubles']), 3)}', '{round(float(recent_batter_stats['hits']), 3)}', '{round(float(recent_batter_stats['homeRuns']), 3)}', '{round(float(recent_batter_stats['obp']), 3)}', '{round(float(recent_batter_stats['ops']), 3)}', '{round(float(recent_batter_stats['rbi']), 3)}', '{round(float(recent_batter_stats['runs']), 3)}', '{round(float(recent_batter_stats['slg']), 3)}', '{round(float(recent_batter_stats['strikeOuts']), 3)}', '{round(float(recent_batter_stats['triples']), 3)}', '{round(float(recent_batter_stats['singles']), 3)}', '{round(float(recent_batter_stats['difficulty']), 3)}')\
                                ON CONFLICT ON CONSTRAINT predict_batter_stats_key DO UPDATE SET atBats = excluded.atBats, avg = excluded.avg, baseOnBalls = excluded.baseOnBalls, doubles = excluded.doubles, hits = excluded.hits, homeRuns = excluded.homeRuns, obp = excluded.obp, ops = excluded.ops, rbi = excluded.rbi, runs = excluded.runs, slg = excluded.slg, strikeOuts = excluded.strikeOuts, triples = excluded.triples, singles = excluded.singles, difficulty = excluded.difficulty;"))
        engine.execute(text(f"INSERT INTO predict_batter_stats(game_date, game_id, player_id, player_name, team, role, atBats, avg, baseOnBalls, doubles, hits, homeRuns, obp, ops, rbi, runs, slg, strikeOuts, triples, singles, difficulty) \
                                VALUES('{output_date}', '{gameid}', '{home_batter}', '{playerData[gameid]['name'][str(home_batter)]}', 'home', 'career', '{round(float(career_batter_data['atBats']), 3)}', '{round(float(career_batter_data['avg']), 3)}', '{round(float(career_batter_data['baseOnBalls']), 3)}', '{round(float(career_batter_data['doubles']), 3)}', '{round(float(career_batter_data['hits']), 3)}', '{round(float(career_batter_data['homeRuns']), 3)}', '{round(float(career_batter_data['obp']), 3)}', '{round(float(career_batter_data['ops']), 3)}', '{round(float(career_batter_data['rbi']), 3)}', '{round(float(career_batter_data['runs']), 3)}', '{round(float(career_batter_data['slg']), 3)}', '{round(float(career_batter_data['strikeOuts']), 3)}', '{round(float(career_batter_data['triples']), 3)}', '{round(float(career_batter_data['singles']), 3)}', '1')\
                                ON CONFLICT ON CONSTRAINT predict_batter_stats_key DO UPDATE SET atBats = excluded.atBats, avg = excluded.avg, baseOnBalls = excluded.baseOnBalls, doubles = excluded.doubles, hits = excluded.hits, homeRuns = excluded.homeRuns, obp = excluded.obp, ops = excluded.ops, rbi = excluded.rbi, runs = excluded.runs, slg = excluded.slg, strikeOuts = excluded.strikeOuts, triples = excluded.triples, singles = excluded.singles, difficulty = excluded.difficulty;"))

    away_starters = playerData[gameid]['away_pitcher']
    for away_starter in away_starters:
        print('away_pitcher_id')
        print(away_starter)
        player_df = starters_c.get_starter_df(away_starter, output_date)
        recent_pitcher_stats, games = starters_c.process_recent_starter_data(player_df, output_date, [], pitcher_stat_list)
        career_pitcher_data = starters_c.process_career_starter_data(games, pitcher_stat_list)

        engine.execute(text(f"INSERT INTO predict_pitcher_stats(game_date, game_id, player_id, player_name, team, role, atBats, baseOnBalls, blownsaves, doubles, earnedRuns, era, hits, holds, homeRuns, inningsPitched, losses, pitchesThrown, rbi, runs, strikeOuts, strikes, triples, whip, wins, difficulty) \
                                VALUES('{output_date}', '{gameid}', '{away_starter}', '{playerData[gameid]['name'][str(away_starter)]}', 'away', 'recent', '{round(float(recent_pitcher_stats['atBats']), 3)}', '{round(float(recent_pitcher_stats['baseOnBalls']), 3)}', '{round(float(recent_pitcher_stats['blownsaves']), 3)}', '{round(float(recent_pitcher_stats['doubles']), 3)}', '{round(float(recent_pitcher_stats['earnedRuns']), 3)}', '{round(float(recent_pitcher_stats['era']), 3)}', '{round(float(recent_pitcher_stats['hits']), 3)}', '{round(float(recent_pitcher_stats['holds']), 3)}', '{round(float(recent_pitcher_stats['homeRuns']), 3)}', '{round(float(recent_pitcher_stats['inningsPitched']), 3)}', '{round(float(recent_pitcher_stats['losses']), 3)}', '{round(float(recent_pitcher_stats['pitchesThrown']), 3)}', '{round(float(recent_pitcher_stats['rbi']), 3)}', '{round(float(recent_pitcher_stats['runs']), 3)}', '{round(float(recent_pitcher_stats['strikeOuts']), 3)}', '{round(float(recent_pitcher_stats['strikes']), 3)}', '{round(float(recent_pitcher_stats['triples']), 3)}', '{round(float(recent_pitcher_stats['whip']), 3)}', '{round(float(recent_pitcher_stats['wins']), 3)}', '{round(float(recent_pitcher_stats['difficulty']), 3)}')\
                                ON CONFLICT ON CONSTRAINT predict_pitcher_stats_key DO UPDATE SET atBats = excluded.atBats, baseOnBalls = excluded.baseOnBalls, blownsaves = excluded.blownsaves, doubles = excluded.doubles, earnedRuns = excluded.earnedRuns, era = excluded.era, hits = excluded.hits, holds = excluded.holds, homeRuns = excluded.homeRuns, inningsPitched = excluded.inningsPitched, losses = excluded.losses, pitchesThrown = excluded.pitchesThrown, rbi = excluded.rbi, runs = excluded.runs, strikeOuts = excluded.strikeOuts, strikes = excluded.strikes, triples = excluded.triples, whip = excluded.whip, wins = excluded.wins, difficulty = excluded.difficulty;"))
        engine.execute(text(f"INSERT INTO predict_pitcher_stats(game_date, game_id, player_id, player_name, team, role, atBats, baseOnBalls, blownsaves, doubles, earnedRuns, era, hits, holds, homeRuns, inningsPitched, losses, pitchesThrown, rbi, runs, strikeOuts, strikes, triples, whip, wins, difficulty) \
                                VALUES('{output_date}', '{gameid}', '{away_starter}', '{playerData[gameid]['name'][str(away_starter)]}', 'away', 'career', '{round(float(career_pitcher_data['atBats']), 3)}', '{round(float(career_pitcher_data['baseOnBalls']), 3)}', '{round(float(career_pitcher_data['blownsaves']), 3)}', '{round(float(career_pitcher_data['doubles']), 3)}', '{round(float(career_pitcher_data['earnedRuns']), 3)}', '{round(float(career_pitcher_data['era']), 3)}', '{round(float(career_pitcher_data['hits']), 3)}', '{round(float(career_pitcher_data['holds']), 3)}', '{round(float(career_pitcher_data['homeRuns']), 3)}', '{round(float(career_pitcher_data['inningsPitched']), 3)}', '{round(float(career_pitcher_data['losses']), 3)}', '{round(float(career_pitcher_data['pitchesThrown']), 3)}', '{round(float(career_pitcher_data['rbi']), 3)}', '{round(float(career_pitcher_data['runs']), 3)}', '{round(float(career_pitcher_data['strikeOuts']), 3)}', '{round(float(career_pitcher_data['strikes']), 3)}', '{round(float(career_pitcher_data['triples']), 3)}', '{round(float(career_pitcher_data['whip']), 3)}', '{round(float(career_pitcher_data['wins']), 3)}', '1')\
                                ON CONFLICT ON CONSTRAINT predict_pitcher_stats_key DO UPDATE SET atBats = excluded.atBats, baseOnBalls = excluded.baseOnBalls, blownsaves = excluded.blownsaves, doubles = excluded.doubles, earnedRuns = excluded.earnedRuns, era = excluded.era, hits = excluded.hits, holds = excluded.holds, homeRuns = excluded.homeRuns, inningsPitched = excluded.inningsPitched, losses = excluded.losses, pitchesThrown = excluded.pitchesThrown, rbi = excluded.rbi, runs = excluded.runs, strikeOuts = excluded.strikeOuts, strikes = excluded.strikes, triples = excluded.triples, whip = excluded.whip, wins = excluded.wins, difficulty = excluded.difficulty;"))

    home_starters = playerData[gameid]['home_pitcher']
    for home_starter in home_starters:
        print('home_pitcher_id')
        print(home_starter)
        player_df = starters_c.get_starter_df(home_starter, output_date)
        recent_pitcher_stats, games = starters_c.process_recent_starter_data(player_df, output_date, [], pitcher_stat_list)
        career_pitcher_data = starters_c.process_career_starter_data(games, pitcher_stat_list)
        
        engine.execute(text(f"INSERT INTO predict_pitcher_stats(game_date, game_id, player_id, player_name, team, role, atBats, baseOnBalls, blownsaves, doubles, earnedRuns, era, hits, holds, homeRuns, inningsPitched, losses, pitchesThrown, rbi, runs, strikeOuts, strikes, triples, whip, wins, difficulty) \
                                VALUES('{output_date}', '{gameid}', '{home_starter}', '{playerData[gameid]['name'][str(home_starter)]}', 'home', 'recent', '{round(float(recent_pitcher_stats['atBats']), 3)}', '{round(float(recent_pitcher_stats['baseOnBalls']), 3)}', '{round(float(recent_pitcher_stats['blownsaves']), 3)}', '{round(float(recent_pitcher_stats['doubles']), 3)}', '{round(float(recent_pitcher_stats['earnedRuns']), 3)}', '{round(float(recent_pitcher_stats['era']), 3)}', '{round(float(recent_pitcher_stats['hits']), 3)}', '{round(float(recent_pitcher_stats['holds']), 3)}', '{round(float(recent_pitcher_stats['homeRuns']), 3)}', '{round(float(recent_pitcher_stats['inningsPitched']), 3)}', '{round(float(recent_pitcher_stats['losses']), 3)}', '{round(float(recent_pitcher_stats['pitchesThrown']), 3)}', '{round(float(recent_pitcher_stats['rbi']), 3)}', '{round(float(recent_pitcher_stats['runs']), 3)}', '{round(float(recent_pitcher_stats['strikeOuts']), 3)}', '{round(float(recent_pitcher_stats['strikes']), 3)}', '{round(float(recent_pitcher_stats['triples']), 3)}', '{round(float(recent_pitcher_stats['whip']), 3)}', '{round(float(recent_pitcher_stats['wins']), 3)}', '{round(float(recent_pitcher_stats['difficulty']), 3)}')\
                                ON CONFLICT ON CONSTRAINT predict_pitcher_stats_key DO UPDATE SET atBats = excluded.atBats, baseOnBalls = excluded.baseOnBalls, blownsaves = excluded.blownsaves, doubles = excluded.doubles, earnedRuns = excluded.earnedRuns, era = excluded.era, hits = excluded.hits, holds = excluded.holds, homeRuns = excluded.homeRuns, inningsPitched = excluded.inningsPitched, losses = excluded.losses, pitchesThrown = excluded.pitchesThrown, rbi = excluded.rbi, runs = excluded.runs, strikeOuts = excluded.strikeOuts, strikes = excluded.strikes, triples = excluded.triples, whip = excluded.whip, wins = excluded.wins, difficulty = excluded.difficulty;"))
        engine.execute(text(f"INSERT INTO predict_pitcher_stats(game_date, game_id, player_id, player_name, team, role, atBats, baseOnBalls, blownsaves, doubles, earnedRuns, era, hits, holds, homeRuns, inningsPitched, losses, pitchesThrown, rbi, runs, strikeOuts, strikes, triples, whip, wins, difficulty) \
                                VALUES('{output_date}', '{gameid}', '{home_starter}', '{playerData[gameid]['name'][str(home_starter)]}', 'home', 'career', '{round(float(career_pitcher_data['atBats']), 3)}', '{round(float(career_pitcher_data['baseOnBalls']), 3)}', '{round(float(career_pitcher_data['blownsaves']), 3)}', '{round(float(career_pitcher_data['doubles']), 3)}', '{round(float(career_pitcher_data['earnedRuns']), 3)}', '{round(float(career_pitcher_data['era']), 3)}', '{round(float(career_pitcher_data['hits']), 3)}', '{round(float(career_pitcher_data['holds']), 3)}', '{round(float(career_pitcher_data['homeRuns']), 3)}', '{round(float(career_pitcher_data['inningsPitched']), 3)}', '{round(float(career_pitcher_data['losses']), 3)}', '{round(float(career_pitcher_data['pitchesThrown']), 3)}', '{round(float(career_pitcher_data['rbi']), 3)}', '{round(float(career_pitcher_data['runs']), 3)}', '{round(float(career_pitcher_data['strikeOuts']), 3)}', '{round(float(career_pitcher_data['strikes']), 3)}', '{round(float(career_pitcher_data['triples']), 3)}', '{round(float(career_pitcher_data['whip']), 3)}', '{round(float(career_pitcher_data['wins']), 3)}', '1')\
                                ON CONFLICT ON CONSTRAINT predict_pitcher_stats_key DO UPDATE SET atBats = excluded.atBats, baseOnBalls = excluded.baseOnBalls, blownsaves = excluded.blownsaves, doubles = excluded.doubles, earnedRuns = excluded.earnedRuns, era = excluded.era, hits = excluded.hits, holds = excluded.holds, homeRuns = excluded.homeRuns, inningsPitched = excluded.inningsPitched, losses = excluded.losses, pitchesThrown = excluded.pitchesThrown, rbi = excluded.rbi, runs = excluded.runs, strikeOuts = excluded.strikeOuts, strikes = excluded.strikes, triples = excluded.triples, whip = excluded.whip, wins = excluded.wins, difficulty = excluded.difficulty;"))