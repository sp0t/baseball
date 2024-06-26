# Dependencies
from datetime import datetime
import numpy as np
import pandas as pd
from database import database
from functions_c import average

def get_starter_df(player_id, gamedate, engine): 

    # engine = database.connect_to_db()

    df = pd.read_sql("SELECT b.game_id, b.game_date, b.home_team, b.away_team, b.home_score, b.away_score, (a.atbats)atBats, "
            "(a.baseonballs)baseonBalls, a.blownsaves, a.doubles, (a.earnedruns)earnedRuns, a.era, a.hits, a.holds, (a.homeruns)homeRuns, "
            "(a.inningspitched)inningsPitched, a.losses, (a.pitchesthrown)pitchesThrown, (a.playerid)playerId, a.rbi, a.runs, (a.strikeouts)strikeOuts, "
            "a.strikes, a.triples, a.whip, a.wins FROM pitcher_table a INNER JOIN game_table b ON a.game_id = b.game_id WHERE a.playerid = '%s' AND a.batter = '0' AND b.game_date < '%s';" %(player_id, gamedate), con = engine)

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

def process_recent_starter_data(player_df, game_date, team_batters, pitcher_stat_list, engine): 

    # engine = database.connect_to_db()
    
    player_df['game_date'] = pd.to_datetime(player_df['game_date'])
    games = player_df[player_df['game_date'] < game_date]
    games = games.sort_values('game_date')
    difficulty = []
    
    if len(games) == 0: 
        recent_difficulty_data = dict(zip(pitcher_stat_list, np.repeat(np.nan, len(pitcher_stat_list))))
        recent_difficulty_data['difficulty'] = 1
    else: 
        team_starter = games.iloc[0]['playerId']
        if len(games) >= 5: 
            recent_df = games.tail(5)
            weights = [0.15,.175,.175,.25,.25]
            
        else: 
            recent_df = games
            weights = list(np.repeat(1/len(recent_df), len(recent_df)))
        
        for index, row in recent_df.iterrows():
            team = pd.read_sql(f"SELECT * FROM pitcher_table WHERE game_id = '{row['game_id']}' AND playerid = '{row['playerId']}';", con=engine).to_dict('records')
            batters = pd.read_sql(f"SELECT * FROM batter_table WHERE game_id = '{row['game_id']}' AND team != '{team[0]['team']}' AND substitution = '0';", con=engine).to_dict('records')
            batter_difficulty = 0
            for batter in batters:
                date_str = str(row['game_date'])
                date_obj = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
                formatted_date = date_obj.strftime('%Y/%m/%d')
                average_obp, average_whip = average.update_league_average(formatted_date, False)
                career_obp, recent_obp = average.cal_batter_average(batter['playerid'], formatted_date, engine)
                if average_obp == 0 or career_obp == 0 or recent_obp == 0:
                    batter_difficulty = batter_difficulty + 8/8
                else:
                    value = average.switch_difficulty(career_obp/average_obp, recent_obp/career_obp)
                    batter_difficulty = batter_difficulty + value

            batter_difficulty = batter_difficulty / 9.0
            difficulty.append(batter_difficulty)

        difficulty_weights = np.array(weights) * np.array(difficulty)
        recent_df['era'] = recent_df.apply(lambda x: 9*x['earnedRuns']/x['inningsPitched'] if x['inningsPitched']>0 else 0,axis=1)
        recent_df['whip'] = recent_df.apply(lambda x: (x['baseOnBalls']+x['hits'])/x['inningsPitched'] if x['inningsPitched']>0 else 0 ,axis=1)

        drop_cols = ['game_date', 'note', 'game_id', 'away_team', 'home_team', 'away_score', 'home_score']
        recent_df = recent_df.drop(drop_cols,axis = 1,errors = 'ignore').astype(float)
        recent_difficulty_data = recent_df.mul(difficulty_weights,axis = 0).sum().to_dict()
        recent_difficulty_data['atBats'] = (recent_df['atBats'] * weights).sum()
        
        DifficultyRating = 0
        average_obp, average_whip = average.update_league_average(game_date, False)

        if team_batters == []:
            career_whip, recent_whip = average.cal_pitcher_average(team_starter, game_date, engine)
            if average_whip == 0 or career_whip == 0 or recent_whip == 0:
                DifficultyRating = 8/8
            else:
                DifficultyRating = average.switch_difficulty(average_whip/career_whip, career_whip/recent_whip)
        else:
            for el in team_batters:
                career_obp, recent_obp = average.cal_batter_average(el, game_date, engine)
                if average_obp == 0 or career_obp == 0 or recent_obp == 0:
                    DifficultyRating = DifficultyRating + 8/8
                else:
                    value = average.switch_difficulty(career_obp/average_obp, recent_obp/career_obp)
                    DifficultyRating = DifficultyRating + value
            
            DifficultyRating = DifficultyRating / 9.0


        recent_difficulty_data['difficulty'] = DifficultyRating
        recent_difficulty_data['playerId'] = team_starter
        
    return recent_difficulty_data, games

def process_career_starter_data(games, pitcher_stat_list): 
    
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

def process_starter_data(team_starter, team, game_date, team_batters, engine): 
    
    pitcher_stat_list=[
        'atBats', 'baseOnBalls', 'blownSave', 'doubles', 'earnedRuns', 'era', 'hits', 'holds', 'homeRuns', 'inningsPitched', 
        'losses', 'pitchesThrown', 'playerId', 'rbi', 'runs', 'strikeOuts', 'strikes', 'triples', 'whip',  'wins']
    
    
    player_df = get_starter_df(team_starter, game_date, engine)

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

def process_starter_data1(team_starters, team, game_date, team_batters, engine): 
    
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
        order = i + 1
        team_starter = team_starters[i]
        player_df = get_starter_df(team_starter, game_date, engine)

        if len(player_df) > 0 : 
            recent_data, games = process_recent_starter_data(player_df, game_date, team_batters, pitcher_stat_list)
            career_data = process_career_starter_data(games, pitcher_stat_list)
        else: 
            recent_data = dict(zip(pitcher_stat_list, np.repeat(0, len(pitcher_stat_list))))
            career_data = dict(zip(pitcher_stat_list, np.repeat(0, len(pitcher_stat_list))))

        recent_data = {f'{team}_starter_recent_{k}':v for k,v in recent_data.items()}
        career_data = {f'{team}_starter_career_{k}':v for k,v in career_data.items()}

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