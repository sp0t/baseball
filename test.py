# Dependencies
import statsapi as mlb
import time
from datetime import date, timedelta, datetime
import numpy as np
import pandas as pd
import sqlite3
from database import database
from sqlalchemy import text
import csv
import requests
from schedule import schedule
import pickle
import joblib

engine = database.connect_to_db()
engine.execute(text("CREATE TABLE IF NOT EXISTS batter_stats_c(game_id TEXT, game_date TEXT, position TEXT, player_id TEXT, career_atBats float8, career_avg float8, career_homeRuns float8, career_obp float8, career_ops float8, career_rbi float8, career_slg float8, career_strikeOuts float8, recent_atBats float8, recent_avg float8, recent_homeRuns float8, recent_obp float8, recent_ops float8, recent_rbi float8, recent_slg float8, recent_strikeOuts float8, difficulty_rating float, UNIQUE (game_id, player_id));"))
engine.execute(text("CREATE TABLE IF NOT EXISTS pitcher_stats_c(game_id TEXT, game_date TEXT, position TEXT, player_id TEXT, career_era float8, career_homeRuns float8, career_whip float8, career_battersFaced float8, recent_era float8, recent_homeRuns float8, recent_whip float8, recent_battersFaced float8, difficulty_rating float, UNIQUE (game_id, player_id));"))
engine.execute(text("CREATE TABLE IF NOT EXISTS league_average(year TEXT, avg FLOAT, obp FLOAT, slg FLOAT, ops FLOAT, era FLOAT, whip FLOAT);"))
engine.execute(text("CREATE TABLE IF NOT EXISTS win_percent_c(game_id TEXT UNIQUE, away_prob FLOAT, home_prob FLOAT);"))

def get_batter_df(team_batter, gamedate): 

    df = pd.read_sql("SELECT b.game_id, b.game_date, b.home_team, b.away_team, b.home_score, b.away_score, (a.atbats)atBats, a.avg, "
            "(a.baseonballs)baseonBalls, a.doubles, a.hits, (a.homeruns)homeRuns, a.obp, a.ops, "
            "(a.playerid)playerId, a.rbi, a.runs, a.slg, (a.strikeouts)strikeOuts, "
            "a.triples FROM batter_table a LEFT JOIN game_table b ON a.game_id = b.game_id WHERE a.playerid = '%s' AND a.substitution = '0' AND b.game_date < '%s';" %(team_batter, gamedate), con = engine)

    string_cols = [col for col in df.columns if 'id' in col.lower()] + ['game_date', 'away_team', 'home_team']

    player_df = df.loc[:,:]

    player_df[string_cols] = df[string_cols].astype(str)
    non_string_cols = [col for col in df.columns if col not in string_cols]
    player_df[non_string_cols] = df[non_string_cols].astype(float)
    player_df['game_date'] = pd.to_datetime(df['game_date'])
    rename_dict = {'pitchesthrown': 'pitchesThrown', 'playerid': 'playerId', 'strikeouts': 'strikeOuts', 
            'baseonballs': 'baseOnBalls', 'homeruns': 'homeRuns', 'atbats': 'atBats', 
            'inningspitched': 'inningsPitched', 'earnedruns': 'earnedRuns'
            }

    new_col_names = []

    for col in player_df.columns: 
        for k,v in rename_dict.items(): 
            col = col.replace(k,v)
        new_col_names.append(col)
    player_df.columns = new_col_names

    player_df = player_df.reset_index(drop = True)
    return player_df

def process_recent_batter_data(player_df, game_date, team_starter, batter_stat_list): 
    player_df['game_date'] = pd.to_datetime(player_df['game_date'])
    games = player_df[player_df['game_date'] < game_date]
    games = games.sort_values('game_date')
    difficulty = []

    if len(games) == 0: 
        recent_games = []
        recent_data = dict(zip(batter_stat_list, np.repeat(0, len(batter_stat_list))))
        
    else: 
        if len(games) >= 15: 
            recent_df = games.tail(15)
            weights = [0.01,0.02,0.03,0.04,0.05,0.05,0.06,0.07,0.08,0.08,0.09,0.09,0.1,0.11,0.12]
            
        else:
            recent_df = games
            weights = list(np.repeat(1/int(len((recent_df))), int(len(recent_df))))
            
        for index, row in recent_df.iterrows():
            team = pd.read_sql(text(f"SELECT * FROM batter_table WHERE game_id = '{row['game_id']}' AND playerid = '{row['playerId']}';"), con=engine).to_dict('records')
            pitcher = pd.read_sql(text(f"SELECT * FROM pitcher_table WHERE game_id = '{row['game_id']}' AND team != '{team[0]['team']}' AND role = 'starter';"), con=engine).to_dict('records')

            date_str = str(row['game_date'])
            date_obj = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
            formatted_date = date_obj.strftime('%Y/%m/%d')
            average_obp, average_whip = update_league_average(formatted_date, False)
            
            last_whip, career_whip, recent_whip = cal_pitcher_average(pitcher[0]['playerid'], formatted_date)
            if average_whip == 0 or last_whip == 0 or career_whip == 0 or recent_whip == 0:
                difficulty.append(8/8)
            else:
                value = switch_difficulty(average_whip/last_whip, recent_whip/career_whip)
                difficulty.append(value)

        difficulty_weights = np.array(weights) * np.array(difficulty)
            
        recent_df['singles'] = recent_df['hits']-recent_df['doubles']-recent_df['triples']-recent_df['homeRuns']
        recent_df['avg'] = recent_df.apply(lambda x: x['hits']/x['atBats'] if x['atBats']>0 else 0,axis=1)
        recent_df['obp'] = recent_df.apply(lambda x: (x['hits']+x['baseOnBalls'])/(x['atBats']+x['baseOnBalls']) if x['atBats']+x['baseOnBalls']>0 else 0,axis=1)
        recent_df['slg'] = recent_df.apply(lambda x: ((x['singles'])+2*(x['doubles'])+3*(x['triples'])+4*(x['homeRuns']))/x['atBats'] if x['atBats']>0 else 0,axis=1)
        recent_df['ops'] = recent_df['obp'] + recent_df['slg']

        last_whip, career_whip, recent_whip = cal_pitcher_average(team_starter, game_date)
        if average_whip == 0 or last_whip == 0 or career_whip == 0 or recent_whip == 0:
            DifficultyRating = 8/8
        else:
            DifficultyRating = switch_difficulty(average_whip/last_whip, recent_whip/career_whip)

        drop_cols = ['game_date', 'note', 'game_id', 'away_team', 'home_team', 'away_score', 'home_score']
        recent_df = recent_df.drop(drop_cols,axis = 1,errors = 'ignore').astype(float)
        recent_data = recent_df.mul(weights,axis = 0).sum().to_dict()
        recent_difficulty_data = recent_df.mul(difficulty_weights,axis = 0).sum().to_dict()

        recent_difficulty_data['difficulty'] = DifficultyRating
        recent_difficulty_data['playerId'] = recent_data['playerId']

    return recent_difficulty_data, games

