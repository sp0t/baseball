# Dependencies
import statsapi as mlb
import time
from datetime import date, timedelta, datetime
import numpy as np
import pandas as pd
import sqlite3
from database import database

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
        recent_data = dict(zip(pitcher_stat_list, np.repeat(np.nan, len(pitcher_stat_list))))
        recent_data['difficulty'] = 8/8
        
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
        recent_data['difficulty'] = 8/8
        recent_games = list(recent_df.index)
        
    return recent_data, recent_games, games

def process_career_bullpen_data(games,pitcher_stat_list): 
    
    if len(games)==0: 
        career_data = dict(zip(pitcher_stat_list, np.repeat(np.nan, len(pitcher_stat_list))))
    else: 
        if len(games) < 40: 
            s_list, weights = [games], [1]
        elif len(games) >= 40: 
            last_40 = games.tail(40)  # Get the last 40 rows of the DataFrame
            sub_df1 = last_40.iloc[-40:-28]
            sub_df2 = last_40.iloc[-28:-14]  
            sub_df3 = last_40.iloc[-14:]
            s_list = [sub_df3,sub_df2,sub_df1]
            weights = [2/3, 1/6,1/6]

        all_s_data=[]
        for s in s_list:
            drop_cols = ['game_id', 'game_date', 'note', 'season','game_id', 'away_team', 'home_team', 'away_score', 'home_score', 'playerId']
            s = s.drop(drop_cols, errors = 'ignore', axis = 1)
            length = len(s) 
            s = s.sum()
            s['era'] = 9*s['earnedRuns']/s['inningsPitched'] if s['inningsPitched']>0 else 0
            s['whip'] = (s['baseOnBalls']+s['hits'])/s['inningsPitched'] if s['inningsPitched']>0 else 0
            exclude_columns = ['era', 'whip']
            for col in s.keys():
                if col not in exclude_columns:
                    s[col] /= length
            s_data = s.to_dict()
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
        career_data = process_career_bullpen_data(games, pitcher_stat_list)
    else: 
        recent_data = dict(zip(pitcher_stat_list, np.repeat(np.nan, len(pitcher_stat_list))))
        career_data = dict(zip(pitcher_stat_list, np.repeat(np.nan, len(pitcher_stat_list))))

    recent_data = {f'{team}_bullpen_recent_{k}':v for k,v in recent_data.items()}
    career_data = {f'{team}_bullpen_career_{k}':v for k,v in career_data.items()}

    team_bullpen_data = {}
    team_bullpen_data.update(career_data)
    team_bullpen_data.update(recent_data)
    
    return team_bullpen_data