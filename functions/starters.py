# Dependencies
import statsapi as mlb
import time
from datetime import date, timedelta, datetime
import numpy as np
import pandas as pd
import sqlite3
from database import database
from sqlalchemy import text

def get_starter_df(player_id): 
    
    engine = database.connect_to_db()

    df = pd.read_sql("SELECT b.game_id, b.game_date, b.home_team, b.away_team, b.home_score, b.away_score, (a.atbats)atBats, "
            "(a.baseonballs)baseonBalls, a.blownsaves, a.doubles, (a.earnedruns)earnedRuns, a.era, a.hits, a.holds, (a.homeruns)homeRuns, "
            "(a.inningspitched)inningsPitched, a.losses, (a.pitchesthrown)pitchesThrown, (a.playerid)playerId, a.rbi, a.runs, (a.strikeouts)strikeOuts, "
            "a.strikes, a.triples, a.whip, a.wins FROM pitcher_table a INNER JOIN game_table b ON a.game_id = b.game_id WHERE a.playerid = '%s' AND a.role = 'starter' AND a.batter = '0';" %(player_id), con = engine)

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

def process_recent_starter_data(player_df, game_date, pitcher_stat_list): 
    
    player_df['game_date'] = pd.to_datetime(player_df['game_date'])
    games = player_df[player_df['game_date'] < game_date]
    games = games.sort_values('game_date')
    
    if len(games) == 0: 
        recent_games = []
        recent_data = dict(zip(pitcher_stat_list, np.repeat(np.nan, len(pitcher_stat_list))))
        
    else: 
        
        if len(games) >= 5: 
            recent_df = games.tail(5)
            weights = [0.15,.175,.175,.25,.25]
            
        else: 
            recent_df = games
            weights = list(np.repeat(1/len(recent_df), len(recent_df)))
            
        drop_cols = ['game_date', 'note', 'game_id', 'away_team', 'home_team', 'away_score', 'home_score']
        recent_df = recent_df.drop(drop_cols,axis = 1,errors = 'ignore').astype(float)

        recent_df['era'] = recent_df.apply(lambda x: 9*x['earnedRuns']/x['inningsPitched'] if x['inningsPitched']>0 else 0,axis=1)
        recent_df['whip'] = recent_df.apply(lambda x: (x['baseOnBalls']+x['hits'])/x['inningsPitched'] if x['inningsPitched']>0 else 0 ,axis=1)
        
        
        recent_data = recent_df.mul(weights,axis = 0).sum().to_dict()
        recent_games = list(recent_df.index)
        
    return recent_data, recent_games, games

def process_career_starter_data(player_id, games, recent_games, pitcher_stat_list, game_date): 
    
    # Get Seasons 
    games['season'] = games['game_date'].dt.year
    seasons = sorted(set(games['season']))[-3:]
    
    if len(seasons)==0: 
        career_data = dict(zip(pitcher_stat_list, np.repeat(np.nan, len(pitcher_stat_list))))
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
        career_data = dict(zip(pitcher_stat_list, np.repeat(np.nan, len(pitcher_stat_list))))
        return career_data

    all_s_data=[]
    for s in s_list: 
        s_df = games[games['season']==s]
        if len(s_df)==0: 
            s_data = dict(zip(pitcher_stat_list, np.repeat(np.nan, len(pitcher_stat_list))))
            all_s_data.append(s_data)
        else: 
            drop_cols = ['game_date', 'note', 'season','game_id', 'away_team', 'home_team', 'away_score', 'home_score']
            s_df = s_df.drop(drop_cols,axis = 1,errors = 'ignore')
            s_df['era'] = s_df.apply(lambda x: 9*x['earnedRuns']/x['inningsPitched'] if x['inningsPitched']>0 else 0,axis=1)
            s_df['whip'] = s_df.apply(lambda x: (x['baseOnBalls']+x['hits'])/x['inningsPitched'] if x['inningsPitched']>0 else 0 ,axis=1)
            s_df = s_df.drop('game_id', errors = 'ignore', axis = 1)
            s_data = s_df.mean().to_dict()
            all_s_data.append(s_data)
            
    career_df = pd.DataFrame(all_s_data)
    career_data = career_df.mul(weights,axis=0).sum().to_dict()
    
    
    
    return career_data

def process_starter_data(team_starter, team, game_date): 
    
    pitcher_stat_list=[
        'atBats', 'baseOnBalls', 'blownSave', 'doubles', 'earnedRuns', 'era', 'hits', 'holds', 'homeRuns', 'inningsPitched', 
        'losses', 'pitchesThrown', 'playerId', 'rbi', 'runs', 'strikeOuts', 'strikes', 'triples', 'whip',  'wins']
    
    
    player_df = get_starter_df(team_starter)
    
    if len(player_df) > 0 : 
        recent_data, recent_games, games = process_recent_starter_data(player_df, game_date, pitcher_stat_list)
        career_data = process_career_starter_data(team_starter, games, recent_games, pitcher_stat_list, game_date)
    else: 
        recent_data = dict(zip(pitcher_stat_list, np.repeat(np.nan, len(pitcher_stat_list))))
        career_data = dict(zip(pitcher_stat_list, np.repeat(np.nan, len(pitcher_stat_list))))

    recent_data = {f'{team}_starter_recent_{k}':v for k,v in recent_data.items()}
    career_data = {f'{team}_starter_career_{k}':v for k,v in career_data.items()}

    team_starter_data = {}
    team_starter_data.update(career_data)
    team_starter_data.update(recent_data)
    print(team_starter_data)
    
    return team_starter_data

