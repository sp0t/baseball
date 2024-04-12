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
import psycopg2
from io import StringIO
import statsapi as mlb
from datetime import date, datetime, timedelta
import time
import pandas as pd
from pytz import timezone
import psycopg2.extras as extras
from sqlalchemy import create_engine
import uuid
import requests


def connect_to_db(): 
    
    try: 
        engine = create_engine('postgresql://postgres:lucamlb123@localhost:5432/betmlb', connect_args = {'connect_timeout': 10}, echo=False, pool_size=20, max_overflow=0)
        # engine = create_engine('postgresql://postgres:lucamlb123@ec2-3-115-115-146.ap-northeast-1.compute.amazonaws.com:5432/betmlb', connect_args = {'connect_timeout': 10}, echo=False, pool_size=20, max_overflow=0)
        # engine = create_engine('postgresql://postgres:postgres@localhost:5432/luca', 
        #                        connect_args = {'connect_timeout': 10}, 
        #                        echo=False, pool_size=20, max_overflow=0)
        print('Connection Initiated')
    except:
        raise ValueError("Can't connect to Heroku PostgreSQL! You must be so embarrassed")
    return engine


def get_game_id_list(start_date, end_date, show_progress = False): 

    delta = end_date - start_date
    game_id_list = []
    error_days=[]
    for i in range(delta.days+1): 
        day = start_date + timedelta(days=i)
        day = datetime.strftime(day, '%Y-%m-%d')
        try: 
            schedule = mlb.schedule(start_date=day)
        except: 
            error_days.append(day)
            continue 
        day_games = [el['game_id'] for el in schedule]
        game_id_list.append(day_games)

        if show_progress and i%25==0:
            print(day, i)
    game_id_list = [item for sublist in game_id_list for item in sublist]
    game_id_list = [str(item) for item in game_id_list]
    
    seen = set()
    seen_add = seen.add
    game_id_list = [x for x in game_id_list if not (x in seen or seen_add(x))]
    
    return game_id_list, error_days

def get_batting_box_score(data, team): 

    key = team + 'Batters'
    data_info = data[key]
    team_batters = []
    subinfo = {}
    num = 1
    for el in data_info:
        if el['personId'] != 0:    
            if el['substitution']:
                if el['battingOrder'] == str((num - 1) * 100 + 1):
                    subinfo[str(el['personId'])] = {}
                    team_batters.append(el['personId'])
                    subinfo[str(el['personId'])]['position'] = num - 1
                    subinfo[str(el['personId'])]['substitution'] = 1
            else:
                subinfo[str(el['personId'])] = {}
                team_batters.append(el['personId'])
                subinfo[str(el['personId'])]['position'] = num
                subinfo[str(el['personId'])]['substitution'] = 0
                num = num + 1

    team_box_score = []
 
    for team_batter in team_batters: 
        order = team_batters.index(team_batter)+1
        pbs = data[team]['players'][f'ID{team_batter}']['stats']['batting']
        pbs.update({'playerId': team_batter})
        pbs.update({'position': subinfo[str(team_batter)]['position']})
        pbs.update({'substitution': subinfo[str(team_batter)]['substitution']})

        # Calculate AVG, OBP, SLG, OPS
        atBats = pbs['atBats']
        atBatsWalks = pbs['atBats'] + pbs['baseOnBalls']
        avg = pbs['hits'] / atBats if atBats > 0 else 0
        obp = (pbs['hits'] + pbs['baseOnBalls']) / atBatsWalks if atBatsWalks > 0 else 0
        singles = pbs['hits'] - (pbs['homeRuns'] - pbs['triples'] - pbs['doubles'])
        slg = (4*pbs['homeRuns'] + 3*pbs['triples'] + 2*pbs['doubles'] + singles) / atBats if atBats > 0 else 0
        pbs.update({
            'avg': avg, 
            'obp': obp, 
            'slg': slg, 
            'ops': obp + slg
        })
        team_box_score.append(pbs)
    return team_box_score, team_batters

