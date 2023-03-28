away_team = 'Toronto Blue Jays'
home_team = 'Philadelphia Phillies'
batter_name = ['George Springer']
pitcher_name = ['Jose Berrios']
# game_id = '718949'

from datetime import date, time, datetime, timedelta
import numpy as np
import pandas as pd
import statsapi as mlb
from sqlalchemy import create_engine

# # engine = create_engine('postgresql://postgres:123@localhost:5432/testdb', connect_args = {'connect_timeout': 10}, echo=False, pool_size=20, max_overflow=0)
engine = create_engine('postgresql://postgres:lucamlb123@ec2-3-115-115-146.ap-northeast-1.compute.amazonaws.com:5432/betmlb', connect_args = {'connect_timeout': 10}, echo=False, pool_size=20, max_overflow=0)
res = pd.read_sql(f"SELECT * FROM schedule WHERE away_name = '{away_team}' and home_name = '{home_team}'", con = engine).iloc[0]
game_id = res['game_id']


def get_batter_df(team_batter): 
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

        recent_df_copy = recent_df.copy()
           
        recent_df_copy['singles'] = recent_df['hits']-recent_df['doubles']-recent_df['triples']-recent_df['homeRuns']
        recent_df_copy['avg'] = recent_df.apply(lambda x: x['hits']/x['atBats'] if x['atBats']>0 else 0,axis=1)
        recent_df_copy['obp'] = recent_df.apply(lambda x: (x['hits']+x['baseOnBalls'])/(x['atBats']+x['baseOnBalls']) if x['atBats']+x['baseOnBalls']>0 else 0,axis=1)
        recent_df_copy['slg'] = recent_df_copy.apply(lambda x: ((x['singles'])+2*(x['doubles'])+3*(x['triples'])+4*(x['homeRuns']))/x['atBats'] if x['atBats']>0 else 0,axis=1)
        recent_df_copy['ops'] = recent_df_copy['obp'] + recent_df_copy['slg']

        tmp_df = recent_df_copy.copy()
        
        drop_cols = ['game_date', 'note', 'game_id', 'away_team', 'home_team', 'away_score', 'home_score']
        drop_dispcols = ['note', 'game_id', 'away_team', 'home_team', 'away_score', 'home_score', 'baseOnBalls', 'doubles', 'hits', 'playerId', 'rbi', 'runs', 'triples', 'singles']
        disp_df = recent_df_copy.drop(drop_dispcols,axis = 1,errors = 'ignore')
        rename_dict = {'game_date': 'gameDate', 'atBats': 'AB', 'avg': 'AVG', 
            'homeRuns': 'HR', 'obp': 'OBP', 'ops': 'OPS', 
            'slg': 'SLG', 'strikeOuts': 'SO'
            }

        new_col_names = []

        for col in disp_df.columns: 
            for k,v in rename_dict.items(): 
                col = col.replace(k,v)
            new_col_names.append(col)
        disp_df.columns = new_col_names

        print('----------------------Player Recent stats----------------------')
        print(disp_df)

        tmp_df = tmp_df.drop(drop_cols,axis = 1,errors = 'ignore').astype(float)
        recent_data = tmp_df.mul(weights,axis = 0).sum().to_dict()
        recent_games = list(tmp_df.index)
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
            s_df_copy['singles'] = s_df['hits']-s_df['doubles']-s_df['triples']-s_df['homeRuns']
            s_df_copy['avg'] = s_df.apply(lambda x: x['hits']/x['atBats'] if x['atBats']>0 else 0,axis=1)
            s_df_copy['obp'] = s_df.apply(lambda x: (x['hits']+x['baseOnBalls'])/(x['atBats']+x['baseOnBalls']) if x['atBats']+x['baseOnBalls']>0 else 0,axis=1)
            s_df_copy['slg'] = s_df_copy.apply(lambda x: ((x['singles'])+2*(x['doubles'])+3*(x['triples'])+4*(x['homeRuns']))/x['atBats'] if x['atBats']>0 else 0,axis=1)
            s_df_copy['ops'] = s_df_copy['obp'] + s_df_copy['slg']
            s_df = s_df_copy.drop('game_id', errors = 'ignore', axis = 1)
            s_data = s_df.mean(numeric_only=True).to_dict()
            all_s_data.append(s_data)
    career_data=pd.DataFrame(all_s_data).mul(weights,axis=0).sum().to_dict()
    df = pd.DataFrame([career_data], columns=career_data.keys())

    drop_dispcols = ['game_id', 'away_score', 'home_score', 'baseOnBalls', 'doubles', 'hits', 'playerId', 'rbi', 'runs', 'triples', 'season', 'singles']
    disp_df = df.drop(drop_dispcols,axis = 1,errors = 'ignore')
    rename_dict = {'game_date': 'gameDate', 'atBats': 'AB', 'avg': 'AVG', 
        'homeRuns': 'HR', 'obp': 'OBP', 'ops': 'OPS', 
        'slg': 'SLG', 'strikeOuts': 'SO'
        }

    new_col_names = []

    for col in disp_df.columns: 
        for k,v in rename_dict.items(): 
            col = col.replace(k,v)
        new_col_names.append(col)
    disp_df.columns = new_col_names
    
    print('----------------------Career stats----------------------')
    print(disp_df)
    return career_data


