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
        # engine = create_engine('postgresql://postgres:lucamlb123@localhost:5432/betmlb', connect_args = {'connect_timeout': 10}, echo=False, pool_size=20, max_overflow=0)
        engine = create_engine('postgresql://postgres:123@localhost:5432/testdb', 
                               connect_args = {'connect_timeout': 10}, 
                               echo=False, pool_size=20, max_overflow=0)
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
    return team_box_score

def get_pitching_box_score(data, team): 
    
    key = team + 'Pitchers'
    data_info = data[key]
    team_starter = []
    team_relievers = []
    starter = True


    for el in data_info:
        if el['personId'] != 0: 
            if starter == True:
                team_starter.append(str(el['personId']))
                starter = False
            elif starter == False:
                team_relievers.append(str(el['personId']))
    team_box_score = {}

    if len(team_starter) == 0: 
        return None
    elif len(team_relievers) == 0:
        team_bullpen_data = None

    # Starter Data 
    team_starter_data = data[team]['players']['ID' + team_starter[0]]['stats']['pitching']
    team_starter_data.update({'playerId': team_starter[0]})
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
    # team_bullpen_data = pd.DataFrame(team_reliever_data_list).mean().to_dict()
    
    team_box_score['starter'] = team_starter_data
    team_box_score['bullpen'] = team_reliever_data_list

    # print(team_box_score)
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
    batter_data = {}
    away_batter_data = get_batting_box_score(data, 'away')
    batter_data['away'] = away_batter_data
    home_batter_data = get_batting_box_score(data, 'home')
    batter_data['home'] = home_batter_data

    if away_batter_data is None or home_batter_data is None: 
        return None
    
    box_score['batter'] = batter_data
    
    # Pitching Data
    pitcher_data = {}
    away_pitcher_data = get_pitching_box_score(data, 'away')
    pitcher_data['away'] = away_pitcher_data
    home_pitcher_data = get_pitching_box_score(data, 'home')
    pitcher_data['home'] = home_pitcher_data
    
    if away_pitcher_data is None or home_pitcher_data is None: 
        return None
    
    box_score['pitcher'] = pitcher_data
        
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
        if(box_list == []):
            new_last_record = pd.read_sql("SELECT * FROM updates", con = engine).iloc[-1]['last_record']
        else:
            for box in box_list: 
                df = pd.concat([df, pd.DataFrame(box).T])
            df = df.drop([col for col in df.columns if 'note' in col], axis = 1)

            if df is None:
                new_last_record = pd.read_sql("SELECT * FROM updates", con = engine).iloc[-1]['last_record']
            else:
                for el in box_list:
                    if el['away_score'] < el['home_score']:
                        winner = 1
                    else:   
                        winner = 0
                    # game_table
                    game_table_sql = 'INSERT INTO game_table( game_id, game_date, away_team, home_team, away_score, home_score, winner) VALUES (' + \
                            '\'' + el['game_id'] + '\'' + ',' +  '\'' + el['game_date'] + '\'' +  ',' + '\'' +  el['away_team'] + '\'' +  ',' + \
                            '\'' + el['home_team'] + '\'' +  ',' + '\'' +  el['away_score'] + '\'' +  ','  + '\'' + el['home_score']\
                            + '\'' + ',' + '\'' + str(winner) + '\'' + ');'
                    engine.execute(game_table_sql)
                    
                    # pitcher_table insert query
                    teams = ['away', 'home']
                    for team in teams:
                        data = el['pitcher'][team]['starter']

                        if data.get("pitchesThrown") is None or data.get("strikes") is None:
                                data['pitchesThrown'] = 0
                                data['strikes'] = 0

                        pitcher_table_sql = 'INSERT INTO pitcher_table( game_id, playerid, team, role, atbats, baseonballs, blownsaves, doubles, earnedruns, era,' \
                                    'hits, holds, homeruns, inningspitched, losses, pitchesthrown, rbi, runs, strikeouts, strikes, triples, whip, wins) VALUES (' + \
                                    '\'' + el['game_id'] + '\'' + ',' +  '\'' + str(data['playerId']) + '\'' +  ',' + '\'' + team + '\'' + ',' + '\'' + 'starter' + '\'' + ',' + \
                                    '\'' + str(data['atBats']) + '\'' +  ',' + '\'' + str(data['baseOnBalls']) + '\'' +  ',' + '\'' + str(data['blownSaves']) + '\'' +  ',' + \
                                    '\'' + str(data['doubles']) + '\'' +  ',' + '\'' + str(data['earnedRuns']) + '\'' +  ',' + '\'' + str(data['era']) + '\'' + ',' + \
                                    '\'' + str(data['hits']) + '\'' +  ',' + '\'' + str(data['holds']) + '\'' +  ',' + '\'' + str(data['homeRuns']) + '\'' +  ',' + \
                                    '\'' + str(data['inningsPitched']) + '\'' +  ',' + '\'' + str(data['losses']) + '\'' +  ',' + '\'' + str(data['pitchesThrown']) + '\'' +  ',' + \
                                    '\'' + str(data['rbi']) + '\'' +  ',' + '\'' + str(data['runs']) + '\'' +  ',' + '\'' + str(data['strikeOuts']) + '\'' +  ',' + \
                                    '\'' + str(data['strikes']) + '\'' +  ',' + '\'' + str(data['triples']) + '\'' +  ',' + '\'' + str(data['whip']) + '\'' +  ',' + \
                                    '\'' + str(data['wins']) + '\'' + ');'
                        engine.execute(pitcher_table_sql)
                        
                        for bullpen in el['pitcher'][team]['bullpen']:
                            if bullpen.get("pitchesThrown") is None or bullpen.get("strikes") is None:
                                bullpen['pitchesThrown'] = 0
                                bullpen['strikes'] = 0


                            bullpen_table_sql = 'INSERT INTO pitcher_table( game_id, playerid, team, role, atbats, baseonballs, blownsaves, doubles, earnedruns, era,' \
                                    'hits, holds, homeruns, inningspitched, losses, pitchesthrown, rbi, runs, strikeouts, strikes, triples, whip, wins) VALUES (' + \
                                    '\'' + el['game_id'] + '\'' + ',' +  '\'' + str(bullpen['playerId']) + '\'' +  ',' + '\'' + team + '\'' + ',' + '\'' + 'bullpen' + '\'' + ',' + \
                                    '\'' + str(bullpen['atBats']) + '\'' +  ',' + '\'' + str(bullpen['baseOnBalls']) + '\'' +  ',' + '\'' + str(bullpen['blownSaves']) + '\'' +  ',' + \
                                    '\'' + str(bullpen['doubles']) + '\'' +  ',' + '\'' + str(bullpen['earnedRuns']) + '\'' +  ',' + '\'' + str(bullpen['era']) + '\'' + ',' + \
                                    '\'' + str(bullpen['hits']) + '\'' +  ',' + '\'' + str(bullpen['holds']) + '\'' +  ',' + '\'' + str(bullpen['homeRuns']) + '\'' +  ',' + \
                                    '\'' + str(bullpen['inningsPitched']) + '\'' +  ',' + '\'' + str(bullpen['losses']) + '\'' +  ',' + '\'' + str(bullpen['pitchesThrown']) + '\'' +  ',' + \
                                    '\'' + str(bullpen['rbi']) + '\'' +  ',' + '\'' + str(bullpen['runs']) + '\'' +  ',' + '\'' + str(bullpen['strikeOuts']) + '\'' +  ',' + \
                                    '\'' + str(bullpen['strikes']) + '\'' +  ',' + '\'' + str(bullpen['triples']) + '\'' +  ',' + '\'' + str(bullpen['whip']) + '\'' +  ',' + \
                                    '\'' + str(bullpen['wins']) + '\'' + ');'
                            engine.execute(bullpen_table_sql)

                    # batter_table insert query
                    for team in teams:
                        for batter in el['batter'][team]:
                            batter_table_sql = 'INSERT INTO batter_table( game_id, playerid, team, position, atbats, avg, baseonballs, doubles, hits, homeruns, '\
                                        'obp, ops, rbi, runs, slg, strikeouts, triples, substitution) VALUES (' + \
                                        '\'' + el['game_id'] + '\'' + ',' +  '\'' + str(batter['playerId']) + '\'' +  ',' + \
                                        '\'' + team + '\'' + ',' + '\'' +  str(batter['position']) + '\'' +  ',' +\
                                        '\'' + str(batter['atBats']) + '\'' +  ',' + '\'' + str(batter['avg']) + '\'' +  ',' + \
                                        '\'' + str(batter['baseOnBalls']) + '\'' +  ',' + '\'' + str(batter['doubles']) + '\'' +  ',' + \
                                        '\'' + str(batter['hits']) + '\'' +  ',' + '\'' + str(batter['homeRuns']) + '\'' +  ',' + \
                                        '\'' + str(batter['obp']) + '\'' +  ',' + '\'' + str(batter['ops']) + '\'' +  ',' + \
                                        '\'' + str(batter['rbi']) + '\'' +  ',' + '\'' + str(batter['runs']) + '\'' +  ',' + '\'' + str(batter['slg']) + '\'' +  ',' + \
                                        '\'' + str(batter['strikeOuts']) + '\'' +  ',' + '\'' + str(batter['triples']) + '\'' + ',' + '\'' + str(batter['substitution']) + '\'' + ');'
                            engine.execute(batter_table_sql)
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
    