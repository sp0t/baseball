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

warnings.filterwarnings('ignore')


# Modules 
from functions import batting, starters, bullpen

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

    # for index, row in batter_df.iterrows():
    #     if state:
    #         engine.execute(text(f"INSERT INTO batter_stats(game_id, game_date, position, player_id, career_atBats, career_avg, career_homeRuns, career_obp, career_ops, career_rbi, career_slg, career_strikeOuts, recent_atBats, recent_avg, recent_homeRuns, recent_obp, recent_ops, recent_rbi, recent_slg, recent_strikeOuts) \
    #                                 VALUES('{gameId}', '{gamedate}', '{index}', '{int(row['player_id'])}', '{round(float(row['career_atBats']), 3)}', '{round(float(row['career_avg']), 3)}', '{round(float(row['career_homeRuns']), 3)}', '{round(float(row['career_obp']), 3)}', '{round(float(row['career_ops']), 3)}', '{round(float(row['career_rbi']), 3)}', '{round(float(row['career_slg']), 3)}', '{round(float(row['career_strikeOuts']), 3)}', '{round(float(row['recent_atBats']), 3)}', '{round(float(row['recent_avg']), 3)}', '{round(float(row['recent_homeRuns']), 3)}', '{round(float(row['recent_obp']), 3)}', '{round(float(row['recent_ops']), 3)}', '{round(float(row['recent_rbi']), 3)}', '{round(float(row['recent_slg']), 3)}', '{round(float(row['recent_strikeOuts']), 3)}') \
    #                                     ON CONFLICT ON CONSTRAINT unique_game_player DO UPDATE SET game_date = excluded.game_date, career_atBats = excluded.career_atBats, career_avg = excluded.career_avg, career_homeRuns = excluded.career_homeRuns, career_obp = excluded.career_obp, career_ops = excluded.career_ops, career_rbi = excluded.career_rbi, career_slg = excluded.career_slg, career_strikeOuts = excluded.career_strikeOuts, \
    #                                     recent_atBats = excluded.recent_atBats, recent_avg = excluded.recent_avg, recent_homeRuns = excluded.recent_homeRuns, recent_obp = excluded.recent_obp, recent_ops = excluded.recent_ops, recent_rbi = excluded.recent_rbi, recent_slg = excluded.recent_slg, recent_strikeOuts = excluded.recent_strikeOuts;"))
    
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
    # for index, row in pitchers.iterrows():
    #     if state:
    #         engine.execute(text(f"INSERT INTO pitcher_stats(game_id, game_date, position, player_id, career_era, career_homeRuns, career_whip, career_battersFaced, recent_era, recent_homeRuns, recent_whip, recent_battersFaced) \
    #                                 VALUES('{gameId}', '{gamedate}', '{index}', '{int(row['player_id'])}', '{round(float(row['career_era']), 3)}', '{round(float(row['career_homeRuns']), 3)}', '{round(float(row['career_whip']), 3)}', '{round(float(row['career_battersFaced']), 3)}', '{round(float(row['recent_era']), 3)}', '{round(float(row['recent_homeRuns']), 3)}', '{round(float(row['recent_whip']), 3)}', '{round(float(row['recent_battersFaced']), 3)}') \
    #                                 ON CONFLICT ON CONSTRAINT unique_pitcher_player DO UPDATE SET game_date = excluded.game_date, career_era = excluded.career_era, career_homeRuns = excluded.career_homeRuns, career_whip = excluded.career_whip, career_battersFaced = excluded.career_battersFaced, recent_era = excluded.recent_era, recent_homeRuns = excluded.recent_homeRuns, recent_whip = excluded.recent_whip, recent_battersFaced = excluded.recent_battersFaced;"))
 
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
    
    column_pattern = 'b\d{1}_rbi|avg|slg|b\d{1}_obp|b\d{1}_ops|homeRuns|inning|era|whip|atBats|baseOnBalls|b\d{1}_strikeOuts'
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

    away_batters, home_batters = [str(el) for el in params['away_batters']], [str(el) for el in params['home_batters']]
    away_starters, home_starters = [str(el) for el in params['away_starters']], [str(el) for el in params['home_starters']]
    away_starter = away_starters[0]
    home_starter = home_starters[0]
    away_name, home_name = params['away_name'], params['home_name']
    game_id = params['game_id']
    
    # Get Data
    game_date = datetime.today()
    
    team_batter = []
    team_home = []

    for el in away_batters:
        team_batter.append(el)

    for el in home_batters:
        team_home.append(el)

    # Batters 
    away_batter_data = batting.process_team_batter_data(team_batter, 'away', game_date)
    home_batter_data = batting.process_team_batter_data(team_home, 'home', game_date)
    # Starters 
    away_starter_data = starters.process_starter_data(away_starters, 'away', game_date)
    home_starter_data = starters.process_starter_data(home_starters, 'home', game_date)

    # Bullpen 
    away_bullpen_data = bullpen.process_bullpen_data(away_name, 'away', game_date)
    home_bullpen_data = bullpen.process_bullpen_data(home_name, 'home', game_date)


    # Combine 
    game_data = {}
    game_data.update(away_bullpen_data)
    game_data.update(away_batter_data)
    game_data.update(away_starter_data)

    game_data.update(home_bullpen_data)
    game_data.update(home_batter_data)
    game_data.update(home_starter_data)
    
    X_test = pd.DataFrame(game_data, index = [0])

    X_test = feature_selection(X_test, fill_null = True)
    X_test, column_names = addBattersFaced(X_test, bullpen = False)

    rosters = schedule.get_rosters(game_id)


    save_batter_data(engine, X_test, away_batters, home_batters, game_id, rosters)
    save_pitcher_data(engine, X_test, away_starter, home_starter, game_id, rosters)

    X_test = standardizeData(X_test, column_names)


    X_test_b = X_test[[col for col in X_test.columns if 'bullpen' not in col]]
    print("Game Row Processed")

    # Make Prediciton    
    pred_1a = pickle.load(open('algorithms/model_1a_v10.sav', 'rb')).predict_proba(X_test)
    print(pred_1a)
    pred_1b = pickle.load(open('algorithms/model_1b_v10.sav', 'rb')).predict_proba(X_test_b)
    print(pred_1b)
    print("Prediction made")
    
    return {"1a": pred_1a, "1b": pred_1b}