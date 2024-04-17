input_team_name_1 = 'Minnesota Twins'
input_team_name_2 = 'Baltimore Orioles'
batter_name = ['Byron Buxton', 'Alex Kirilloff']
pitcher_name = ['Pablo Lopez']
game_id = '747049'


from datetime import date, time, datetime, timedelta
import numpy as np
import pandas as pd
import statsapi as mlb
from sqlalchemy import create_engine

# engine = create_engine('postgresql://postgres:123@localhost:5432/testdb', connect_args = {'connect_timeout': 10}, echo=False, pool_size=20, max_overflow=0)
engine = create_engine('postgresql://postgres:lucamlb123@ec2-13-230-35-170.ap-northeast-1.compute.amazonaws.com:5432/betmlb', connect_args = {'connect_timeout': 10}, echo=False, pool_size=20, max_overflow=0)
res = pd.read_sql(f"SELECT * FROM schedule WHERE away_name = '{input_team_name_1}' and home_name = '{input_team_name_2}'", con = engine).iloc[0]
game_id = res['game_id']


def get_batter_df(player_id): 
    
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
    
    print('----------------------Player Recent stats----------------------')
    print(recent_df_float)
        
    return recent_df_float, recent_games, games

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
    
    print('----------------------Career stats----------------------')
    print(df)
    
    return career_data

def get_starter_df(player_id): 
    
    df = pd.read_sql("SELECT b.game_id, b.game_date, b.home_team, b.away_team, b.home_score, b.away_score, (a.atbats)atBats, "
            "(a.baseonballs)baseonBalls, a.blownsaves, a.doubles, (a.earnedruns)earnedRuns, a.hits, a.holds, (a.homeruns)homeRuns, a.era, "
            "(a.inningspitched)inningsPitched, a.losses, (a.pitchesthrown)pitchesThrown, (a.playerid)playerId, a.rbi, a.runs, (a.strikeouts)strikeOuts, "
            "a.strikes, a.triples, a.whip, a.wins FROM pitcher_table a LEFT JOIN game_table b ON a.game_id = b.game_id WHERE a.playerid = '%s' ORDER BY game_date DESC;" %(player_id), con = engine)

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
        recent_data = dict(zip(pitcher_stat_list, np.repeat(np.nan, len(pitcher_stat_list))))
        
    else: 
        
        if len(games) >= 5: 
            recent_df = games.tail(5)
            weights = [0.15,.175,.175,.25,.25]
            
        else: 
            recent_df = games
            weights = list(np.repeat(1/len(recent_df), len(recent_df)))
         
        recent_df_copy = recent_df.copy()
        recent_df_copy['ERA'] = recent_df.apply(lambda x: 9*x['earnedRuns']/x['inningsPitched'] if x['inningsPitched']>0 else 0,axis=1)
        recent_df_copy['WHIP'] = recent_df.apply(lambda x: (x['baseOnBalls']+x['hits'])/x['inningsPitched'] if x['inningsPitched']>0 else 0 ,axis=1)
        recent_df_copy['BattersFaced'] = recent_df['baseOnBalls'] + recent_df['atBats'] 
        
        drop_cols = ['note', 'game_id', 'away_team', 'home_team', 'away_score', 'home_score', 'playerId', 'atBats', 'baseOnBalls', 'blownsaves', 'doubles', 'earnedRuns', 'hits', 'holds',
                    'inningsPitched', 'losses', 'pitchesThrown', 'rbi', 'runs', 'strikeOuts', 'strikes', 'triples', 'wins']
        
        recent_df_copy = recent_df_copy.drop(drop_cols,axis = 1,errors = 'ignore')
        numeric_cols = recent_df_copy.select_dtypes(include=['float64', 'int64']).columns
        numeric_df = recent_df_copy[numeric_cols].astype(float)
        recent_df_float = pd.concat([recent_df_copy.drop(numeric_cols, axis=1), numeric_df], axis=1)
        recent_games = list(recent_df.index)
     
    print('----------------------Player Recent stats----------------------')
    print(recent_df_float)
    return recent_df_float, recent_games, games

def process_career_starter_data(player_id, games, recent_games, pitcher_stat_list, game_date): 
    
    # Get Seasons 
    games['season'] = games['GameDate'].dt.year
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
    
    print('----------------------Career stats----------------------')
    df = pd.DataFrame([career_data], columns=career_data.keys())
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
            career_data = process_career_batter_data(player_id, games, recent_games, batter_stat_list, game_date)
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
    print(rosters)
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
        career_data = process_career_starter_data(player_id, games, recent_games, pitcher_stat_list, game_date)
    else: 
        recent_data = dict(zip(pitcher_stat_list, np.repeat(np.nan, len(pitcher_stat_list))))
        career_data = dict(zip(pitcher_stat_list, np.repeat(np.nan, len(pitcher_stat_list))))

    print('===================================================================')