def process_career_batter_data(games, batter_stat_list): 
    
    if len(games)==0: 
        career_data = dict(zip(batter_stat_list, np.repeat(np.nan, len(batter_stat_list))))
        return career_data

    if len(games) < 200: 
        s_list, weights = [games], [1]
    elif len(games) >= 200: 
        last_40 = games.tail(200)  # Get the last 40 rows of the DataFrame
        sub_df1 = last_40.iloc[-200:-134]
        sub_df2 = last_40.iloc[-133:-67]  
        sub_df3 = last_40.iloc[-66:]
        s_list = [sub_df3,sub_df2,sub_df1]
        weights = [2/3,1/6,1/6]
    all_s_data=[]
    for s_df in s_list: 
        s_df['singles'] = s_df['hits']-s_df['doubles']-s_df['triples']-s_df['homeRuns']
        s_df['avg'] = s_df.apply(lambda x: x['hits']/x['atBats'] if x['atBats']>0 else 0,axis=1)
        s_df['obp'] = s_df.apply(lambda x: (x['hits']+x['baseOnBalls'])/(x['atBats']+x['baseOnBalls']) if x['atBats']+x['baseOnBalls']>0 else 0,axis=1)
        s_df['slg'] = s_df.apply(lambda x: ((x['singles'])+2*(x['doubles'])+3*(x['triples'])+4*(x['homeRuns']))/x['atBats'] if x['atBats']>0 else 0,axis=1)
        s_df['ops'] = s_df['obp'] + s_df['slg']
        drop_cols = ['game_date', 'note', 'season','game_id', 'away_team', 'home_team', 'away_score', 'home_score']
        s_df = s_df.drop(drop_cols, errors = 'ignore', axis = 1)
        s_data = s_df.mean().to_dict()
        all_s_data.append(s_data)
    career_data=pd.DataFrame(all_s_data).mul(weights,axis=0).sum().to_dict()

    return career_data

def process_team_batter_data(team_batters, team, game_date, team_starter): 
    
    batter_stat_list = ['home_score', 'away_score', 'atBats', 'avg', 'baseOnBalls', 'doubles', 'hits', 'homeRuns', 'obp', 'ops', 'playerId', 'rbi', 'runs', 
                        'slg', 'strikeOuts', 'triples', 'season', 'singles']

    team_batter_data = {}
    team_recent_data = {}
    team_career_data = {}

    # for team_batter in team_batters: 
    for i in range(9):
        # order = team_batters.index(team_batter)+1
        order = i + 1
        team_batter = team_batters[i]
        player_df = get_batter_df(team_batter, game_date)

        if len(player_df) > 0 : 
            recent_data, games = process_recent_batter_data(player_df, game_date, team_starter, batter_stat_list)
            career_data = process_career_batter_data(games, batter_stat_list)
        else: 
            recent_data = dict(zip(batter_stat_list, np.repeat(0, len(batter_stat_list))))
            recent_data['dificulty'] = 0
            career_data = dict(zip(batter_stat_list, np.repeat(0, len(batter_stat_list))))

        # break
        recent_data = {f'{team}_recent_b{order}_{k}':v for k,v in recent_data.items()}
        career_data = {f'{team}_career_b{order}_{k}':v for k,v in career_data.items()}
            
        team_recent_data.update(recent_data)
        team_career_data.update(career_data)
      
    team_batter_data.update(team_career_data)
    team_batter_data.update(team_recent_data)

    return team_batter_data

def get_starter_df(player_id, gamedate): 

    df = pd.read_sql("SELECT b.game_id, b.game_date, b.home_team, b.away_team, b.home_score, b.away_score, (a.atbats)atBats, "
            "(a.baseonballs)baseonBalls, a.blownsaves, a.doubles, (a.earnedruns)earnedRuns, a.era, a.hits, a.holds, (a.homeruns)homeRuns, "
            "(a.inningspitched)inningsPitched, a.losses, (a.pitchesthrown)pitchesThrown, (a.playerid)playerId, a.rbi, a.runs, (a.strikeouts)strikeOuts, "
            "a.strikes, a.triples, a.whip, a.wins FROM pitcher_table a LEFT JOIN game_table b ON a.game_id = b.game_id WHERE a.playerid = '%s' AND a.role = 'starter' AND a.batter = '0' AND b.game_date < '%s';" %(player_id, gamedate), con = engine)

    string_cols = [col for col in df.columns if 'id' in col.lower()] + ['game_date', 'away_team', 'home_team']

    player_df = df.loc[:,:]

    player_df[string_cols] = df[string_cols].astype(str)
    non_string_cols = [col for col in df.columns if col not in string_cols]
    player_df[non_string_cols] = df[non_string_cols].astype(float)
    player_df['game_date'] = pd.to_datetime(df['game_date'])
    rename_dict = {'pitchesthrown': 'pitchesThrown', 'playerid': 'playerId', 'strikeouts': 'strikeOuts', 
            'baseonballs': 'baseOnBalls', 'homeruns': 'homeRuns', 'atbats': 'atBats', 
            'inningspitched': 'inningsPitched', 'earnedruns': 'earnedRuns'
            }

    new_col_names = []

    for col in player_df.columns: 
        for k,v in rename_dict.items(): 
            col = col.replace(k,v)
        new_col_names.append(col)
    player_df.columns = new_col_names

    player_df = player_df.reset_index(drop = True)
    return player_df