def get_starter_df(player_id): 
    
    df = pd.read_sql("SELECT b.game_id, b.game_date, b.home_team, b.away_team, b.home_score, b.away_score, (a.atbats)atBats, "
            "(a.baseonballs)baseonBalls, a.blownsaves, a.doubles, (a.earnedruns)earnedRuns, a.era, a.hits, a.holds, (a.homeruns)homeRuns, "
            "(a.inningspitched)inningsPitched, a.losses, (a.pitchesthrown)pitchesThrown, (a.playerid)playerId, a.rbi, a.runs, (a.strikeouts)strikeOuts, "
            "a.strikes, a.triples, a.whip, a.wins FROM pitcher_table a LEFT JOIN game_table b ON a.game_id = b.game_id WHERE a.playerid = '%s';" %(player_id), con = engine)

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
            
        recent_df_copy = recent_df.copy()
        recent_df_copy['era'] = recent_df.apply(lambda x: 9*x['earnedRuns']/x['inningsPitched'] if x['inningsPitched']>0 else 0,axis=1)
        recent_df_copy['whip'] = recent_df.apply(lambda x: (x['baseOnBalls']+x['hits'])/x['inningsPitched'] if x['inningsPitched']>0 else 0 ,axis=1)
        recent_df_copy['BattersFaced'] = recent_df['baseOnBalls'] + recent_df['atBats']
        tmp_df = recent_df_copy.copy()
        
        dropdis_cols = ['note', 'game_id', 'away_team', 'home_team', 'away_score', 'home_score', 'strikeOuts', 'wins', 'atBats', 'baseOnBalls', 'blownsaves', 'doubles', 'earnedRuns', 'hits', 'holds', 'inningsPitched', 'losses', 'pitchesThrown', 'playerId', 'rbi', 'runs', 'strikes', 'triples']
        recent_df_copy = recent_df_copy.drop(dropdis_cols,axis = 1,errors = 'ignore')

        rename_dict = {'game_date':'GameDate', 'era':'ERA', 'homeRuns':'HR', 'whip':'WHIP'}

        new_col_names = []

        for col in recent_df_copy.columns: 
            for k,v in rename_dict.items(): 
                col = col.replace(k,v)
            new_col_names.append(col)
        recent_df_copy.columns = new_col_names
        
        print('----------------------Player Recent stats----------------------')
        print(recent_df_copy)


        drop_cols = ['game_date', 'note', 'game_id', 'away_team', 'home_team', 'away_score', 'home_score', 'BattersFaced']
        tmp_df = tmp_df.drop(drop_cols,axis = 1,errors = 'ignore').astype(float)
        recent_data = tmp_df.mul(weights,axis = 0).sum().to_dict()
        recent_games = list(tmp_df.index)
  
    return recent_data, recent_games, games

