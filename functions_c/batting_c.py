# Dependencies
from datetime import datetime
import numpy as np
import pandas as pd
from database import database
from functions_c import average

def get_batter_df(team_batter, gamedate, engine): 

    # engine = database.connect_to_db()

    df = pd.read_sql("SELECT b.game_id, b.game_date, b.home_team, b.away_team, b.home_score, b.away_score, (a.atbats)atBats, a.avg, "
            "(a.baseonballs)baseonBalls, a.doubles, a.hits, (a.homeruns)homeRuns, a.obp, a.ops, "
            "(a.playerid)playerId, a.rbi, a.runs, a.slg, (a.strikeouts)strikeOuts, "
            "a.triples FROM batter_table a INNER JOIN game_table b ON a.game_id = b.game_id WHERE a.playerid = '%s' AND b.game_date < '%s';" %(team_batter, gamedate), con = engine)

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

def process_recent_batter_data(player_df, game_date, team_starter, batter_stat_list, engine): 

    # engine = database.connect_to_db()

    player_df['game_date'] = pd.to_datetime(player_df['game_date'])
    games = player_df[player_df['game_date'] < game_date]
    games = games.sort_values('game_date')
    difficulty = []

    if len(games) == 0: 
        recent_difficulty_data = dict(zip(batter_stat_list, np.repeat(np.nan, len(batter_stat_list))))
        recent_difficulty_data['difficulty'] = 8/8
        
    else: 
        team_batter = games.iloc[0]['playerId']
        if len(games) >= 15: 
            recent_df = games.tail(15)
            weights = [0.01,0.02,0.03,0.04,0.05,0.05,0.06,0.07,0.08,0.08,0.09,0.09,0.1,0.11,0.12]
            
        else:
            recent_df = games
            weights = list(np.repeat(1/int(len((recent_df))), int(len(recent_df))))
            
        for index, row in recent_df.iterrows():
            team = pd.read_sql(f"SELECT * FROM batter_table WHERE game_id = '{row['game_id']}' AND playerid = '{row['playerId']}';", con=engine).to_dict('records')
            pitcher = pd.read_sql(f"SELECT * FROM pitcher_table WHERE game_id = '{row['game_id']}' AND team != '{team[0]['team']}' AND role = 'starter';", con=engine).to_dict('records')

            date_str = str(row['game_date'])
            date_obj = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
            formatted_date = date_obj.strftime('%Y/%m/%d')
            average_obp, average_whip = average.update_league_average(formatted_date, False, engine)
            
            career_whip, recent_whip = average.cal_pitcher_average(pitcher[0]['playerid'], formatted_date, engine)
            if average_whip == 0 or career_whip == 0 or recent_whip == 0:
                difficulty.append(8/8)
            else:
                value = average.switch_difficulty(average_whip/career_whip, career_whip/recent_whip)
                difficulty.append(value)

        difficulty_weights = np.array(weights) * np.array(difficulty)
            
        recent_df['singles'] = recent_df['hits']-recent_df['doubles']-recent_df['triples']-recent_df['homeRuns']
        recent_df['avg'] = recent_df.apply(lambda x: x['hits']/x['atBats'] if x['atBats']>0 else 0,axis=1)
        recent_df['obp'] = recent_df.apply(lambda x: (x['hits']+x['baseOnBalls'])/(x['atBats']+x['baseOnBalls']) if x['atBats']+x['baseOnBalls']>0 else 0,axis=1)
        recent_df['slg'] = recent_df.apply(lambda x: ((x['singles'])+2*(x['doubles'])+3*(x['triples'])+4*(x['homeRuns']))/x['atBats'] if x['atBats']>0 else 0,axis=1)
        recent_df['ops'] = recent_df['obp'] + recent_df['slg']

        drop_cols = ['game_date', 'note', 'game_id', 'away_team', 'home_team', 'away_score', 'home_score']
        recent_df = recent_df.drop(drop_cols,axis = 1,errors = 'ignore').astype(float)
        recent_difficulty_data = recent_df.mul(difficulty_weights,axis = 0).sum().to_dict()
        recent_difficulty_data['atBats'] = (recent_df['atBats'] * weights).sum()

        average_obp, average_whip = average.update_league_average(game_date, False, engine)

        if team_starter == '':
            career_obp, recent_obp = average.cal_batter_average(team_batter, game_date, engine)
            if average_obp == 0 or career_obp == 0 or recent_obp == 0:
                DifficultyRating = 8/8
            else:
                DifficultyRating = average.switch_difficulty(career_obp/average_obp, recent_obp/career_obp)
        else:
            career_whip, recent_whip = average.cal_pitcher_average(team_starter, game_date, engine)
            if average_whip == 0 or career_whip == 0 or recent_whip == 0:
                DifficultyRating = 8/8
            else:
                DifficultyRating = average.switch_difficulty(average_whip/career_whip, career_whip/recent_whip)

        print('average_obp')
        print(average_obp)
        print('career_obp')
        print(career_obp)
        print('recent_obp')
        print(recent_obp)

        recent_difficulty_data['difficulty'] = DifficultyRating
        recent_difficulty_data['playerId'] = team_batter

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
        sub_df2 = last_40.iloc[-134:-67]  
        sub_df3 = last_40.iloc[-67:]
        s_list = [sub_df3,sub_df2,sub_df1]
        weights = [2/3,1/6,1/6]
    all_s_data=[]
    for s_df in s_list: 
        drop_cols = ['game_date', 'note', 'season','game_id', 'away_team', 'home_team', 'away_score', 'home_score', 'playerId']
        s_df = s_df.drop(drop_cols, errors = 'ignore', axis = 1)
        length = len(s_df)
        s_df['singles'] = s_df['hits']-s_df['doubles']-s_df['triples']-s_df['homeRuns']
        s_df = s_df.sum()
        s_df['avg'] = s_df['hits']/s_df['atBats'] if s_df['atBats']>0 else 0
        s_df['obp'] = (s_df['hits']+s_df['baseOnBalls'])/(s_df['atBats']+s_df['baseOnBalls']) if (s_df['atBats']+s_df['baseOnBalls'])>0 else 0
        s_df['slg'] = ((s_df['singles'])+2*(s_df['doubles'])+3*(s_df['triples'])+4*(s_df['homeRuns']))/s_df['atBats'] if s_df['atBats']>0 else 0
        s_df['ops'] = s_df['obp'] + s_df['slg']
        exclude_columns = ['avg', 'obp', 'slg', 'ops']
        for col in s_df.keys():
            if col not in exclude_columns:
                s_df[col] /= length
        s_data = s_df.to_dict()
        all_s_data.append(s_data)
    career_data=pd.DataFrame(all_s_data).mul(weights,axis=0).sum().to_dict()

    return career_data

def process_team_batter_data(team_batters, team, game_date, engine): 
    
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
        player_df = get_batter_df(team_batter, engine)

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