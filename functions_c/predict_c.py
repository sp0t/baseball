# Dependencies
import pickle
import statsapi as mlb
import time
from datetime import date, timedelta, datetime
import numpy as np
import pandas as pd
import sqlite3
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from database import database
import joblib
import warnings 
from schedule import schedule
from sqlalchemy import text
from functions_c import batting_c, starters_c, bullpen_c

warnings.filterwarnings('ignore')


# Modules 

# Setup 
batter_id_cols = ['away_b1_playerId','away_b2_playerId','away_b3_playerId',
                  'away_b4_playerId','away_b5_playerId','away_b6_playerId',
                  'away_b7_playerId', 'away_b8_playerId', 'away_b9_playerId', 
                      
                  'home_b1_playerId', 'home_b2_playerId', 'home_b3_playerId',
                  'home_b4_playerId', 'home_b5_playerId', 'home_b6_playerId',
                  'home_b7_playerId', 'home_b8_playerId', 'home_b9_playerId']

pitcher_id_cols = ['away_starter_playerId', 'home_starter_playerId']


away_batter_id_cols = [col for col in batter_id_cols if 'away' in col]
home_batter_id_cols = [col for col in batter_id_cols if 'home' in col]

def save_batter_data(engine, row, away_batters, home_batters, gameId, rosters): 

    d_list = []
    for i in range(1,10): 
        recent_cols=[col for col in row if f'away_recent_b{i}' in col]
        career_cols=[col for col in row.columns if f'away_career_b{i}' in col]
        player_stats=row[career_cols+recent_cols].to_dict('records')[0]

        recent_cols=[col[5:].replace(f'_b{i}', '') for col in recent_cols]
        career_cols=['career_'+col[15:] for col in career_cols]
        player_stats=dict(zip(career_cols+recent_cols, list(player_stats.values())))
        player_stats={k:np.round(v,4) for k,v in player_stats.items()}
        d_list.append(player_stats)
    away_batter_df = pd.DataFrame(d_list)
    away_batter_df.insert(0, 'batterOrder', [f"Batter {i}" for i in range(1,10)])
    away_batter_df.insert(1, 'game_id', gameId)
    away_batter_df.insert(2, 'player_id', away_batters)
    away_batter_df=away_batter_df.set_index('batterOrder')

    # Home Batters
    d_list = []
    for i in range(1,10): 
        recent_cols=[col for col in row if f'home_recent_b{i}' in col]
        career_cols=[col for col in row.columns if f'home_career_b{i}' in col]
        player_stats=row[career_cols+recent_cols].to_dict('records')[0]

        recent_cols=[col[5:].replace(f'_b{i}', '') for col in recent_cols]
        career_cols=['career_'+col[15:] for col in career_cols]
        player_stats=dict(zip(career_cols+recent_cols, list(player_stats.values())))
        player_stats={k:np.round(v,4) for k,v in player_stats.items()}
        d_list.append(player_stats)
    home_batter_df = pd.DataFrame(d_list)
    home_batter_df.insert(0, 'batterOrder', [f"Batter {i}" for i in range(1,10)])
    home_batter_df.insert(1, 'game_id', gameId)
    home_batter_df.insert(2, 'player_id', home_batters)
    home_batter_df=home_batter_df.set_index('batterOrder')

    
    away_batter_df.index = ['Away ' + el for el in away_batter_df.index]
    home_batter_df.index = ['Home ' + el for el in home_batter_df.index]

    # blank_row = pd.DataFrame(dict(zip(list(away_batter_df.columns), np.repeat('//', len(away_batter_df.columns)))), index = ['//'])
    # batter_df = pd.concat([away_batter_df, blank_row])
    batter_df = pd.concat([away_batter_df, home_batter_df])
    data = mlb.boxscore_data(gameId)
    gamedate = data['gameId'][:10]

    state = False

    for el in rosters['position']['away']:
        if el != int(away_batters[rosters['position']['away'][el] - 1]):
            state = False
        else:
            state = True
    for el in rosters['position']['home']:
        if el != int(home_batters[rosters['position']['home'][el] - 1]):
            state = False
        else:
            state = True

    for index, row in batter_df.iterrows():
        if state:
            engine.execute(text(f"INSERT INTO batter_stats_c(game_id, game_date, position, player_id, career_atBats, career_avg, career_homeRuns, career_obp, career_ops, career_rbi, career_slg, career_strikeOuts, recent_atBats, recent_avg, recent_homeRuns, recent_obp, recent_ops, recent_rbi, recent_slg, recent_strikeOuts, difficulty_rating) \
                                    VALUES('{gameId}', '{gamedate}', '{index}', '{int(row['player_id'])}', '{round(float(row['career_atBats']), 3)}', '{round(float(row['career_avg']), 3)}', '{round(float(row['career_homeRuns']), 3)}', '{round(float(row['career_obp']), 3)}', '{round(float(row['career_ops']), 3)}', '{round(float(row['career_rbi']), 3)}', '{round(float(row['career_slg']), 3)}', '{round(float(row['career_strikeOuts']), 3)}', '{round(float(row['recent_atBats']), 3)}', '{round(float(row['recent_avg']), 3)}', '{round(float(row['recent_homeRuns']), 3)}', '{round(float(row['recent_obp']), 3)}', '{round(float(row['recent_ops']), 3)}', '{round(float(row['recent_rbi']), 3)}', '{round(float(row['recent_slg']), 3)}', '{round(float(row['recent_strikeOuts']), 3)}', \
                                        '{round(float(row['recent_difficulty']), 3)}') ON CONFLICT ON CONSTRAINT batter_stats_c_game_id_player_id_key DO UPDATE SET game_date = excluded.game_date, career_atBats = excluded.career_atBats, career_avg = excluded.career_avg, career_homeRuns = excluded.career_homeRuns, career_obp = excluded.career_obp, career_ops = excluded.career_ops, career_rbi = excluded.career_rbi, career_slg = excluded.career_slg, career_strikeOuts = excluded.career_strikeOuts, \
                                        recent_atBats = excluded.recent_atBats, recent_avg = excluded.recent_avg, recent_homeRuns = excluded.recent_homeRuns, recent_obp = excluded.recent_obp, recent_ops = excluded.recent_ops, recent_rbi = excluded.recent_rbi, recent_slg = excluded.recent_slg, recent_strikeOuts = excluded.recent_strikeOuts, difficulty_rating = excluded.difficulty_rating;"))
    
    return batter_df

def save_pitcher_data(engine, row, away_starter, home_starter, gameId, rosters): 
    away_recent_cols = [col for col in row.columns if 'away_starter_recent' in col]
    away_career_cols = [col for col in row.columns if 'away_starter_career' in col]
    player_stats = row[away_career_cols+away_recent_cols].to_dict('records')[0]
    player_stats = dict(zip([el.replace('away_starter_', '') for el in player_stats], player_stats.values()))
    away_df = pd.DataFrame(player_stats, index = ["Away Starter"])
    away_df.insert(0, 'player_id', away_starter)

    home_recent_cols = [col for col in row.columns if 'home_starter_recent' in col]
    home_career_cols = [col for col in row.columns if 'home_starter_career' in col]
    player_stats = row[home_career_cols+home_recent_cols].to_dict('records')[0]
    player_stats = dict(zip([el.replace('home_starter_', '') for el in player_stats], player_stats.values()))
    home_df = pd.DataFrame(player_stats, index = ["Home Starter"])
    home_df.insert(0, 'player_id', home_starter)

    pitcher_df = pd.concat([away_df,home_df]).T.astype(str)
    pitchers = pitcher_df.T
    data = mlb.boxscore_data(gameId)
    gamedate = data['gameId'][:10]

    state = False

    for el in rosters['pitcher']['away']:
        if el != int(away_starter):
            state = False
        else:
            state = True
    for el in rosters['pitcher']['home']:
        if el != int(home_starter):
            state = False
        else:
            state = True
    for index, row in pitchers.iterrows():
        if state:
            engine.execute(text(f"INSERT INTO pitcher_stats_c(game_id, game_date, position, player_id, career_era, career_homeRuns, career_whip, career_battersFaced, recent_era, recent_homeRuns, recent_whip, recent_battersFaced, difficulty_rating) \
                                    VALUES('{gameId}', '{gamedate}', '{index}', '{int(row['player_id'])}', '{round(float(row['career_era']), 3)}', '{round(float(row['career_homeRuns']), 3)}', '{round(float(row['career_whip']), 3)}', '{round(float(row['career_battersFaced']), 3)}', '{round(float(row['recent_era']), 3)}', '{round(float(row['recent_homeRuns']), 3)}', '{round(float(row['recent_whip']), 3)}', '{round(float(row['recent_battersFaced']), 3)}', \
                                    '{round(float(row['recent_difficulty']), 3)}') ON CONFLICT ON CONSTRAINT pitcher_stats_c_game_id_player_id_key DO UPDATE SET game_date = excluded.game_date, career_era = excluded.career_era, career_homeRuns = excluded.career_homeRuns, career_whip = excluded.career_whip, career_battersFaced = excluded.career_battersFaced, recent_era = excluded.recent_era, recent_homeRuns = excluded.recent_homeRuns, recent_whip = excluded.recent_whip, recent_battersFaced = excluded.recent_battersFaced, difficulty_rating = excluded.difficulty_rating;"))
 
    return pitcher_df