def get_pitching_box_score(data, team): 
    
    key = team + 'Pitchers'
    data_info = data[key]
    team_relievers = []
    team_starter = ''
    starter = True

    for el in data_info:
        if el['personId'] != 0: 
            if starter == True:
                team_starter = (str(el['personId']))
                starter = False
            elif starter == False:
                team_relievers.append(str(el['personId']))
    team_box_score = {}

    if team_starter == '': 
        return None, '', []
    elif team_starter == []:
        team_reliever_data_list = None
        team_bullpen_data = None

    # Starter Data 
    team_starter_data = data[team]['players']['ID' + team_starter]['stats']['pitching']
    team_starter_data.update({'playerId': team_starter})
    team_starter_data['inningsPitched'] = float(team_starter_data['inningsPitched'])
    ip = team_starter_data['inningsPitched']
    era = 9*team_starter_data['earnedRuns']/ip if ip > 0 else 0
    whip = (team_starter_data['baseOnBalls'] + team_starter_data['hits']) / ip if ip > 0 else 0
    team_starter_data.update({
        'era': era, 
        'whip': whip, 
    })

    team_starter_data = {k:v for k,v in team_starter_data.items() if k not in ['leftOnBase', 'stolenBases', 'note', 'notes','numberOfPitches']}

    team_reliever_data_list = []
    for team_reliever in team_relievers: 
        team_reliever_data = data[team]['players']['ID' + team_reliever]['stats']['pitching']
        team_reliever_data.update({'playerId': team_reliever})
        team_reliever_data['inningsPitched'] = float(team_reliever_data['inningsPitched'])
        ip = team_reliever_data['inningsPitched']
        era = 9*team_reliever_data['earnedRuns']/ip if ip > 0 else 0
        whip = (team_reliever_data['baseOnBalls'] + team_reliever_data['hits']) / ip if ip > 0 else 0
        team_reliever_data.update({
            'era': era, 
            'whip': whip, 
        })

        team_reliever_data = {k:v for k,v in team_reliever_data.items() if k not in ['leftOnBase', 'stolenBases', 'note', 'notes','numberOfPitches']}
        team_reliever_data_list.append(team_reliever_data)
    team_bullpen_data = pd.DataFrame(team_reliever_data_list).mean().to_dict()
    
    team_box_score['starter'] = team_starter_data
    team_box_score['bullpen'] = team_reliever_data_list
    team_box_score['bullpenAvg'] = team_bullpen_data

    return team_box_score, team_starter, team_relievers