def process_career_starter_data(games, recent_games, pitcher_stat_list): 
    
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
        s1=seasons[1]
        s_list = [s0,s1] if season_game_count>15 else [s1]
        weights = [2/3,1/6] if season_game_count>15 else [1]        
    # Case #3: 3+ Years
    elif len(seasons)==3: 
        s1,s2 = seasons[1], seasons[2]
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
            s_df_copy = s_df.copy() 
            s_df_copy['era'] = s_df.apply(lambda x: 9*x['earnedRuns']/x['inningsPitched'] if x['inningsPitched']>0 else 0,axis=1)
            s_df_copy['whip'] = s_df.apply(lambda x: (x['baseOnBalls']+x['hits'])/x['inningsPitched'] if x['inningsPitched']>0 else 0 ,axis=1)
            s_df_copy['BattersFaced'] = s_df_copy['baseOnBalls'] + s_df_copy['atBats']  
            s_df_copy = s_df_copy.drop('game_id', errors = 'ignore', axis = 1)
            s_data = s_df_copy.mean(numeric_only=True).to_dict()
            all_s_data.append(s_data)
            
    career_df = pd.DataFrame(all_s_data)
    drop_cols = ['game_date', 'note', 'season','game_id', 'away_team', 'home_team', 'away_score', 'home_score']
    career_df = career_df.drop(drop_cols,axis = 1,errors = 'ignore')
    career_data = career_df.mul(weights,axis=0).sum().to_dict()
    
    print('----------------------Career stats----------------------')
    dropdisp_cols = ['note', 'game_id', 'away_team', 'home_team', 'away_score', 'home_score', 'strikeOuts', 'wins', 'atBats', 'baseOnBalls', 'blownsaves', 'doubles', 'earnedRuns', 'hits', 'holds', 'inningsPitched', 'losses', 'pitchesThrown', 'playerId', 'rbi', 'runs', 'strikes', 'triples']
    
    df = pd.DataFrame([career_data], columns=career_data.keys())
    df = df.drop(dropdisp_cols,axis = 1,errors = 'ignore')

    rename_dict = {'era':'ERA', 'homeRuns':'HR', 'whip':'WHIP'}

    new_col_names = []

    for col in df.columns: 
        for k,v in rename_dict.items(): 
            col = col.replace(k,v)
        new_col_names.append(col)
    df.columns = new_col_names
    print(df)
    
    return career_data


data = mlb.boxscore_data(game_id)

away_team_id = data['teamInfo']['away']['id']
home_team_id = data['teamInfo']['home']['id']
away_roster = mlb.get('team_roster', params = {'teamId':away_team_id,'date':date.today()})['roster']
away_roster = [el['person'] for el in away_roster]
away_roster = [{k:v for k,v in el.items() if k!='link'} for el in away_roster]
home_roster = mlb.get('team_roster', params = {'teamId':home_team_id,'date':date.today()})['roster']
home_roster = [el['person'] for el in home_roster]
home_roster = [{k:v for k,v in el.items() if k!='link'} for el in home_roster]  
rosters = home_roster + away_roster

print('###################################################################################')
print('####                              Batters Data                                 ####')
print('###################################################################################')
print('===================================================================')


for player_name in batter_name:
    print(player_name)
    print('===================================================================')
    player_id = [x['id'] for x in rosters if x['fullName'] == player_name][0]
 
    game_date = datetime.today()

    
    batter_stat_list = ['runs', 'doubles', 'triples', 'homeRuns', 'strikeOuts', 'baseOnBalls',
                     'hits', 'atBats', 'rbi', 'singles', 'avg', 'slg', 'obp', 'ops']
    
    player_df = get_batter_df(player_id)
    
    recent_data = {}
    career_data = {}
    
    if len(player_df) > 0 : 
            
            recent_data, recent_games, games = process_recent_batter_data(player_df, game_date, batter_stat_list)
            career_data = process_career_batter_data(games, recent_games, batter_stat_list)
    else: 
        recent_data = dict(zip(batter_stat_list, np.repeat(np.nan, len(batter_stat_list))))
        career_data = dict(zip(batter_stat_list, np.repeat(np.nan, len(batter_stat_list))))

    print('===================================================================')

print('###################################################################################')
print('####                              Pitchers Data                                ####')
print('###################################################################################')
print('===================================================================')

for player_name in pitcher_name:
    print(player_name)
    print('===================================================================')
    player_id = [x['id'] for x in rosters if x['fullName'] == player_name][0]

    game_date = datetime.today()
    
    pitcher_stat_list=[
        'runs', 'doubles', 'triples', 'homeRuns', 'strikeOuts', 'baseOnBalls', 'hits', 'atBats', 
        'stolenBases', 'inningsPitched', 'wins', 'losses', 'holds', 'blownSave',
        'pitchesThrown', 'strikes', 'rbi', 'era', 'whip', 'obp']
    
    
    player_df = get_starter_df(player_id)
    
    recent_data = {}
    career_data = {}
    
    if len(player_df) > 0 : 
        recent_data, recent_games, games = process_recent_starter_data(player_df, game_date, pitcher_stat_list)
        career_data = process_career_starter_data(games, recent_games, pitcher_stat_list)
    else: 
        recent_data = dict(zip(pitcher_stat_list, np.repeat(np.nan, len(pitcher_stat_list))))
        career_data = dict(zip(pitcher_stat_list, np.repeat(np.nan, len(pitcher_stat_list))))

    print('===================================================================')