def get_df(engine, batter_id_cols, pitcher_id_cols): 
    df = pd.read_sql('SELECT * FROM games', con = engine)
    for col in batter_id_cols: 
        df[col] = df[col].astype(float).astype(str).str.replace('.', ',').str.replace(',0', '')
    for col in pitcher_id_cols: 
        df[col] = df[col].astype(float).astype(str).str.replace('.', ',').str.replace(',0', '')
    df['game_date'] = [datetime.strptime(el, '%Y/%m/%d') for el in df['game_date']]
    df = df.drop('index', axis = 1)
    
    return df

def feature_selection(X_test, fill_null = True): 
    
    column_pattern = 'b\d{1}_rbi|avg|slg|b\d{1}_obp|b\d{1}_ops|homeRuns|inning|era|whip|atBats|baseOnBalls|difficulty|b\d{1}_strikeOuts'
    feature_cols = X_test.columns[X_test.columns.str.contains(column_pattern)]
    X_test = X_test[feature_cols]
    
    if fill_null: 
        X_test = X_test.fillna(0)
        
    return X_test

def addBattersFaced(X_test, bullpen = False): 
    
    
    starter_col_list = ['away_starter_recent_', 'away_starter_career_', 
                'home_starter_recent_', 'home_starter_career_']
    
    for col in starter_col_list: 
        X_test[col + 'battersFaced'] = X_test[col + 'atBats'] + X_test[col + 'baseOnBalls']
        
    if bullpen: 
        bullpen_col_list = ['away_bullpen_recent_', 'away_bullpen_career_', 
                'home_bullpen_recent_', 'home_bullpen_career_']
        
        for col in bullpen_col_list: 
            X_test[col + 'battersFaced'] = X_test[col + 'atBats'] + X_test[col + 'baseOnBalls']
            
    drop_cols = [col for col in X_test.columns if 'inningsPitched' in col or 'baseOnBalls' in col]
    drop_cols = drop_cols + ['away_starter_recent_atBats', 'away_starter_career_atBats', 
                             'home_starter_recent_atBats', 'home_starter_career_atBats', ]
    X_test = X_test.drop(drop_cols,axis=1)   
    column_names = X_test.columns
    
    return X_test, column_names 

def standardizeData(X_test, column_names): 
    scaler = joblib.load("functions/scaler.bin")
    X_test=scaler.transform(X_test)
    X_test = pd.DataFrame(X_test, columns = column_names)
    
    return X_test