def get_box_score(game_id): 
    
    engine = database.connect_to_db()
    data = mlb.boxscore_data(game_id)
    
    # Game Info 
    game_date = data['gameId'][:10]
    away_team = data['teamInfo']['away']['abbreviation']
    home_team = data['teamInfo']['home']['abbreviation']

    #insert position data
    awayBatters = data['awayBatters']
    homeBatters = data['homeBatters']

    away_c = ""
    away_b1 = ""
    away_b2 = ""
    away_b3 = ""
    away_ss = ""
    away_lf = ""
    away_cf = ""
    away_rf = ""
    away_dh = ""

    # for batter in awayBatters:
    #     if batter['personId'] != 0 and batter['substitution'] == False:
    #         url = f"https://statsapi.mlb.com/api/v1/people/{batter['personId']}"
    #         response = requests.get(url)
    #         if response.status_code == 200:
    #             result = response.json()
    #             hander = result['people'][0]['batSide']['code']
    #         else:
    #             hander = 'R'

    #         if batter['position'] == 'C':
    #             away_c = batter['name'].replace("'", " ") + "   " + hander
    #         elif batter['position'] == '1B':
    #             away_b1 = batter['name'].replace("'", " ") + "   " + hander
    #         elif batter['position'] == '2B':
    #             away_b2 = batter['name'].replace("'", " ") + "   " + hander
    #         elif batter['position'] == '3B':
    #             away_b3 = batter['name'].replace("'", " ") + "   " + hander
    #         elif batter['position'] == 'SS':
    #             away_ss = batter['name'].replace("'", " ") + "   " + hander
    #         elif batter['position'] == 'LF':
    #             away_lf = batter['name'].replace("'", " ") + "   " + hander
    #         elif batter['position'] == 'CF':
    #             away_cf = batter['name'].replace("'", " ") + "   " + hander
    #         elif batter['position'] == 'RF':
    #             away_rf = batter['name'].replace("'", " ") + "   " + hander
    #         elif batter['position'] == 'DH':
    #             away_dh = batter['name'].replace("'", " ") + "   " + hander




    # engine.execute(f"INSERT INTO position(game_id, game_date, team, role, c, b1, b2, b3, ss, lf, cf, rf, dh) \
    #                                 VALUES('{game_id}', '{game_date}', '{away_team}', 'away', '{away_c}', '{away_b1}', '{away_b2}', '{away_b3}', '{away_ss}', '{away_lf}', '{away_cf}', '{away_rf}', '{away_dh}');")
    # home_c = ""
    # home_b1 = ""
    # home_b2 = ""
    # home_b3 = ""
    # home_ss = ""
    # home_lf = ""
    # home_cf = ""
    # home_rf = ""
    # home_dh = ""

    # for batter in homeBatters:
    #     if batter['personId'] != 0 and batter['substitution'] == False:
    #         url = f"https://statsapi.mlb.com/api/v1/people/{batter['personId']}"
    #         response = requests.get(url)
    #         if response.status_code == 200:
    #             result = response.json()
    #             hander = result['people'][0]['batSide']['code']
    #         else:
    #             hander = 'R'

    #         if batter['position'] == 'C':
    #             home_c = batter['name'].replace("'", " ") + "   " + hander
    #         elif batter['position'] == '1B':
    #             home_b1 = batter['name'].replace("'", " ") + "   " + hander
    #         elif batter['position'] == '2B':
    #             home_b2 = batter['name'].replace("'", " ") + "   " + hander
    #         elif batter['position'] == '3B':
    #             home_b3 = batter['name'].replace("'", " ") + "   " + hander
    #         elif batter['position'] == 'SS':
    #             home_ss = batter['name'].replace("'", " ") + "   " + hander
    #         elif batter['position'] == 'LF':
    #             home_lf = batter['name'].replace("'", " ") + "   " + hander
    #         elif batter['position'] == 'CF':
    #             home_cf = batter['name'].replace("'", " ") + "   " + hander
    #         elif batter['position'] == 'RF':
    #             home_rf = batter['name'].replace("'", " ") + "   " + hander
    #         elif batter['position'] == 'DH':
    #             home_dh = batter['name'].replace("'", " ") + "   " + hander

    # engine.execute(f"INSERT INTO position(game_id, game_date, team, role, c, b1, b2, b3, ss, lf, cf, rf, dh) \
    #                                 VALUES('{game_id}', '{game_date}', '{home_team}', 'home', '{home_c}', '{home_b1}', '{home_b2}', '{home_b3}', '{home_ss}', '{home_lf}', '{home_cf}', '{home_rf}', '{home_dh}');")

    
    away_score = data['awayBattingTotals']['r']
    home_score = data['homeBattingTotals']['r']
    
    box_score = {
        'game_id': game_id,
        'game_date': game_date, 
        'away_team': away_team, 
        'home_team': home_team, 
        'away_score': away_score, 
        'home_score': home_score,
    }

    # Batting Data
    batter_data = {}
    batter_player = []
    away_batter_data, away_batter_playerid = get_batting_box_score(data, 'away')
    batter_player.extend(away_batter_playerid)
    batter_data['away'] = away_batter_data
    home_batter_data, home_batter_playerid = get_batting_box_score(data, 'home')
    batter_player.extend(home_batter_playerid)
    batter_data['home'] = home_batter_data

    if away_batter_data is None or home_batter_data is None: 
        return None
    
    box_score['batter'] = batter_data
    
    # Pitching Data
    pitcher_data = {}
    pitcher_starter = []
    pitcher_reliever = []
    away_pitcher_data, away_starter_playerid, away_reliever_playerid = get_pitching_box_score(data, 'away')
    pitcher_starter.append(away_starter_playerid)
    pitcher_reliever.extend(away_reliever_playerid)
    pitcher_data['away'] = away_pitcher_data
    home_pitcher_data, home_starter_playerid, home_reliever_playerid = get_pitching_box_score(data, 'home')
    pitcher_starter.append(home_starter_playerid)
    pitcher_reliever.extend(home_reliever_playerid)
    pitcher_data['home'] = home_pitcher_data
    
    if away_pitcher_data is None or home_pitcher_data is None: 
        return None
    
    box_score['pitcher'] = pitcher_data
    box_score['batterid'] = batter_player
    box_score['starterid'] = pitcher_starter
    box_score['bullpenid'] = pitcher_reliever
        
    return box_score