def process_recent_starter_data(player_df, game_date, team_batters, pitcher_stat_list): 
    
    player_df['game_date'] = pd.to_datetime(player_df['game_date'])
    games = player_df[player_df['game_date'] < game_date]
    games = games.sort_values('game_date')
    difficulty = []
    
    if len(games) == 0: 
        recent_data = dict(zip(pitcher_stat_list, np.repeat(0, len(pitcher_stat_list))))
        
    else: 
        
        if len(games) >= 5: 
            recent_df = games.tail(5)
            weights = [0.15,.175,.175,.25,.25]
            
        else: 
            recent_df = games
            weights = list(np.repeat(1/len(recent_df), len(recent_df)))
        
        for index, row in recent_df.iterrows():
            team = pd.read_sql(text(f"SELECT * FROM pitcher_table WHERE game_id = '{row['game_id']}' AND playerid = '{row['playerId']}';"), con=engine).to_dict('records')
            batters = pd.read_sql(text(f"SELECT * FROM batter_table WHERE game_id = '{row['game_id']}' AND team != '{team[0]['team']}' AND substitution = '0';"), con=engine).to_dict('records')
            batter_difficulty = 0
            for batter in batters:
                date_str = str(row['game_date'])
                date_obj = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
                formatted_date = date_obj.strftime('%Y/%m/%d')
                average_obp, average_whip = update_league_average(formatted_date, False)
                last_obp, career_obp, recent_obp = cal_batter_average(batter['playerid'], formatted_date)
                if average_obp == 0 or last_obp == 0 or career_obp == 0 or recent_obp == 0:
                    batter_difficulty = batter_difficulty + 8/8
                else:
                    value = switch_difficulty(last_obp/average_obp, recent_obp/career_obp)
                    batter_difficulty = batter_difficulty + value

            batter_difficulty = batter_difficulty / 9.0
            difficulty.append(batter_difficulty)

        difficulty_weights = np.array(weights) * np.array(difficulty)
        recent_df['era'] = recent_df.apply(lambda x: 9*x['earnedRuns']/x['inningsPitched'] if x['inningsPitched']>0 else 0,axis=1)
        recent_df['whip'] = recent_df.apply(lambda x: (x['baseOnBalls']+x['hits'])/x['inningsPitched'] if x['inningsPitched']>0 else 0 ,axis=1)
        
        DifficultyRating = 0
        for el in team_batters:
            last_obp, career_obp, recent_obp = cal_batter_average(el, game_date)
            if average_obp == 0 or last_obp == 0 or career_obp == 0 or recent_obp == 0:
                DifficultyRating = DifficultyRating + 8/8
            else:
                value = switch_difficulty(last_obp/average_obp, recent_obp/career_obp)
                DifficultyRating = DifficultyRating + value
        
        DifficultyRating = DifficultyRating / 9.0
        difficulty_weights = np.array(weights) * np.array(difficulty)

        drop_cols = ['game_date', 'note', 'game_id', 'away_team', 'home_team', 'away_score', 'home_score']
        recent_df = recent_df.drop(drop_cols,axis = 1,errors = 'ignore').astype(float)
        recent_data = recent_df.mul(weights,axis = 0).sum().to_dict()
        recent_difficulty_data = recent_df.mul(difficulty_weights,axis = 0).sum().to_dict()

        recent_difficulty_data['difficulty'] = DifficultyRating
        recent_difficulty_data['playerId'] = recent_data['playerId']
        
    return recent_difficulty_data, games

def process_career_starter_data(games, pitcher_stat_list): 
    
    if len(games)==0: 
        career_data = dict(zip(pitcher_stat_list, np.repeat(0, len(pitcher_stat_list))))
    else: 
        if len(games) < 40: 
            s_list, weights = [games], [1]
        elif len(games) >= 40: 
            last_40 = games.tail(40)  # Get the last 40 rows of the DataFrame
            sub_df1 = last_40.iloc[-40:-29]
            sub_df2 = last_40.iloc[-28:-15]  
            sub_df3 = last_40.iloc[-14:]
            s_list = [sub_df3,sub_df2,sub_df1]
            weights = [2/3,1/6,1/6]

        all_s_data=[]
        for s in s_list: 
            s['era'] = s.apply(lambda x: 9*x['earnedRuns']/x['inningsPitched'] if x['inningsPitched']>0 else 0,axis=1)
            s['whip'] = s.apply(lambda x: (x['baseOnBalls']+x['hits'])/x['inningsPitched'] if x['inningsPitched']>0 else 0 ,axis=1)
            drop_cols = ['game_id', 'game_date', 'note', 'season','game_id', 'away_team', 'home_team', 'away_score', 'home_score']
            s = s.drop(drop_cols, errors = 'ignore', axis = 1)
            s_data = s.mean().to_dict()
            all_s_data.append(s_data)
            
        career_df = pd.DataFrame(all_s_data)
        career_data = career_df.mul(weights,axis=0).sum().to_dict()
    
    return career_data

