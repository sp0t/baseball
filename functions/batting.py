# Dependencies
import statsapi as mlb
import time
from datetime import date, timedelta, datetime
import numpy as np
import pandas as pd
import sqlite3
from database import database


def get_batter_df(team_batter): 
    
    engine = database.connect_to_db()

    df = pd.read_sql("SELECT b.game_id, b.game_date, b.home_team, b.away_team, b.home_score, b.away_score, (a.atbats)atBats, a.avg, "
            "(a.baseonballs)baseonBalls, a.doubles, a.hits, (a.homeruns)homeRuns, a.obp, a.ops, "
            "(a.playerid)playerId, a.rbi, a.runs, a.slg, (a.strikeouts)strikeOuts, "
            "a.triples FROM batter_table a LEFT JOIN game_table b ON a.game_id = b.game_id WHERE a.playerid = '%s';" %(team_batter), con = engine)

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

def process_recent_batter_data(player_df, game_date, batter_stat_list): 
    
    player_df['game_date'] = pd.to_datetime(player_df['game_date'])
    games = player_df[player_df['game_date'] < game_date]
    games = games.sort_values('game_date')
    
    if len(games) == 0: 
        recent_games = []
        recent_data = dict(zip(batter_stat_list, np.repeat(np.nan, len(batter_stat_list))))
        
    else: 
        
        if len(games) >= 15: 
            recent_df = games.tail(15)
            weights = [0.01,0.02,0.03,0.04,0.05,0.05,0.06,0.07,0.08,0.08,0.09,0.09,0.1,0.11,0.12]
            
        else: 
            recent_df = games
            weights = list(np.repeat(1/int(len((recent_df))), int(len(recent_df))))
            
        recent_df['singles'] = recent_df['hits']-recent_df['doubles']-recent_df['triples']-recent_df['homeRuns']
        recent_df['avg'] = recent_df.apply(lambda x: x['hits']/x['atBats'] if x['atBats']>0 else 0,axis=1)
        recent_df['obp'] = recent_df.apply(lambda x: (x['hits']+x['baseOnBalls'])/(x['atBats']+x['baseOnBalls']) if x['atBats']+x['baseOnBalls']>0 else 0,axis=1)
        recent_df['slg'] = recent_df.apply(lambda x: ((x['singles'])+2*(x['doubles'])+3*(x['triples'])+4*(x['homeRuns']))/x['atBats'] if x['atBats']>0 else 0,axis=1)
        recent_df['ops'] = recent_df['obp'] + recent_df['slg']
        
        drop_cols = ['game_date', 'note', 'game_id', 'away_team', 'home_team', 'away_score', 'home_score']
        recent_df = recent_df.drop(drop_cols,axis = 1,errors = 'ignore').astype(float)
        recent_data = recent_df.mul(weights,axis = 0).sum().to_dict()
        recent_games = list(recent_df.index)
        
    return recent_data, recent_games, games

def process_career_batter_data(games, recent_games, batter_stat_list): 
    
    # Get Seasons 
    games['season']=games['game_date'].dt.year
    seasons = sorted(set(games['season']))[-3:]
    
    if len(seasons)==0: 
        career_data = dict(zip(batter_stat_list, np.repeat(np.nan, len(batter_stat_list))))
        return career_data
    
    # Get Season Game Count 
    s0 = seasons[-1]
    season_game_count = len(games[games['season']==s0])
    games = games.drop(recent_games,axis=0)
    
    # Case #1: Rookie
    if len(seasons)==1: 
        s_list, weights = [s0], [2/3]
    # Case #2: 2nd Year
    elif len(seasons)==2: 
        s1=seasons[0]
        s_list = [s0,s1] if season_game_count>15 else [s1]
        weights = [2/3,1/6] if season_game_count>15 else [1]        
    # Case #3: 3+ Years
    elif len(seasons)==3: 
        s1,s2 = seasons[1], seasons[0]
        s_list = [s0,s1,s2] if season_game_count>15 else [s1,s2]
        weights = [2/3,1/6,1/6] if season_game_count>15 else [1/2,1/2]
    else: 
        career_data = dict(zip(batter_stat_list, np.repeat(np.nan, len(batter_stat_list))))
        return career_data

    all_s_data=[]
    for s in s_list: 
        s_df = games[games['season']==s]
        if len(s_df)==0: 
            s_data = dict(zip(batter_stat_list, np.repeat(np.nan, len(batter_stat_list))))
            all_s_data.append(s_data)
        else: 
            s_df['singles'] = s_df['hits']-s_df['doubles']-s_df['triples']-s_df['homeRuns']
            s_df['avg'] = s_df.apply(lambda x: x['hits']/x['atBats'] if x['atBats']>0 else 0,axis=1)
            s_df['obp'] = s_df.apply(lambda x: (x['hits']+x['baseOnBalls'])/(x['atBats']+x['baseOnBalls']) if x['atBats']+x['baseOnBalls']>0 else 0,axis=1)
            s_df['slg'] = s_df.apply(lambda x: ((x['singles'])+2*(x['doubles'])+3*(x['triples'])+4*(x['homeRuns']))/x['atBats'] if x['atBats']>0 else 0,axis=1)
            s_df['ops'] = s_df['obp'] + s_df['slg']
            s_df = s_df.drop('game_id', errors = 'ignore', axis = 1)
            s_data = s_df.mean().to_dict()
            all_s_data.append(s_data)
    career_data=pd.DataFrame(all_s_data).mul(weights,axis=0).sum().to_dict()

    return career_data

def process_team_batter_data(team_batters, team, game_date): 
    
    batter_stat_list = ['home_score', 'away_score', 'atBats', 'runs', 'avg', 'baseOnBalls', 'doubles', 'hits', 'homeRuns', 'triples', 'obp', 'ops', 
                       'playerId', 'rbi', 'runs', 'slg', 'strikeOuts', 'triples', 'season', 'singles']

    team_batter_data = {}
    team_recent_data = {}
    team_career_data = {}

    for team_batter in team_batters: 
        order = team_batters.index(team_batter)+1
        player_df = get_batter_df(team_batter)
        if len(player_df) > 0 : 
            
            recent_data, recent_games, games = process_recent_batter_data(player_df, game_date, batter_stat_list)
            career_data = process_career_batter_data(games, recent_games, batter_stat_list)
        else: 
            recent_data = dict(zip(batter_stat_list, np.repeat(np.nan, len(batter_stat_list))))
            career_data = dict(zip(batter_stat_list, np.repeat(np.nan, len(batter_stat_list))))
            
        recent_data = {f'{team}_recent_b{order}_{k}':v for k,v in recent_data.items()}
        career_data = {f'{team}_career_b{order}_{k}':v for k,v in career_data.items()}
            
        team_recent_data.update(recent_data)
        team_career_data.update(career_data)
            
    team_batter_data.update(team_career_data)
    team_batter_data.update(team_recent_data)

    return team_batter_data