def get_probabilities(params): 
    
    engine = database.connect_to_db()

    pred_1c = [[0.51486457, 0.48513543]]
    return pred_1c


    away_batters, home_batters = [str(el) for el in params['away_batters']], [str(el) for el in params['home_batters']]
    away_starters, home_starters = [str(el) for el in params['away_starters']], [str(el) for el in params['home_starters']]
    savestate = params['savestate']
    away_starter = away_starters[0]
    home_starter = home_starters[0]

    away_name, home_name = params['away_name'], params['home_name']
    game_id = params['game_id']
    
    # Get Data
    game_date = datetime.today().strftime("%Y/%m/%d")
    
    order = 1

    away_batter_data = {}
    home_batter_data = {}
    away_starter_data = {}
    home_starter_data = {}
    away_bullpen_data = {}
    home_bullpen_data = {}

    rename_dict = {'pitchesthrown': 'pitchesThrown', 'player_id': 'playerId', 'strikeouts': 'strikeOuts', 
            'baseonballs': 'baseOnBalls', 'homeruns': 'homeRuns', 'atbats': 'atBats', 
            'inningspitched': 'inningsPitched', 'earnedruns': 'earnedRuns'
            }
    
    batter_stat_list = ['home_score', 'away_score', 'atBats', 'avg', 'baseOnBalls', 'doubles', 'hits', 'homeRuns', 'obp', 'ops', 'playerId', 'rbi', 'runs', 
                        'slg', 'strikeOuts', 'triples', 'season', 'singles']
    pitcher_stat_list=[
        'atBats', 'baseOnBalls', 'blownSave', 'doubles', 'earnedRuns', 'era', 'hits', 'holds', 'homeRuns', 'inningsPitched', 
        'losses', 'pitchesThrown', 'playerId', 'rbi', 'runs', 'strikeOuts', 'strikes', 'triples', 'whip',  'wins']

    team_recent_data = {}
    team_career_data = {}
    for batter in away_batters:
        print('awayBatter============>', batter)
        away_batter_res = pd.read_sql(f"SELECT * FROM predict_batter_stats WHERE game_id = '{game_id}' AND player_id = '{batter}';", con = engine).to_dict('records')
        if (len(away_batter_res) > 0 ):
            print('is in the table')
            for away_stas in away_batter_res:
                if away_stas['role'] == 'recent':
                    keys_to_remove = ['game_date', 'game_id', 'player_name', 'team', 'role']
                    for key in keys_to_remove:
                        away_stas.pop(key, None)

                    updated_stas = {}
                    for old_key, value in away_stas.items():
                        if old_key in rename_dict.keys():
                            updated_stas[rename_dict[old_key]] = value
                        else:
                            updated_stas[old_key] = value

                    recent_data = {f'away_recent_b{order}_{k}':v for k,v in updated_stas.items()}
                    team_recent_data.update(recent_data)
                elif away_stas['role'] == 'career':
                    keys_to_remove = ['game_date', 'game_id', 'player_id', 'player_name', 'team', 'role', 'difficulty']
                    for key in keys_to_remove:
                        away_stas.pop(key, None)

                    updated_stas = {}
                    for old_key, value in away_stas.items():
                        if old_key in rename_dict.keys():
                            updated_stas[rename_dict[old_key]] = value
                        else:
                            updated_stas[old_key] = value

                    career_data = {f'away_career_b{order}_{k}':v for k,v in updated_stas.items()}
                    team_career_data.update(career_data)
        else:
            print('not in the table')
            player_df = batting_c.get_batter_df(batter, game_date)

            if len(player_df) > 0 : 
                recent_data, games = batting_c.process_recent_batter_data(player_df, game_date, '', batter_stat_list)
                career_data = batting_c.process_career_batter_data(games, batter_stat_list)
            else: 
                recent_data = dict(zip(batter_stat_list, np.repeat(0, len(batter_stat_list))))
                recent_data['dificulty'] = 0
                career_data = dict(zip(batter_stat_list, np.repeat(0, len(batter_stat_list))))

            player_name_res = pd.read_sql(f"SELECT * FROM player_table WHERE p_id = '{batter}';", con = engine).to_dict('records')
            player_name = ''

            if (len(player_name_res) > 0):
                player_name = player_name_res[0]['p_name']
            else:
                player_name = batter

            print('Insert in the table')

            engine.execute(text(f"INSERT INTO predict_batter_stats(game_date, game_id, player_id, player_name, team, role, atBats, avg, baseOnBalls, doubles, hits, homeRuns, obp, ops, rbi, runs, slg, strikeOuts, triples, singles, difficulty) \
                                    VALUES('{game_date}', '{game_id}', '{batter}', '{player_name}', 'away', 'recent', '{round(float(recent_data['atBats']), 3)}', '{round(float(recent_data['avg']), 3)}', '{round(float(recent_data['baseOnBalls']), 3)}', '{round(float(recent_data['doubles']), 3)}', '{round(float(recent_data['hits']), 3)}', '{round(float(recent_data['homeRuns']), 3)}', '{round(float(recent_data['obp']), 3)}', '{round(float(recent_data['ops']), 3)}', '{round(float(recent_data['rbi']), 3)}', '{round(float(recent_data['runs']), 3)}', '{round(float(recent_data['slg']), 3)}', '{round(float(recent_data['strikeOuts']), 3)}', '{round(float(recent_data['triples']), 3)}', '{round(float(recent_data['singles']), 3)}', '{round(float(recent_data['difficulty']), 3)}')\
                                    ON CONFLICT ON CONSTRAINT predict_batter_stats_key DO UPDATE SET atBats = excluded.atBats, avg = excluded.avg, baseOnBalls = excluded.baseOnBalls, doubles = excluded.doubles, hits = excluded.hits, homeRuns = excluded.homeRuns, obp = excluded.obp, ops = excluded.ops, rbi = excluded.rbi, runs = excluded.runs, slg = excluded.slg, strikeOuts = excluded.strikeOuts, triples = excluded.triples, singles = excluded.singles, difficulty = excluded.difficulty;"))
            engine.execute(text(f"INSERT INTO predict_batter_stats(game_date, game_id, player_id, player_name, team, role, atBats, avg, baseOnBalls, doubles, hits, homeRuns, obp, ops, rbi, runs, slg, strikeOuts, triples, singles, difficulty) \
                                    VALUES('{game_date}', '{game_id}', '{batter}', '{player_name}', 'away', 'career', '{round(float(career_data['atBats']), 3)}', '{round(float(career_data['avg']), 3)}', '{round(float(career_data['baseOnBalls']), 3)}', '{round(float(career_data['doubles']), 3)}', '{round(float(career_data['hits']), 3)}', '{round(float(career_data['homeRuns']), 3)}', '{round(float(career_data['obp']), 3)}', '{round(float(career_data['ops']), 3)}', '{round(float(career_data['rbi']), 3)}', '{round(float(career_data['runs']), 3)}', '{round(float(career_data['slg']), 3)}', '{round(float(career_data['strikeOuts']), 3)}', '{round(float(career_data['triples']), 3)}', '{round(float(career_data['singles']), 3)}', '1')\
                                    ON CONFLICT ON CONSTRAINT predict_batter_stats_key DO UPDATE SET atBats = excluded.atBats, avg = excluded.avg, baseOnBalls = excluded.baseOnBalls, doubles = excluded.doubles, hits = excluded.hits, homeRuns = excluded.homeRuns, obp = excluded.obp, ops = excluded.ops, rbi = excluded.rbi, runs = excluded.runs, slg = excluded.slg, strikeOuts = excluded.strikeOuts, triples = excluded.triples, singles = excluded.singles, difficulty = excluded.difficulty;"))
            # break
            recent_data = {f'away_recent_b{order}_{k}':v for k,v in recent_data.items()}
            career_data = {f'away_career_b{order}_{k}':v for k,v in career_data.items()}
            team_recent_data.update(recent_data)
            team_career_data.update(career_data)
        order = order + 1
    away_batter_data.update(team_career_data)
    away_batter_data.update(team_recent_data)

    order = 1

    team_recent_data = {}
    team_career_data = {}
    for batter in home_batters:
        print('homeBatter============>', batter)
        home_batter_res = pd.read_sql(f"SELECT * FROM predict_batter_stats WHERE game_id = '{game_id}' AND player_id = '{batter}';", con = engine).to_dict('records')
        if (len(home_batter_res) > 0):
            print('is in the table')
            for home_stas in home_batter_res:
                if home_stas['role'] == 'recent':
                    keys_to_remove = ['game_date', 'game_id', 'player_name', 'team', 'role']
                    for key in keys_to_remove:
                        home_stas.pop(key, None)

                    updated_stas = {}
                    for old_key, value in home_stas.items():
                        if old_key in rename_dict.keys():
                            updated_stas[rename_dict[old_key]] = value
                        else:
                            updated_stas[old_key] = value

                    recent_data = {f'home_recent_b{order}_{k}':v for k,v in updated_stas.items()}
                    team_recent_data.update(recent_data)
                elif home_stas['role'] == 'career':
                    keys_to_remove = ['game_date', 'game_id', 'player_id', 'player_name', 'team', 'role', 'difficulty']
                    for key in keys_to_remove:
                        home_stas.pop(key, None)

                    updated_stas = {}
                    for old_key, value in home_stas.items():
                        if old_key in rename_dict.keys():
                            updated_stas[rename_dict[old_key]] = value
                        else:
                            updated_stas[old_key] = value

                    career_data = {f'home_career_b{order}_{k}':v for k,v in updated_stas.items()}
                    team_career_data.update(career_data)
        else:
            print('not in the table')
            player_df = batting_c.get_batter_df(batter, game_date)

            if len(player_df) > 0 : 
                recent_data, games = batting_c.process_recent_batter_data(player_df, game_date, '', batter_stat_list)
                career_data = batting_c.process_career_batter_data(games, batter_stat_list)
            else: 
                recent_data = dict(zip(batter_stat_list, np.repeat(0, len(batter_stat_list))))
                recent_data['dificulty'] = 0
                career_data = dict(zip(batter_stat_list, np.repeat(0, len(batter_stat_list))))

            player_name_res = pd.read_sql(f"SELECT * FROM player_table WHERE p_id = '{batter}';", con = engine).to_dict('records')
            player_name = ''

            if (len(player_name_res) > 0):
                player_name = player_name_res[0]['p_name']
            else:
                player_name = batter

            print('insert in the table')
            engine.execute(text(f"INSERT INTO predict_batter_stats(game_date, game_id, player_id, player_name, team, role, atBats, avg, baseOnBalls, doubles, hits, homeRuns, obp, ops, rbi, runs, slg, strikeOuts, triples, singles, difficulty) \
                                    VALUES('{game_date}', '{game_id}', '{batter}', '{player_name}', 'home', 'recent', '{round(float(recent_data['atBats']), 3)}', '{round(float(recent_data['avg']), 3)}', '{round(float(recent_data['baseOnBalls']), 3)}', '{round(float(recent_data['doubles']), 3)}', '{round(float(recent_data['hits']), 3)}', '{round(float(recent_data['homeRuns']), 3)}', '{round(float(recent_data['obp']), 3)}', '{round(float(recent_data['ops']), 3)}', '{round(float(recent_data['rbi']), 3)}', '{round(float(recent_data['runs']), 3)}', '{round(float(recent_data['slg']), 3)}', '{round(float(recent_data['strikeOuts']), 3)}', '{round(float(recent_data['triples']), 3)}', '{round(float(recent_data['singles']), 3)}', '{round(float(recent_data['difficulty']), 3)}')\
                                    ON CONFLICT ON CONSTRAINT predict_batter_stats_key DO UPDATE SET atBats = excluded.atBats, avg = excluded.avg, baseOnBalls = excluded.baseOnBalls, doubles = excluded.doubles, hits = excluded.hits, homeRuns = excluded.homeRuns, obp = excluded.obp, ops = excluded.ops, rbi = excluded.rbi, runs = excluded.runs, slg = excluded.slg, strikeOuts = excluded.strikeOuts, triples = excluded.triples, singles = excluded.singles, difficulty = excluded.difficulty;"))
            engine.execute(text(f"INSERT INTO predict_batter_stats(game_date, game_id, player_id, player_name, team, role, atBats, avg, baseOnBalls, doubles, hits, homeRuns, obp, ops, rbi, runs, slg, strikeOuts, triples, singles, difficulty) \
                                    VALUES('{game_date}', '{game_id}', '{batter}', '{player_name}', 'home', 'career', '{round(float(career_data['atBats']), 3)}', '{round(float(career_data['avg']), 3)}', '{round(float(career_data['baseOnBalls']), 3)}', '{round(float(career_data['doubles']), 3)}', '{round(float(career_data['hits']), 3)}', '{round(float(career_data['homeRuns']), 3)}', '{round(float(career_data['obp']), 3)}', '{round(float(career_data['ops']), 3)}', '{round(float(career_data['rbi']), 3)}', '{round(float(career_data['runs']), 3)}', '{round(float(career_data['slg']), 3)}', '{round(float(career_data['strikeOuts']), 3)}', '{round(float(career_data['triples']), 3)}', '{round(float(career_data['singles']), 3)}', '1')\
                                    ON CONFLICT ON CONSTRAINT predict_batter_stats_key DO UPDATE SET atBats = excluded.atBats, avg = excluded.avg, baseOnBalls = excluded.baseOnBalls, doubles = excluded.doubles, hits = excluded.hits, homeRuns = excluded.homeRuns, obp = excluded.obp, ops = excluded.ops, rbi = excluded.rbi, runs = excluded.runs, slg = excluded.slg, strikeOuts = excluded.strikeOuts, triples = excluded.triples, singles = excluded.singles, difficulty = excluded.difficulty;"))
            
            # break
            recent_data = {f'home_recent_b{order}_{k}':v for k,v in recent_data.items()}
            career_data = {f'home_career_b{order}_{k}':v for k,v in career_data.items()}
            team_recent_data.update(recent_data)
            team_career_data.update(career_data)
        order = order + 1
    home_batter_data.update(team_career_data)
    home_batter_data.update(team_recent_data)

    if savestate == False:
        team_recent_data = {}
        team_career_data = {}

        print('awaystarter============>', away_starter)
        away_pitcher_res = pd.read_sql(f"SELECT * FROM predict_pitcher_stats WHERE game_id = '{game_id}' AND player_id = '{away_starter}';", con = engine).to_dict('records')
        
        if (len(away_pitcher_res) > 0):
            print('is in the table')
            for away_start_stas in away_pitcher_res:
                if away_start_stas['role'] == 'recent':
                    keys_to_remove = ['game_date', 'game_id', 'player_name', 'team', 'role']
                    for key in keys_to_remove:
                        away_start_stas.pop(key, None)

                    updated_stas = {}
                    for old_key, value in away_start_stas.items():
                        if old_key in rename_dict.keys():
                            updated_stas[rename_dict[old_key]] = value
                        else:
                            updated_stas[old_key] = value

                    recent_data = {f'away_starter_recent_{k}':v for k,v in updated_stas.items()}
                    team_recent_data.update(recent_data)
                elif away_start_stas['role'] == 'career':
                    keys_to_remove = ['game_date', 'game_id', 'player_id', 'player_name', 'team', 'role', 'difficulty']
                    for key in keys_to_remove:
                        away_start_stas.pop(key, None)

                    updated_stas = {}
                    for old_key, value in away_start_stas.items():
                        if old_key in rename_dict.keys():
                            updated_stas[rename_dict[old_key]] = value
                        else:
                            updated_stas[old_key] = value

                    career_data = {f'away_starter_career_{k}':v for k,v in updated_stas.items()}
                    team_career_data.update(career_data)
        else:
            print('not in the table')

            player_df = starters_c.get_starter_df(away_starter, game_date)

            if len(player_df) > 0 : 
                recent_data, games = starters_c.process_recent_starter_data(player_df, game_date, [], pitcher_stat_list)
                career_data = starters_c.process_career_starter_data(games, pitcher_stat_list)
            else: 
                recent_data = dict(zip(pitcher_stat_list, np.repeat(0, len(pitcher_stat_list))))
                career_data = dict(zip(pitcher_stat_list, np.repeat(0, len(pitcher_stat_list))))

            player_name_res = pd.read_sql(f"SELECT * FROM player_table WHERE p_id = '{away_starter}';", con = engine).to_dict('records')
            player_name = ''

            if (len(player_name_res) > 0):
                player_name = player_name_res[0]['p_name']
            else:
                player_name = away_starter

            print('insert in the table')

            engine.execute(text(f"INSERT INTO predict_pitcher_stats(game_date, game_id, player_id, player_name, team, role, atBats, baseOnBalls, blownsaves, doubles, earnedRuns, era, hits, holds, homeRuns, inningsPitched, losses, pitchesThrown, rbi, runs, strikeOuts, strikes, triples, whip, wins, difficulty) \
                                        VALUES('{game_date}', '{game_id}', '{away_starter}', '{player_name}', 'away', 'recent', '{round(float(recent_data['atBats']), 3)}', '{round(float(recent_data['baseOnBalls']), 3)}', '{round(float(recent_data['blownsaves']), 3)}', '{round(float(recent_data['doubles']), 3)}', '{round(float(recent_data['earnedRuns']), 3)}', '{round(float(recent_data['era']), 3)}', '{round(float(recent_data['hits']), 3)}', '{round(float(recent_data['holds']), 3)}', '{round(float(recent_data['homeRuns']), 3)}', '{round(float(recent_data['inningsPitched']), 3)}', '{round(float(recent_data['losses']), 3)}', '{round(float(recent_data['pitchesThrown']), 3)}', '{round(float(recent_data['rbi']), 3)}', '{round(float(recent_data['runs']), 3)}', '{round(float(recent_data['strikeOuts']), 3)}', '{round(float(recent_data['strikes']), 3)}', '{round(float(recent_data['triples']), 3)}', '{round(float(recent_data['whip']), 3)}', '{round(float(recent_data['wins']), 3)}', '{round(float(recent_data['difficulty']), 3)}')\
                                        ON CONFLICT ON CONSTRAINT predict_pitcher_stats_key DO UPDATE SET atBats = excluded.atBats, baseOnBalls = excluded.baseOnBalls, blownsaves = excluded.blownsaves, doubles = excluded.doubles, earnedRuns = excluded.earnedRuns, era = excluded.era, hits = excluded.hits, holds = excluded.holds, homeRuns = excluded.homeRuns, inningsPitched = excluded.inningsPitched, losses = excluded.losses, pitchesThrown = excluded.pitchesThrown, rbi = excluded.rbi, runs = excluded.runs, strikeOuts = excluded.strikeOuts, strikes = excluded.strikes, triples = excluded.triples, whip = excluded.whip, wins = excluded.wins, difficulty = excluded.difficulty;"))
            engine.execute(text(f"INSERT INTO predict_pitcher_stats(game_date, game_id, player_id, player_name, team, role, atBats, baseOnBalls, blownsaves, doubles, earnedRuns, era, hits, holds, homeRuns, inningsPitched, losses, pitchesThrown, rbi, runs, strikeOuts, strikes, triples, whip, wins, difficulty) \
                                    VALUES('{game_date}', '{game_id}', '{away_starter}', '{player_name}', 'away', 'career', '{round(float(career_data['atBats']), 3)}', '{round(float(career_data['baseOnBalls']), 3)}', '{round(float(career_data['blownsaves']), 3)}', '{round(float(career_data['doubles']), 3)}', '{round(float(career_data['earnedRuns']), 3)}', '{round(float(career_data['era']), 3)}', '{round(float(career_data['hits']), 3)}', '{round(float(career_data['holds']), 3)}', '{round(float(career_data['homeRuns']), 3)}', '{round(float(career_data['inningsPitched']), 3)}', '{round(float(career_data['losses']), 3)}', '{round(float(career_data['pitchesThrown']), 3)}', '{round(float(career_data['rbi']), 3)}', '{round(float(career_data['runs']), 3)}', '{round(float(career_data['strikeOuts']), 3)}', '{round(float(career_data['strikes']), 3)}', '{round(float(career_data['triples']), 3)}', '{round(float(career_data['whip']), 3)}', '{round(float(career_data['wins']), 3)}', '1')\
                                    ON CONFLICT ON CONSTRAINT predict_pitcher_stats_key DO UPDATE SET atBats = excluded.atBats, baseOnBalls = excluded.baseOnBalls, blownsaves = excluded.blownsaves, doubles = excluded.doubles, earnedRuns = excluded.earnedRuns, era = excluded.era, hits = excluded.hits, holds = excluded.holds, homeRuns = excluded.homeRuns, inningsPitched = excluded.inningsPitched, losses = excluded.losses, pitchesThrown = excluded.pitchesThrown, rbi = excluded.rbi, runs = excluded.runs, strikeOuts = excluded.strikeOuts, strikes = excluded.strikes, triples = excluded.triples, whip = excluded.whip, wins = excluded.wins, difficulty = excluded.difficulty;"))

            recent_data = {f'away_starter_recent_{k}':v for k,v in recent_data.items()}
            career_data = {f'away_starter_career_{k}':v for k,v in career_data.items()}

            team_career_data.update(career_data)
            team_recent_data.update(recent_data)
        away_starter_data.update(team_career_data)
        away_starter_data.update(team_recent_data)

        home_pitcher_res = pd.read_sql(f"SELECT * FROM predict_pitcher_stats WHERE game_id = '{game_id}' AND player_id = '{home_starter}';", con = engine).to_dict('records')
        team_recent_data = {}
        team_career_data = {}

        print('homestarter============>', home_starter)


        if (len(home_pitcher_res) > 0):
            print('is in the table')
            for home_start_stas in home_pitcher_res:
                if home_start_stas['role'] == 'recent':
                    keys_to_remove = ['game_date', 'game_id', 'player_name', 'team', 'role']
                    for key in keys_to_remove:
                        home_start_stas.pop(key, None)

                    updated_stas = {}
                    for old_key, value in home_start_stas.items():
                        if old_key in rename_dict.keys():
                            updated_stas[rename_dict[old_key]] = value
                        else:
                            updated_stas[old_key] = value

                    recent_data = {f'home_starter_recent_{k}':v for k,v in updated_stas.items()}
                    team_recent_data.update(recent_data)
                elif home_start_stas['role'] == 'career':
                    keys_to_remove = ['game_date', 'game_id', 'player_id', 'player_name', 'team', 'role', 'difficulty']
                    for key in keys_to_remove:
                        home_start_stas.pop(key, None)

                    updated_stas = {}
                    for old_key, value in home_start_stas.items():
                        if old_key in rename_dict.keys():
                            updated_stas[rename_dict[old_key]] = value
                        else:
                            updated_stas[old_key] = value

                    career_data = {f'home_starter_career_{k}':v for k,v in updated_stas.items()}
                    team_career_data.update(career_data)
        else:
            print('not in the table')
            
            player_df = starters_c.get_starter_df(home_starter, game_date)

            if len(player_df) > 0 : 
                recent_data, games = starters_c.process_recent_starter_data(player_df, game_date, [], pitcher_stat_list)
                career_data = starters_c.process_career_starter_data(games, pitcher_stat_list)
            else: 
                recent_data = dict(zip(pitcher_stat_list, np.repeat(0, len(pitcher_stat_list))))
                career_data = dict(zip(pitcher_stat_list, np.repeat(0, len(pitcher_stat_list))))

            player_name_res = pd.read_sql(f"SELECT * FROM player_table WHERE p_id = '{home_starter}';", con = engine).to_dict('records')
            player_name = ''

            if (len(player_name_res) > 0):
                player_name = player_name_res[0]['p_name']
            else:
                player_name = home_starter

            print('insert in the table')

            engine.execute(text(f"INSERT INTO predict_pitcher_stats(game_date, game_id, player_id, player_name, team, role, atBats, baseOnBalls, blownsaves, doubles, earnedRuns, era, hits, holds, homeRuns, inningsPitched, losses, pitchesThrown, rbi, runs, strikeOuts, strikes, triples, whip, wins, difficulty) \
                                        VALUES('{game_date}', '{game_id}', '{home_starter}', '{player_name}', 'home', 'recent', '{round(float(recent_data['atBats']), 3)}', '{round(float(recent_data['baseOnBalls']), 3)}', '{round(float(recent_data['blownsaves']), 3)}', '{round(float(recent_data['doubles']), 3)}', '{round(float(recent_data['earnedRuns']), 3)}', '{round(float(recent_data['era']), 3)}', '{round(float(recent_data['hits']), 3)}', '{round(float(recent_data['holds']), 3)}', '{round(float(recent_data['homeRuns']), 3)}', '{round(float(recent_data['inningsPitched']), 3)}', '{round(float(recent_data['losses']), 3)}', '{round(float(recent_data['pitchesThrown']), 3)}', '{round(float(recent_data['rbi']), 3)}', '{round(float(recent_data['runs']), 3)}', '{round(float(recent_data['strikeOuts']), 3)}', '{round(float(recent_data['strikes']), 3)}', '{round(float(recent_data['triples']), 3)}', '{round(float(recent_data['whip']), 3)}', '{round(float(recent_data['wins']), 3)}', '{round(float(recent_data['difficulty']), 3)}')\
                                        ON CONFLICT ON CONSTRAINT predict_pitcher_stats_key DO UPDATE SET atBats = excluded.atBats, baseOnBalls = excluded.baseOnBalls, blownsaves = excluded.blownsaves, doubles = excluded.doubles, earnedRuns = excluded.earnedRuns, era = excluded.era, hits = excluded.hits, holds = excluded.holds, homeRuns = excluded.homeRuns, inningsPitched = excluded.inningsPitched, losses = excluded.losses, pitchesThrown = excluded.pitchesThrown, rbi = excluded.rbi, runs = excluded.runs, strikeOuts = excluded.strikeOuts, strikes = excluded.strikes, triples = excluded.triples, whip = excluded.whip, wins = excluded.wins, difficulty = excluded.difficulty;"))
            engine.execute(text(f"INSERT INTO predict_pitcher_stats(game_date, game_id, player_id, player_name, team, role, atBats, baseOnBalls, blownsaves, doubles, earnedRuns, era, hits, holds, homeRuns, inningsPitched, losses, pitchesThrown, rbi, runs, strikeOuts, strikes, triples, whip, wins, difficulty) \
                                    VALUES('{game_date}', '{game_id}', '{home_starter}', '{player_name}', 'home', 'career', '{round(float(career_data['atBats']), 3)}', '{round(float(career_data['baseOnBalls']), 3)}', '{round(float(career_data['blownsaves']), 3)}', '{round(float(career_data['doubles']), 3)}', '{round(float(career_data['earnedRuns']), 3)}', '{round(float(career_data['era']), 3)}', '{round(float(career_data['hits']), 3)}', '{round(float(career_data['holds']), 3)}', '{round(float(career_data['homeRuns']), 3)}', '{round(float(career_data['inningsPitched']), 3)}', '{round(float(career_data['losses']), 3)}', '{round(float(career_data['pitchesThrown']), 3)}', '{round(float(career_data['rbi']), 3)}', '{round(float(career_data['runs']), 3)}', '{round(float(career_data['strikeOuts']), 3)}', '{round(float(career_data['strikes']), 3)}', '{round(float(career_data['triples']), 3)}', '{round(float(career_data['whip']), 3)}', '{round(float(career_data['wins']), 3)}', '1')\
                                    ON CONFLICT ON CONSTRAINT predict_pitcher_stats_key DO UPDATE SET atBats = excluded.atBats, baseOnBalls = excluded.baseOnBalls, blownsaves = excluded.blownsaves, doubles = excluded.doubles, earnedRuns = excluded.earnedRuns, era = excluded.era, hits = excluded.hits, holds = excluded.holds, homeRuns = excluded.homeRuns, inningsPitched = excluded.inningsPitched, losses = excluded.losses, pitchesThrown = excluded.pitchesThrown, rbi = excluded.rbi, runs = excluded.runs, strikeOuts = excluded.strikeOuts, strikes = excluded.strikes, triples = excluded.triples, whip = excluded.whip, wins = excluded.wins, difficulty = excluded.difficulty;"))

            recent_data = {f'home_starter_recent_{k}':v for k,v in recent_data.items()}
            career_data = {f'home_starter_career_{k}':v for k,v in career_data.items()}

            team_career_data.update(career_data)
            team_recent_data.update(recent_data)
        home_starter_data.update(team_career_data)
        home_starter_data.update(team_recent_data)
    elif savestate == True:
        team_recent_data = []
        team_career_data = []
        weights = [0.5552, 0.1112, 0.1112, 0.1112, 0.1112]


        for starter in away_starters:
            away_pitcher_res = pd.read_sql(f"SELECT * FROM predict_pitcher_stats WHERE game_id = '{game_id}' AND player_id = '{starter}';", con = engine).to_dict('records')
        
            if (len(away_pitcher_res) > 0):
                print('is in the table')
                for away_start_stas in away_pitcher_res:
                    if away_start_stas['role'] == 'recent':
                        keys_to_remove = ['game_date', 'game_id', 'player_name', 'team', 'role']
                        for key in keys_to_remove:
                            away_start_stas.pop(key, None)

                        updated_stas = {}
                        for old_key, value in away_start_stas.items():
                            if old_key in rename_dict.keys():
                                updated_stas[rename_dict[old_key]] = value
                            else:
                                updated_stas[old_key] = value

                        recent_data = {f'away_starter_recent_{k}':v for k,v in updated_stas.items()}
                        team_recent_data.append(recent_data)
                    elif away_start_stas['role'] == 'career':
                        keys_to_remove = ['game_date', 'game_id', 'player_id', 'player_name', 'team', 'role', 'difficulty']
                        for key in keys_to_remove:
                            away_start_stas.pop(key, None)

                        updated_stas = {}
                        for old_key, value in away_start_stas.items():
                            if old_key in rename_dict.keys():
                                updated_stas[rename_dict[old_key]] = value
                            else:
                                updated_stas[old_key] = value

                        career_data = {f'away_starter_career_{k}':v for k,v in updated_stas.items()}
                        team_career_data.append(career_data)
                engine.execute(text(f"INSERT INTO pitcher_stats_c(game_id, game_date, position, player_id, career_era, career_homeRuns, career_whip, career_battersFaced, recent_era, recent_homeRuns, recent_whip, recent_battersFaced, difficulty_rating) \
                                        VALUES('{game_id}', '{game_date}', 'awayStarter', '{int(starter)}', '{round(float(career_data['away_starter_career_era']), 3)}', '{round(float(career_data['away_starter_career_homeRuns']), 3)}', '{round(float(career_data['away_starter_career_whip']), 3)}', '{round(float(career_data['away_starter_career_atBats']), 3) + round(float(career_data['away_starter_career_baseOnBalls']), 3)}', '{round(float(recent_data['away_starter_recent_era']), 3)}', '{round(float(recent_data['away_starter_recent_homeRuns']), 3)}', '{round(float(recent_data['away_starter_recent_whip']), 3)}', '{round(float(recent_data['away_starter_recent_atBats']), 3) + round(float(recent_data['away_starter_recent_baseOnBalls']), 3)}', '{round(float(recent_data['away_starter_recent_difficulty']), 3)}')\
                                        ON CONFLICT ON CONSTRAINT pitcher_stats_c_game_id_player_id_key DO UPDATE SET game_date = excluded.game_date, career_era = excluded.career_era, career_homeRuns = excluded.career_homeRuns, career_whip = excluded.career_whip, career_battersFaced = excluded.career_battersFaced, recent_era = excluded.recent_era, recent_homeRuns = excluded.recent_homeRuns, recent_whip = excluded.recent_whip, recent_battersFaced = excluded.recent_battersFaced, difficulty_rating = excluded.difficulty_rating;"))

            else:
                print('not in the table')

                player_df = starters_c.get_starter_df(away_starter, game_date)

                if len(player_df) > 0 : 
                    recent_data, games = starters_c.process_recent_starter_data(player_df, game_date, [], pitcher_stat_list)
                    career_data = starters_c.process_career_starter_data(games, pitcher_stat_list)
                else: 
                    recent_data = dict(zip(pitcher_stat_list, np.repeat(0, len(pitcher_stat_list))))
                    career_data = dict(zip(pitcher_stat_list, np.repeat(0, len(pitcher_stat_list))))

                player_name_res = pd.read_sql(f"SELECT * FROM player_table WHERE p_id = '{starter}';", con = engine).to_dict('records')
                player_name = ''

                if (len(player_name_res) > 0):
                    player_name = player_name_res[0]['p_name']
                else:
                    player_name = starter

                print('insert in the table')

                engine.execute(text(f"INSERT INTO predict_pitcher_stats(game_date, game_id, player_id, player_name, team, role, atBats, baseOnBalls, blownsaves, doubles, earnedRuns, era, hits, holds, homeRuns, inningsPitched, losses, pitchesThrown, rbi, runs, strikeOuts, strikes, triples, whip, wins, difficulty) \
                                            VALUES('{game_date}', '{game_id}', '{starter}', '{player_name}', 'away', 'recent', '{round(float(recent_data['atBats']), 3)}', '{round(float(recent_data['baseOnBalls']), 3)}', '{round(float(recent_data['blownsaves']), 3)}', '{round(float(recent_data['doubles']), 3)}', '{round(float(recent_data['earnedRuns']), 3)}', '{round(float(recent_data['era']), 3)}', '{round(float(recent_data['hits']), 3)}', '{round(float(recent_data['holds']), 3)}', '{round(float(recent_data['homeRuns']), 3)}', '{round(float(recent_data['inningsPitched']), 3)}', '{round(float(recent_data['losses']), 3)}', '{round(float(recent_data['pitchesThrown']), 3)}', '{round(float(recent_data['rbi']), 3)}', '{round(float(recent_data['runs']), 3)}', '{round(float(recent_data['strikeOuts']), 3)}', '{round(float(recent_data['strikes']), 3)}', '{round(float(recent_data['triples']), 3)}', '{round(float(recent_data['whip']), 3)}', '{round(float(recent_data['wins']), 3)}', '{round(float(recent_data['difficulty']), 3)}')\
                                            ON CONFLICT ON CONSTRAINT predict_pitcher_stats_key DO UPDATE SET atBats = excluded.atBats, baseOnBalls = excluded.baseOnBalls, blownsaves = excluded.blownsaves, doubles = excluded.doubles, earnedRuns = excluded.earnedRuns, era = excluded.era, hits = excluded.hits, holds = excluded.holds, homeRuns = excluded.homeRuns, inningsPitched = excluded.inningsPitched, losses = excluded.losses, pitchesThrown = excluded.pitchesThrown, rbi = excluded.rbi, runs = excluded.runs, strikeOuts = excluded.strikeOuts, strikes = excluded.strikes, triples = excluded.triples, whip = excluded.whip, wins = excluded.wins, difficulty = excluded.difficulty;"))
                engine.execute(text(f"INSERT INTO predict_pitcher_stats(game_date, game_id, player_id, player_name, team, role, atBats, baseOnBalls, blownsaves, doubles, earnedRuns, era, hits, holds, homeRuns, inningsPitched, losses, pitchesThrown, rbi, runs, strikeOuts, strikes, triples, whip, wins, difficulty) \
                                        VALUES('{game_date}', '{game_id}', '{starter}', '{player_name}', 'away', 'career', '{round(float(career_data['atBats']), 3)}', '{round(float(career_data['baseOnBalls']), 3)}', '{round(float(career_data['blownsaves']), 3)}', '{round(float(career_data['doubles']), 3)}', '{round(float(career_data['earnedRuns']), 3)}', '{round(float(career_data['era']), 3)}', '{round(float(career_data['hits']), 3)}', '{round(float(career_data['holds']), 3)}', '{round(float(career_data['homeRuns']), 3)}', '{round(float(career_data['inningsPitched']), 3)}', '{round(float(career_data['losses']), 3)}', '{round(float(career_data['pitchesThrown']), 3)}', '{round(float(career_data['rbi']), 3)}', '{round(float(career_data['runs']), 3)}', '{round(float(career_data['strikeOuts']), 3)}', '{round(float(career_data['strikes']), 3)}', '{round(float(career_data['triples']), 3)}', '{round(float(career_data['whip']), 3)}', '{round(float(career_data['wins']), 3)}', '1')\
                                        ON CONFLICT ON CONSTRAINT predict_pitcher_stats_key DO UPDATE SET atBats = excluded.atBats, baseOnBalls = excluded.baseOnBalls, blownsaves = excluded.blownsaves, doubles = excluded.doubles, earnedRuns = excluded.earnedRuns, era = excluded.era, hits = excluded.hits, holds = excluded.holds, homeRuns = excluded.homeRuns, inningsPitched = excluded.inningsPitched, losses = excluded.losses, pitchesThrown = excluded.pitchesThrown, rbi = excluded.rbi, runs = excluded.runs, strikeOuts = excluded.strikeOuts, strikes = excluded.strikes, triples = excluded.triples, whip = excluded.whip, wins = excluded.wins, difficulty = excluded.difficulty;"))

                recent_data = {f'away_starter_recent_{k}':v for k,v in recent_data.items()}
                career_data = {f'away_starter_career_{k}':v for k,v in career_data.items()}

                engine.execute(text(f"INSERT INTO pitcher_stats_c(game_id, game_date, position, player_id, career_era, career_homeRuns, career_whip, career_battersFaced, recent_era, recent_homeRuns, recent_whip, recent_battersFaced, difficulty_rating) \
                                        VALUES('{game_id}', '{game_date}', 'awayStarter', '{int(starter)}', '{round(float(career_data['away_starter_career_era']), 3)}', '{round(float(career_data['away_starter_career_homeRuns']), 3)}', '{round(float(career_data['away_starter_career_whip']), 3)}', '{round(float(career_data['away_starter_career_atBats']), 3) + round(float(career_data['away_starter_career_baseOnBalls']), 3)}', '{round(float(recent_data['away_starter_recent_era']), 3)}', '{round(float(recent_data['away_starter_recent_homeRuns']), 3)}', '{round(float(recent_data['away_starter_recent_whip']), 3)}', '{round(float(recent_data['away_starter_recent_atBats']), 3) + round(float(recent_data['away_starter_recent_baseOnBalls']), 3)}', '{round(float(recent_data['away_starter_recent_difficulty']), 3)}')\
                                        ON CONFLICT ON CONSTRAINT pitcher_stats_c_game_id_player_id_key DO UPDATE SET game_date = excluded.game_date, career_era = excluded.career_era, career_homeRuns = excluded.career_homeRuns, career_whip = excluded.career_whip, career_battersFaced = excluded.career_battersFaced, recent_era = excluded.recent_era, recent_homeRuns = excluded.recent_homeRuns, recent_whip = excluded.recent_whip, recent_battersFaced = excluded.recent_battersFaced, difficulty_rating = excluded.difficulty_rating;"))

                team_career_data.append(career_data)
                team_recent_data.append(recent_data)

        team_starter_data = {}

        for j in range(len(team_career_data)):
            obj = team_career_data[j]
            for key in obj:
                if key in team_starter_data:
                    team_starter_data[key] += obj[key] * weights[j]
                else:
                    team_starter_data[key] = obj[key] * weights[j]

        away_starter_data.update(team_starter_data)
        team_starter_data = {}

        print(team_recent_data)
        for i in range(len(team_recent_data)):
            obj = team_recent_data[i]
            obj['away_starter_recent_playerId'] = int(obj['away_starter_recent_playerId'])
            for key in obj:
                if key in team_starter_data:
                    team_starter_data[key] += obj[key] * weights[i]
                else:
                    team_starter_data[key] = obj[key] * weights[i]
        away_starter_data.update(team_starter_data)


        team_recent_data = []
        team_career_data = []



        for starter in home_starters:

            home_pitcher_res = pd.read_sql(f"SELECT * FROM predict_pitcher_stats WHERE game_id = '{game_id}' AND player_id = '{starter}';", con = engine).to_dict('records')

            if (len(home_pitcher_res) > 0):
                print('is in the table')
                for home_start_stas in home_pitcher_res:
                    if home_start_stas['role'] == 'recent':
                        keys_to_remove = ['game_date', 'game_id', 'player_name', 'team', 'role']
                        for key in keys_to_remove:
                            home_start_stas.pop(key, None)

                        updated_stas = {}
                        for old_key, value in home_start_stas.items():
                            if old_key in rename_dict.keys():
                                updated_stas[rename_dict[old_key]] = value
                            else:
                                updated_stas[old_key] = value

                        recent_data = {f'home_starter_recent_{k}':v for k,v in updated_stas.items()}
                        team_recent_data.append(recent_data)
                    elif home_start_stas['role'] == 'career':
                        keys_to_remove = ['game_date', 'game_id', 'player_id', 'player_name', 'team', 'role', 'difficulty']
                        for key in keys_to_remove:
                            home_start_stas.pop(key, None)

                        updated_stas = {}
                        for old_key, value in home_start_stas.items():
                            if old_key in rename_dict.keys():
                                updated_stas[rename_dict[old_key]] = value
                            else:
                                updated_stas[old_key] = value

                        career_data = {f'home_starter_career_{k}':v for k,v in updated_stas.items()}
                        team_career_data.append(career_data)
                engine.execute(text(f"INSERT INTO pitcher_stats_c(game_id, game_date, position, player_id, career_era, career_homeRuns, career_whip, career_battersFaced, recent_era, recent_homeRuns, recent_whip, recent_battersFaced, difficulty_rating) \
                                        VALUES('{game_id}', '{game_date}', 'homeStarter', '{int(starter)}', '{round(float(career_data['home_starter_career_era']), 3)}', '{round(float(career_data['home_starter_career_homeRuns']), 3)}', '{round(float(career_data['home_starter_career_whip']), 3)}', '{round(float(career_data['home_starter_career_atBats']), 3) + round(float(career_data['home_starter_career_baseOnBalls']), 3)}', '{round(float(recent_data['home_starter_recent_era']), 3)}', '{round(float(recent_data['home_starter_recent_homeRuns']), 3)}', '{round(float(recent_data['home_starter_recent_whip']), 3)}', '{round(float(recent_data['home_starter_recent_atBats']), 3) + round(float(recent_data['home_starter_recent_baseOnBalls']), 3)}', '{round(float(recent_data['home_starter_recent_difficulty']), 3)}')\
                                        ON CONFLICT ON CONSTRAINT pitcher_stats_c_game_id_player_id_key DO UPDATE SET game_date = excluded.game_date, career_era = excluded.career_era, career_homeRuns = excluded.career_homeRuns, career_whip = excluded.career_whip, career_battersFaced = excluded.career_battersFaced, recent_era = excluded.recent_era, recent_homeRuns = excluded.recent_homeRuns, recent_whip = excluded.recent_whip, recent_battersFaced = excluded.recent_battersFaced, difficulty_rating = excluded.difficulty_rating;"))
            else:
                print('not in the table')
                
                player_df = starters_c.get_starter_df(home_starter, game_date)

                if len(player_df) > 0 : 
                    recent_data, games = starters_c.process_recent_starter_data(player_df, game_date, [], pitcher_stat_list)
                    career_data = starters_c.process_career_starter_data(games, pitcher_stat_list)
                else: 
                    recent_data = dict(zip(pitcher_stat_list, np.repeat(0, len(pitcher_stat_list))))
                    career_data = dict(zip(pitcher_stat_list, np.repeat(0, len(pitcher_stat_list))))

                player_name_res = pd.read_sql(f"SELECT * FROM player_table WHERE p_id = '{starter}';", con = engine).to_dict('records')
                player_name = ''

                if (len(player_name_res) > 0):
                    player_name = player_name_res[0]['p_name']
                else:
                    player_name = starter

                print('insert in the table')

                engine.execute(text(f"INSERT INTO predict_pitcher_stats(game_date, game_id, player_id, player_name, team, role, atBats, baseOnBalls, blownsaves, doubles, earnedRuns, era, hits, holds, homeRuns, inningsPitched, losses, pitchesThrown, rbi, runs, strikeOuts, strikes, triples, whip, wins, difficulty) \
                                            VALUES('{game_date}', '{game_id}', '{starter}', '{player_name}', 'home', 'recent', '{round(float(recent_data['atBats']), 3)}', '{round(float(recent_data['baseOnBalls']), 3)}', '{round(float(recent_data['blownsaves']), 3)}', '{round(float(recent_data['doubles']), 3)}', '{round(float(recent_data['earnedRuns']), 3)}', '{round(float(recent_data['era']), 3)}', '{round(float(recent_data['hits']), 3)}', '{round(float(recent_data['holds']), 3)}', '{round(float(recent_data['homeRuns']), 3)}', '{round(float(recent_data['inningsPitched']), 3)}', '{round(float(recent_data['losses']), 3)}', '{round(float(recent_data['pitchesThrown']), 3)}', '{round(float(recent_data['rbi']), 3)}', '{round(float(recent_data['runs']), 3)}', '{round(float(recent_data['strikeOuts']), 3)}', '{round(float(recent_data['strikes']), 3)}', '{round(float(recent_data['triples']), 3)}', '{round(float(recent_data['whip']), 3)}', '{round(float(recent_data['wins']), 3)}', '{round(float(recent_data['difficulty']), 3)}')\
                                            ON CONFLICT ON CONSTRAINT predict_pitcher_stats_key DO UPDATE SET atBats = excluded.atBats, baseOnBalls = excluded.baseOnBalls, blownsaves = excluded.blownsaves, doubles = excluded.doubles, earnedRuns = excluded.earnedRuns, era = excluded.era, hits = excluded.hits, holds = excluded.holds, homeRuns = excluded.homeRuns, inningsPitched = excluded.inningsPitched, losses = excluded.losses, pitchesThrown = excluded.pitchesThrown, rbi = excluded.rbi, runs = excluded.runs, strikeOuts = excluded.strikeOuts, strikes = excluded.strikes, triples = excluded.triples, whip = excluded.whip, wins = excluded.wins, difficulty = excluded.difficulty;"))
                engine.execute(text(f"INSERT INTO predict_pitcher_stats(game_date, game_id, player_id, player_name, team, role, atBats, baseOnBalls, blownsaves, doubles, earnedRuns, era, hits, holds, homeRuns, inningsPitched, losses, pitchesThrown, rbi, runs, strikeOuts, strikes, triples, whip, wins, difficulty) \
                                        VALUES('{game_date}', '{game_id}', '{starter}', '{player_name}', 'home', 'career', '{round(float(career_data['atBats']), 3)}', '{round(float(career_data['baseOnBalls']), 3)}', '{round(float(career_data['blownsaves']), 3)}', '{round(float(career_data['doubles']), 3)}', '{round(float(career_data['earnedRuns']), 3)}', '{round(float(career_data['era']), 3)}', '{round(float(career_data['hits']), 3)}', '{round(float(career_data['holds']), 3)}', '{round(float(career_data['homeRuns']), 3)}', '{round(float(career_data['inningsPitched']), 3)}', '{round(float(career_data['losses']), 3)}', '{round(float(career_data['pitchesThrown']), 3)}', '{round(float(career_data['rbi']), 3)}', '{round(float(career_data['runs']), 3)}', '{round(float(career_data['strikeOuts']), 3)}', '{round(float(career_data['strikes']), 3)}', '{round(float(career_data['triples']), 3)}', '{round(float(career_data['whip']), 3)}', '{round(float(career_data['wins']), 3)}', '1')\
                                        ON CONFLICT ON CONSTRAINT predict_pitcher_stats_key DO UPDATE SET atBats = excluded.atBats, baseOnBalls = excluded.baseOnBalls, blownsaves = excluded.blownsaves, doubles = excluded.doubles, earnedRuns = excluded.earnedRuns, era = excluded.era, hits = excluded.hits, holds = excluded.holds, homeRuns = excluded.homeRuns, inningsPitched = excluded.inningsPitched, losses = excluded.losses, pitchesThrown = excluded.pitchesThrown, rbi = excluded.rbi, runs = excluded.runs, strikeOuts = excluded.strikeOuts, strikes = excluded.strikes, triples = excluded.triples, whip = excluded.whip, wins = excluded.wins, difficulty = excluded.difficulty;"))

                engine.execute(text(f"INSERT INTO pitcher_stats_c(game_id, game_date, position, player_id, career_era, career_homeRuns, career_whip, career_battersFaced, recent_era, recent_homeRuns, recent_whip, recent_battersFaced, difficulty_rating) \
                                            VALUES('{game_id}', '{game_date}', 'homeStarter', '{int(starter)}', '{round(float(career_data['era']), 3)}', '{round(float(career_data['homeRuns']), 3)}', '{round(float(career_data['whip']), 3)}', '{round(float(career_data['atBats']), 3) + round(float(career_data['baseOnBalls']), 3)}', '{round(float(recent_data['era']), 3)}', '{round(float(recent_data['homeRuns']), 3)}', '{round(float(recent_data['whip']), 3)}', '{round(float(recent_data['atBats']), 3) + round(float(recent_data['baseOnBalls']), 3)}', '{round(float(recent_data['difficulty']), 3)}')\
                                            ON CONFLICT ON CONSTRAINT pitcher_stats_c_game_id_player_id_key DO UPDATE SET game_date = excluded.game_date, career_era = excluded.career_era, career_homeRuns = excluded.career_homeRuns, career_whip = excluded.career_whip, career_battersFaced = excluded.career_battersFaced, recent_era = excluded.recent_era, recent_homeRuns = excluded.recent_homeRuns, recent_whip = excluded.recent_whip, recent_battersFaced = excluded.recent_battersFaced, difficulty_rating = excluded.difficulty_rating;"))

                recent_data = {f'home_starter_recent_{k}':v for k,v in recent_data.items()}
                career_data = {f'home_starter_career_{k}':v for k,v in career_data.items()}

                team_career_data.append(career_data)
                team_recent_data.append(recent_data)

        team_starter_data = {}        
        for j in range(len(team_career_data)):
            obj = team_career_data[j]
            for key in obj:
                if key in team_starter_data:
                    team_starter_data[key] += obj[key] * weights[j]
                else:
                    team_starter_data[key] = obj[key] * weights[j]

        home_starter_data.update(team_starter_data)
        team_starter_data = {}
        for i in range(len(team_recent_data)):
            obj = team_recent_data[i]
            obj['home_starter_recent_playerId'] = int(obj['home_starter_recent_playerId'])
            for key in obj:
                if key in team_starter_data:
                    team_starter_data[key] += obj[key] * weights[i]
                else:
                    team_starter_data[key] = obj[key] * weights[i]

        home_starter_data.update(team_starter_data)
        
    # Bullpen 
    away_bullpen_data = bullpen_c.process_bullpen_data(away_name, 'away', game_date)
    home_bullpen_data = bullpen_c.process_bullpen_data(home_name, 'home', game_date)


    # Combine 
    game_data = {}
    game_data.update(away_bullpen_data)
    game_data.update(away_batter_data)
    game_data.update(away_starter_data)

    game_data.update(home_bullpen_data)
    game_data.update(home_batter_data)
    game_data.update(home_starter_data)

    print(game_data)
    
    X_test = pd.DataFrame(game_data, index = [0])

    X_test = feature_selection(X_test, fill_null = True)
    X_test, column_names = addBattersFaced(X_test, bullpen = False)


    if savestate:
        rosters = schedule.get_rosters(game_id)
        save_batter_data(engine, X_test, away_batters, home_batters, game_id, rosters)
        # save_pitcher_data(engine, X_test, away_starter, home_starter, game_id, rosters)

    X_test = X_test[[col for col in X_test.columns if 'difficulty' not in col]]
    column_names = [el for el in column_names if 'difficulty' not in el]

    X_test = standardizeData(X_test, column_names)

    # Make Prediciton    
    pred_1c = pickle.load(open('algorithms/model_1a_v10.sav', 'rb')).predict_proba(X_test)
    print('pred_1c ======================>', pred_1c)

    
    return pred_1c