def process_starter_data(team_starter, team, game_date, team_batters): 
    
    pitcher_stat_list=[
        'atBats', 'baseOnBalls', 'blownSave', 'doubles', 'earnedRuns', 'era', 'hits', 'holds', 'homeRuns', 'inningsPitched', 
        'losses', 'pitchesThrown', 'playerId', 'rbi', 'runs', 'strikeOuts', 'strikes', 'triples', 'whip',  'wins']
    
    
    player_df = get_starter_df(team_starter, game_date)

    if len(player_df) > 0 : 
        recent_data, games = process_recent_starter_data(player_df, game_date, team_batters, pitcher_stat_list)
        career_data = process_career_starter_data(games, pitcher_stat_list)
    else: 
        recent_data = dict(zip(pitcher_stat_list, np.repeat(0, len(pitcher_stat_list))))
        career_data = dict(zip(pitcher_stat_list, np.repeat(0, len(pitcher_stat_list))))

    recent_data = {f'{team}_starter_recent_{k}':v for k,v in recent_data.items()}
    career_data = {f'{team}_starter_career_{k}':v for k,v in career_data.items()}

    team_starter_data = {}
    team_starter_data.update(career_data)
    team_starter_data.update(recent_data)
    
    return team_starter_data

def get_bullpen_df(team_name): 

    engine = database.connect_to_db()

    df = pd.read_sql("SELECT b.game_id, b.game_date, b.home_team, b.away_team, b.home_score, b.away_score, (a.atbats)atBats, "
            "(a.baseonballs)baseonBalls, a.blownsaves, a.doubles, (a.earnedruns)earnedRuns, a.era, a.hits, a.holds, (a.homeruns)homeRuns, "
            "(a.inningspitched)inningsPitched, a.losses, (a.pitchesthrown)pitchesThrown, (a.playerid)playerId, a.rbi, a.runs, (a.strikeouts)strikeOuts, "
            "a.strikes, a.triples, a.whip, a.wins FROM pitcher_table a LEFT JOIN game_table b ON a.game_id = b.game_id WHERE ((b.away_team = '%s' AND a.team = 'away') OR "
            "(b.home_team = '%s' AND a.team = 'home')) AND a.role = 'bullpenAvg' AND a.batter = '0';" %(team_name, team_name), con = engine)

    string_cols = [col for col in df.columns if 'id' in col.lower()] + ['game_date', 'away_team', 'home_team']

    bullpen_df = df.loc[:,:]

    bullpen_df[string_cols] = df[string_cols].astype(str)
    non_string_cols = [col for col in df.columns if col not in string_cols]
    bullpen_df[non_string_cols] = df[non_string_cols].astype(float)
    bullpen_df['game_date'] = pd.to_datetime(df['game_date'])
    rename_dict = {'pitchesthrown': 'pitchesThrown', 'playerid': 'playerId', 'strikeouts': 'strikeOuts', 
            'baseonballs': 'baseOnBalls', 'homeruns': 'homeRuns', 'atbats': 'atBats', 
            'inningspitched': 'inningsPitched', 'earnedruns': 'earnedRuns'
            }

    new_col_names = []

    for col in bullpen_df.columns: 
        for k,v in rename_dict.items(): 
            col = col.replace(k,v)
        new_col_names.append(col)
    bullpen_df.columns = new_col_names

    bullpen_df = bullpen_df.reset_index(drop = True)

    return bullpen_df

def process_recent_bullpen_data(bullpen_df, game_date, pitcher_stat_list): 
    
    bullpen_df['game_date'] = pd.to_datetime(bullpen_df['game_date'])
    games = bullpen_df[bullpen_df['game_date'] < game_date]
    games = games.sort_values('game_date')
    
    
    if len(games) == 0: 
        recent_games = []
        recent_data = dict(zip(pitcher_stat_list, np.repeat(0, len(pitcher_stat_list))))
        
    else: 
        
        if len(games) >= 5: 
            recent_df = games.tail(5)
            weights = [0.15,.175,.175,.25,.25]
            
        else: 
            recent_df = games
            weights = list(np.repeat(1/len(recent_df), len(recent_df)))
            
        recent_df['era'] = recent_df.apply(lambda x: 9*x['earnedRuns']/x['inningsPitched'] if x['inningsPitched']>0 else 0,axis=1)
        recent_df['whip'] = recent_df.apply(lambda x: (x['baseOnBalls']+x['hits'])/x['inningsPitched'] if x['inningsPitched']>0 else 0 ,axis=1)
        
        
        drop_cols = ['game_date', 'note', 'game_id', 'away_team', 'home_team', 'away_score', 'home_score']
        recent_df = recent_df.drop(drop_cols,axis = 1,errors = 'ignore').astype(float)
        recent_data = recent_df.mul(weights,axis = 0).sum().to_dict()
        recent_games = list(recent_df.index)
        
    return recent_data, recent_games, games

