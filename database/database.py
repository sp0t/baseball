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



def connect_to_db(): 
    
    try: 
        engine = create_engine('postgresql://postgres:123@ec2-18-180-226-162.ap-northeast-1.compute.amazonaws.com:5432/betmlb', 
                                connect_args = {'connect_timeout': 10}, 
                                echo=False, pool_size=20, max_overflow=0)
        #engine = create_engine('postgresql://postgres:123@localhost:5432/testdb', 
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

    team_batters = [str(el) for el in data[team]['batters'][:9]]
    team_box_score = {}
    for team_batter in team_batters: 
        order = team_batters.index(team_batter)+1
        pbs = data[team]['players'][f'ID{team_batter}']['stats']['batting']
        pbs.update({'playerId': team_batter})

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

        pbs = {f'{team}_b{order}_{k}':v for k,v in pbs.items() if k not in ['leftOnBase', 'stolenBases']}
        team_box_score.update(pbs)

    return team_box_score

def get_pitching_box_score(data, team): 
    
    pitchers = data[team]['pitchers']
    if len(pitchers) == 0: 
        return None
    team_starter = str(data[team]['pitchers'][0])
    team_box_score = {}
    
    
    team_pitchers = [str(el) for el in data[team]['pitchers']]
    if len(team_pitchers) == 0: 
        return None
    elif len(team_pitchers) == 1:
        team_bullpen_data = None
        
    team_starter = team_pitchers[0]
    team_relievers = team_pitchers[1:]

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

    team_starter_data = {f'{team}_starter_{k}':v for k,v in team_starter_data.items() if k not in ['leftOnBase', 'stolenBases', 'note', 'notes','numberOfPitches']}


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
    team_bullpen_data = {f'{team}_bullpen_{k}':v for k,v in team_bullpen_data.items()}
    
    team_box_score.update(team_starter_data)
    team_box_score.update(team_bullpen_data)
    
    
    return team_box_score

def get_box_score(game_id): 
    
    data = mlb.boxscore_data(game_id)
    
    # Game Info 
    game_date = data['gameId'][:10]
    away_team = data['teamInfo']['away']['abbreviation']
    home_team = data['teamInfo']['home']['abbreviation']
    
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
    away_batter_data = get_batting_box_score(data, 'away')
    home_batter_data = get_batting_box_score(data, 'home')
    box_score.update(away_batter_data)
    box_score.update(home_batter_data)
    
    # Pitching Data
    away_pitcher_data = get_pitching_box_score(data, 'away')
    home_pitcher_data = get_pitching_box_score(data, 'home')
    
    if away_pitcher_data is None or home_pitcher_data is None: 
        return None
    box_score.update(away_pitcher_data)
    box_score.update(home_pitcher_data)
    
    box_score = {box_score['game_id']:box_score}
        
    
    return box_score

