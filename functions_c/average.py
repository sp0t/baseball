from datetime import datetime
import numpy as np
import pandas as pd
from database import database
from sqlalchemy import text
from functions_c import batting_c, starters_c

def update_league_average(gamedate, state):
    print('gamedate=======================', gamedate)

    engine = database.connect_to_db()

    date_object = datetime.strptime(gamedate, '%Y/%m/%d')
    # Extract the year from the datetime object
    year = date_object.year
    batter_df = pd.read_sql(f"SELECT b.game_id, b.game_date, b.home_team, b.away_team, b.home_score, b.away_score, (a.atbats)atBats, a.avg, \
            (a.baseonballs)baseonBalls, a.doubles, a.hits, (a.homeruns)homeRuns, a.obp, a.ops, \
            (a.playerid)playerId, a.rbi, a.runs, a.slg, (a.strikeouts)strikeOuts, \
            a.triples FROM batter_table a LEFT JOIN game_table b ON a.game_id = b.game_id WHERE b.game_date LIKE '{year}%%' AND b.game_date < '{gamedate}';", con = engine).to_dict('records')

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
            a.strikes, a.triples, a.whip, a.wins FROM pitcher_table a LEFT JOIN game_table b ON a.game_id = b.game_id WHERE a.batter = '0' AND b.game_date LIKE '{year}%%' AND b.game_date < '{gamedate}';", con = engine).to_dict('records')
    
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
    df = batting_c.get_batter_df(team_batter, gamedate)

    if len(df) == 0:
        return 0, 0
    
    if len(df) < 70:
        return 0, 0
    
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
    return career_data['obp'], recent_data['obp']

def cal_pitcher_average(team_pitcher, gamedate):
  
    df = starters_c.get_starter_df(team_pitcher, gamedate)
    
    if len(df) == 0: 
        return 0, 0
    
    if len(df) < 23:
        return 0, 0
        
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
    return career_data['whip'], recent_data['whip']

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