def process_career_bullpen_data(player_id, games, recent_games, pitcher_stat_list, game_date): 
    
    # Get Seasons 
    games['season'] = games['game_date'].dt.year
    seasons = sorted(set(games['season']))[-3:]
    
    if len(seasons)==0: 
        career_data = dict(zip(pitcher_stat_list, np.repeat(0, len(pitcher_stat_list))))
        return career_data
    
    # Get Season Game Count 
    s0 = seasons[-1]
    season_game_count = len(games[games['season']==s0])
    games = games.drop(recent_games, axis = 0)
    
    # Case #1: Rookie
    if len(seasons)==1: 
        s_list, weights = [s0], [2/3]
    # Case #2: 2nd Year
    elif len(seasons)==2: 
        s1=seasons[0]
        s_list = [s0,s1] if season_game_count > 15 else [s1]
        weights = [2/3,1/6] if season_game_count > 15 else [1]        
    # Case #3: 3+ Years
    elif len(seasons)==3: 
        s1,s2 = seasons[1], seasons[0]
        s_list = [s0,s1,s2] if season_game_count>15 else [s1,s2]
        weights = [2/3,1/6,1/6] if season_game_count>15 else [1/2,1/2]
    else: 
        career_data = dict(zip(pitcher_stat_list, np.repeat(np.nan, len(pitcher_stat_list))))
        return career_data

    all_s_data=[]
    for s in s_list: 
        s_df = games[games['season']==s]
        if len(s_df)==0: 
            s_data = dict(zip(pitcher_stat_list, np.repeat(np.nan, len(pitcher_stat_list))))
            all_s_data.append(s_data)
        else: 
            s_df['era'] = s_df.apply(lambda x: 9*x['earnedRuns']/x['inningsPitched'] if x['inningsPitched']>0 else 0,axis=1)
            s_df['whip'] = s_df.apply(lambda x: (x['baseOnBalls']+x['hits'])/x['inningsPitched'] if x['inningsPitched']>0 else 0 ,axis=1)
            drop_cols = ['game_date', 'note', 'game_id', 'away_team', 'season','home_team', 'away_score', 'home_score']
            s_df = s_df.drop(drop_cols,axis = 1,errors = 'ignore')
            s_data = s_df.mean().to_dict()
            all_s_data.append(s_data)
            
    career_df = pd.DataFrame(all_s_data)
    career_data = career_df.mul(weights,axis=0).sum().to_dict()
    
    
    return career_data

def process_bullpen_data(team_name, team, game_date): 
    
    pitcher_stat_list=['atBats', 'baseOnBalls', 'blownSave', 'doubles', 'earnedRuns', 'era', 'hits', 'holds', 'homeRuns', 'inningsPitched', 
        'losses', 'pitchesThrown', 'playerId', 'rbi', 'runs', 'strikeOuts', 'strikes', 'triples', 'whip',  'wins']
    
    bullpen_df = get_bullpen_df(team_name)
    
    
    if len(bullpen_df) > 0 : 
        recent_data, recent_games, games = process_recent_bullpen_data(bullpen_df, game_date, pitcher_stat_list)
        career_data = process_career_bullpen_data(team_name, games, recent_games, pitcher_stat_list, game_date)
    else: 
        recent_data = dict(zip(pitcher_stat_list, np.repeat(0, len(pitcher_stat_list))))
        career_data = dict(zip(pitcher_stat_list, np.repeat(0, len(pitcher_stat_list))))

    recent_data = {f'{team}_bullpen_recent_{k}':v for k,v in recent_data.items()}
    career_data = {f'{team}_bullpen_career_{k}':v for k,v in career_data.items()}

    team_bullpen_data = {}
    team_bullpen_data.update(career_data)
    team_bullpen_data.update(recent_data)
    
    return team_bullpen_data

def update_league_average(gamedate, state):

    date_object = datetime.strptime(gamedate, '%Y/%m/%d')
    # Extract the year from the datetime object
    year = date_object.year
    batter_df = pd.read_sql(f"SELECT b.game_id, b.game_date, b.home_team, b.away_team, b.home_score, b.away_score, (a.atbats)atBats, a.avg, \
            (a.baseonballs)baseonBalls, a.doubles, a.hits, (a.homeruns)homeRuns, a.obp, a.ops, \
            (a.playerid)playerId, a.rbi, a.runs, a.slg, (a.strikeouts)strikeOuts, \
            a.triples FROM batter_table a LEFT JOIN game_table b ON a.game_id = b.game_id WHERE a.substitution = '0' AND b.game_date LIKE '{year}%%' AND b.game_date < '{gamedate}';", con = engine).to_dict('records')

    atbats = 0
    hits = 0
    doubles = 0
    triples = 0
    b_homeruns = 0
    baseonballs = 0
    era = 0
    whip = 0
    rbi = 0
    strikeouts = 0

    for row in batter_df:
        atbats = atbats + float(row['atbats'])
        hits = hits + float(row['hits'])
        doubles = doubles + float(row['doubles'])
        triples = triples + float(row['triples'])
        b_homeruns = b_homeruns + float(row['homeruns'])
        baseonballs = baseonballs + float(row['baseonballs'])
        rbi = rbi + float(row['rbi'])
        strikeouts = strikeouts + float(row['strikeouts'])

    singles = hits-doubles-triples-b_homeruns
    avg = hits/atbats if atbats>0 else 0
    obp = (hits+baseonballs)/(atbats+baseonballs) if (atbats+baseonballs)>0 else 0
    slg = (singles+2*doubles+3*triples+4*b_homeruns)/atbats if atbats>0 else 0
    atbats = atbats / len(batter_df) if len(batter_df)>0 else 0
    b_homeruns = b_homeruns / len(batter_df) if len(batter_df)>0 else 0
    rbi = rbi / len(batter_df) if len(batter_df)>0 else 0
    strikeouts = strikeouts / len(batter_df) if len(batter_df)>0 else 0
    ops = obp + slg
    atbats = round(atbats, 3)
    rbi = round(rbi, 3)
    strikeouts = round(strikeouts, 3)
    b_homeruns = round(b_homeruns, 3)
    avg = round(avg, 3)
    obp = round(obp, 3)
    slg = round(slg, 3)
    ops = round(ops, 3)

    pitcher_df = pd.read_sql(f"SELECT b.game_id, b.game_date, b.home_team, b.away_team, b.home_score, b.away_score, (a.atbats)atBats, \
            (a.baseonballs)baseonBalls, a.blownsaves, a.doubles, (a.earnedruns)earnedRuns, a.era, a.hits, a.holds, (a.homeruns)homeRuns, \
            (a.inningspitched)inningsPitched, a.losses, (a.pitchesthrown)pitchesThrown, (a.playerid)playerId, a.rbi, a.runs, (a.strikeouts)strikeOuts, \
            a.strikes, a.triples, a.whip, a.wins FROM pitcher_table a LEFT JOIN game_table b ON a.game_id = b.game_id WHERE a.role = 'starter' AND a.batter = '0' AND b.game_date LIKE '{year}%%' AND b.game_date < '{gamedate}';", con = engine).to_dict('records')
    
    baseonballs = 0
    hits = 0
    inningspitched = 0
    earnedruns = 0
    battersfaced = 0
    atbats = 0
    p_homeruns = 0

    for row in pitcher_df:
        atbats = atbats + float(row['atbats'])
        p_homeruns = p_homeruns + float(row['homeruns'])
        hits = hits + float(row['hits'])
        baseonballs = baseonballs + float(row['baseonballs'])
        inningspitched = inningspitched + float(row['inningspitched'])
        earnedruns = earnedruns + float(row['earnedruns'])

    battersfaced = baseonballs + atbats
    era = 9*earnedruns/inningspitched if inningspitched>0 else 0
    whip = (baseonballs+hits)/inningspitched if inningspitched>0 else 0
    battersfaced = battersfaced / len(pitcher_df) if len(pitcher_df)>0 else 0
    p_homeruns = p_homeruns / len(pitcher_df) if len(pitcher_df)>0 else 0

    era = round(era, 3)
    whip = round(whip, 3)
    battersfaced = round(battersfaced, 3)
    p_homeruns = round(p_homeruns, 3)
    if state:
        engine.execute(text(f"INSERT INTO league_average (year, avg, obp, slg, ops, era, whip) VALUES ('{year}', '{avg}', '{obp}', '{slg}', '{ops}', '{era}', '{whip}') ON CONFLICT (year) DO UPDATE SET avg = excluded.avg, obp = excluded.obp, slg = excluded.slg, ops = excluded.ops, era = excluded.era, whip = excluded.whip;"))   
    
    return obp, whip