def update_database(): 
    engine = database.connect_to_db()
    # game_sched = mlb.schedule(start_date = "2024-04-08")
    # info_keys = ['game_id', 'game_datetime','away_name', 'home_name']
    # game_sched = [{k:v for k,v in el.items() if k in info_keys} for el in game_sched]
    # game_id_list = []
    # for game in game_sched:
    #     game_id_list.append(game['game_id'])
    game_id_list = ['745432']

    if len(game_id_list) > 0: 
        # Get Box Scores! 
        box_list = []
        tic = time.time()
        num_games = len(game_id_list)
        errored_games = []
        for game_id in game_id_list: 
            game_index = game_id_list.index(game_id)
            if(game_id == '747989'):
                continue
            box = get_box_score(game_id)
            if box is None: 
                errored_games.append(game_id)
                continue
            box_list.append(box)

            if game_index % 10 == 0: 
                print(f'Game {game_index} of {num_games} -- {time.time() - tic:.2f} sec')
        # Convert to df
        df = pd.DataFrame()
        if(box_list == []):
            new_last_record = pd.read_sql("SELECT * FROM updates", con = engine).iloc[-1]['last_record']
        else:
            for el in box_list:
                if el['away_score'] < el['home_score']:
                    winner = 1
                else:   
                    winner = 0

                print(str(winner))
                # game_table

                game_table_sql = 'INSERT INTO game_table(game_id, game_date, away_team, home_team, away_score, home_score, winner) VALUES (%s, %s, %s, %s, %s, %s, %s)'
                data_tuple = (el['game_id'], el['game_date'], el['away_team'], el['home_team'], el['away_score'], el['home_score'], winner)
                engine.execute(game_table_sql, data_tuple)
                # game_table_sql = 'INSERT INTO game_table( game_id, game_date, away_team, home_team, away_score, home_score, winner) VALUES (' + \
                #         '\'' + el['game_id'] + '\'' + ',' +  '\'' + el['game_date'] + '\'' +  ',' + '\'' +  el['away_team'] + '\'' +  ',' + \
                #         '\'' + el['home_team'] + '\'' +  ',' + '\'' +  el['away_score'] + '\'' +  ','  + '\'' + el['home_score']\
                #         + '\'' + ',' + '\'' + str(winner) + '\'' + ');'
                # engine.execute(game_table_sql)
                
                # pitcher_table insert query
                teams = ['away', 'home']
                for team in teams:
                    data = el['pitcher'][team]['starter']
                    
                    batter = 0
                    
                    if int(data['playerId']) in el['batterid']:
                        batter = 1

                    if data.get("pitchesThrown") is None or data.get("strikes") is None:
                        data['pitchesThrown'] = 0
                        data['strikes'] = 0

                    pitcher_table_sql = '''
                    INSERT INTO pitcher_table(
                        game_id, playerid, team, role, atbats, baseonballs, blownsaves, doubles, earnedruns, era,
                        hits, holds, homeruns, inningspitched, losses, pitchesthrown, rbi, runs, strikeouts, strikes, triples, whip, wins, batter
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    '''
                    data_tuple = (
                        el['game_id'], data['playerId'], team, 'starter',
                        data['atBats'], data['baseOnBalls'], data['blownSaves'], data['doubles'], data['earnedRuns'], data['era'],
                        data['hits'], data['holds'], data['homeRuns'], data['inningsPitched'], data['losses'], data['pitchesThrown'],
                        data['rbi'], data['runs'], data['strikeOuts'], data['strikes'], data['triples'], data['whip'], data['wins'], batter
                    )
                    engine.execute(pitcher_table_sql, data_tuple)

                    bullpenAvgdata = el['pitcher'][team]['bullpenAvg']

                    if bullpenAvgdata != {}:
                        if bullpenAvgdata.get("pitchesThrown") is None or bullpenAvgdata.get("strikes") is None:
                            bullpenAvgdata['pitchesThrown'] = 0
                            bullpenAvgdata['strikes'] = 0

                        bullpenAvg_table_sql = '''
                        INSERT INTO pitcher_table(
                            game_id, playerid, team, role, atbats, baseonballs, blownsaves, doubles, earnedruns, era,
                            hits, holds, homeruns, inningspitched, losses, pitchesthrown, rbi, runs, strikeouts, strikes, triples, whip, wins, batter
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        '''
                        data_tuple = (
                            el['game_id'], bullpenAvgdata['playerId'], team, 'bullpenAvg',
                            bullpenAvgdata['atBats'], bullpenAvgdata['baseOnBalls'], bullpenAvgdata['blownSaves'], bullpenAvgdata['doubles'], bullpenAvgdata['earnedRuns'], bullpenAvgdata['era'],
                            bullpenAvgdata['hits'], bullpenAvgdata['holds'], bullpenAvgdata['homeRuns'], bullpenAvgdata['inningsPitched'], bullpenAvgdata['losses'], bullpenAvgdata['pitchesThrown'],
                            bullpenAvgdata['rbi'], bullpenAvgdata['runs'], bullpenAvgdata['strikeOuts'], bullpenAvgdata['strikes'], bullpenAvgdata['triples'], bullpenAvgdata['whip'], bullpenAvgdata['wins'], 0
                        )

                        engine.execute(bullpenAvg_table_sql, data_tuple)

                    for bullpen in el['pitcher'][team]['bullpen']:
                        if bullpen.get("pitchesThrown") is None or bullpen.get("strikes") is None:
                            bullpen['pitchesThrown'] = 0
                            bullpen['strikes'] = 0
                        
                        batter = 0

                        if int(bullpen['playerId']) in el['batterid']:
                            batter = 1

                        # Define the SQL command with placeholders for parameters
                        bullpen_table_sql = '''
                        INSERT INTO pitcher_table(
                            game_id, playerid, team, role, atbats, baseonballs, blownsaves, doubles, earnedruns, era,
                            hits, holds, homeruns, inningspitched, losses, pitchesthrown, rbi, runs, strikeouts, strikes, triples, whip, wins, batter
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        '''

                        # Create a tuple of values to insert into the database
                        data_tuple = (
                            el['game_id'], bullpen['playerId'], team, 'bullpen',
                            bullpen['atBats'], bullpen['baseOnBalls'], bullpen['blownSaves'], bullpen['doubles'], bullpen['earnedRuns'], bullpen['era'],
                            bullpen['hits'], bullpen['holds'], bullpen['homeRuns'], bullpen['inningsPitched'], bullpen['losses'], bullpen['pitchesThrown'],
                            bullpen['rbi'], bullpen['runs'], bullpen['strikeOuts'], bullpen['strikes'], bullpen['triples'], bullpen['whip'], bullpen['wins'], batter
                        )

                        engine.execute(bullpen_table_sql, data_tuple)


                # batter_table insert query
                for team in teams:
                    for batter in el['batter'][team]:

                        pitcher = 0

                        if int(batter['playerId']) in el['starterid']:
                            pitcher = 1
                        
                        if int(batter['playerId']) in el['bullpenid']:
                            pitcher = 2

                        batter_table_sql = '''
                        INSERT INTO batter_table(
                            game_id, playerid, team, position, atbats, avg, baseonballs, doubles, hits, homeruns,
                            obp, ops, rbi, runs, slg, strikeouts, triples, substitution, pitcher
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        '''

                        # Create a tuple of values to be inserted
                        data_tuple = (
                            el['game_id'], batter['playerId'], team, batter['position'],
                            batter['atBats'], batter['avg'], batter['baseOnBalls'], batter['doubles'], batter['hits'], batter['homeRuns'],
                            batter['obp'], batter['ops'], batter['rbi'], batter['runs'], batter['slg'], batter['strikeOuts'], batter['triples'], batter['substitution'], pitcher
                        )
                        engine.execute(batter_table_sql, data_tuple)

                new_last_record = el['game_date']
    else: 
        new_last_record = pd.read_sql("SELECT * FROM updates", con = engine).iloc[-1]['last_record']
        

    tz = timezone('US/Eastern')
    last_update_date = date.today()
    last_update_time = datetime.now() + timedelta(hours = 3)
    last_update_time = datetime.strftime(last_update_time, '%H:%M:%S')
    new_updates = pd.DataFrame({'update_id': str(uuid.uuid4()), 
                                'update_date': last_update_date, 
                     'update_time': last_update_time, 
                     'last_record': new_last_record}, index = [0])

    new_updates.to_sql(con = engine, 
                 name = 'updates', 
                 if_exists = 'append', 
                 index = False)    
    print('DB Updated')
    return last_update_date, last_update_time, new_last_record, len(game_id_list)

update_database()