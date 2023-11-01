from datetime import date, time, datetime, timedelta
import numpy as np
import pandas as pd
import statsapi as mlb
from sqlalchemy import create_engine
from database import database
from sqlalchemy import text


def get_batter_df(player_id): 
    engine = database.connect_to_db()
    
    df = pd.read_sql("SELECT b.game_id, b.game_date, b.home_team, b.away_team, b.home_score, b.away_score,  (a.homeruns)homeRuns, (a.atbats)atBats, a.avg, "
            " a.slg,  a.obp,  a.ops, (a.baseonballs)baseonBalls, a.doubles, a.hits,"
            "(a.playerid)playerId, a.rbi, a.runs, (a.strikeouts)strikeOuts, "
            "a.triples FROM batter_table a LEFT JOIN game_table b ON a.game_id = b.game_id WHERE a.playerid = '%s' ORDER BY game_date;" %(player_id), con = engine)

    string_cols = [col for col in df.columns if 'id' in col.lower()] + ['game_date', 'away_team', 'home_team']

    player_df = df.loc[:,:]

    player_df[string_cols] = df[string_cols].astype(str)
    non_string_cols = [col for col in df.columns if col not in string_cols]
    player_df[non_string_cols] = df[non_string_cols].astype(float)
    player_df['game_date'] = pd.to_datetime(df['game_date'])
    rename_dict = {'pitchesthrown': 'pitchesThrown', 'playerid': 'playerId', 'strikeouts': 'SO', 
            'baseonballs': 'baseOnBalls', 'homeruns': 'HR', 'atbats': 'AB', 
            'inningspitched': 'inningsPitched', 'earnedruns': 'earnedRuns',
            'avg':'AVG', 'slg':'SLG', 'obp':'OBP', 'ops':'OPS', 'game_date':'GameDate'
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
    
    player_df['GameDate'] = pd.to_datetime(player_df['GameDate'])
    games = player_df[player_df['GameDate'] < game_date]
    games = games.sort_values('GameDate')
    
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
            
        recent_df_copy = recent_df.copy()
        recent_df_copy['singles'] = recent_df['hits']-recent_df['doubles']-recent_df['triples']-recent_df['HR']
        recent_df_copy['AVG'] = recent_df.apply(lambda x: x['hits']/x['AB'] if x['AB']>0 else 0,axis=1)
        recent_df_copy['OBP'] = recent_df.apply(lambda x: (x['hits']+x['baseOnBalls'])/(x['AB']+x['baseOnBalls']) if x['AB']+x['baseOnBalls']>0 else 0,axis=1)
        recent_df_copy['SLG'] = recent_df_copy.apply(lambda x: ((x['singles'])+2*(x['doubles'])+3*(x['triples'])+4*(x['HR']))/x['AB'] if x['AB']>0 else 0,axis=1)
        recent_df_copy['OPS'] = recent_df_copy['OBP'] + recent_df_copy['SLG']
        
        drop_cols = ['note', 'game_id', 'away_team', 'home_team', 'away_score', 'home_score', 'baseOnBalls', 'doubles', 'hits', 'playerId', 'rbi', 'runs', 'triples', 'singles']
        recent_df_copy = recent_df_copy.drop(drop_cols,axis = 1,errors = 'ignore')
        numeric_cols = recent_df_copy.select_dtypes(include=['float64', 'int64']).columns
        numeric_df = recent_df_copy[numeric_cols].astype(float)
        recent_df_float = pd.concat([recent_df_copy.drop(numeric_cols, axis=1), numeric_df], axis=1)
        recent_games = list(recent_df.index)

    return recent_df_float

def process_career_batter_data(player_id, games, recent_games, batter_stat_list, game_date): 
    
    # Get Seasons 
    games['season']=games['GameDate'].dt.year
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
        s1=seasons[1]
        s_list = [s0,s1] if season_game_count>15 else [s1]
        weights = [2/3,1/6] if season_game_count>15 else [1]        
    # Case #3: 3+ Years
    elif len(seasons)==3: 
        s1,s2 = seasons[1], seasons[2]
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
            s_df_copy = s_df.copy()
            s_df_copy['singles'] = s_df['hits']-s_df['doubles']-s_df['triples']-s_df['HR']
            s_df_copy['AVG'] = s_df.apply(lambda x: x['hits']/x['AB'] if x['AB']>0 else 0,axis=1)
            s_df_copy['OBP'] = s_df.apply(lambda x: (x['hits']+x['baseOnBalls'])/(x['AB']+x['baseOnBalls']) if x['AB']+x['baseOnBalls']>0 else 0,axis=1)
            s_df_copy['SLG'] = s_df_copy.apply(lambda x: ((x['singles'])+2*(x['doubles'])+3*(x['triples'])+4*(x['HR']))/x['AB'] if x['AB']>0 else 0,axis=1)
            s_df_copy['OPS'] = s_df_copy['OBP'] + s_df_copy['SLG']
            drop_cols = ['game_id', 'away_team', 'home_team', 'away_score', 'home_score', 'baseOnBalls', 'doubles', 'hits', 'playerId', 'rbi', 'runs', 'triples', 'singles', 'season']
            s_df_copy = s_df_copy.drop(drop_cols, errors = 'ignore', axis = 1)
            s_data = s_df_copy.mean(numeric_only=True).to_dict()
            all_s_data.append(s_data)
    
    career_data=pd.DataFrame(all_s_data).mul(weights,axis=0).sum().to_dict()
    df = pd.DataFrame([career_data], columns=career_data.keys())
    
    return career_data

def get_starter_df(player_id, year): 
    engine = database.connect_to_db()
    
    df = pd.read_sql(text(f"SELECT b.game_id, b.game_date, b.home_team, b.away_team, b.home_score, b.away_score, (a.atbats)atBats, "
            f"(a.baseonballs)baseonBalls, a.blownsaves, a.doubles, (a.earnedruns)earnedRuns, a.hits, a.holds, (a.homeruns)homeRuns, a.era, "
            f"(a.inningspitched)inningsPitched, a.losses, (a.pitchesthrown)pitchesThrown, (a.playerid)playerId, a.rbi, a.runs, (a.strikeouts)strikeOuts, "
            f"a.strikes, a.triples, a.whip, a.wins FROM pitcher_table a LEFT JOIN game_table b ON a.game_id = b.game_id WHERE a.playerid = '{player_id}' ORDER BY game_date;"), con = engine)

    print(player_id)
    
    string_cols = [col for col in df.columns if 'id' in col.lower()] + ['game_date', 'away_team', 'home_team']

    player_df = df.loc[:,:]

    player_df[string_cols] = df[string_cols].astype(str)
    non_string_cols = [col for col in df.columns if col not in string_cols]
    player_df[non_string_cols] = df[non_string_cols].astype(float)
    player_df['game_date'] = pd.to_datetime(df['game_date'])
    rename_dict = {'pitchesthrown': 'pitchesThrown', 'playerid': 'playerId', 'strikeouts': 'strikeOuts', 
            'baseonballs': 'baseOnBalls', 'homeruns': 'HR', 'atbats': 'atBats', 
            'inningspitched': 'inningsPitched', 'earnedruns': 'earnedRuns', 'era':'ERA', 'whip':'WHIP', 'game_date':'GameDate'
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
    
    player_df['GameDate'] = pd.to_datetime(player_df['GameDate'])
    games = player_df[player_df['GameDate'] < game_date]
    games = games.sort_values('GameDate')
    
    
    if len(games) == 0: 
        recent_games = []
        recent_data = dict(zip(pitcher_stat_list, np.repeat(0, len(pitcher_stat_list))))
        
    else: 
        
        if len(games) >= 5: 
            recent_df = games.tail(5)
            weights = [0.15,0.175,0.175,0.25,0.25]
            
        else: 
            recent_df = games
            weights = list(np.repeat(1/len(recent_df), len(recent_df)))

        drop_cols = ['note', 'game_id', 'away_team', 'home_team', 'away_score', 'home_score', 'playerId', 'blownsaves', 'doubles',  'holds',
                     'losses', 'pitchesThrown', 'rbi', 'runs', 'strikeOuts', 'strikes', 'triples', 'wins']
        
        recent_df = recent_df.drop(drop_cols,axis = 1,errors = 'ignore')
        recent_data = recent_df.sum().to_dict()
        recent_data['ERA'] = 9*recent_data['earnedRuns']/recent_data['inningsPitched'] if recent_data['inningsPitched']>0 else 0
        recent_data['WHIP'] = (recent_data['baseOnBalls']+recent_data['hits'])/recent_data['inningsPitched'] if recent_data['inningsPitched']>0 else 0
        recent_data['BattersFaced'] = recent_data['baseOnBalls'] + recent_data['atBats'] 
        recent_games = list(recent_df.index)
        print(recent_data)
    return recent_games, games, recent_data

def process_career_starter_data(player_id, games, recent_games, pitcher_stat_list, game_date): 
    
    # Get Seasons 
    games['season'] = games['GameDate'].dt.year
    seasons = sorted(set(games['season']))[-3:]
    
    if len(seasons)==0: 
        return {'HR': 0, 'ERA': 0, 'WHIP': 0, 'BattersFaced': 0}
    
    # Get Season Game Count 
    s0 = seasons[-1]
    season_game_count = len(games[games['season']==s0])
    games = games.drop(recent_games,axis=0)
    
    # Case #1: Rookie
    if len(seasons)==1: 
        s_list, weights = [s0], [2/3]
    # Case #2: 2nd Year
    elif len(seasons)==2: 
        s1=seasons[1]
        s_list = [s0,s1] if season_game_count>15 else [s1]
        weights = [2/3,1/6] if season_game_count>15 else [1]        
    # Case #3: 3+ Years
    elif len(seasons)==3: 
        s1,s2 = seasons[1], seasons[2]
        s_list = [s0,s1,s2] if season_game_count>15 else [s1,s2]
        weights = [2/3,1/6,1/6] if season_game_count>15 else [1/2,1/2]
    else: 
        return {'HR': 0, 'ERA': 0, 'WHIP': 0, 'BattersFaced': 0}

    all_s_data=[]
    for s in s_list: 
        s_df = games[games['season']==s]
        if len(s_df)==0: 
            s_data = dict(zip(pitcher_stat_list, np.repeat(0, len(pitcher_stat_list))))
            s_data['HR'] = 0
            s_data['ERA'] = 0
            s_data['WHIP'] = 0
            s_data['BattersFaced'] = 0
            all_s_data.append(s_data)
        else:
            s_df_copy = s_df.copy()
            s_df_copy['ERA'] = s_df.apply(lambda x: 9*x['earnedRuns']/x['inningsPitched'] if x['inningsPitched']>0 else 0,axis=1)
            s_df_copy['WHIP'] = s_df.apply(lambda x: (x['baseOnBalls']+x['hits'])/x['inningsPitched'] if x['inningsPitched']>0 else 0 ,axis=1)
            s_df_copy['BattersFaced'] = s_df_copy['baseOnBalls'] + s_df_copy['atBats']  
            s_data = s_df_copy.mean(numeric_only=True).to_dict()
            all_s_data.append(s_data)
                    
    career_df = pd.DataFrame(all_s_data)
    drop_cols = ['game_date', 'note', 'season','game_id', 'away_team', 'home_team', 'away_score', 'home_score', 'playerId', 'atBats', 'baseOnBalls', 'blownsaves', 'doubles', 'earnedRuns', 'hits', 'holds',
                    'inningsPitched', 'losses', 'pitchesThrown', 'rbi', 'runs', 'strikeOuts', 'strikes', 'triples', 'wins']
    career_df = career_df.drop(drop_cols,axis = 1,errors = 'ignore')
    career_data = career_df.mul(weights,axis=0).sum().to_dict()
    
    return career_data