def cal_batter_average(team_batter, gamedate):
    df = get_batter_df(team_batter, gamedate)

    if len(df) == 0:
        return 0, 0, 0

    last_obp = df.iloc[-1]['obp']

    if len(df) >= 15: 
        recent_df = df.tail(15)
        weights = [0.01,0.02,0.03,0.04,0.05,0.05,0.06,0.07,0.08,0.08,0.09,0.09,0.1,0.11,0.12]
        
    else: 
        recent_df = df
        weights = list(np.repeat(1/len(recent_df), len(recent_df)))
        
    recent_df['singles'] = recent_df['hits']-recent_df['doubles']-recent_df['triples']-recent_df['homeRuns']
    recent_df['avg'] = recent_df.apply(lambda x: x['hits']/x['atBats'] if x['atBats']>0 else 0,axis=1)
    recent_df['obp'] = recent_df.apply(lambda x: (x['hits']+x['baseOnBalls'])/(x['atBats']+x['baseOnBalls']) if x['atBats']+x['baseOnBalls']>0 else 0,axis=1)
    recent_df['slg'] = recent_df.apply(lambda x: ((x['singles'])+2*(x['doubles'])+3*(x['triples'])+4*(x['homeRuns']))/x['atBats'] if x['atBats']>0 else 0,axis=1)
    recent_df['ops'] = recent_df['obp'] + recent_df['slg']
    
    drop_cols = ['game_date', 'note', 'game_id', 'away_team', 'home_team', 'away_score', 'home_score']
    recent_df = recent_df.drop(drop_cols,axis = 1,errors = 'ignore').astype(float)
    recent_data = recent_df.mul(weights,axis = 0).sum().to_dict()
    
    if len(df) < 200: 
        s_list, weights = [df], [1]
    elif len(df) >= 200: 
        last_40 = df.tail(200)  # Get the last 40 rows of the DataFrame
        sub_df1 = last_40.iloc[-200:-134]
        sub_df2 = last_40.iloc[-133:-67]  
        sub_df3 = last_40.iloc[-66:]
        s_list = [sub_df3,sub_df2,sub_df1]
        weights = [2/3,1/6,1/6]
    all_s_data=[]
    for s_df in s_list: 
        s_df['singles'] = s_df['hits']-s_df['doubles']-s_df['triples']-s_df['homeRuns']
        s_df['avg'] = s_df.apply(lambda x: x['hits']/x['atBats'] if x['atBats']>0 else 0,axis=1)
        s_df['obp'] = s_df.apply(lambda x: (x['hits']+x['baseOnBalls'])/(x['atBats']+x['baseOnBalls']) if x['atBats']+x['baseOnBalls']>0 else 0,axis=1)
        s_df['slg'] = s_df.apply(lambda x: ((x['singles'])+2*(x['doubles'])+3*(x['triples'])+4*(x['homeRuns']))/x['atBats'] if x['atBats']>0 else 0,axis=1)
        s_df['ops'] = s_df['obp'] + s_df['slg']
        drop_cols = ['game_date', 'note', 'season','game_id', 'away_team', 'home_team', 'away_score', 'home_score']
        s_df = s_df.drop(drop_cols, errors = 'ignore', axis = 1)
        s_data = s_df.mean().to_dict()
        all_s_data.append(s_data)
    career_data=pd.DataFrame(all_s_data).mul(weights,axis=0).sum().to_dict()

    return last_obp, career_data['obp'], recent_data['obp']