def process_starter_data1(team_starters, team, game_date, gameid): 
    
    pitcher_stat_list=[
        'atBats', 'baseOnBalls', 'blownSave', 'doubles', 'earnedRuns', 'era', 'hits', 'holds', 'homeRuns', 'inningsPitched', 
        'losses', 'pitchesThrown', 'playerId', 'rbi', 'runs', 'strikeOuts', 'strikes', 'triples', 'whip',  'wins']
    
    team_starter_data = {}
    team_recent_data = []
    team_career_data = []
    weights = [0.5552, 0.1112, 0.1112, 0.1112, 0.1112]
    engine = database.connect_to_db()
    formatted_date = game_date.strftime('%Y/%m/%d')
    
    for i in range(5):
        # order = team_batters.index(team_batter)+1
        order = i + 1
        team_starter = team_starters[i]
        player_df = get_starter_df(team_starter)

        if len(player_df) > 0 : 
            recent_data, recent_games, games = process_recent_starter_data(player_df, game_date, pitcher_stat_list)
            career_data = process_career_starter_data(team_starter, games, recent_games, pitcher_stat_list, game_date)
        else: 
            recent_data = dict(zip(pitcher_stat_list, np.repeat(0, len(pitcher_stat_list))))
            career_data = dict(zip(pitcher_stat_list, np.repeat(0, len(pitcher_stat_list))))

        recent_data = {f'{team}_starter_recent_{k}':v for k,v in recent_data.items()}
        career_data = {f'{team}_starter_career_{k}':v for k,v in career_data.items()}
        print(team, '===================================', order)
        
        print(text(f"INSERT INTO pitcher_stats(game_id, game_date, position, player_id, career_era, career_homeRuns, career_whip, career_battersFaced, recent_era, recent_homeRuns, recent_whip, recent_battersFaced) \
                                    VALUES('{gameid}', '{formatted_date}', '{f'{team} pitcher {order}'}', '{team_starter}', '{round(float(career_data[f'{team}_starter_career_era']), 3)}', '{round(float(career_data[f'{team}_starter_career_homeRuns']), 3)}', '{round(float(career_data[f'{team}_starter_career_whip']), 3)}', '{round(float(career_data[f'{team}_starter_career_atBats']) + float(career_data[f'{team}_starter_career_baseOnBalls']), 3)}', '{round(float(recent_data[f'{team}_starter_recent_era']), 3)}', '{round(float(recent_data[f'{team}_starter_recent_homeRuns']), 3)}', '{round(float(recent_data[f'{team}_starter_recent_whip']), 3)}', '{round(float(recent_data[f'{team}_starter_recent_atBats']) + float(recent_data[f'{team}_starter_recent_baseOnBalls']), 3)}') \
                                    ON CONFLICT ON CONSTRAINT unique_pitcher_player DO UPDATE SET game_date = excluded.game_date, career_era = excluded.career_era, career_homeRuns = excluded.career_homeRuns, career_whip = excluded.career_whip, career_battersFaced = excluded.career_battersFaced, recent_era = excluded.recent_era, recent_homeRuns = excluded.recent_homeRuns, recent_whip = excluded.recent_whip, recent_battersFaced = excluded.recent_battersFaced;"))
        engine.execute(text(f"INSERT INTO pitcher_stats(game_id, game_date, position, player_id, career_era, career_homeRuns, career_whip, career_battersFaced, recent_era, recent_homeRuns, recent_whip, recent_battersFaced) \
                                    VALUES('{gameid}', '{formatted_date}', '{f'{team} pitcher {order}'}', '{team_starter}', '{round(float(career_data[f'{team}_starter_career_era']), 3)}', '{round(float(career_data[f'{team}_starter_career_homeRuns']), 3)}', '{round(float(career_data[f'{team}_starter_career_whip']), 3)}', '{round(float(career_data[f'{team}_starter_career_atBats']) + float(career_data[f'{team}_starter_career_baseOnBalls']), 3)}', '{round(float(recent_data[f'{team}_starter_recent_era']), 3)}', '{round(float(recent_data[f'{team}_starter_recent_homeRuns']), 3)}', '{round(float(recent_data[f'{team}_starter_recent_whip']), 3)}', '{round(float(recent_data[f'{team}_starter_recent_atBats']) + float(recent_data[f'{team}_starter_recent_baseOnBalls']), 3)}') \
                                    ON CONFLICT ON CONSTRAINT unique_pitcher_player DO UPDATE SET game_date = excluded.game_date, career_era = excluded.career_era, career_homeRuns = excluded.career_homeRuns, career_whip = excluded.career_whip, career_battersFaced = excluded.career_battersFaced, recent_era = excluded.recent_era, recent_homeRuns = excluded.recent_homeRuns, recent_whip = excluded.recent_whip, recent_battersFaced = excluded.recent_battersFaced;"))
            
        team_recent_data.append(recent_data)
        team_career_data.append(career_data)

    for j in range(len(team_career_data)):
        obj = team_career_data[j]
        for key in obj:
            if key in team_starter_data:
                team_starter_data[key] += obj[key] * weights[j]
            else:
                team_starter_data[key] = obj[key] * weights[j]

    for i in range(len(team_recent_data)):
        obj = team_recent_data[i]
        for key in obj:
            if key in team_starter_data:
                team_starter_data[key] += obj[key] * weights[i]
            else:
                team_starter_data[key] = obj[key] * weights[i]

    return team_starter_data