def update_database(): 
    engine = connect_to_db()
    res = engine.execute("SELECT game_id,game_date FROM game_table").fetchall()

    current_game_list = [el[0] for el in res]
    last_record = max([el[1] for el in res])
    last_record = datetime.strptime(last_record, '%Y/%m/%d').date()
    print(f'Old Last Record is {last_record}')
    game_id_list, errored_days = get_game_id_list(start_date = last_record, 
                                                  end_date = date.today() - timedelta(days = 1), 
                                                  show_progress = False )
    print(game_id_list, errored_days)

    game_id_list = [el for el in game_id_list if el not in current_game_list]
    print(f'Games to add = {len(game_id_list)}')
    if len(game_id_list) > 0: 
        # Get Box Scores! 
        box_list = []
        tic = time.time()
        num_games = len(game_id_list)
        errored_games = []
        for game_id in game_id_list: 
            game_index = game_id_list.index(game_id)
            box = get_box_score(game_id)
            if box is None: 
                errored_games.append(game_id)
                continue
            box_list.append(box)

            if game_index % 10 == 0: 
                print(f'Game {game_index} of {num_games} -- {time.time() - tic:.2f} sec')
        # Convert to df
        df = pd.DataFrame()
        for box in box_list: 
            df = pd.concat([df, pd.DataFrame(box).T])
        df = df.drop([col for col in df.columns if 'note' in col], axis = 1)
        meta_cols = ['game_id','game_date', 'away_team', 'home_team', 'away_score', 'home_score']
        df1 = df[meta_cols]
        df2 = df[[col for col in df.columns if col not in meta_cols]]
        df = pd.concat([df1, df2], axis = 1)
        df['winner'] = df.apply(lambda row: 1 if row['home_score'] > row['away_score'] else 0, axis = 1)
        df = df.astype(str).reset_index(drop = True)
        df.columns = df.columns.str.lower()
        new_games = df
        new_last_record = new_games['game_date'].max()
        
        for index, row in new_games.iterrows():
            #game_table
            game_table_sql = 'INSERT INTO game_table( game_id, game_date, away_team, home_team, away_score, home_score, winner) VALUES (' + \
                     '\'' + str(row[0]) + '\'' + ',' +  '\'' + row[1] + '\'' +  ',' + '\'' +  row[2] + '\'' +  ',' + \
                     '\'' + str(row[3]) + '\'' +  ',' + '\'' +  str(row[4]) + '\'' +  ','  + '\'' + str(row[5])\
                     + '\'' + ',' + '\'' +str(row[338]) + '\'' + ');'
            engine.execute(game_table_sql)
            
            #pitcher_table insert query
            for k in range(1, 5):
                if k % 4 == 0:
                    key, team, role = 298, 'home', 'bullpen'
                elif k % 4 == 1:
                    key, team, role = 152, 'away', 'starter'
                elif k % 4 == 2:
                    key, team, role = 132, 'away', 'bullpen'
                elif k % 4 == 3:
                    key, team, role = 318, 'home', 'starter'

                pitcher_table_sql = 'INSERT INTO pitcher_table( game_id, playerid, team, role, atbats, baseonballs, blownsaves, doubles, earnedruns, era,' \
                              'hits, holds, homeruns, inningspitched, losses, pitchesthrown, rbi, runs, strikeouts, strikes, triples, whip, wins) VALUES (' + \
                             '\'' + str(row[0]) + '\'' + ',' +  '\'' + str(row[key+12]) + '\'' +  ',' + '\'' +  team + '\'' +  ',' + '\'' + role + '\'' +  ',' + \
                             '\'' + str(row[key+0]) + '\'' +  ',' + '\'' + str(row[key+1]) + '\'' +  ',' + '\'' + str(row[key+2]) + '\'' +  ',' + \
                             '\'' + str(row[key+3]) + '\'' +  ',' + '\'' + str(row[key+4]) + '\'' +  ',' + '\'' + str(row[key+5]) + '\'' + ',' + \
                             '\'' + str(row[key+6]) + '\'' +  ',' + '\'' + str(row[key+7]) + '\'' +  ',' + '\'' + str(row[key+8]) + '\'' +  ',' + \
                             '\'' + str(row[key+9]) + '\'' +  ',' + '\'' + str(row[key+10]) + '\'' +  ',' + '\'' + str(row[key+11]) + '\'' +  ',' + \
                             '\'' + str(row[key+13]) + '\'' +  ',' + '\'' + str(row[key+14]) + '\'' +  ',' + '\'' + str(row[key+15]) + '\'' +  ',' + \
                             '\'' + str(row[key+16]) + '\'' +  ',' + '\'' + str(row[key+17]) + '\'' +  ',' + '\'' + str(row[key+18]) + '\'' +  ',' + \
                             '\'' + str(row[key+19]) + '\'' + ');'
                engine.execute(pitcher_table_sql)
            
             #batter_table insert query
            for j in range(1, 19):
                if(j < 10):
                    batter_table_sql = 'INSERT INTO batter_table( game_id, playerid, team, position, atbats, avg, baseonballs, doubles, hits, homeruns, '\
                                 'obp, ops, rbi, runs, slg, strikeouts, triples) VALUES (' + \
                                 '\'' + str(row[0]) + '\'' + ',' +  '\'' + str(row[6 + (j - 1) * 14 + 8]) + '\'' +  ',' + \
                                 '\'' + 'away' + '\'' + ',' + '\'' +  str(j) + '\'' +  ',' +\
                                 '\'' + str(row[6 + (j - 1) * 14 + 0]) + '\'' +  ',' + '\'' + str(row[6 + (j - 1) * 14 + 1]) + '\'' +  ',' + \
                                 '\'' + str(row[6 + (j - 1) * 14 + 2]) + '\'' +  ',' + '\'' + str(row[6 + (j - 1) * 14 + 3]) + '\'' +  ',' + \
                                 '\'' + str(row[6 + (j - 1) * 14 + 4]) + '\'' +  ',' + '\'' + str(row[6 + (j - 1) * 14 + 5]) + '\'' +  ',' + \
                                 '\'' + str(row[6 + (j - 1) * 14 + 6]) + '\'' +  ',' + '\'' + str(row[6 + (j - 1) * 14 + 7]) + '\'' +  ',' + \
                                 '\'' + str(row[6 + (j - 1) * 14 + 9]) + '\'' +  ',' + '\'' + str(row[6 + (j - 1) * 14 + 10]) + '\'' +  ',' + '\'' + str(row[6 + (j - 1) * 14 + 11]) + '\'' +  ',' + \
                                 '\'' + str(row[6 + (j - 1) * 14 + 12]) + '\'' +  ',' + '\'' + str(row[6 + (j - 1) * 14 + 13]) + '\'' + ');'
                else:
                    batter_table_sql = 'INSERT INTO batter_table( game_id, playerid, team, position, atbats, avg, baseonballs, doubles, hits, homeruns, '\
                                 'obp, ops, rbi, runs, slg, strikeouts, triples) VALUES (' + \
                                 '\'' + str(row[0]) + '\'' + ',' +  '\'' + str(row[172 + (j - 10) * 14 + 8]) + '\'' +  ',' + \
                                 '\'' + 'home' + '\'' + ',' + '\'' +  str(j - 9) + '\'' +  ',' +\
                                 '\'' + str(row[172 + (j - 10) * 14 + 0]) + '\'' +  ',' + '\'' + str(row[172 + (j - 10) * 14 + 1]) + '\'' +  ',' + \
                                 '\'' + str(row[172 + (j - 10) * 14 + 2]) + '\'' +  ',' + '\'' + str(row[172 + (j - 10) * 14 + 3]) + '\'' +  ',' + \
                                 '\'' + str(row[172 + (j - 10) * 14 + 4]) + '\'' +  ',' + '\'' + str(row[172 + (j - 10) * 14 + 5]) + '\'' +  ',' + \
                                 '\'' + str(row[172 + (j - 10) * 14 + 6]) + '\'' +  ',' + '\'' + str(row[172 + (j - 10) * 14 + 7]) + '\'' +  ',' + \
                                 '\'' + str(row[172 + (j - 10) * 14 + 9]) + '\'' +  ',' + '\'' + str(row[172 + (j - 10) * 14 + 10]) + '\'' +  ',' + '\'' + str(row[6 + (j - 10) * 14 + 11]) + '\'' +  ',' + \
                                 '\'' + str(row[172 + (j - 12) * 14 + 11]) + '\'' +  ',' + '\'' + str(row[172 + (j - 10) * 14 + 13]) + '\'' + ');'
                engine.execute(batter_table_sql)
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