def cal_pitcher_average(team_pitcher, gamedate):
  
    df = get_starter_df(team_pitcher, gamedate)
    
    if len(df) == 0: 
        return 0, 0, 0
    
    last_whip = df.iloc[-1]['whip']
        
    if len(df) >= 5: 
        recent_df = df.tail(5)
        weights = [0.15,.175,.175,.25,.25]
        
    else: 
        recent_df = df
        weights = list(np.repeat(1/len(recent_df), len(recent_df)))
        
    recent_df['era'] = recent_df.apply(lambda x: 9*x['earnedRuns']/x['inningsPitched'] if x['inningsPitched']>0 else 0,axis=1)
    recent_df['whip'] = recent_df.apply(lambda x: (x['baseOnBalls']+x['hits'])/x['inningsPitched'] if x['inningsPitched']>0 else 0 ,axis=1)
    
    
    drop_cols = ['game_date', 'note', 'game_id', 'away_team', 'home_team', 'away_score', 'home_score']
    recent_df = recent_df.drop(drop_cols,axis = 1,errors = 'ignore').astype(float)
    recent_data = recent_df.mul(weights,axis = 0).sum().to_dict()
    
    if len(df) < 40: 
        s_list, weights = [df], [1]
    elif len(df) >= 40: 
        last_40 = df.tail(40)  # Get the last 40 rows of the DataFrame
        sub_df1 = last_40.iloc[-40:-29]
        sub_df2 = last_40.iloc[-28:-15]  
        sub_df3 = last_40.iloc[-14:]
        s_list = [sub_df3,sub_df2,sub_df1]
        weights = [2/3,1/6,1/6]

    all_s_data=[]
    for s in s_list: 
        s['era'] = s.apply(lambda x: 9*x['earnedRuns']/x['inningsPitched'] if x['inningsPitched']>0 else 0,axis=1)
        s['whip'] = s.apply(lambda x: (x['baseOnBalls']+x['hits'])/x['inningsPitched'] if x['inningsPitched']>0 else 0 ,axis=1)
        drop_cols = ['game_id', 'game_date', 'note', 'season','game_id', 'away_team', 'home_team', 'away_score', 'home_score']
        s = s.drop(drop_cols, errors = 'ignore', axis = 1)
        s_data = s.mean().to_dict()
        all_s_data.append(s_data)
        
    career_df = pd.DataFrame(all_s_data)
    career_data = career_df.mul(weights,axis=0).sum().to_dict()
    return last_whip, career_data['whip'], recent_data['whip']

def switch_difficulty(leaguefactor, recentfacotr):
    if leaguefactor >= 1.3 and recentfacotr >= 1.08:
        return 15/8
    elif leaguefactor >= 1.3 and recentfacotr < 1.08 and recentfacotr >= 0.93:
        return 14/8
    elif leaguefactor >= 1.3 and  recentfacotr < 0.93:
        return 13/8
    elif leaguefactor >= 1.1 and leaguefactor < 1.3 and recentfacotr >= 1.08:
        return 12/8
    elif leaguefactor >= 1.1 and leaguefactor < 1.3 and recentfacotr < 1.08 and recentfacotr >= 0.93:
        return 11/8
    elif leaguefactor >= 1.1 and leaguefactor < 1.3 and recentfacotr < 0.93:
        return 10/8
    elif leaguefactor >= 0.9 and leaguefactor < 1.1 and recentfacotr >= 1.08:
        return 9/8
    elif leaguefactor >= 0.9 and leaguefactor < 1.1 and recentfacotr < 1.08 and recentfacotr >= 0.93:
        return 8/8
    elif leaguefactor >= 0.9 and leaguefactor < 1.1 and recentfacotr < 0.93:
        return 7/8
    elif leaguefactor >= 0.7 and leaguefactor < 0.9 and recentfacotr >= 1.08:
        return 6/8
    elif leaguefactor >= 0.7 and leaguefactor < 0.9 and recentfacotr < 1.08 and recentfacotr >= 0.93:
        return 5/8
    elif leaguefactor >= 0.7 and leaguefactor < 0.9 and recentfacotr < 0.93:
        return 4/8
    elif leaguefactor < 0.7 and recentfacotr >= 1.08:
        return 3/8
    elif leaguefactor < 0.7 and recentfacotr < 1.08 and recentfacotr >= 0.93:
        return 2/8
    elif leaguefactor < 0.7 and recentfacotr < 0.93:
        return 1/8
    
def switch_group(difficulty):
    if difficulty >= 29/16:
        return "BG"
    elif difficulty >=27/16 and difficulty < 29/16:
        return "BA"
    elif difficulty >=25/16 and difficulty < 27/16:
        return "BB"
    elif difficulty >=23/16 and difficulty < 25/16:
        return "GG"
    elif difficulty >=21/16 and difficulty < 23/16:
        return "GA"
    elif difficulty >=19/16 and difficulty < 21/16:
        return "GB"
    elif difficulty >=17/16 and difficulty < 19/16:
        return "AG"
    elif difficulty >=15/16 and difficulty < 17/16:
        return "AA"
    elif difficulty >=13/16 and difficulty < 15/16:
        return "AB"
    elif difficulty >=11/16 and difficulty < 13/16:
        return "BAG"
    elif difficulty >=9/16 and difficulty < 11/16:
        return "BAA"
    elif difficulty >=7/16 and difficulty < 9/16:
        return "BAB"
    elif difficulty >=5/16 and difficulty < 7/16:
        return "PG"
    elif difficulty >=3/16 and difficulty < 5/16:
        return "PA"
    elif difficulty >=1/16 and difficulty < 3/16:
        return "PB"

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
    print('#################################          drop_cols            ##############################################')
    print(drop_cols)
    X_test = X_test.drop(drop_cols,axis=1)
    print('#################################          X_test 2_1            ##############################################')
    print(drop_cols)    
    column_names = X_test.columns
    
    return X_test, column_names   

def save_batter_data(engine, row, away_batters, home_batters, gameId, rosters): 
    print(row)

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
                                        '{float(row['recent_difficulty'])}') ON CONFLICT ON CONSTRAINT batter_stats_c_game_id_player_id_key DO UPDATE SET game_date = excluded.game_date, career_atBats = excluded.career_atBats, career_avg = excluded.career_avg, career_homeRuns = excluded.career_homeRuns, career_obp = excluded.career_obp, career_ops = excluded.career_ops, career_rbi = excluded.career_rbi, career_slg = excluded.career_slg, career_strikeOuts = excluded.career_strikeOuts, \
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
                                    '{float(row['recent_difficulty'])}') ON CONFLICT ON CONSTRAINT pitcher_stats_c_game_id_player_id_key DO UPDATE SET game_date = excluded.game_date, career_era = excluded.career_era, career_homeRuns = excluded.career_homeRuns, career_whip = excluded.career_whip, career_battersFaced = excluded.career_battersFaced, recent_era = excluded.recent_era, recent_homeRuns = excluded.recent_homeRuns, recent_whip = excluded.recent_whip, recent_battersFaced = excluded.recent_battersFaced, difficulty_rating = excluded.difficulty_rating;"))
 
    return pitcher_df

def standardizeData(X_test, column_names): 
    scaler = joblib.load("functions/scaler.bin")
    X_test=scaler.transform(X_test)
    X_test = pd.DataFrame(X_test, columns = column_names)
    
    return X_test
    
today  = date.today()
# result = engine.execute(text(f"SELECT * FROM game_table WHERE game_date LIKE '{today.year}%';")).fetchall()
# result = engine.execute(text(f"SELECT * FROM game_table WHERE game_date LIKE '{today.year}%';")).fetchall()

# for game in result:
awaybatters = []
homebatters = []
away_starter = ''
home_starter = ''
batters = pd.read_sql(text(f"SELECT * FROM batter_table WHERE game_id = '717368' and substitution = '0' ORDER BY team, position;"), con = engine).to_dict('records')
for batter in batters:
    if batter['team'] == 'away':
        awaybatters.append(batter['playerid'])
    if batter['team'] == 'home':
        homebatters.append(batter['playerid'])

pithcers = pd.read_sql(text(f"SELECT * FROM pitcher_table WHERE game_id = '717368' AND role = 'starter';"), con = engine).to_dict('records')

for pitcher in pithcers:
    if pitcher['team'] == 'away':
        away_starter = pitcher['playerid']
    if pitcher['team'] == 'home':
        home_starter = pitcher['playerid']

# if len(awaybatters) != 9 or len(homebatters) != 9 or away_starter == '' or home_starter == '':
#     engine.execute(text(f"DELETE FROM game_table WHERE game_id = '717381';"))
#     continue


# Batters
away_batter_data = process_team_batter_data(awaybatters, 'away', '2023/07/17', home_starter)
home_batter_data = process_team_batter_data(homebatters, 'home', '2023/07/17', away_starter)

# # Starters 
away_starter_data = process_starter_data(away_starter, 'away', '2023/07/17', homebatters)
home_starter_data = process_starter_data(home_starter, 'home', '2023/07/17', awaybatters)

print('#################################          Data             ##############################################')
print('---------------------------------      away_batter_data    ------------------------------------------------')
print(away_batter_data)
print('---------------------------------      home_batter_data    ------------------------------------------------')
print(home_batter_data)
print('---------------------------------      away_starter_data    ------------------------------------------------')
print(away_starter_data)
print('---------------------------------      home_starter_data    ------------------------------------------------')
print(home_starter_data)
# Bullpen 
# away_bullpen_data = process_bullpen_data(game[2], 'away', game[1])
# home_bullpen_data = process_bullpen_data(game[3], 'home', game[1])

# Combine 
game_data = {}
# game_data.update(away_bullpen_data)
game_data.update(away_batter_data)
game_data.update(away_starter_data)

# game_data.update(home_bullpen_data)
game_data.update(home_batter_data)
game_data.update(home_starter_data)

X_test = pd.DataFrame(game_data, index = [0])

print('#################################          X_test 1            ##############################################')
print(X_test)

X_test = feature_selection(X_test, fill_null = True)

print('#################################          X_test 2            ##############################################')
print(X_test)
X_test, column_names = addBattersFaced(X_test, bullpen = False)

print('#################################          X_test 3            ##############################################')
print(X_test)

rosters = schedule.get_rosters('717368')

save_batter_data(engine, X_test, awaybatters, homebatters, '717368', rosters)
save_pitcher_data(engine, X_test, away_starter, home_starter, '717368', rosters)

X_test = standardizeData(X_test, column_names)

# X_test_b = X_test[[col for col in X_test.columns if 'bullpen' not in col]]
# print(X_test)

X_test_b = X_test[[col for col in X_test.columns if col not in ['difficulty', 'group']]]
# print(X_test_b)
# Make Prediciton    
# pred_1a = pickle.load(open('algorithms/model_1a_v10.sav', 'rb')).predict_proba(X_test)
# print(pred_1a)
pred_1b = pickle.load(open('algorithms/model_1b_v10.sav', 'rb')).predict_proba(X_test_b)
print(pred_1b)
engine.execute(f"INSERT INTO win_percent(game_id, away_prob, home_prob) VALUES('{717381}', '{pred_1b['away_prob']}', '{pred_1b['home_prob']}') ON CONFLICT win_percent_c_game_id_key DO UPDATE SET away_prob = excluded.away_prob, home_prob = excluded.home_prob;")  
print("Prediction made")
